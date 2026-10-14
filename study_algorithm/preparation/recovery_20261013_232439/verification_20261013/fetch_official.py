"""Cache public official sources with hashes and visible retrieval/version status."""

import argparse
import hashlib
import html
import http.client
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AS_OF = "2026-10-13"


class PlainText(HTMLParser):
    """Extract visible HTML text while preserving article and paragraph breaks."""

    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden_depth = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag in {"script", "style"}:
            self.hidden_depth += 1
        if tag in {"p", "div", "br", "tr", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")
        if tag == "img" and "/flDownload.do" in attributes.get("src", ""):
            alternative = attributes.get("alt", "").strip()
            self.parts.append("\n[조문 이미지 대체텍스트] " + (alternative or "[대체텍스트 없음: 원본 이미지 확인 필요]") + "\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.hidden_depth:
            self.hidden_depth -= 1
        if tag in {"p", "div", "tr", "li"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden_depth:
            self.parts.append(data)

    def text(self):
        """Return readable nonempty lines."""
        return "\n".join(line.strip() for line in "".join(self.parts).splitlines() if line.strip())


def fetch(source_id, url, *, follow_iframe=True):
    """Cache an official resource; an incomplete response is never silently complete."""
    url = urllib.parse.quote(url, safe=":/?=&%#")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"})
    complete = True
    with urllib.request.urlopen(req, timeout=40) as response:
        try:
            raw = response.read()
        except http.client.IncompleteRead as exc:
            raw = exc.partial
            complete = False
        final_url = response.url
        charset = response.headers.get_content_charset() or "utf-8"
    content = raw.decode(charset, errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    if follow_iframe:
        frame = re.search(r'<iframe[^>]+src="([^"]+)"', content, re.I)
        if frame:
            return fetch(source_id, urllib.parse.urljoin(final_url, html.unescape(frame.group(1))), follow_iframe=False)
    # This is the same public body endpoint loaded by the official law viewer.
    if "/lsInfoP.do?" in final_url:
        return fetch(source_id, final_url.replace("/lsInfoP.do?", "/lsInfoR.do?"), follow_iframe=False)
    if "/admRulLsInfoP.do?" in final_url:
        return fetch(source_id, final_url.replace("/admRulLsInfoP.do?", "/admRulLsInfoR.do?"), follow_iframe=False)
    if "/admRulInfoP.do?" in final_url:
        return fetch(source_id, final_url.replace("/admRulInfoP.do?", "/admRulLsInfoR.do?"), follow_iframe=False)
    folder = ROOT / "sources"
    folder.mkdir(exist_ok=True)
    (folder / f"{source_id}.html").write_text(content, encoding="utf-8")
    parser = PlainText()
    parser.feed(content)
    text = parser.text()
    (folder / f"{source_id}.txt").write_text(text, encoding="utf-8")
    metadata = {
        "id": source_id, "requested_url": url, "retrieved_url": final_url,
        "retrieved_at": datetime.now(timezone.utc).isoformat(), "as_of": AS_OF,
        "http_complete": complete, "characters": len(text),
        "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "status": "retrieved_not_claim_verified" if complete else "incomplete_response_do_not_release",
        "effective_date_candidates": re.findall(r"시행\s*(20\d{2})[.\s-]+(\d{1,2})[.\s-]+(\d{1,2})", text)[:8],
    }
    (folder / f"{source_id}.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return metadata


def main():
    """Fetch a named public source specified explicitly by the reviewer."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z][a-z0-9_]+", args.id):
        raise ValueError("Source ID must be a safe ASCII identifier")
    print(json.dumps(fetch(args.id, args.url), ensure_ascii=False))


if __name__ == "__main__":
    main()
