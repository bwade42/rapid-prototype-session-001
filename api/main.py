"""Thin FastAPI wrapper around the AllergyLens engine.

Run locally:

    uvicorn api.main:app --reload

Endpoints:
* ``GET  /health``       - liveness check.
* ``POST /scan/text``    - JSON ``{"text": "..."}`` -> ScanResult.
* ``POST /scan/image``   - multipart file upload  -> ScanResult (runs OCR).

Both scan endpoints return the spec-shaped ScanResult (camelCase keys) so the
same JSON contract works whether the frontend imports the package directly or
calls over HTTP.
"""

from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from allergylens_engine import scan_label, scan_text

app = FastAPI(title="AllergyLens Engine", version="0.1.0")

# Wide-open CORS for the 1-hour prototype; tighten before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScanTextRequest(BaseModel):
    text: str
    include_concerns: bool = False


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/scan/text")
def scan_text_endpoint(req: ScanTextRequest) -> dict:
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Field 'text' must not be empty.")
    return scan_text(req.text, include_concerns=req.include_concerns).to_dict()


@app.post("/scan/image")
async def scan_image_endpoint(
    file: UploadFile = File(...), include_concerns: bool = False
) -> dict:
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")
    return scan_label(image_bytes, include_concerns=include_concerns).to_dict()
