"""Match parsed ingredients against the allergen database and alias table.

Two kinds of matches:

* **Direct** — an ingredient contains a known allergen keyword (e.g. "whey"
  -> dairy). Severity: high.
* **Alias / ambiguous** — an ingredient is a hidden-source term that *might*
  contain an allergen (e.g. "natural flavors" -> could be dairy/soy/egg).
  Severity: medium, needs review.
"""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from typing import Dict, List, Tuple

from .models import DetectedAllergen

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Categories that aren't classic allergens but need a friendlier display name.
_LABELS = {"gerd_lpr": "GERD/LPR", "histamine": "Histamine"}


@lru_cache(maxsize=1)
def load_allergens() -> Dict[str, List[str]]:
    """Load the allergen -> keyword map from data/allergens.json."""
    with open(os.path.join(_DATA_DIR, "allergens.json"), encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def load_dietary_concerns() -> Dict[str, List[str]]:
    """Load the non-allergen dietary-trigger map (GERD/LPR, histamine, ...)."""
    with open(os.path.join(_DATA_DIR, "dietary_concerns.json"), encoding="utf-8") as fh:
        return json.load(fh).get("concerns", {})


@lru_cache(maxsize=1)
def load_aliases() -> Dict[str, List[str]]:
    """Load the ambiguous-ingredient -> possible-allergen map."""
    with open(os.path.join(_DATA_DIR, "ingredient_aliases.json"), encoding="utf-8") as fh:
        return json.load(fh).get("aliases", {})


def _display_name(allergen_key: str) -> str:
    """'tree_nut' -> 'Tree Nut'."""
    return _LABELS.get(allergen_key, allergen_key.replace("_", " ").title())


def detect_dietary_concerns(ingredients: List[str]) -> List[str]:
    """Return informational warning strings for any dietary triggers found.

    These are surfaced as warnings (not allergen detections) so they never
    affect the allergen risk level — a GERD trigger shouldn't read as "high
    risk allergen".
    """
    concerns = load_dietary_concerns()
    messages: List[str] = []
    for concern_key, keywords in concerns.items():
        hits = sorted(
            {ing for ing in ingredients for kw in keywords if _keyword_in(kw, ing.lower())}
        )
        if hits:
            messages.append(
                f"Possible {_display_name(concern_key)} trigger(s): {', '.join(hits)}."
            )
    return messages


def detect_allergens(ingredients: List[str]) -> List[DetectedAllergen]:
    """Return every allergen match found across the ingredient list.

    At most one detection per (allergen, ingredient) pair, preferring a direct
    (high) match over an alias (medium) match for the same allergen.
    """
    allergens = load_allergens()
    aliases = load_aliases()

    # Keyed by (allergen, ingredient) so we can dedupe and upgrade severity.
    found: Dict[Tuple[str, str], DetectedAllergen] = {}

    for ingredient in ingredients:
        ing = ingredient.lower()

        # Direct allergen keyword matches (high severity).
        for allergen_key, keywords in allergens.items():
            for keyword in keywords:
                if _keyword_in(keyword, ing):
                    key = (allergen_key, ingredient)
                    found[key] = DetectedAllergen(
                        allergen=_display_name(allergen_key),
                        matched_ingredient=ingredient,
                        severity="high",
                        reason=f"'{ingredient}' is a known source of {_display_name(allergen_key)}.",
                    )

        # Alias / ambiguous matches (medium severity) — don't overwrite a direct hit.
        for alias, possible in aliases.items():
            if _keyword_in(alias, ing):
                for allergen_key in possible:
                    key = (allergen_key, ingredient)
                    if key in found and found[key].severity == "high":
                        continue
                    found[key] = DetectedAllergen(
                        allergen=_display_name(allergen_key),
                        matched_ingredient=ingredient,
                        severity="medium",
                        reason=(
                            f"'{ingredient}' can be a hidden source of "
                            f"{_display_name(allergen_key)} — needs review."
                        ),
                    )

    return list(found.values())


def _keyword_in(keyword: str, ingredient: str) -> bool:
    """Word-boundary aware containment so 'egg' doesn't match 'eggplant'... etc.

    Multi-word keywords (e.g. 'soy lecithin') fall back to substring matching.
    """
    keyword = keyword.lower()
    if " " in keyword:
        return keyword in ingredient
    # Allow a simple plural suffix so "almond" matches "almonds" but not
    # "almondmilk"-style runs — and "egg" still won't match "eggplant".
    return re.search(rf"\b{re.escape(keyword)}(?:s|es)?\b", ingredient) is not None
