// Turn raw OCR/label text into a clean ingredient list.
// Mirrors allergylens_engine/parser.py.

const INGREDIENTS_HEADER = /ingredients?\s*[:\-]/i;
const END_MARKERS =
  /\b(contains|may contain|manufactured|distributed|allergen|nutrition|net wt|best by|directions|storage)\b/i;

/** Return the substring holding the ingredient list (whole text if no header). */
export function findIngredientsSection(rawText: string): string {
  if (!rawText) return "";

  const header = INGREDIENTS_HEADER.exec(rawText);
  let section = header ? rawText.slice(header.index + header[0].length) : rawText;

  const end = END_MARKERS.exec(section);
  if (end) section = section.slice(0, end.index);

  return section.trim();
}

/** Normalize whitespace and repair common OCR line-break artifacts. */
export function cleanText(rawText: string): string {
  let text = rawText.replace(/\r/g, "\n");
  // Join words split across a line break by a hyphen: "leci-\nthin" -> "lecithin".
  text = text.replace(/-\s*\n\s*/g, "");
  // Treat remaining newlines as spaces.
  text = text.replace(/\s*\n\s*/g, " ");
  // Collapse runs of whitespace.
  text = text.replace(/\s{2,}/g, " ");
  return text.trim();
}

function cleanIngredient(item: string): string {
  let out = item.trim().replace(/^[.;:*•·\-\s]+|[.;:*•·\-\s]+$/g, "");
  out = out.replace(/\s{2,}/g, " ").trim();
  return out.toLowerCase();
}

/** Parse raw text into a de-duplicated ingredient list. */
export function parseIngredients(rawText: string): string[] {
  let section = cleanText(findIngredientsSection(rawText));
  if (!section) return [];

  // Flatten parenthetical sub-ingredients so hidden allergens aren't lost:
  // "chocolate (cocoa, milk fat)" -> "chocolate, cocoa, milk fat".
  section = section.replace(/[()[\]]/g, ", ");

  const parts = section.split(/[,;•·|]| and /);

  const seen = new Set<string>();
  const ingredients: string[] = [];
  for (const part of parts) {
    const cleaned = cleanIngredient(part);
    if (!cleaned || cleaned.length < 2 || seen.has(cleaned)) continue;
    seen.add(cleaned);
    ingredients.push(cleaned);
  }
  return ingredients;
}
