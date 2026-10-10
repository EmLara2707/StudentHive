"""Supabase-backed review storage (B4). Same method names as ReviewRepository, plus
has_reviewed(). No Streamlit: the per-session client is passed in.

Notes
- Reviews are created ONLY through the submit_review() database function (there is no
  insert policy). It checks that the transaction is Completed and that the caller took
  part in it, then inserts. unique(transaction_id, reviewer_id) stops a double submit.
- Emails <-> uuids: `profiles` is queried here (never via Person A's code). The
  signed-in user's client is required (profiles are readable only by members).
- reviews has TWO foreign keys to profiles (reviewer_id, subject_id), so the embedded
  select names its key: profiles!reviewer_id(email, name).
- The reviewer's name comes from that join. Seeded sample reviews have no reviewer
  account (reviewer_id is NULL) and keep their text in reviewer_name instead.
- Not cached: client.table(...) is looked up fresh on every use.
- delete_for_user / delete_by_reviewer do nothing and return 0: deleting a profile
  cascades to its reviews (written and received), and there is no DELETE policy.
"""
from postgrest.exceptions import APIError

from models.review import Review
from repositories.errors import ConflictError, NotFoundError, RepositoryError

_SELECT = "*, reviewer:profiles!reviewer_id(email, name)"
# submit_review raises a plain exception (P0001) when the checks fail; a double submit
# hits the unique constraint (23505).
_CONFLICT_CODES = {"P0001", "23505"}


class SupabaseReviewRepository:
    in_memory = False      # session.end_session() drops repositories tied to a client

    def __init__(self, client) -> None:
        self._client = client

    # ------------------------------------------------------------ helpers
    def _fail(self, exc: Exception) -> RepositoryError:
        err = RepositoryError()
        err.__cause__ = exc
        return err

    def _uid(self, email: str) -> str:
        email = (email or "").strip().lower()
        try:
            rows = (self._client.table("profiles").select("id")
                    .eq("email", email).limit(1).execute().data)
        except APIError as exc:
            raise self._fail(exc)
        if not rows:
            raise NotFoundError("That account could not be found.")
        return rows[0]["id"]

    # ------------------------------------------------------------ reads
    def get_for_user(self, email: str) -> list[Review]:
        """Every review written about the user, oldest first."""
        email = (email or "").strip().lower()
        uid = self._uid(email)
        try:
            rows = (self._client.table("reviews").select(_SELECT)
                    .eq("subject_id", uid).order("id").execute().data)
        except APIError as exc:
            raise self._fail(exc)
        reviews = []
        for row in rows:
            reviewer = row.get("reviewer") or {}
            reviews.append(Review(
                reviewer=reviewer.get("name") or row.get("reviewer_name") or "Student",
                subject_email=email,
                rating=float(row["rating"]),
                text=row.get("text") or "",
                reviewer_email=reviewer.get("email") or "",
                transaction_id=row.get("transaction_id"),
            ))
        return reviews

    def has_reviewed(self, transaction_id: int, email: str) -> bool:
        uid = self._uid(email)
        try:
            rows = (self._client.table("reviews").select("id")
                    .eq("transaction_id", transaction_id).eq("reviewer_id", uid)
                    .limit(1).execute().data)
        except APIError as exc:
            raise self._fail(exc)
        return bool(rows)

    # ------------------------------------------------------------ writes
    def add(self, review: Review) -> None:
        if review.transaction_id is None:
            raise RepositoryError("A review must belong to a transaction.")
        try:
            self._client.rpc("submit_review", {
                "p_transaction_id": review.transaction_id,
                "p_rating": int(review.rating),
                "p_text": review.text,
            }).execute()
        except APIError as exc:
            if getattr(exc, "code", None) in _CONFLICT_CODES:
                conflict = ConflictError()
                conflict.__cause__ = exc
                raise conflict
            raise self._fail(exc)

    def delete_for_user(self, email: str) -> int:
        return 0       # the foreign-key cascade removes them when the profile is deleted

    def delete_by_reviewer(self, email: str) -> int:
        return 0       # same: cascade
