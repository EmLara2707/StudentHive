"""B6: DEV / STAGING ONLY. Fills Supabase with the sample marketplace: listings,
transactions and reviews, the same ones the in-memory app ships.

    python scripts/seed_users.py      # FIRST: creates the demo account and 12 students
    python scripts/seed_market.py     # asks you to confirm the project first
    python scripts/seed_market.py --yes   # no question (scripts, CI)

Why this exists: with the Supabase repositories switched on, the demo user's Dashboard,
Gigs, Rentals and the Marketplace would otherwise be empty. This recreates the sample
history so a fresh dev project looks like the in-memory demo.

It reads the sample data from the in-memory repositories (ListingRepository.seeded,
TransactionRepository.seeded, ReviewRepository.seeded), so the two can never drift apart.

What it creates
  * 15 listings: the demo user's 8 and the 7 marketplace samples from Ana R. They are
    inserted one at a time, oldest first, so the marketplace shows them in the same order
    as the in-memory app (newest first).
  * 26 transactions between the demo user and the sample students, dated relative to
    TODAY (Asia/Manila) in every status (Pending, Active, Completed, Cancelled).
  * the sample reviews (two per person). They have no reviewer account: the reviewer_id
    is NULL and the name ("Student A") sits in reviewer_name, as the schema intends.

Safe to run again: anything that already exists is skipped, not duplicated (a listing is
matched by owner + title, a transaction by provider + requester + item, a sample review
by subject + reviewer name + text). To start over, delete the rows (or the profiles; the
foreign keys cascade) and run it again. Transaction dates are not refreshed on a re-run.

It uses the ADMIN (service-role) key, which bypasses row level security. That is the only
way to write rows for other people, and why this must never run against production.
Credentials come from src/.streamlit/secrets.toml (the same file the app uses), or from
the SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables. Keep the key out of git
and out of chat.
"""
import argparse
import os
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


# ------------------------------------------------------------ the sample data
def build_seed():
    """(listings, transactions, reviews) exactly as the in-memory app seeds them."""
    from repositories.listing_repository import ListingRepository
    from repositories.review_repository import ReviewRepository
    from repositories.transaction_repository import TransactionRepository

    listings = ListingRepository.seeded().get_all()          # newest first
    transactions = TransactionRepository.seeded()._items
    reviews = ReviewRepository.seeded()._reviews
    return listings, transactions, reviews


def emails_needed(listings, transactions, reviews) -> set[str]:
    emails = {l.owner_email for l in listings} | {r.subject_email for r in reviews}
    for t in transactions:
        emails |= {t.provider_email, t.requester_email}
    return {e.strip().lower() for e in emails}


def load_ids(admin, emails: set[str]) -> dict[str, str]:
    """{email: profile uuid}. Exits with a clear message if seed_users.py was not run."""
    rows = admin.table("profiles").select("id,email").in_("email", sorted(emails)).execute().data
    ids = {r["email"]: r["id"] for r in rows}
    missing = sorted(emails - set(ids))
    if missing:
        sys.exit("These accounts do not exist yet, so nothing was written:\n  "
                 + "\n  ".join(missing)
                 + "\nRun  python scripts/seed_users.py  first.")
    return ids


# ------------------------------------------------------------ writers (one per table)
def seed_listings(admin, ids: dict[str, str], listings) -> tuple[int, int]:
    """Returns (created, skipped). Oldest first, one insert each, so created_at differs
    and the marketplace (newest first) shows the same order as the in-memory app."""
    have = {(r["owner_id"], r["title"])
            for r in admin.table("listings").select("owner_id,title").execute().data}
    created = skipped = 0
    for l in reversed(listings):
        owner_id = ids[l.owner_email.strip().lower()]
        if (owner_id, l.title) in have:
            skipped += 1
            continue
        admin.table("listings").insert({
            "owner_id": owner_id,
            "title": l.title,
            "price": round(float(l.price), 2),
            "category": l.category,
            "deliverable": l.deliverable,
            "unit": l.unit,
            "description": l.description,
            "status": l.status.value,
        }).execute()
        created += 1
    return created, skipped


