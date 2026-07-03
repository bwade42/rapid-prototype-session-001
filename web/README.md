# AllergyLens — Web App & Engine

**🔗 Live: https://bwade42.github.io/rapid-prototype-session-001/**

Scan a food label (photo, live camera, or pasted text), extract the
ingredients, and see whether they match your allergy profile. Runs **fully in
the browser** — no server — so it works on GitHub Pages.

## What's in here

```
web/
├── allergy-scanner.html   # the app UI (profile → scan → result)
├── support.js             # UI runtime (React/Babel auto-loaded from CDN)
├── engine.browser.js      # client-side engine: parse + allergen match + OCR
├── index.html             # redirect to allergy-scanner.html
├── data/                  # allergen + alias + dietary-concern data (JSON)
│
├── lib/                   # TypeScript engine (Node/Next reference build)
│   ├── ocr.ts  parser.ts  allergenEngine.ts  riskScoring.ts  index.ts
│   └── engine.test.ts
├── types/                 # ScanResult / DetectedAllergen types
└── app/api/scan/route.ts  # optional Next.js API route (server-side use)
```

The **deployed app** is `allergy-scanner.html` + `support.js` +
`engine.browser.js`. The **`lib/` TypeScript engine** is a Node/Next reference
build (same logic, run via `npm run test`); it is not needed for the live site.

## Using the app

1. **Allergy Profile** — pick the allergens you avoid (or add custom ones).
2. **Scan a label** — three input paths:
   - **Upload Photo** — pick a label image; runs OCR.
   - **Live Camera** — streams your device camera; **Capture Label** grabs a
     frame and runs OCR. Needs camera permission and a secure context
     (`https://` or `localhost`). If permission is denied or no camera exists,
     it falls back with a message pointing you to upload/paste.
   - **Paste ingredients text** — the reliable manual fallback; skips OCR.
3. **Result** — Safe / Unsure / Not safe, with the flagged ingredients and the
   full parsed list, checked against your profile.

### OCR notes
OCR uses [tesseract.js](https://github.com/naptha/tesseract.js) loaded from a
CDN on first use (~a few MB download, a few seconds to run). Real label photos
work best; blurry images may read poorly — paste text if OCR struggles.

## Run locally

Any static server works (the app is just files):

```bash
cd web
python3 -m http.server 4173
# open http://localhost:4173/allergy-scanner.html
```

The page pulls React/ReactDOM/Babel and tesseract.js from unpkg, so it needs
internet access.

### TypeScript engine tests (optional)

```bash
cd web
npm install
npm run test        # runs lib/engine.test.ts via tsx
npm run typecheck   # tsc --noEmit
```

## Engine parity

The same logic exists in three places, all producing the identical `ScanResult`
shape and sharing the same allergen data:

| Build            | File(s)                       | Used for                     |
| ---------------- | ----------------------------- | ---------------------------- |
| Browser (JS)     | `engine.browser.js`           | the live app / GitHub Pages  |
| TypeScript       | `lib/*.ts`                    | Node/Next reference + tests  |
| Python           | `../allergylens_engine/`      | Python frontend / FastAPI    |

Shared behavior: `Ingredients:` section detection, hyphenated line-break repair,
parenthetical flattening (`chocolate (milk)` → keeps `milk`), plural-aware
matching (`almond` → `almonds`), direct (high) vs. alias (medium) severity, and
opt-in GERD/LPR + histamine dietary-concern warnings.

## Deployment

Pushing to `main` runs [`.github/workflows/pages.yml`](../.github/workflows/pages.yml),
which publishes this `web/` directory to GitHub Pages. Only `main` is allowed to
deploy to the `github-pages` environment.
