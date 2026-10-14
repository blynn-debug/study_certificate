"""Inspect contents pages or a compact page catalog without claiming full review."""

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    """Print complete contents pages or explicitly abbreviated page previews."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=100000)
    arguments = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    path = Path(__file__).resolve().parent / "extracted" / f"{arguments.document}.json"
    for page in json.loads(path.read_text(encoding="utf-8")):
        if not arguments.start <= page["page"] <= arguments.end:
            continue
        compact = " ".join(page["text"].split())
        if arguments.preview:
            print(f"{arguments.document} p{page['page']}: {compact[:100]} ... [preview only]")
        elif "학습체크" in compact.replace(" ", ""):
            print(f"=== {arguments.document} p{page['page']} ===\n{page['text']}")


if __name__ == "__main__":
    main()
