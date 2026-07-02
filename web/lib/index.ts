// Public API for the TypeScript engine — mirror of the Python package.
//
//   import { scanText, scanLabel } from "@/lib";
//   const result = scanText("Ingredients: enriched wheat flour, sugar, whey.");
//   result.riskLevel; // "high"

import { detectAllergens, detectDietaryConcerns } from "./allergenEngine";
import { extractText } from "./ocr";
import { parseIngredients } from "./parser";
import { scoreRisk } from "./riskScoring";
import type { ScanResult } from "../types/scan";

export type { ScanResult, DetectedAllergen } from "../types/scan";
export { detectAllergens, detectDietaryConcerns } from "./allergenEngine";

interface ScanOptions {
  ocrOk?: boolean;
  includeConcerns?: boolean;
}

/** Run the full pipeline on already-extracted label text. */
export function scanText(rawText: string, opts: ScanOptions = {}): ScanResult {
  const { ocrOk = true, includeConcerns = false } = opts;

  const ingredients = parseIngredients(rawText);
  const detectedAllergens = detectAllergens(ingredients);
  const { riskLevel, confidence, warnings } = scoreRisk(
    ingredients,
    detectedAllergens,
    ocrOk,
  );

  const allWarnings = includeConcerns
    ? [...warnings, ...detectDietaryConcerns(ingredients)]
    : warnings;

  return {
    rawText,
    ingredients,
    detectedAllergens,
    warnings: allWarnings,
    riskLevel,
    confidence,
  };
}

/** Run OCR on an image, then the full pipeline. */
export async function scanLabel(
  image: string | Buffer | Blob,
  opts: ScanOptions = {},
): Promise<ScanResult> {
  const ocr = await extractText(image);
  if (!ocr.ok) {
    return {
      rawText: "",
      ingredients: [],
      detectedAllergens: [],
      warnings: [
        ocr.error ?? "OCR failed.",
        "Try a clearer photo or enter text manually.",
      ],
      riskLevel: "unknown",
      confidence: "low",
    };
  }
  return scanText(ocr.text, { ocrOk: true, includeConcerns: opts.includeConcerns });
}
