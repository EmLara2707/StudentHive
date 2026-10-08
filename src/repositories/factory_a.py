"""PERSON A's half of the repository factory: users and sign-in.

Each build_* takes the per-session Supabase client (or None when no Supabase is
configured) and returns the repository the app should use. While the flag below is
False, the app keeps using the in-memory seeded repository, which is the fallback
until the final step. Only Person A edits this file. No Streamlit.

Convention for Supabase-backed repositories: set `in_memory = False` on the class.
views/session.py uses it so a logout drops a repository that is tied to one user's
client but keeps the in-memory "database" (otherwise registered demo accounts would
vanish on logout).
"""
from repositories.user_repository import UserRepository

# Flip to True once SupabaseUserRepository and the auth gateway are both ready.
USE_SUPABASE_USERS = False


def build_user_repository(client) -> UserRepository:
    if USE_SUPABASE_USERS:
        # A4: from repositories.supabase_user_repository import SupabaseUserRepository
        #     return SupabaseUserRepository(client)
        raise NotImplementedError("SupabaseUserRepository is not written yet (A4).")
    return UserRepository.seeded()


def build_auth_gateway(client, get_admin_client):
    """The object AuthController signs people in and out with (A2/A3).

    Returns None until the gateway exists: nothing calls it yet, and the
    in-memory AuthController still checks passwords itself. `get_admin_client` is a
    function (not a client) so the service-role key is only touched when an account
    is actually deleted."""
    if USE_SUPABASE_USERS:
        # A2: return SupabaseAuthGateway(client, get_admin_client)
        raise NotImplementedError("The auth gateway is not written yet (A2).")
    return None
