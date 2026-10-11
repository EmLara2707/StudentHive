"""The profile-photo crop box: the picture with a circle on it. Drag a corner to resize
(the opposite corner stays put) or grab the frame itself to move it. No sliders, no buttons.

Built with Streamlit's own custom-component support (st.components.v2, Streamlit 1.51+),
so it needs no extra package. The JavaScript draws on a canvas and reports the box as
fractions of the picture; utils/images.crop_fractions cuts the real photo with them."""
import streamlit as st

from utils import images

_CSS = """
.pc-wrap { display: flex; justify-content: center; }
.pc-wrap canvas { display: block; max-width: 100%; border-radius: 10px; touch-action: none; }
"""

_JS = """
export default function (component) {
  const { data, setStateValue, parentElement } = component;
  const root = document.createElement('div');
  root.className = 'pc-wrap';
  parentElement.appendChild(root);
  const canvas = document.createElement('canvas');
  root.appendChild(canvas);

  const HIT = 24, MIN = 56, ARM = 26, THICK = 5;
  const dpr = window.devicePixelRatio || 1;
  const img = new Image();
  let dw = 0, dh = 0, box = null, drag = null;

  // which way the box grows away from the corner you hold (the opposite corner is the anchor)
  const CORNERS = {
    tl: { sx: -1, sy: -1, cursor: 'nwse-resize' },
    tr: { sx:  1, sy: -1, cursor: 'nesw-resize' },
    bl: { sx: -1, sy:  1, cursor: 'nesw-resize' },
    br: { sx:  1, sy:  1, cursor: 'nwse-resize' },
  };
  const cornerPoint = (n) => ({
    x: CORNERS[n].sx > 0 ? box.x + box.s : box.x,
    y: CORNERS[n].sy > 0 ? box.y + box.s : box.y,
  });
  const anchorPoint = (n) => ({
    x: CORNERS[n].sx > 0 ? box.x : box.x + box.s,
    y: CORNERS[n].sy > 0 ? box.y : box.y + box.s,
  });

  function draw() {
    const c = canvas.getContext('2d');
    c.setTransform(dpr, 0, 0, dpr, 0, 0);
    c.clearRect(0, 0, dw, dh);
    c.drawImage(img, 0, 0, dw, dh);

    const cx = box.x + box.s / 2, cy = box.y + box.s / 2, r = box.s / 2;
    c.fillStyle = 'rgba(8, 14, 32, 0.62)';              // dim everything outside the circle
    c.beginPath();
    c.rect(0, 0, dw, dh);
    c.arc(cx, cy, r, 0, Math.PI * 2);
    c.fill('evenodd');

    c.strokeStyle = '#ffffff';                          // the circle
    c.lineWidth = 2;
    c.beginPath();
    c.arc(cx, cy, r - 1, 0, Math.PI * 2);
    c.stroke();

    c.lineWidth = THICK;                                // the four corner brackets
    c.lineCap = 'butt';
    const inset = THICK / 2;
    for (const n of Object.keys(CORNERS)) {
      const px = CORNERS[n].sx > 0 ? box.x + box.s - inset : box.x + inset;
      const py = CORNERS[n].sy > 0 ? box.y + box.s - inset : box.y + inset;
      c.beginPath();
      c.moveTo(px - CORNERS[n].sx * ARM, py);
      c.lineTo(px, py);
      c.lineTo(px, py - CORNERS[n].sy * ARM);
      c.stroke();
    }
  }

  const where = (e) => {
    const r = canvas.getBoundingClientRect();
    return { x: (e.clientX - r.left) * dw / r.width, y: (e.clientY - r.top) * dh / r.height };
  };
  function cornerAt(p) {
    let best = null, bestD = HIT;
    for (const n of Object.keys(CORNERS)) {
      const q = cornerPoint(n);
      const d = Math.max(Math.abs(p.x - q.x), Math.abs(p.y - q.y));
      if (d <= bestD) { best = n; bestD = d; }
    }
    return best;
  }
  const inside = (p) => p.x >= box.x && p.x <= box.x + box.s && p.y >= box.y && p.y <= box.y + box.s;
  const emit = () => setStateValue('crop', { x: box.x / dw, y: box.y / dh, s: box.s / dw });

  canvas.addEventListener('pointerdown', (e) => {
    const p = where(e), n = cornerAt(p);
    if (n) {                                            // a corner: resize
      drag = { n, anchor: anchorPoint(n) };
    } else if (inside(p)) {                             // the frame itself: move
      drag = { move: true, dx: p.x - box.x, dy: p.y - box.y };
      canvas.style.cursor = 'grabbing';
    } else {
      return;
    }
    canvas.setPointerCapture(e.pointerId);
    e.preventDefault();
  });
  canvas.addEventListener('pointermove', (e) => {
    const p = where(e);
    if (!drag) {
      const n = cornerAt(p);
      canvas.style.cursor = n ? CORNERS[n].cursor : (inside(p) ? 'grab' : 'default');
      return;
    }
    if (drag.move) {                                    // slide the whole frame, size unchanged
      box = {
        x: Math.min(Math.max(p.x - drag.dx, 0), dw - box.s),
        y: Math.min(Math.max(p.y - drag.dy, 0), dh - box.s),
        s: box.s,
      };
      draw();
      return;
    }
    const { sx, sy } = CORNERS[drag.n], a = drag.anchor;
    const want = Math.max((p.x - a.x) * sx, (p.y - a.y) * sy);
    const room = Math.min(sx > 0 ? dw - a.x : a.x, sy > 0 ? dh - a.y : a.y);
    const s = Math.min(room, Math.max(MIN, want));      // stays square and inside the picture
    box = { x: sx > 0 ? a.x : a.x - s, y: sy > 0 ? a.y : a.y - s, s };
    draw();
  });
  const release = () => {
    if (drag) { drag = null; canvas.style.cursor = 'default'; emit(); }
  };
  canvas.addEventListener('pointerup', release);
  canvas.addEventListener('pointercancel', release);

  img.onload = () => {
    const room = Math.max(240, Math.min(root.clientWidth || 420, 440));
    const k = Math.min(room / img.naturalWidth, 420 / img.naturalHeight);
    dw = Math.round(img.naturalWidth * k);
    dh = Math.round(img.naturalHeight * k);
    canvas.width = dw * dpr; canvas.height = dh * dpr;
    canvas.style.width = dw + 'px'; canvas.style.height = dh + 'px';
    const s0 = data.crop;                                // where the box starts (fractions)
    box = { x: s0.x * dw, y: s0.y * dh, s: s0.s * dw };
    draw();
  };
  img.src = data.src;

  return () => { root.remove(); };
}
"""

