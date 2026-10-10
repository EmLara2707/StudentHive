"""How long a Supabase access token (a JWT) is still valid. No Streamlit.

Only the payload is decoded, to read its `exp` (expiry, seconds since 1970). The
signature is NOT checked: this is a scheduling hint for "refresh soon", not security.
Supabase itself rejects a bad or expired token."""
import base64
import json
import time


def seconds_left(access_token: str | None, now: float | None = None) -> float | None:
    """Seconds until the token expires (negative if it already did), or None when the
    token can't be read."""
    try:
        payload = access_token.split(".")[1]
        payload += "=" * (-len(payload) % 4)            # base64url without padding
        exp = json.loads(base64.urlsafe_b64decode(payload))["exp"]
        return float(exp) - (time.time() if now is None else now)
    except Exception:
        return None
