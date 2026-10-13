"""PERSON A's half of the repository factory: users and sign-in.

Each build_* takes the per-session Supabase client and returns the Supabase-backed
object the app uses. Only Person A edits this file. No Streamlit.

`in_memory = False` on a Supabase-backed class tells views/session.py to drop it on
logout (it is tied to one user's client)."""
from repositories.auth_gateway import SupabaseAuthGateway
from repositories.supabase_user_repository import SupabaseUserRepository


def build_user_repository(client) -> SupabaseUserRepository:
    return SupabaseUserRepository(client)


def build_auth_gateway(client, get_admin_client, users=None) -> SupabaseAuthGateway:
    """What AuthController signs people in and out with (A2/A3).

    `get_admin_client` is a function (not a client) so the service-role key is only
    touched when an account is actually deleted. `users` is unused (kept so the call in
    views/session.py does not change)."""
    return SupabaseAuthGateway(client, get_admin_client)
