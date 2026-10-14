"""Inspect OCR words and normalized positions on one PDF page."""

import argparse
import json
import sys
from pathlib import Path

import pymupdf


def main() -> None:
    """Print normalized OCR coordinates for extraction debugging."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document")
    parser.add_argument("page", type=int)
    arguments = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    base = Path(__file__).resolve().parent
    manifest = json.loads((base / "target_manifest.json").read_text(encoding="utf-8"))
    source = next(item for item in manifest["documents"] if item["id"] == arguments.document)
    with pymupdf.open(base.parent.parent / source["path"]) as document:
        page = document[arguments.page - 1]
        for x0, y0, x1, y1, word, *_ in page.get_text("words", sort=True):
            print(f"{x0/page.rect.width:.3f} {y0/page.rect.height:.3f} {x1/page.rect.width:.3f} {y1/page.rect.height:.3f} {word}")


if __name__ == "__main__":
    main()
