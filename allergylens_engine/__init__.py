"""AllergyLens engine — OCR, ingredient parsing, allergen matching, risk scoring.

Public API for the (Python) frontend:

    from allergylens_engine import scan_label, scan_text

    result = scan_text("Ingredients: enriched wheat flour, sugar, whey.")
    print(result.risk_level)        # "high"
    print(result.to_dict())         # spec-shaped ScanResult (camelCase keys)

``scan_label`` takes an image (path or bytes) and runs OCR first;
``scan_text`` skips OCR and takes label text directly (the manual-input
fallback, and the fastest path for testing).
"""

from __future__ import annotations

from typing import Union

from .allergen_engine import detect_allergens, detect_dietary_concerns
from .models import DetectedAllergen, ScanResult
from .ocr import extract_text
from .parser import parse_ingredients
from .risk_scoring import score_risk

__all__ = [
    "scan_label",
    "scan_text",
    "ScanResult",
    "DetectedAllergen",
]


def scan_text(
    raw_text: str, *, ocr_ok: bool = True, include_concerns: bool = False
) -> ScanResult:
    """Run the full pipeline on already-extracted label text.

    Set ``include_concerns=True`` to also flag non-allergen dietary triggers
    (GERD/LPR, histamine) as informational warnings.
    """
    ingredients = parse_ingredients(raw_text)
    detected = detect_allergens(ingredients)
    risk, confidence, warnings = score_risk(ingredients, detected, ocr_ok=ocr_ok)

    if include_concerns:
        warnings = warnings + detect_dietary_concerns(ingredients)

    return ScanResult(
        raw_text=raw_text,
        ingredients=ingredients,
        detected_allergens=detected,
        warnings=warnings,
        risk_level=risk,
        confidence=confidence,
    )


def scan_label(image: Union[str, bytes], *, include_concerns: bool = False) -> ScanResult:
    """Run OCR on an image, then the full pipeline.

    On OCR failure the returned :class:`ScanResult` has an ``unknown`` risk and
    a warning, so the UI can prompt for manual text entry.
    """
    ocr = extract_text(image)
    if not ocr.ok:
        return ScanResult(
            raw_text="",
            warnings=[ocr.error or "OCR failed.", "Try a clearer photo or enter text manually."],
            risk_level="unknown",
            confidence="low",
        )
    return scan_text(ocr.text, ocr_ok=True, include_concerns=include_concerns)
