#!/usr/bin/env python3
"""AllergyLens CLI demo — scan a label from a file, an image, or stdin.

Examples:
    python demo.py examples/spec_example.txt
    python demo.py examples/granola_bar.txt --concerns
    python demo.py label_photo.jpg --image
    echo "Ingredients: milk, sugar" | python demo.py

This is the manual-input fallback path in action, and a quick way to eyeball
the engine without the frontend.
"""

from __future__ import annotations

import argparse
import sys

from allergylens_engine import scan_label, scan_text
from allergylens_engine.models import ScanResult

# Map risk level -> a plain-text banner so the CLI reads like the spec's result.
_RISK_BANNER = {
    "high": "⛔  CONTAINS ALLERGEN — High Risk",
    "medium": "⚠️   WARNING — Medium Risk (needs review)",
    "low": "✅  SAFE — Low Risk (no known allergens)",
    "unknown": "❓  UNABLE TO DETERMINE",
}


def _print_report(result: ScanResult) -> None:
    print("=" * 52)
    print(_RISK_BANNER.get(result.risk_level, result.risk_level))
    print(f"Confidence: {result.confidence}")
    print("=" * 52)

    if result.ingredients:
        print("\nIngredients read:")
        for ing in result.ingredients:
            print(f"  • {ing}")

    if result.detected_allergens:
        print("\nDetected allergens:")
        for a in result.detected_allergens:
            tag = "DIRECT" if a.severity == "high" else "review"
            print(f"  [{tag}] {a.allergen}  ←  {a.matched_ingredient}")

    if result.warnings:
        print("\nNotes:")
        for w in result.warnings:
            print(f"  ! {w}")
    print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan a food label with AllergyLens.")
    parser.add_argument(
        "source",
        nargs="?",
        help="Path to a label text file or image. Omit to read text from stdin.",
    )
    parser.add_argument(
        "--image", action="store_true", help="Treat source as an image and run OCR."
    )
    parser.add_argument(
        "--concerns",
        action="store_true",
        help="Also flag dietary triggers (GERD/LPR, histamine).",
    )
    args = parser.parse_args(argv)

    if args.image:
        if not args.source:
            parser.error("--image requires an image path.")
        result = scan_label(args.source, include_concerns=args.concerns)
    else:
        if args.source:
            with open(args.source, encoding="utf-8") as fh:
                text = fh.read()
        else:
            text = sys.stdin.read()
        result = scan_text(text, include_concerns=args.concerns)

    _print_report(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