try:                                    # Streamlit 1.51+; older versions fall back to no crop
    import streamlit.components.v2 as _v2
    _CROPPER = _v2.component("sh_photo_cropper", css=_CSS, js=_JS)
except Exception:                       # pragma: no cover
    _CROPPER = None


def crop_controls(raw: bytes, key: str) -> tuple[bytes, str] | None:
    """Show the crop box for `raw` and return the cropped square as (bytes, mime) for the
    corners' current position. Returns None when it can't be shown (old Streamlit, Pillow
    missing, unreadable image) so the caller can save the original instead.

    `key` must change with every new upload (use the file's id) so the box starts fresh."""
    if _CROPPER is None:
        return None
    preview = images.preview_for_cropper(raw)
    if preview is None:
        return None
    src, width, height = preview
    side = min(width, height)           # start with the biggest centred square
    start = {"x": (width - side) / 2 / width, "y": (height - side) / 2 / height,
             "s": side / width}
    st.caption("Drag the corners to resize, or drag the frame to move it.")
    result = _CROPPER(
        key=f"photo_cropper_{key}",
        data={"src": src, "crop": start},
        default={"crop": start},
        on_crop_change=lambda: None,
    )
    box = result.crop or start
    return images.crop_fractions(raw, box["x"], box["y"], box["s"])
