// OCR text extraction. Uses tesseract.js when available and degrades
// gracefully so the UI can fall back to manual text entry.
// Mirrors allergylens_engine/ocr.py.

export interface OcrResult {
  text: string;
  ok: boolean;
  error?: string;
}

/**
 * Extract text from an image. `image` is anything tesseract.js accepts
 * (a URL/path, a Buffer, a Blob, or an ImageLike). Returns `ok: false` with an
 * error message when OCR can't run, instead of throwing.
 */
export async function extractText(
  image: string | Buffer | Blob,
  lang = "eng",
): Promise<OcrResult> {
  let recognize: typeof import("tesseract.js").recognize;
  try {
    ({ recognize } = await import("tesseract.js"));
  } catch {
    return {
      text: "",
      ok: false,
      error: "tesseract.js not installed; use manual text input fallback.",
    };
  }

  try {
    const { data } = await recognize(image as never, lang);
    const text = (data.text ?? "").trim();
    if (!text) return { text: "", ok: false, error: "No text detected in image." };
    return { text, ok: true };
  } catch (err) {
    return { text: "", ok: false, error: `OCR failed: ${String(err)}` };
  }
}
