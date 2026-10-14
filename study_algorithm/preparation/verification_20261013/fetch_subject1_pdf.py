"""Preserve a new PDF response and its digital text with verifiable hashes."""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

import pymupdf


def download(source_id: str, url: str) -> None:
    """Store a complete response and extraction under an unused source identifier."""
    base = Path(__file__).resolve().parent / "sources"
    target = base / source_id
    if target.with_suffix(".pdf").exists():
        raise FileExistsError(target)
    with urlopen(url, timeout=40) as response:
        raw = response.read()
        length = response.headers.get("Content-Length")
        if length is not None and int(length) != len(raw):
            raise ValueError("Incomplete HTTP response")
        metadata = {
            "id": source_id, "requested_url": url, "retrieved_url": response.url,
            "http_complete": True, "http_status": response.status,
            "http_content_length": length, "downloaded_bytes": len(raw),
            "retrieved_at": datetime.now(timezone.utc).isoformat(), "as_of": "2026-10-13",
            "pdf_sha256": hashlib.sha256(raw).hexdigest(),
        }
    with pymupdf.open(stream=raw, filetype="pdf") as document:
        pages = [{"page": number + 1, "text": page.get_text()} for number, page in enumerate(document)]
    text = "\n".join(page["text"] for page in pages)
    metadata.update(content_sha256=hashlib.sha256(text.encode()).hexdigest(), characters=len(text))
    target.with_suffix(".pdf").write_bytes(raw)
    target.with_suffix(".txt").write_text(text, encoding="utf-8")
    target.with_suffix(".json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    target.with_suffix(".pages.json").write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
    print(source_id, len(raw), len(pages), len(text))


if __name__ == "__main__":
    download(sys.argv[1], sys.argv[2])
