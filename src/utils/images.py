"""Image helpers shared by listing screens (no Streamlit)."""
import base64
import io


def compress_image(raw: bytes, mime: str) -> tuple[bytes, str]:
    """Shrink uploads to a 1200px JPEG so the page stays fast.
    Falls back to the original bytes if Pillow is missing or the file can't be read."""
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(raw))
        img.thumbnail((1200, 1200))
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=82)
        return buf.getvalue(), "image/jpeg"
    except Exception:
        return raw, mime


def to_data_uri(raw: bytes, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"
