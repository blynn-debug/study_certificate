"""Cache official PDFs and index exact, bounded evidence in non-statutory sources."""

import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent


def save(path, value):
    """Keep Unicode evidence readable and reproducible."""
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cache_pdf(source_id, url):
    """Download a public official PDF, retaining both binary and extracted-text hashes."""
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=40) as response:
        raw = response.read()
        final_url = response.url
    if not raw.startswith(b"%PDF-"):
        raise ValueError("Expected a PDF, not an HTML denial or login page")
    with pymupdf.open(stream=raw, filetype="pdf") as document:
        pages = [{"page": i + 1, "text": page.get_text()} for i, page in enumerate(document)]
    text = "\n\n".join(f"[PDF page {p['page']}]\n{p['text']}" for p in pages)
    binary_hash = hashlib.sha256(raw).hexdigest()
    metadata = {
        "id": source_id, "requested_url": url, "retrieved_url": final_url,
        "retrieved_at": datetime.now(timezone.utc).isoformat(), "as_of": "2026-10-13",
        "http_complete": True, "content_sha256": binary_hash, "binary_sha256": binary_hash,
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "pages": len(pages), "characters": len(text), "status": "retrieved_not_claim_verified",
    }
    folder = ROOT / "sources"
    (folder / f"{source_id}.pdf").write_bytes(raw)
    (folder / f"{source_id}.txt").write_text(text, encoding="utf-8")
    save(folder / f"{source_id}.pages.json", pages)
    save(folder / f"{source_id}.json", metadata)
    return metadata


def register_units(source_id, units):
    """Index reviewed spans with exact source positions; never mark the whole source reviewed.

    Each unit is (label, start, end). Duplicate labels and invalid spans fail closed.
    The legal evidence reader accepts these explicit labels without pretending they are laws.
    """
    source = ROOT / "sources" / f"{source_id}.txt"
    text = source.read_text(encoding="utf-8")
    metadata = json.loads(source.with_suffix(".json").read_text(encoding="utf-8"))
    if not metadata["http_complete"]:
        raise ValueError("Incomplete source")
    items = []
    for label, start, end in units:
        if not 0 <= start < end <= len(text):
            raise ValueError(f"Invalid evidence span: {label}")
        value = text[start:end].strip()
        items.append({
            "id": f"{source_id}:{label}", "source_id": source_id, "article": label,
            "heading": label, "text": value, "start": start, "end": end,
            "sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(),
        })
    if len(items) != len({item["article"] for item in items}):
        raise ValueError("Duplicate evidence unit")
    save(ROOT / "articles" / f"{source_id}.json", {
        "source_id": source_id, "source_metadata": metadata,
        "kind": "official_publication_selected_units", "count": len(items), "items": items,
        "warning": "These spans support only individually reviewed claims, not the whole publication.",
    })
    return items


def provision_units(source_id, labels):
    """Select exact GIPS headings, excluding cross-references and subsequent provisions."""
    text = (ROOT / "sources" / f"{source_id}.txt").read_text(encoding="utf-8")
    headings = list(re.finditer(r"(?m)^Provision ([1-8]\.[ABC]\.\d+(?:\.[a-z])?)\s*$", text))
    units = []
    for label in labels:
        matches = [(i, match) for i, match in enumerate(headings) if match.group(1) == label]
        if len(matches) != 1:
            raise ValueError(f"Ambiguous or missing provision heading: {label}")
        i, match = matches[0]
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        units.append((label, match.start(), end))
    return register_units(source_id, units)
