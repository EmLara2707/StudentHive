"""Supabase-backed transaction storage (B3). Same method names as
TransactionRepository, except save() also takes the status that was read.
No Streamlit: the per-session client is passed in.

Notes
- Lifecycle rules (accept, reject, withdraw, complete, cancel) stay in the Transaction
  model. The database only guards invariants (constraints, the unique index).
- Emails <-> uuids: `profiles` is queried here (never via Person A's code). The
  signed-in user's client is required, because profiles/transactions are readable only
  by signed-in members (RLS).
- transactions has THREE foreign keys to profiles (provider_id, requester_id,
  cancelled_by), so every embedded select names its key: profiles!provider_id(email).
- Transaction.image: a listing-image URL is stored as its Storage path in image_path;
  the placeholder is stored as NULL. Both are turned back into URLs on read.
- Not cached: client.table(...) is looked up fresh on every use (supabase-py resets
  handles on sign-in and token refresh).
- Reviews are B4: Transaction.reviewed_by is NOT stored here (it comes back empty).
"""
from datetime import date, time

from postgrest.exceptions import APIError

from models.transaction import (
    PLACEHOLDER_IMAGE, Transaction, TransactionKind, TransactionStatus,
)
from repositories import storage
from repositories.errors import ConflictError, NotFoundError, RepositoryError
from utils.clock import now_manila

LISTING_BUCKET = "listing-images"
DUPLICATE_INDEX = "transactions_no_duplicate_request"
DUPLICATE_MESSAGE = "You've already sent this request."
_SELECT = ("*, provider:profiles!provider_id(email), "
           "requester:profiles!requester_id(email), "
           "canceller:profiles!cancelled_by(email)")


def _t(value: str | None) -> time | None:
    return time.fromisoformat(value) if value else None


def _d(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


class SupabaseTransactionRepository:
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

    def _image_path(self, image: str) -> str | None:
        marker = f"/{LISTING_BUCKET}/"
        return image.split(marker, 1)[1] if marker in (image or "") else None

    def _image_url(self, path: str | None) -> str:
        return storage.public_url(self._client, LISTING_BUCKET, path) if path else PLACEHOLDER_IMAGE

    def _to_transaction(self, row: dict) -> Transaction:
        canceller = row.get("canceller")
        return Transaction(
            id=int(row["id"]),
            kind=TransactionKind(row["kind"]),
            item=row["item"],
            image=self._image_url(row.get("image_path")),
            provider_email=row["provider"]["email"],
            requester_email=row["requester"]["email"],
            start=_d(row["start_date"]),
            end=_d(row["end_date"]),
            price=float(row["price"]),
            unit=row["unit"],
            quantity=float(row["quantity"]),
            total=float(row["total"]),
            status=TransactionStatus(row["status"]),
            cancelled_by=canceller["email"] if canceller else None,
            listing_id=row.get("listing_id"),
            start_time=_t(row.get("start_time")),
            end_time=_t(row.get("end_time")),
            meeting_mode=row.get("meeting_mode"),
            location=row.get("location") or "",
            project_details=row.get("project_details") or "",
            deadline=_d(row.get("deadline")),
        )

    # ------------------------------------------------------------ reads
    def get(self, transaction_id: int) -> Transaction | None:
        try:
            rows = (self._client.table("transactions").select(_SELECT)
                    .eq("id", transaction_id).limit(1).execute().data)
        except APIError as exc:
            raise self._fail(exc)
        return self._to_transaction(rows[0]) if rows else None

    def get_for_user(self, email: str, kind: TransactionKind | None = None) -> list[Transaction]:
        """Every transaction the user is part of, oldest id first."""
        uid = self._uid(email)
        try:
            query = (self._client.table("transactions").select(_SELECT)
                     .or_(f"provider_id.eq.{uid},requester_id.eq.{uid}"))
            if kind is not None:
                query = query.eq("kind", kind.value)
            rows = query.order("id").execute().data
        except APIError as exc:
            raise self._fail(exc)
        return [self._to_transaction(r) for r in rows]

    # ------------------------------------------------------------ writes
    def add(self, transaction: Transaction) -> Transaction:
        """Insert a new (Pending) request. The database assigns the id, which is set on
        the result. An identical open request raises ConflictError (unique index)."""
        provider_id = self._uid(transaction.provider_email)
        requester_id = self._uid(transaction.requester_email)
        payload = {
            "kind": transaction.kind.value,
            "listing_id": transaction.listing_id,
            "item": transaction.item,
            "image_path": self._image_path(transaction.image),
            "provider_id": provider_id,
            "requester_id": requester_id,
            "start_date": transaction.start.isoformat(),
            "end_date": transaction.end.isoformat(),
            "start_time": transaction.start_time.isoformat() if transaction.start_time else None,
            "end_time": transaction.end_time.isoformat() if transaction.end_time else None,
            "price": round(float(transaction.price), 2),
            "unit": transaction.unit,
            "quantity": round(float(transaction.quantity), 2),
            "total": round(float(transaction.total), 2),
            "status": TransactionStatus.PENDING.value,
            "meeting_mode": transaction.meeting_mode,
            "location": transaction.location,
            "project_details": transaction.project_details,
            "deadline": transaction.deadline.isoformat() if transaction.deadline else None,
        }
        try:
            row = self._client.table("transactions").insert(payload).execute().data[0]
        except APIError as exc:
            if exc.code == "23505" and DUPLICATE_INDEX in (exc.message or ""):
                raise ConflictError(DUPLICATE_MESSAGE) from exc
            raise self._fail(exc)
        transaction.id = int(row["id"])
        return transaction

    def save(self, transaction: Transaction, expected_status: TransactionStatus) -> None:
        """Persist a lifecycle change. The row is updated only if it still has the status
        that was read; otherwise nothing is written and ConflictError is raised (someone
        else answered first)."""
        cancelled_by = (self._uid(transaction.cancelled_by)
                        if transaction.cancelled_by else None)
        try:
            changed = (self._client.table("transactions").update({
                "status": transaction.status.value,
                "cancelled_by": cancelled_by,
                "updated_at": now_manila().isoformat(),
            }).eq("id", transaction.id).eq("status", expected_status.value)
                .execute().data)
        except APIError as exc:
            raise self._fail(exc)
        if not changed:
            raise ConflictError()

    def delete_for_user(self, email: str) -> int:
        """No-op here: deleting the user cascades to their transactions (foreign key).
        Kept only because AuthController.delete_account still calls it; removed in the
        final PR."""
        return 0
