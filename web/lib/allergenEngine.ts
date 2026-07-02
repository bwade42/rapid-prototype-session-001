// Match ingredients against the allergen DB + alias table, and flag dietary
// concerns. Mirrors allergylens_engine/allergen_engine.py.

import type { DetectedAllergen } from "../types/scan";
import type { AliasMap, AllergenMap, ConcernMap } from "../types/allergens";
import allergensData from "../data/allergens.json";
import aliasesData from "../data/ingredientAliases.json";
import concernsData from "../data/dietaryConcerns.json";

const ALLERGENS = allergensData as AllergenMap;
const ALIASES = (aliasesData as { aliases: AliasMap }).aliases;
const CONCERNS = (concernsData as { concerns: ConcernMap }).concerns;

// Categories needing a friendlier display name than title-casing gives.
const LABELS: Record<string, string> = {
  gerd_lpr: "GERD/LPR",
  histamine: "Histamine",
};

function displayName(key: string): string {
  if (LABELS[key]) return LABELS[key];
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Word-boundary aware containment with a simple plural suffix, so "almond"
 * matches "almonds" but "egg" still won't match "eggplant". Multi-word keywords
 * fall back to substring matching.
 */
function keywordIn(keyword: string, ingredient: string): boolean {
  const kw = keyword.toLowerCase();
  if (kw.includes(" ")) return ingredient.includes(kw);
  return new RegExp(`\\b${escapeRegExp(kw)}(?:s|es)?\\b`).test(ingredient);
}

/** Every allergen match across the ingredient list (deduped, direct beats alias). */
export function detectAllergens(ingredients: string[]): DetectedAllergen[] {
  const found = new Map<string, DetectedAllergen>();

  for (const ingredient of ingredients) {
    const ing = ingredient.toLowerCase();

    // Direct keyword matches (high severity).
    for (const [allergenKey, keywords] of Object.entries(ALLERGENS)) {
      for (const keyword of keywords) {
        if (keywordIn(keyword, ing)) {
          found.set(`${allergenKey}::${ingredient}`, {
            allergen: displayName(allergenKey),
            matchedIngredient: ingredient,
            severity: "high",
            reason: `'${ingredient}' is a known source of ${displayName(allergenKey)}.`,
          });
        }
      }
    }

    // Alias / ambiguous matches (medium) — never overwrite a direct hit.
    for (const [alias, possible] of Object.entries(ALIASES)) {
      if (keywordIn(alias, ing)) {
        for (const allergenKey of possible) {
          const key = `${allergenKey}::${ingredient}`;
          const existing = found.get(key);
          if (existing && existing.severity === "high") continue;
          found.set(key, {
            allergen: displayName(allergenKey),
            matchedIngredient: ingredient,
            severity: "medium",
            reason: `'${ingredient}' can be a hidden source of ${displayName(
              allergenKey,
            )} — needs review.`,
          });
        }
      }
    }
  }

  return [...found.values()];
}

/** Informational warnings for non-allergen dietary triggers (GERD/LPR, histamine). */
export function detectDietaryConcerns(ingredients: string[]): string[] {
  const messages: string[] = [];
  for (const [concernKey, keywords] of Object.entries(CONCERNS)) {
    const hits = [
      ...new Set(
        ingredients.filter((ing) =>
          keywords.some((kw) => keywordIn(kw, ing.toLowerCase())),
        ),
      ),
    ].sort();
    if (hits.length) {
      messages.push(
        `Possible ${displayName(concernKey)} trigger(s): ${hits.join(", ")}.`,
      );
    }
  }
  return messages;
}
