"""Cache public HTML with Windows curl's verified system TLS path."""

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from fetch_official import PlainText

ROOT = Path(__file__).resolve().parent / "sources"


def cache(source_id, url):
    """Require successful HTTP transfer; retain raw response and text hashes."""
    target = ROOT / f"{source_id}.html"
    if target.exists():
        raise FileExistsError(target)
    result = subprocess.run(
        ["curl.exe", "--fail", "--location", "--silent", "--show-error",
         "--max-time", "45", "--output", str(target), "--write-out", "%{json}", url],
        capture_output=True, text=True, check=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    transfer = json.loads(result.stdout)
    raw = target.read_bytes()
    assert len(raw) == int(transfer["size_download"])
    parser = PlainText()
    parser.feed(raw.decode("utf-8"))
    text = parser.text()
    target.with_suffix(".txt").write_text(text, encoding="utf-8")
    metadata = {
        "id": source_id, "requested_url": url,
        "retrieved_url": transfer["url_effective"],
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "as_of": "2026-10-13", "http_complete": True,
        "http_status": transfer["http_code"], "downloaded_bytes": len(raw),
        "content_sha256": hashlib.sha256(raw).hexdigest(),
        "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "characters": len(text), "tls_verify_result": transfer["ssl_verify_result"],
        "download_verification": "curl exit 0; HTTP failure checking; byte count matches transfer; system TLS verification enabled",
        "status": "retrieved_not_claim_verified",
    }
    target.with_suffix(".json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(source_id, len(text))


if __name__ == "__main__":
    cache(sys.argv[1], sys.argv[2])
