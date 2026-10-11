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


# ---- square crop for profile photos (the picture is shown in a circle) ----
def _load_rgb(raw: bytes):
    """Open an upload as an upright RGB image (EXIF rotation applied, transparency on white)."""
    from PIL import Image, ImageOps
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(raw)))
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        flat = Image.new("RGB", img.size, "white")
        flat.paste(img, mask=img.split()[3])
        return flat
    return img.convert("RGB")


def preview_for_cropper(raw: bytes, longest: int = 900) -> tuple[str, int, int] | None:
    """(data URI, width, height) of an upright, shrunken copy of the upload for the crop box
    to draw, or None if the file can't be read (or Pillow is missing)."""
    try:
        img = _load_rgb(raw)
        img.thumbnail((longest, longest))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return to_data_uri(buf.getvalue(), "image/jpeg"), img.width, img.height
    except Exception:
        return None


def crop_fractions(raw: bytes, x: float, y: float, side: float,
                   size: int = 800) -> tuple[bytes, str] | None:
    """Cut the square chosen in the crop box out of the FULL-size image.

    x, y = top-left corner as a fraction of the image width / height; side = the square's
    side as a fraction of the image WIDTH. Fractions (not pixels) because the crop box
    works on a shrunken preview. Values outside the picture are pulled back inside.
    Returns a size x size JPEG, or None if the file can't be read."""
    try:
        from PIL import Image
        img = _load_rgb(raw)
        width, height = img.size
        px = min(max(side * width, 1.0), float(min(width, height)))     # side in pixels
        left = min(max(x * width, 0.0), width - px)
        top = min(max(y * height, 0.0), height - px)
        piece = img.crop((round(left), round(top), round(left + px), round(top + px)))
        piece = piece.resize((size, size), Image.LANCZOS)
        buf = io.BytesIO()
        piece.save(buf, format="JPEG", quality=88)
        return buf.getvalue(), "image/jpeg"
    except Exception:
        return None


def to_data_uri(raw: bytes, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"
