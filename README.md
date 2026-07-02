# AllergyLens — OCR & Parser Engine

The logic / computer-vision side of AllergyLens: take a food-label image (or
raw text), extract the ingredients, detect common allergens, and return a clear
risk report. This branch (`ocr-parser-engine`) owns the engine; the Python
frontend lives on `ui-camera-results`.

## What's here

```
allergylens_engine/          # importable core package
├── __init__.py              # public API: scan_label(), scan_text()
├── ocr.py                   # image -> text (Tesseract, graceful fallback)
├── parser.py                # text -> clean ingredient list
├── allergen_engine.py       # ingredients -> detected allergens
├── risk_scoring.py          # allergens -> risk level + confidence
├── models.py                # ScanResult / DetectedAllergen dataclasses
└── data/
    ├── allergens.json           # allergen -> keyword map
    └── ingredient_aliases.json  # ambiguous ingredient -> possible allergens
api/
└── main.py                  # thin FastAPI wrapper over the package
tests/
└── test_engine.py           # pipeline tests (no OCR / network needed)
```

## Two ways for the frontend to use it

**1. Import the package directly** (simplest — same process):

```python
from allergylens_engine import scan_text, scan_label

result = scan_text("Ingredients: enriched wheat flour, sugar, whey.")
print(result.risk_level)   # "high"
print(result.to_dict())    # spec-shaped ScanResult (camelCase keys)

result = scan_label("label.jpg")   # runs OCR first
```

**2. Call the HTTP API** (decoupled):

```bash
uvicorn api.main:app --reload
# POST /scan/text   {"text": "..."}     -> ScanResult JSON
# POST /scan/image  multipart file      -> ScanResult JSON
# GET  /health
```

Both return the same spec-shaped `ScanResult` JSON, so the UI can pick either.

## The ScanResult contract

```jsonc
{
  "rawText": "Ingredients: ...",
  "ingredients": ["enriched wheat flour", "sugar", "whey"],
  "detectedAllergens": [
    { "allergen": "Wheat", "matchedIngredient": "enriched wheat flour",
      "severity": "high", "reason": "..." }
  ],
  "warnings": [],
  "riskLevel": "high",     // high | medium | low | unknown
  "confidence": "medium"   // high | medium | low
}
```

**Risk levels:** `high` = a direct allergen; `medium` = only ambiguous/alias
ingredients (needs review); `low` = none found; `unknown` = nothing readable.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# OCR also needs the Tesseract binary: brew install tesseract
pytest            # run the tests
```

The core (`scan_text`) runs on the standard library alone — the deps in
`requirements.txt` are only for OCR (`scan_label`) and the API.
