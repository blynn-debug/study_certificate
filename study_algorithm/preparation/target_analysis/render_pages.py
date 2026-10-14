"""Render source PDF pages for visual OCR verification."""

import argparse
import json
from pathlib import Path

import pymupdf


def main() -> None:
    """Render selected one-based pages to local PNGs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document")
    parser.add_argument("pages", nargs="+", type=int)
    arguments = parser.parse_args()
    base = Path(__file__).resolve().parent
    manifest = json.loads((base / "target_manifest.json").read_text(encoding="utf-8"))
    source = next(item for item in manifest["documents"] if item["id"] == arguments.document)
    output = base / "rendered"
    output.mkdir(exist_ok=True)
    with pymupdf.open(base.parent.parent / source["path"]) as document:
        for number in arguments.pages:
            path = output / f"{arguments.document}_{number:04}.png"
            document[number - 1].get_pixmap(matrix=pymupdf.Matrix(1.4, 1.4)).save(path)
            print(path)


if __name__ == "__main__":
    main()
