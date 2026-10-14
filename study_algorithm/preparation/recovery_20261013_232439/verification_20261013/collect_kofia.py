"""Retrieve current KOFIA versions discovered in its public current-law tree."""

import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fetch_official import ROOT, fetch

WANTED = {
    "135": "kofia_sanctions", "136": "kofia_business",
    "137": "kofia_business_details", "138": "kofia_personnel",
    "139": "kofia_personnel_details", "140": "kofia_underwriting",
    "141": "kofia_terms", "149": "kofia_recommendation",
    "150": "kofia_internal_control", "154": "kofia_ethics",
    "333": "kofia_business_ethics", "346": "kofia_consumer",
    "339": "kofia_complex", "322": "kofia_qib",
    "323": "kofia_qib_details", "134": "kofia_fx",
    "316": "kofia_isa_trust", "317": "kofia_isa_managed",
    "343": "kofia_isa_brokerage", "297": "kofia_kotc",
}
AS_OF_PINS = {
    "136": ("1803", "1811은 2026-12-01 시행: 2026-10-13 적용 제외"),
    "339": ("1745", "1812는 2026-12-01 시행: 2026-10-13 적용 제외"),
}


def collect_one(entry):
    """Keep version selection evidence separate from content verification."""
    seq, history, name = entry
    selected_history, reason = AS_OF_PINS.get(seq, (history, "공식 최신본; 부칙의 시행조건 별도 확인"))
    history = selected_history
    source_id = WANTED[seq]
    url = ("https://law.kofia.or.kr/service/law/lawFullScreenContent.do?"
           f"historySeq={history}&seq={seq}")
    path = ROOT / "sources" / f"{source_id}.json"
    if path.exists():
        metadata = json.loads(path.read_text(encoding="utf-8"))
        if (metadata["http_complete"] and metadata["characters"] > 2000
                and f"historySeq={history}" in metadata["requested_url"]
                and "history_seq" in metadata):
            return metadata
    for _ in range(3):
        metadata = fetch(source_id, url, follow_iframe=False)
        if metadata["http_complete"]:
            break
    metadata.update(
        name=name, kofia_seq=seq, history_seq=history,
        version_selection=reason,
        version_selection_source="sources/kofia_tree.html",
    )
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return metadata


def main():
    """Collect only the regulations relevant to the supplied exam corpus."""
    tree = (ROOT / "sources/kofia_tree.html").read_text(encoding="utf-8")
    entries = []
    for line in tree.splitlines():
        if ".action=" not in line:
            continue
        values = re.findall(r"'([^']*)'", line)
        if len(values) > 10 and values[0] in WANTED:
            entries.append((values[0], values[-2], values[2]))
    if len(entries) != len(WANTED):
        raise ValueError("Incomplete current KOFIA tree")
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(collect_one, entries))
    (ROOT / "kofia_registry.json").write_text(
        json.dumps({"count": len(results), "items": results}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    for item in results:
        print(item["id"], item["history_seq"], item["characters"], item["http_complete"])


if __name__ == "__main__":
    main()
