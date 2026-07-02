"""Tests for the AllergyLens engine core (no OCR / no network needed)."""

from allergylens_engine import scan_text
from allergylens_engine.parser import parse_ingredients


SPEC_LABEL = "Ingredients: enriched wheat flour, sugar, soybean oil, whey, soy lecithin, natural flavors."


def test_parse_matches_spec_example():
    # The exact example from the spec's Ingredient Parser section.
    ingredients = parse_ingredients(SPEC_LABEL)
    assert ingredients == [
        "enriched wheat flour",
        "sugar",
        "soybean oil",
        "whey",
        "soy lecithin",
        "natural flavors",
    ]


def test_direct_allergens_are_high_risk():
    result = scan_text(SPEC_LABEL)
    assert result.risk_level == "high"
    names = {a.allergen for a in result.detected_allergens}
    assert {"Wheat", "Soy", "Dairy"} <= names


def test_alias_only_is_medium_risk():
    result = scan_text("Ingredients: sugar, natural flavors, citric acid.")
    assert result.risk_level == "medium"
    assert all(a.severity == "medium" for a in result.detected_allergens)


def test_no_allergens_is_low_risk():
    result = scan_text("Ingredients: water, sugar, citric acid, salt.")
    assert result.risk_level == "low"
    assert result.detected_allergens == []


def test_empty_input_is_unknown():
    result = scan_text("")
    assert result.risk_level == "unknown"
    assert result.warnings


def test_to_dict_uses_spec_camelcase_keys():
    result = scan_text(SPEC_LABEL)
    d = result.to_dict()
    assert set(d.keys()) == {
        "rawText",
        "ingredients",
        "detectedAllergens",
        "warnings",
        "riskLevel",
        "confidence",
    }
    assert set(d["detectedAllergens"][0].keys()) == {
        "allergen",
        "matchedIngredient",
        "severity",
        "reason",
    }


def test_word_boundary_avoids_false_positive():
    # "eggplant" should not trigger the egg allergen.
    result = scan_text("Ingredients: eggplant, water, salt.")
    names = {a.allergen for a in result.detected_allergens}
    assert "Egg" not in names
