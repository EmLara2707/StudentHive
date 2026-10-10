"""Builds Supabase clients. Credentials are passed in, never read here: this module
must not import Streamlit (views/session.py reads st.secrets and calls these).

Rules from the handoff:
  * One client per browser session, carrying that user's token. Never share a
    user client (no st.cache_resource), or two people would act as each other.
  * The admin (service-role) client bypasses RLS. It is only for deleting accounts
    and for seed scripts, and its key lives only in secrets.
  * Repositories must call client.table(...) / client.storage fresh on every use and
    must not keep those handles: signing in or refreshing the token resets them.
"""
import httpx
from supabase import Client
from supabase import create_client as _create_client
from supabase.lib.client_options import SyncClientOptions


def _http_client() -> httpx.Client:
    """One plain HTTP/1.1 client per Supabase client. The library's default is HTTP/2,
    where every request shares one long-lived connection; across Streamlit's reruns and
    threads (or after the server drops an idle connection) that surfaces as
    httpx.ReadError [Errno 11] Resource temporarily unavailable. HTTP/1.1 drops dead
    pooled connections and opens a fresh one instead."""
    return httpx.Client(
        http2=False,
        timeout=httpx.Timeout(20.0, connect=10.0),
        transport=httpx.HTTPTransport(retries=2),   # retries failed connects
        follow_redirects=True,
    )


def create_client(url: str, anon_key: str) -> Client:
    """A client for one browser session, signed out until with_token() or sign-in.

    No background refresh thread and nothing persisted by the library: Streamlit
    reruns the script constantly and the app stores the tokens itself."""
    return _create_client(
        url, anon_key,
        options=SyncClientOptions(auto_refresh_token=False, persist_session=False,
                                  httpx_client=_http_client()),
    )


def with_token(client: Client, access_token: str, refresh_token: str) -> Client:
    """Make `client` act as the user these tokens belong to. Returns the same client.

    Raises whatever the library raises if the tokens are invalid or expired beyond
    refresh; auth_gateway.restore_session wraps that into a plain result."""
    client.auth.set_session(access_token, refresh_token)
    return client


def create_admin_client(url: str, service_key: str) -> Client:
    """Service-role client. Never hand this to a view or a repository that serves
    a normal request."""
    return _create_client(
        url, service_key,
        options=SyncClientOptions(auto_refresh_token=False, persist_session=False,
                                  httpx_client=_http_client()),
    )
