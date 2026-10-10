"""Supabase-backed listing storage (B2). Same method names as ListingRepository.
No Streamlit: the per-session client is passed in.

Notes
- Owner emails are mapped to profile uuids by querying `profiles` here (never via
  Person A's code). `profiles` is readable only by signed-in users, so the client
  must carry the user's token.
- Images live in the public `listing-images` bucket at <owner uuid>/<random>.<ext>;
  `listing_images` keeps (listing_id, position, storage_path). Listing.images holds
  the public URLs.
- client.table(...) / client.storage are looked up fresh on every use (supabase-py
  resets them on sign-in and token refresh).
- Adding or saving a listing is two writes (listing row, then image rows). It is not
  one database transaction; on a failure the code cleans up what it can.
"""
import uuid

from postgrest.exceptions import APIError

from models.listing import ALLOWED_MIMES, MAX_IMAGES, Listing, ListingStatus
from repositories import storage
from repositories.errors import NotFoundError, RepositoryError

BUCKET = "listing-images"
_EXT = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
_SELECT_LIGHT = "*, profiles(email), listing_images(position, storage_path)"


class SupabaseListingRepository:
    in_memory = False      # session.end_session() drops repositories tied to a client

    def __init__(self, client) -> None:
        self._client = client

    # ------------------------------------------------------------ helpers
    def _fail(self, exc: Exception) -> RepositoryError:
        err = RepositoryError()
        err.__cause__ = exc
        return err

    def _owner_id(self, email: str) -> str:
        email = (email or "").strip().lower()
        try:
            rows = (self._client.table("profiles").select("id")
                    .eq("email", email).limit(1).execute().data)
        except APIError as exc:
            raise self._fail(exc)
        if not rows:
            raise NotFoundError("That account could not be found.")
        return rows[0]["id"]

    def _url(self, path: str) -> str:
        return storage.public_url(self._client, BUCKET, path)

    def _path_of(self, url: str) -> str:
        """Storage path from a public URL we produced (inverse of _url)."""
        marker = f"/{BUCKET}/"
        return url.split(marker, 1)[1] if marker in url else url

    def _to_listing(self, row: dict, first_image_only: bool = False) -> Listing:
        images = sorted(row.get("listing_images") or [], key=lambda r: r["position"])
        if first_image_only:
            images = images[:1]
        return Listing(
            id=int(row["id"]),
            owner_email=row["profiles"]["email"],
            title=row["title"],
            price=float(row["price"]),
            category=row["category"],
            deliverable=row["deliverable"],
            unit=row["unit"],
            description=row["description"],
            images=[self._url(r["storage_path"]) for r in images],
            status=ListingStatus(row["status"]),
        )

    # ------------------------------------------------------------ reads
    def get_all(self) -> list[Listing]:
        """Every listing, newest first. Lightweight: first image only."""
        try:
            rows = (self._client.table("listings").select(_SELECT_LIGHT)
                    .eq("listing_images.position", 0)
                    .order("created_at", desc=True).order("id", desc=True)
                    .execute().data)
        except APIError as exc:
            raise self._fail(exc)
        return [self._to_listing(r, first_image_only=True) for r in rows]

    def get_by_owner(self, owner_email: str) -> list[Listing]:
        owner_id = self._owner_id(owner_email)
        try:
            rows = (self._client.table("listings").select(_SELECT_LIGHT)
                    .eq("owner_id", owner_id)
                    .order("created_at", desc=True).order("id", desc=True)
                    .execute().data)
        except APIError as exc:
            raise self._fail(exc)
        return [self._to_listing(r) for r in rows]

    def get(self, listing_id: int) -> Listing | None:
        """One listing with ALL its images (gallery and edit form need them)."""
        try:
            rows = (self._client.table("listings").select(_SELECT_LIGHT)
                    .eq("id", listing_id).limit(1).execute().data)
        except APIError as exc:
            raise self._fail(exc)
        return self._to_listing(rows[0]) if rows else None

    # ------------------------------------------------------------ images
    def store_images(self, owner_email: str, images: list[tuple[bytes, str]]) -> list[str]:
        """Upload already-compressed (bytes, mime) images; returns their public URLs."""
        images = images[:MAX_IMAGES]
        if not images:
            return []
        owner_id = self._owner_id(owner_email)
        done: list[str] = []
        try:
            for data, mime in images:
                mime = mime if mime in ALLOWED_MIMES else "image/jpeg"
                path = f"{owner_id}/{uuid.uuid4().hex}.{_EXT[mime]}"
                done.append(storage.upload(self._client, BUCKET, path, data, mime))
        except RepositoryError:
            self._discard(done)
            raise
        return [self._url(p) for p in done]

    def _discard(self, paths: list[str]) -> None:
        try:
            storage.remove(self._client, BUCKET, paths)
        except RepositoryError:
            pass                       # best effort: an orphan file is harmless

    def _write_image_rows(self, listing_id: int, urls: list[str]) -> None:
        self._client.table("listing_images").delete().eq("listing_id", listing_id).execute()
        rows = [{"listing_id": listing_id, "position": i, "storage_path": self._path_of(u)}
                for i, u in enumerate(urls[:MAX_IMAGES])]
        if rows:
            self._client.table("listing_images").insert(rows).execute()

    # ------------------------------------------------------------ writes
    def add(self, listing: Listing) -> Listing:
        """Insert a listing. The database assigns the id, which is set on the result."""
        owner_id = self._owner_id(listing.owner_email)
        try:
            row = (self._client.table("listings").insert({
                "owner_id": owner_id,
                "title": listing.title,
                "price": round(float(listing.price), 2),
                "category": listing.category,
                "deliverable": listing.deliverable,
                "unit": listing.unit,
                "description": listing.description,
                "status": listing.status.value,
            }).execute().data[0])
            listing.id = int(row["id"])
            self._write_image_rows(listing.id, listing.images)
        except APIError as exc:
            self._discard([self._path_of(u) for u in listing.images])
            raise self._fail(exc)
        return listing

    def save(self, listing: Listing) -> None:
        """Persist changes to an existing listing (fields and the image list)."""
        try:
            before = self.get(listing.id)
            if before is None:
                raise NotFoundError("This listing no longer exists.")
            self._client.table("listings").update({
                "title": listing.title,
                "price": round(float(listing.price), 2),
                "unit": listing.unit,
                "description": listing.description,
                "status": listing.status.value,
            }).eq("id", listing.id).execute()
            self._write_image_rows(listing.id, listing.images)
        except APIError as exc:
            raise self._fail(exc)
        dropped = set(before.images) - set(listing.images)
        self._discard([self._path_of(u) for u in dropped])

    def delete(self, listing_id: int) -> bool:
        try:
            before = self.get(listing_id)
            if before is None:
                return False
            gone = (self._client.table("listings").delete()
                    .eq("id", listing_id).execute().data)
        except APIError as exc:
            raise self._fail(exc)
        if gone:
            self._discard([self._path_of(u) for u in before.images])
        return bool(gone)

    def delete_by_owner(self, owner_email: str) -> int:
        """No-op here: deleting the user cascades to their listings (foreign key).
        Kept only because AuthController.delete_account still calls it; removed in
        the final PR."""
        return 0
