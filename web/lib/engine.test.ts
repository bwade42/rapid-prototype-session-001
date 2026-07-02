// Minimal, dependency-free test runner for the engine core.
// Run with: npx tsx lib/engine.test.ts   (mirrors tests/test_engine.py)

import { scanText } from "./index";
import { parseIngredients } from "./parser";

let passed = 0;
let failed = 0;

function check(name: string, cond: boolean) {
  if (cond) {
    passed++;
    console.log(`  ok  - ${name}`);
  } else {
    failed++;
    console.error(`  FAIL - ${name}`);
  }
}

const SPEC_LABEL =
  "Ingredients: enriched wheat flour, sugar, soybean oil, whey, soy lecithin, natural flavors.";

// parse matches the spec example
check(
  "parse matches spec example",
  JSON.stringify(parseIngredients(SPEC_LABEL)) ===
    JSON.stringify([
      "enriched wheat flour",
      "sugar",
      "soybean oil",
      "whey",
      "soy lecithin",
      "natural flavors",
    ]),
);

// direct allergens -> high risk
const spec = scanText(SPEC_LABEL);
const specNames = new Set(spec.detectedAllergens.map((a) => a.allergen));
check("spec label is high risk", spec.riskLevel === "high");
check(
  "wheat/soy/dairy detected",
  ["Wheat", "Soy", "Dairy"].every((n) => specNames.has(n)),
);

// alias-only -> medium
check(
  "alias-only is medium",
  scanText("Ingredients: sugar, natural flavors, citric acid.").riskLevel === "medium",
);

// clean label -> low
check(
  "clean label is low",
  scanText("Ingredients: water, sugar, citric acid, salt.").riskLevel === "low",
);

// empty -> unknown
check("empty is unknown", scanText("").riskLevel === "unknown");

// plurals: almonds/cashews caught
check(
  "plural tree nuts detected",
  new Set(
    scanText("Ingredients: rolled oats, almonds, cashews.").detectedAllergens.map(
      (a) => a.allergen,
    ),
  ).has("Tree Nut"),
);

// eggplant is not egg
check(
  "eggplant is not egg",
  !new Set(
    scanText("Ingredients: eggplant, water, salt.").detectedAllergens.map(
      (a) => a.allergen,
    ),
  ).has("Egg"),
);

// parentheticals flattened
check(
  "parenthetical milk fat survives",
  scanText("Ingredients: dark chocolate (cocoa, milk fat), oats.").ingredients.includes(
    "milk fat",
  ),
);

// dietary concerns opt-in
const withConcerns = scanText("Ingredients: water, citric acid, salt.", {
  includeConcerns: true,
});
check(
  "concerns opt-in surfaces GERD/LPR without changing risk",
  withConcerns.riskLevel === "low" &&
    withConcerns.warnings.some((w) => w.includes("GERD/LPR")),
);

console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) process.exit(1);
