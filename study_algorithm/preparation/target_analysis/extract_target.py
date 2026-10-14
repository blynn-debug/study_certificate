"""Extract supplied exam PDFs with stable document and one-based page references."""

import hashlib
import json
from pathlib import Path

import pymupdf

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent.parent
DOCUMENTS = {
    "P12": "1과목_2과목.pdf",
    "P3": "3과목.pdf",
    "CALC": "계산문제.pdf",
    "MOCK": "모의고사.pdf",
    "NOTE": "핵심정리노트.pdf",
}


def save_json(path: Path, value: object) -> None:
    """Write Korean JSON without ASCII escaping."""
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    """Extract each page; extraction is not a claim of semantic review."""
    output = BASE / "extracted"
    output.mkdir(parents=True, exist_ok=True)
    manifest = []
    for document_id, filename in DOCUMENTS.items():
        source = ROOT / "src" / "target" / filename
        pages = []
        with pymupdf.open(source) as document:
            for index, page in enumerate(document):
                text = page.get_text(sort=True)
                pages.append({"page": index + 1, "text": text, "characters": len(text)})
            record = {
                "id": document_id,
                "path": source.relative_to(ROOT).as_posix(),
                "bytes": source.stat().st_size,
                "sha256": hashlib.file_digest(source.open("rb"), "sha256").hexdigest(),
                "pages": len(pages),
                "characters": sum(page["characters"] for page in pages),
                "low_text_pages": [page["page"] for page in pages if page["characters"] < 40],
                "bookmarks": document.get_toc(),
                "pdf_metadata": document.metadata,
                "semantic_review": "pending",
            }
        save_json(output / f"{document_id}.json", pages)
        (output / f"{document_id}.txt").write_text(
            "\n\n".join(f"=== {document_id} PDF page {page['page']} ===\n{page['text']}" for page in pages),
            encoding="utf-8",
        )
        manifest.append(record)
        print(json.dumps(record, ensure_ascii=False), flush=True)
    save_json(BASE / "target_manifest.json", {"documents": manifest, "page_numbering": "PDF one-based"})


if __name__ == "__main__":
    main()
