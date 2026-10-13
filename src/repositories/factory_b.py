"""PERSON B's half of the repository factory: listings, transactions, reviews.

Each build_* takes the per-session Supabase client and returns the Supabase-backed
repository the app uses. Only Person B edits this file. No Streamlit.

`in_memory = False` on a Supabase-backed class tells views/session.py to drop it on
logout (it is tied to one user's client)."""
from repositories.supabase_listing_repository import SupabaseListingRepository
from repositories.supabase_review_repository import SupabaseReviewRepository
from repositories.supabase_transaction_repository import SupabaseTransactionRepository


def build_listing_repository(client) -> SupabaseListingRepository:
    return SupabaseListingRepository(client)


def build_transaction_repository(client) -> SupabaseTransactionRepository:
    return SupabaseTransactionRepository(client)


def build_review_repository(client) -> SupabaseReviewRepository:
    return SupabaseReviewRepository(client)
