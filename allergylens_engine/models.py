"""Data models for the AllergyLens engine.

These mirror the ScanResult / DetectedAllergen types in the spec. Internally we
use snake_case (Pythonic), but ``to_dict()`` emits the camelCase keys the spec
defines so the JSON shape stays consistent for any consumer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal

RiskLevel = Literal["low", "medium", "high", "unknown"]
Confidence = Literal["low", "medium", "high"]
Severity = Literal["low", "medium", "high"]


@dataclass
class DetectedAllergen:
    """A single allergen match found in the ingredient list."""

    allergen: str
    matched_ingredient: str
    severity: Severity
    reason: str

    def to_dict(self) -> dict:
        return {
            "allergen": self.allergen,
            "matchedIngredient": self.matched_ingredient,
            "severity": self.severity,
            "reason": self.reason,
        }


@dataclass
class ScanResult:
    """The full result of scanning a label, ready to hand to the UI."""

    raw_text: str = ""
    ingredients: List[str] = field(default_factory=list)
    detected_allergens: List[DetectedAllergen] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    risk_level: RiskLevel = "unknown"
    confidence: Confidence = "low"

    def to_dict(self) -> dict:
        return {
            "rawText": self.raw_text,
            "ingredients": self.ingredients,
            "detectedAllergens": [a.to_dict() for a in self.detected_allergens],
            "warnings": self.warnings,
            "riskLevel": self.risk_level,
            "confidence": self.confidence,
        }