def seed_transactions(admin, ids: dict[str, str], transactions) -> tuple[int, int]:
    have = {(r["provider_id"], r["requester_id"], r["item"])
            for r in admin.table("transactions").select("provider_id,requester_id,item").execute().data}
    created = skipped = 0
    for t in transactions:
        provider_id = ids[t.provider_email.strip().lower()]
        requester_id = ids[t.requester_email.strip().lower()]
        if (provider_id, requester_id, t.item) in have:
            skipped += 1
            continue
        admin.table("transactions").insert({
            "kind": t.kind.value,
            "listing_id": None,                       # sample history, not tied to a listing
            "item": t.item,
            "image_path": None,                       # NULL = the placeholder image
            "provider_id": provider_id,
            "requester_id": requester_id,
            "start_date": t.start.isoformat(),
            "end_date": t.end.isoformat(),
            "price": round(float(t.price), 2),
            "unit": t.unit,
            "quantity": round(float(t.quantity), 2),
            "total": round(float(t.total), 2),
            "status": t.status.value,
            "cancelled_by": ids[t.cancelled_by.strip().lower()] if t.cancelled_by else None,
            "location": t.location,
            "project_details": t.project_details,
        }).execute()
        created += 1
    return created, skipped


def seed_reviews(admin, ids: dict[str, str], reviews) -> tuple[int, int]:
    """Sample reviews have no reviewer account: reviewer_id stays NULL and the name is
    stored in reviewer_name. (Real reviews only ever come from submit_review.)"""
    have = {(r["subject_id"], r["reviewer_name"], r["text"])
            for r in (admin.table("reviews").select("subject_id,reviewer_name,text")
                      .is_("reviewer_id", "null").execute().data)}
    created = skipped = 0
    for r in reviews:
        subject_id = ids[r.subject_email.strip().lower()]
        if (subject_id, r.reviewer, r.text) in have:
            skipped += 1
            continue
        admin.table("reviews").insert({
            "reviewer_id": None,
            "reviewer_name": r.reviewer,
            "subject_id": subject_id,
            "rating": r.rating,
            "text": r.text,
        }).execute()
        created += 1
    return created, skipped


def seed_market(admin) -> dict[str, tuple[int, int]]:
    """Run everything. Returns {table: (created, skipped)}."""
    listings, transactions, reviews = build_seed()
    ids = load_ids(admin, emails_needed(listings, transactions, reviews))
    return {
        "listings": seed_listings(admin, ids, listings),
        "transactions": seed_transactions(admin, ids, transactions),
        "reviews": seed_reviews(admin, ids, reviews),
    }


# ------------------------------------------------------------ command line
def load_credentials(secrets_path: Path) -> tuple[str, str]:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not (url and key) and secrets_path.exists():
        section = tomllib.loads(secrets_path.read_text()).get("supabase", {})
        url, key = url or section.get("url"), key or section.get("service_key")
    if not url or not key:
        sys.exit(f"No Supabase url / service_key found in {secrets_path} "
                 "(or SUPABASE_URL / SUPABASE_SERVICE_KEY).")
    return url, key


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--yes", action="store_true", help="do not ask for confirmation")
    parser.add_argument("--secrets", type=Path, default=ROOT / "src" / ".streamlit" / "secrets.toml")
    args = parser.parse_args(argv)

    url, key = load_credentials(args.secrets)
    listings, transactions, reviews = build_seed()

    print(f"Project: {url}")
    print(f"This will add up to {len(listings)} listings, {len(transactions)} transactions "
          f"and {len(reviews)} sample reviews (existing ones are skipped).")
    print("DEV / STAGING ONLY. Never run this against production.")
    if not args.yes and input("Type 'dev' to continue: ").strip().lower() != "dev":
        print("Cancelled.")
        return 1

    from repositories.supabase_client import create_admin_client
    admin = create_admin_client(url, key)

    try:
        result = seed_market(admin)
    except Exception as exc:                  # the rows written so far stay; a re-run resumes
        print(f"\nFAILED: {exc}\nRows written before the failure are kept; run it again to finish.")
        return 1
    for table, (created, skipped) in result.items():
        print(f"  {table:13} {created} created, {skipped} already there")
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
