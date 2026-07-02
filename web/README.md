# AllergyLens — TypeScript / Next.js engine

A cross-compatible mirror of the Python engine (`../allergylens_engine`), built
in the spec's recommended stack (Next.js + TypeScript). Same logic, same
`ScanResult` JSON contract — pick whichever language your frontend uses.

## Layout (mirrors the spec's folder structure)

```
web/
├── lib/
│   ├── ocr.ts            # image -> text (tesseract.js, graceful fallback)
│   ├── parser.ts         # text -> clean ingredient list
│   ├── allergenEngine.ts # ingredients -> detected allergens + concerns
│   ├── riskScoring.ts    # allergens -> risk level + confidence
│   ├── index.ts          # public API: scanText(), scanLabel()
│   └── engine.test.ts    # dependency-free test runner
├── data/
│   ├── allergens.json
│   ├── ingredientAliases.json
│   └── dietaryConcerns.json
├── types/
│   ├── scan.ts           # ScanResult / DetectedAllergen
│   └── allergens.ts
└── app/
    └── api/scan/route.ts # POST /api/scan  (JSON text or multipart image)
```

> UI components (`app/page.tsx`, `components/*`) are intentionally left for the
> frontend owner — this branch only scaffolds the engine + its API route.

## Use it

```ts
import { scanText, scanLabel } from "@/lib";

const result = scanText("Ingredients: enriched wheat flour, sugar, whey.");
result.riskLevel;          // "high"
result.detectedAllergens;  // [{ allergen: "Wheat", ... }, ...]

const fromImage = await scanLabel(fileBlob); // runs OCR
```

Or over HTTP once Next is running (`npm run dev`):

```bash
curl -X POST localhost:3000/api/scan \
  -H "content-type: application/json" \
  -d '{"text":"Ingredients: milk, peanuts","includeConcerns":true}'
```

## Setup

```bash
cd web
npm install
npm run test        # runs lib/engine.test.ts via tsx (no Next needed)
npm run typecheck   # tsc --noEmit
npm run dev         # Next dev server + /api/scan
```

`tesseract.js` is an optional dependency — text scanning (`scanText`) works
without it; only image OCR (`scanLabel`) needs it.

## Parity with the Python engine

Both engines produce the identical `ScanResult` shape and share the same data
files, so the two frontends stay interchangeable:

| Concern            | Python                          | TypeScript                 |
| ------------------ | ------------------------------- | -------------------------- |
| Entry point        | `scan_text` / `scan_label`      | `scanText` / `scanLabel`   |
| Result keys        | `to_dict()` -> camelCase        | camelCase natively         |
| Risk levels        | high / medium / low / unknown   | same                       |
| Plural matching    | `almond` matches `almonds`      | same                       |
| Parenthetical flatten | yes                          | same                       |
| Dietary concerns   | opt-in warnings                 | opt-in warnings            |
