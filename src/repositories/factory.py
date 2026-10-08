"""LOCKED: re-exports only. Do not edit without telling the other person (handoff rule 3).

Person A's builders live in factory_a.py, Person B's in factory_b.py, so the two of
you never touch the same file. views/session.py calls these."""
from repositories.factory_a import build_auth_gateway, build_user_repository
from repositories.factory_b import (
    build_listing_repository,
    build_review_repository,
    build_transaction_repository,
)

__all__ = [
    "build_auth_gateway",
    "build_listing_repository",
    "build_review_repository",
    "build_transaction_repository",
    "build_user_repository",
]
