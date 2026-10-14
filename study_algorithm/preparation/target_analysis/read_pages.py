"""Display complete extracted PDF pages for manual review, without clipping."""

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    """Read an inclusive one-based PDF page interval."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document")
    parser.add_argument("start", type=int)
    parser.add_argument("end", type=int)
    arguments = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    path = Path(__file__).resolve().parent / "extracted" / f"{arguments.document}.json"
    pages = json.loads(path.read_text(encoding="utf-8"))
    assert 1 <= arguments.start <= arguments.end <= len(pages)
    for page in pages[arguments.start - 1 : arguments.end]:
        print(f"\n=== {arguments.document} PDF page {page['page']} ===\n{page['text']}")


if __name__ == "__main__":
    main()
