"""A7: DEV / STAGING ONLY. Creates the demo account and the 12 sample students in Supabase.

    python scripts/seed_users.py              # asks you to confirm the project first
    python scripts/seed_users.py --yes        # no question (scripts, CI)

Why this exists: the in-memory app ships a demo user and 12 sample students. With
USE_SUPABASE_USERS on they must be real rows, because profiles.id references
auth.users, and listings/transactions/reviews point at those ids.

What it does, for each person:
  * no account yet  -> creates it through the ADMIN API, already email-confirmed
                       (no confirmation email is sent, so no email rate limit is used)
  * account exists  -> reuses it (for example the rows made by supabase/dev/test_profiles.sql,
                       which have fixed ids and no password) and confirms its email
  * then fills in the profile row (onboarded, major, bio, skills, socials), because the
    signup trigger only creates a default, un-onboarded profile.

The demo account gets the password below. Sample students get a random password that is
thrown away, so nobody can sign in as them (same as the in-memory seed).

Safe to run again: it updates instead of failing. Production starts EMPTY: never run this
there, and never ship the demo account (final step A8).

Credentials come from src/.streamlit/secrets.toml (the same file the app uses), or from
the SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables. The service key bypasses
row level security: keep it out of git and out of chat.
"""
import argparse
import os
import secrets
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

DEMO_PASSWORD = "demo1234"          # same as the in-memory demo account


@dataclass(frozen=True)
class SeedUser:
    name: str
    email: str
    major: str
    bio: str
    skills: list
    socials: list
    password: str | None            # None = unusable random password, only for new accounts


def build_users(demo_password: str = DEMO_PASSWORD) -> list[SeedUser]:
    """The demo user and the sample students, read from the same source the in-memory
    app uses (UserRepository.seeded), so the two can never drift apart."""
    from repositories.seed_data import SAMPLE_STUDENTS
    from repositories.user_repository import DEMO_EMAIL, UserRepository

    repo = UserRepository.seeded()
    people = []
    for email in [DEMO_EMAIL, *[s.email for s in SAMPLE_STUDENTS]]:
        user = repo.get_by_email(email)
        people.append(SeedUser(
            name=user.name, email=user.email, major=user.profile.major,
            bio=user.profile.bio, skills=list(user.profile.skills),
            socials=list(user.profile.socials),
            password=demo_password if email == DEMO_EMAIL else None,
        ))
    return people


def _find_id(admin, email: str) -> str | None:
    """The auth user id for this email, via the profiles table (the signup trigger and
    test_profiles.sql both create a profile row per auth user)."""
    rows = (admin.table("profiles").select("id").eq("email", email).limit(1).execute().data)
    return rows[0]["id"] if rows else None


def seed_user(admin, person: SeedUser) -> str:
    """Create or update one person. Returns 'created' or 'updated'."""
    user_id = _find_id(admin, person.email)
    if user_id is None:
        created = admin.auth.admin.create_user({
            "email": person.email,
            "password": person.password or secrets.token_urlsafe(32),
            "email_confirm": True,
            "user_metadata": {"name": person.name},
        })
        user_id, outcome = str(created.user.id), "created"
    else:
        changes = {"email_confirm": True}
        if person.password:                     # the demo account: make the password known
            changes["password"] = person.password
        admin.auth.admin.update_user_by_id(user_id, changes)
        outcome = "updated"

    rows = (admin.table("profiles").update({
        "name": person.name,
        "onboarded": True,
        "major": person.major,
        "bio": person.bio,
        "skills": person.skills,
        "socials": person.socials,
    }).eq("id", user_id).execute().data)
    if not rows:
        raise RuntimeError(f"{person.email}: account exists but its profile row is missing")
    return outcome


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
    parser.add_argument("--demo-password", default=DEMO_PASSWORD)
    args = parser.parse_args(argv)

    url, key = load_credentials(args.secrets)
    people = build_users(args.demo_password)

    print(f"Project: {url}")
    print(f"This will create or update {len(people)} accounts (demo + sample students).")
    print("DEV / STAGING ONLY. Never run this against production.")
    if not args.yes and input("Type 'dev' to continue: ").strip().lower() != "dev":
        print("Cancelled.")
        return 1

    from repositories.supabase_client import create_admin_client
    admin = create_admin_client(url, key)

    failures = 0
    for person in people:
        try:
            print(f"  {seed_user(admin, person):8} {person.email}")
        except Exception as exc:                # keep going: report every problem at the end
            failures += 1
            print(f"  FAILED   {person.email}: {exc}")
    print(f"\nDone: {len(people) - failures} ok, {failures} failed.")
    if not failures:
        print(f"Demo login: {people[0].email} / {args.demo_password}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
