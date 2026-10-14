"""Cache distinct official webpages without touching shared source registries."""

import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class TextParser(HTMLParser):
    """Extract visible text without optional dependencies."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden = False

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in {"script", "style"}:
            self.hidden = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self.hidden = False

    def handle_data(self, data: str) -> None:
        if not self.hidden and data.strip():
            self.parts.append(data.strip())


def cache(source_id: str, url: str) -> str:
    """Retain a complete HTTP response and parsed text for bounded indexing."""
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=40) as response:
        raw = response.read()
        final_url = response.url
    parser = TextParser()
    parser.feed(raw.decode("utf-8"))
    value = "\n".join(parser.parts)
    metadata = {
        "id": source_id, "requested_url": url, "retrieved_url": final_url,
        "retrieved_at": datetime.now(timezone.utc).isoformat(), "as_of": "2026-10-13",
        "http_complete": True, "content_sha256": hashlib.sha256(raw).hexdigest(),
        "text_sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(),
        "characters": len(value), "status": "retrieved_not_claim_verified",
    }
    base = ROOT / "sources" / source_id
    base.with_suffix(".html").write_bytes(raw)
    base.with_suffix(".txt").write_text(value, encoding="utf-8")
    base.with_suffix(".json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return value


if __name__ == "__main__":
    source_id = "s1_krx_elw_trading"
    value = cache(source_id, "https://regulation.krx.co.kr/contents/RGL/03/03060300/RGL03060300.jsp")
    start = value.index("매매수량단위")
    end = value.index("컨텐츠 문의", start)
    metadata = json.loads((ROOT / "sources" / f"{source_id}.json").read_text(encoding="utf-8"))
    passage = value[start:end].strip()
    index = {
        "source_id": source_id, "source_metadata": metadata,
        "kind": "official_publication_selected_units", "count": 1,
        "items": [{"id": f"{source_id}:매매제도", "source_id": source_id,
                   "article": "매매제도", "heading": "매매제도", "text": passage,
                   "start": start, "end": end,
                   "sha256": hashlib.sha256(passage.encode("utf-8")).hexdigest()}],
        "warning": "Only the identified passage supports separately reviewed claims.",
    }
    (ROOT / "articles" / f"{source_id}.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(value[start:end])
