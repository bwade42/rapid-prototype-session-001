"""Turn raw OCR text into a clean list of ingredients.

Handles the messy realities of OCR output: an "Ingredients:" header, line
breaks mid-word, parenthetical sub-ingredients, trailing "Contains:" statements,
and stray punctuation.
"""

from __future__ import annotations

import re
from typing import List

# Where the ingredient list starts and (optionally) ends.
_INGREDIENTS_HEADER = re.compile(r"ingredients?\s*[:\-]", re.IGNORECASE)
_END_MARKERS = re.compile(
    r"\b(contains|may contain|manufactured|distributed|allergen|nutrition|"
    r"net wt|best by|directions|storage)\b",
    re.IGNORECASE,
)


def find_ingredients_section(raw_text: str) -> str:
    """Return the substring that holds the ingredient list.

    Falls back to the whole text if no explicit "Ingredients:" header is found,
    so free-form pasted lists still parse.
    """
    if not raw_text:
        return ""

    header = _INGREDIENTS_HEADER.search(raw_text)
    section = raw_text[header.end():] if header else raw_text

    end = _END_MARKERS.search(section)
    if end:
        section = section[: end.start()]

    return section.strip()


def clean_text(raw_text: str) -> str:
    """Normalize whitespace and repair common OCR line-break artifacts."""
    text = raw_text.replace("\r", "\n")
    # Join words split across a line break by a hyphen: "leci-\nthin" -> "lecithin"
    text = re.sub(r"-\s*\n\s*", "", text)
    # Treat remaining newlines as spaces.
    text = re.sub(r"\s*\n\s*", " ", text)
    # Collapse runs of whitespace.
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _clean_ingredient(item: str) -> str:
    item = item.strip().strip(".;:*•·-")
    # Drop parenthetical sub-ingredient qualifiers, e.g. "flour (wheat)" -> "flour".
    item = re.sub(r"\([^)]*\)", "", item)
    item = re.sub(r"\s{2,}", " ", item).strip()
    return item.lower()


def parse_ingredients(raw_text: str) -> List[str]:
    """Parse raw OCR/label text into a de-duplicated list of ingredients."""
    section = find_ingredients_section(raw_text)
    section = clean_text(section)
    if not section:
        return []

    # Split on the usual separators between ingredients.
    parts = re.split(r"[,;•·\|]| and ", section)

    seen = set()
    ingredients: List[str] = []
    for part in parts:
        cleaned = _clean_ingredient(part)
        if not cleaned or len(cleaned) < 2:
            continue
        if cleaned in seen:
            continue
        seen.add(cleaned)
        ingredients.append(cleaned)

    return ingredients
