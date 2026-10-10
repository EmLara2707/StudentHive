"""PERSON B's half of the repository factory: listings, transactions, reviews.

Each build_* takes the per-session Supabase client (or None when no Supabase is
configured) and returns the repository the app should use. While a flag below is
False, the app keeps using the in-memory seeded repository, which is the fallback
until the final step. Only Person B edits this file. No Streamlit.

Convention for Supabase-backed repositories: set `in_memory = False` on the class.
views/session.py uses it so a logout drops a repository that is tied to one user's
client but keeps the in-memory "database".
"""
from repositories.listing_repository import ListingRepository
from repositories.supabase_listing_repository import SupabaseListingRepository
from repositories.review_repository import ReviewRepository
from repositories.transaction_repository import TransactionRepository

# Flip each to True once its Supabase repository is ready.
USE_SUPABASE_LISTINGS = True
USE_SUPABASE_TRANSACTIONS = False
USE_SUPABASE_REVIEWS = False


def build_listing_repository(client) -> ListingRepository | SupabaseListingRepository:
    if USE_SUPABASE_LISTINGS and client is not None:
        return SupabaseListingRepository(client)
    return ListingRepository.seeded()


def build_transaction_repository(client) -> TransactionRepository:
    if USE_SUPABASE_TRANSACTIONS:
        # B3: return SupabaseTransactionRepository(client)
        raise NotImplementedError("SupabaseTransactionRepository is not written yet (B3).")
    return TransactionRepository.seeded()


def build_review_repository(client) -> ReviewRepository:
    if USE_SUPABASE_REVIEWS:
        # B4: return SupabaseReviewRepository(client)
        raise NotImplementedError("SupabaseReviewRepository is not written yet (B4).")
    return ReviewRepository.seeded()
