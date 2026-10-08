"""Supabase Storage helpers shared by both tracks (avatars, listing-images).
No Streamlit: the client is passed in.

Path convention (so a bucket policy can check ownership):
    <user id>/<file name>
e.g. avatars/3f2c.../avatar.jpg. Decide public-read vs signed URLs first (open
question in the handoff): use public_url() for public buckets, signed_url() for private.
"""
from supabase import Client

from repositories.errors import RepositoryError


def upload(client: Client, bucket: str, path: str, data: bytes, mime: str) -> str:
    """Store `data` at `path` (replacing any file already there). Returns the path,
    which is what the database keeps."""
    try:
        client.storage.from_(bucket).upload(
            path, data, {"content-type": mime, "upsert": "true"},
        )
    except Exception as exc:                      # network, permissions, size limits...
        raise RepositoryError("Couldn't upload that image. Please try again.") from exc
    return path


def public_url(client: Client, bucket: str, path: str) -> str:
    """URL for a file in a PUBLIC bucket. No network call."""
    return client.storage.from_(bucket).get_public_url(path)


def signed_url(client: Client, bucket: str, path: str, expires_in: int = 3600) -> str:
    """Temporary URL for a file in a PRIVATE bucket."""
    try:
        url = client.storage.from_(bucket).create_signed_url(path, expires_in)["signedURL"]
    except Exception as exc:
        raise RepositoryError("Couldn't load that image. Please try again.") from exc
    if not url:
        raise RepositoryError("Couldn't load that image. Please try again.")
    return url


def remove(client: Client, bucket: str, paths: list[str]) -> None:
    """Delete files. Missing files are not an error."""
    if not paths:
        return
    try:
        client.storage.from_(bucket).remove(paths)
    except Exception as exc:
        raise RepositoryError("Couldn't remove that image. Please try again.") from exc
