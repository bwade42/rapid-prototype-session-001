"""OCR text extraction from a food-label image.

Uses Tesseract (via ``pytesseract`` + Pillow) when available, and degrades
gracefully when it is not: the caller always gets a string back, plus a flag so
the UI can fall back to manual text entry (per the spec's "handle bad/unclear
images gracefully" acceptance criterion).
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class OcrResult:
    text: str
    ok: bool
    error: Optional[str] = None


def _load_image(image: Union[str, bytes, "os.PathLike"]):
    """Load an image from a path or raw bytes using Pillow."""
    from PIL import Image  # imported lazily so the package imports without Pillow

    if isinstance(image, bytes):
        return Image.open(io.BytesIO(image))
    return Image.open(image)


def extract_text(image: Union[str, bytes], *, lang: str = "eng") -> OcrResult:
    """Extract raw text from an image path or bytes.

    Returns an :class:`OcrResult`. ``ok`` is False (with an ``error`` message)
    when OCR could not run or produced no usable text, so the frontend can show
    the manual-input fallback instead of crashing.
    """
    try:
        import pytesseract
    except ImportError:
        return OcrResult(
            text="",
            ok=False,
            error="pytesseract not installed; use manual text input fallback.",
        )

    try:
        img = _load_image(image)
    except Exception as exc:  # noqa: BLE001 - surface any load failure to the UI
        return OcrResult(text="", ok=False, error=f"Could not read image: {exc}")

    try:
        text = pytesseract.image_to_string(img, lang=lang)
    except Exception as exc:  # noqa: BLE001 - e.g. tesseract binary missing
        return OcrResult(text="", ok=False, error=f"OCR failed: {exc}")

    text = text.strip()
    if not text:
        return OcrResult(text="", ok=False, error="No text detected in image.")

    return OcrResult(text=text, ok=True)
