// POST /api/scan — the engine's HTTP entry point for the UI.
//
// Accepts either:
//   * JSON:      { "text": "...", "includeConcerns"?: boolean }
//   * multipart: form-data with an "image" file (runs OCR)
//
// Returns a spec-shaped ScanResult (same JSON as the Python engine).

import { NextResponse } from "next/server";
import { scanLabel, scanText } from "@/lib";

export async function POST(req: Request) {
  const contentType = req.headers.get("content-type") ?? "";

  try {
    if (contentType.includes("application/json")) {
      const body = await req.json();
      const text = typeof body?.text === "string" ? body.text : "";
      if (!text.trim()) {
        return NextResponse.json(
          { error: "Field 'text' must not be empty." },
          { status: 400 },
        );
      }
      return NextResponse.json(
        scanText(text, { includeConcerns: Boolean(body?.includeConcerns) }),
      );
    }

    if (contentType.includes("multipart/form-data")) {
      const form = await req.formData();
      const file = form.get("image");
      if (!(file instanceof Blob) || file.size === 0) {
        return NextResponse.json(
          { error: "Provide a non-empty 'image' file." },
          { status: 400 },
        );
      }
      const includeConcerns = form.get("includeConcerns") === "true";
      const result = await scanLabel(file, { includeConcerns });
      return NextResponse.json(result);
    }

    return NextResponse.json(
      { error: "Send application/json or multipart/form-data." },
      { status: 415 },
    );
  } catch (err) {
    return NextResponse.json(
      { error: `Could not process request: ${String(err)}` },
      { status: 500 },
    );
  }
}
