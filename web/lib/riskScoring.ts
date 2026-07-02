// Roll detected allergens up into a risk level + confidence.
// Mirrors allergylens_engine/risk_scoring.py.

import type { Confidence, DetectedAllergen, RiskLevel } from "../types/scan";

export interface RiskScore {
  riskLevel: RiskLevel;
  confidence: Confidence;
  warnings: string[];
}

export function scoreRisk(
  ingredients: string[],
  detected: DetectedAllergen[],
  ocrOk = true,
): RiskScore {
  const warnings: string[] = [];

  if (ingredients.length === 0) {
    warnings.push("No ingredients could be read. Try a clearer photo or manual input.");
    return { riskLevel: "unknown", confidence: "low", warnings };
  }

  const hasHigh = detected.some((a) => a.severity === "high");
  const hasMedium = detected.some((a) => a.severity === "medium");

  let riskLevel: RiskLevel;
  if (hasHigh) {
    riskLevel = "high";
  } else if (hasMedium) {
    riskLevel = "medium";
    warnings.push(
      "Some ingredients are ambiguous and may hide allergens — review carefully.",
    );
  } else {
    riskLevel = "low";
  }

  let confidence = scoreConfidence(ingredients, ocrOk);
  if (riskLevel === "medium" && confidence === "high") confidence = "medium";

  return { riskLevel, confidence, warnings };
}

function scoreConfidence(ingredients: string[], ocrOk: boolean): Confidence {
  if (!ocrOk) return "low";
  if (ingredients.length >= 5) return "high";
  if (ingredients.length >= 2) return "medium";
  return "low";
}
