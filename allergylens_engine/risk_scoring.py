"""Roll detected allergens up into an overall risk level and confidence.

Risk levels (from the spec):
* **high**   - a direct allergen was found.
* **medium** - only alias / ambiguous ingredients matched.
* **low**    - no known allergens found.
* **unknown**- nothing to score (no ingredients parsed).
"""

from __future__ import annotations

from typing import List, Tuple

from .models import Confidence, DetectedAllergen, RiskLevel


def score_risk(
    ingredients: List[str],
    detected: List[DetectedAllergen],
    *,
    ocr_ok: bool = True,
) -> Tuple[RiskLevel, Confidence, List[str]]:
    """Return ``(risk_level, confidence, warnings)``."""
    warnings: List[str] = []

    if not ingredients:
        warnings.append("No ingredients could be read. Try a clearer photo or manual input.")
        return "unknown", "low", warnings

    has_high = any(a.severity == "high" for a in detected)
    has_medium = any(a.severity == "medium" for a in detected)

    if has_high:
        risk: RiskLevel = "high"
    elif has_medium:
        risk = "medium"
        warnings.append("Some ingredients are ambiguous and may hide allergens — review carefully.")
    else:
        risk = "low"

    confidence = _score_confidence(ingredients, ocr_ok)
    if risk == "medium" and confidence == "high":
        # Ambiguity caps our confidence in a clean result.
        confidence = "medium"

    return risk, confidence, warnings


def _score_confidence(ingredients: List[str], ocr_ok: bool) -> Confidence:
    """Confidence in the read itself, driven by OCR success and list richness."""
    if not ocr_ok:
        return "low"
    if len(ingredients) >= 5:
        return "high"
    if len(ingredients) >= 2:
        return "medium"
    return "low"
