// ScanResult / DetectedAllergen — the contract shared with the UI and the
// Python engine (identical JSON shape).

export type RiskLevel = "low" | "medium" | "high" | "unknown";
export type Confidence = "low" | "medium" | "high";
export type Severity = "low" | "medium" | "high";

export interface DetectedAllergen {
  allergen: string;
  matchedIngredient: string;
  severity: Severity;
  reason: string;
}

export interface ScanResult {
  rawText: string;
  ingredients: string[];
  detectedAllergens: DetectedAllergen[];
  warnings: string[];
  riskLevel: RiskLevel;
  confidence: Confidence;
}
