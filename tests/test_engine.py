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


def test_plural_allergen_keywords_match():
    # Plurals must be caught — missing "almonds"/"cashews" would be a safety bug.
    result = scan_text("Ingredients: rolled oats, almonds, cashews, honey.")
    names = {a.allergen for a in result.detected_allergens}
    assert "Tree Nut" in names
    assert result.risk_level == "high"


def test_parenthetical_subingredients_are_flattened():
    # Allergens hidden inside parentheses must survive parsing.
    result = scan_text("Ingredients: dark chocolate (cocoa, sugar, milk fat), oats.")
    assert "milk fat" in result.ingredients
    names = {a.allergen for a in result.detected_allergens}
    assert "Dairy" in names


def test_dietary_concerns_are_opt_in_and_dont_change_risk():
    label = "Ingredients: water, sugar, citric acid, salt."
    # Off by default: still low risk, no concern warnings.
    default = scan_text(label)
    assert default.risk_level == "low"
    assert default.warnings == []

    # Opt in: citric acid surfaces as a GERD/LPR warning, risk stays low.
    with_concerns = scan_text(label, include_concerns=True)
    assert with_concerns.risk_level == "low"
    assert any("GERD/LPR" in w for w in with_concerns.warnings)
