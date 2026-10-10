"""A4: users on Supabase (the `profiles` table). Same method names as the in-memory
UserRepository, so controllers do not change.

Rules (handoff + Phase 0):
  * No Streamlit import.
  * Models still use emails as identifiers; the uuid stays inside this file.
  * Fresh objects every call. Nothing is cached, and no client.table(...) / storage
    handle is kept between calls (signing in resets them).
  * Failures raise RepositoryError (student-safe message), never raw Supabase errors.
  * Passwords live in Supabase Auth, so User.password_hash is always "" here.
"""
import time

from models.profile import IdVerificationStatus, Profile
from models.user import User
from repositories import storage
from repositories.errors import RepositoryError

AVATAR_BUCKET = "avatars"
_ALLOWED_MIME = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


class SupabaseUserRepository:
    in_memory = False       # views/session.py drops this on logout (tied to one client)

    def __init__(self, client) -> None:
        self._client = client

    @staticmethod
    def _key(email: str) -> str:
        return (email or "").strip().lower()

    # ---- row <-> model ----
    def _to_user(self, row: dict) -> User:
        photo_url = None
        if row.get("photo_path"):
            photo_url = storage.public_url(self._client, AVATAR_BUCKET, row["photo_path"])
        return User(
            name=row["name"],
            email=row["email"],
            password_hash="",
            onboarded=bool(row.get("onboarded")),
            profile=Profile(
                major=row.get("major") or "",
                bio=row.get("bio") or "",
                skills=list(row.get("skills") or []),
                portfolio=row.get("portfolio") or "",
                linkedin=row.get("linkedin") or "",
                github=row.get("github") or "",
                socials=list(row.get("socials") or []),
                id_status=IdVerificationStatus(row.get("id_status") or "not_submitted"),
                photo_url=photo_url,
                photo_mime=row.get("photo_mime"),
            ),
        )

    @staticmethod
    def _to_row(user: User) -> dict:
        """Columns save() writes. Photo columns are NOT here: only set_photo changes them."""
        p = user.profile
        return {
            "name": user.name,
            "onboarded": user.onboarded,
            "major": p.major,
            "bio": p.bio,
            "skills": list(p.skills),
            "portfolio": p.portfolio,
            "linkedin": p.linkedin,
            "github": p.github,
            "socials": list(p.socials),
            "id_status": IdVerificationStatus(p.id_status).value,
        }

    # ---- reads ----
    def get_by_email(self, email: str) -> User | None:
        try:
            rows = (self._client.table("profiles").select("*")
                    .eq("email", self._key(email)).limit(1).execute().data)
        except Exception as exc:
            raise RepositoryError() from exc
        return self._to_user(rows[0]) if rows else None

    def get_many(self, emails) -> "dict[str, User]":
        """{lower-cased email: User} in one query. Unknown emails are missing."""
        keys = sorted({self._key(e) for e in emails if self._key(e)})
        if not keys:
            return {}
        try:
            rows = (self._client.table("profiles").select("*")
                    .in_("email", keys).execute().data)
        except Exception as exc:
            raise RepositoryError() from exc
        return {row["email"]: self._to_user(row) for row in rows}

    def exists(self, email: str) -> bool:
        """Works before anyone is signed in (the sign-up form): it calls the
        email_registered() function from migration 001, which returns only true/false."""
        try:
            result = self._client.rpc("email_registered", {"p_email": self._key(email)}).execute()
        except Exception as exc:
            raise RepositoryError() from exc
        return bool(result.data)

    # ---- writes ----
    def save(self, user: User) -> None:
        """Update the signed-in user's profile row. Raises if no row matched."""
        try:
            rows = (self._client.table("profiles").update(self._to_row(user))
                    .eq("email", self._key(user.email)).execute().data)
        except Exception as exc:
            raise RepositoryError() from exc
        if not rows:
            raise RepositoryError()     # not found, or not allowed (row-level security)

    def add(self, user: User) -> None:
        """The signup trigger already created the row, so adding is an update."""
        self.save(user)

    def delete(self, email: str) -> bool:
        """Accounts are deleted through the auth gateway (admin_delete_user); the
        foreign keys then remove the profile. Nothing should call this."""
        raise RepositoryError("Accounts are deleted through the auth gateway.")

    def set_photo(self, email: str, data: bytes, mime: str) -> bool:
        """Upload the (already compressed) photo to the avatars bucket and point the
        profile at it. A new file name per upload, so browsers never show a stale
        picture; the previous file is removed afterwards (best effort)."""
        ext = _ALLOWED_MIME.get(mime)
        if ext is None:
            raise RepositoryError("Please choose a JPG, PNG or WebP image.")
        try:
            rows = (self._client.table("profiles").select("id, photo_path")
                    .eq("email", self._key(email)).limit(1).execute().data)
        except Exception as exc:
            raise RepositoryError() from exc
        if not rows:
            return False
        user_id, old_path = rows[0]["id"], rows[0].get("photo_path")

        path = f"{user_id}/avatar-{int(time.time())}.{ext}"
        storage.upload(self._client, AVATAR_BUCKET, path, data, mime)   # RepositoryError on failure
        try:
            updated = (self._client.table("profiles")
                       .update({"photo_path": path, "photo_mime": mime})
                       .eq("id", user_id).execute().data)
        except Exception as exc:
            self._remove_quietly([path])            # don't leave an orphan upload
            raise RepositoryError() from exc
        if not updated:
            self._remove_quietly([path])
            raise RepositoryError()
        if old_path and old_path != path:
            self._remove_quietly([old_path])
        return True

    def _remove_quietly(self, paths: list[str]) -> None:
        try:
            storage.remove(self._client, AVATAR_BUCKET, paths)
        except RepositoryError:
            pass
