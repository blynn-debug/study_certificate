"""Report saved approvals, individually held reviews, and untouched work separately."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent


def read_json(path: Path) -> Any:
    """Read a persisted UTF-8 artifact without changing its contents."""
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    """Write a complete item queue and a compact chapter tree from saved results."""
    items = read_json(ROOT / "item_verification_registry.json")["items"]
    summary = read_json(ROOT / "verification_summary.json")
    chapters = read_json(ROOT.parent / "target_analysis/outline.json")["chapters"]
    ids = {row["id"] for row in items}
    holds: dict[str, list[dict[str, Any]]] = {}
    for filename in (
        "subject1_holds.json", "subject2_holds.json", "subject3_holds.json", "root_holds.json",
        "final_bond_holds.json", "final_derivative_holds.json",
        "root_final_law_holds.json",
    ):
        path = ROOT / filename
        if not path.exists():
            continue
        data = read_json(path)
        rows = data["items"] if isinstance(data, dict) else data
        for row in rows:
            if row["id"] not in ids or not row.get("reason"):
                raise ValueError(f"Invalid individual hold in {filename}: {row}")
            holds.setdefault(row["id"], []).append({**row, "record_file": filename})
    prior = ROOT / "resume_progress.json"
    if prior.exists():
        for row in read_json(prior).get("reviewed_but_unreleased", []):
            holds.setdefault(row["id"], []).append({**row, "record_file": prior.name})

    correspondence = {}
    for path in sorted(ROOT.glob("*_correspondence_audit.json")):
        for row in read_json(path).get("items", []):
            if row.get("status") == "resolved":
                continue
            if row["id"] not in ids:
                raise ValueError(f"Unknown correspondence item: {row['id']}")
            correspondence.setdefault(row["id"], []).append({**row, "record_file": path.name})

    queue = []
    for row in items:
        released = row["source_state"] == "adjudicated_current"
        state = "released" if released else "reviewed_held" if row["id"] in holds else "pending"
        queue.append({"id": row["id"], "chapter_id": row["chapter_id"], "state": state,
                      "holds": [] if released else holds.get(row["id"], []),
                      "target_correspondence_recheck": correspondence.get(row["id"], [])})
    counts = {state: sum(row["state"] == state for row in queue)
              for state in ("released", "reviewed_held", "pending")}
    if counts["released"] != summary["individually_released_items"] or sum(counts.values()) != len(ids):
        raise ValueError("Progress and verification registry disagree")
    chapter_rows = []
    for chapter in chapters:
        selected = [row for row in queue if row["chapter_id"] == chapter["id"]]
        chapter_rows.append({
            "id": chapter["id"], "name": chapter["name"], "total": len(selected),
            **{state: sum(row["state"] == state for row in selected) for state in counts},
        })
    progress = {
        "recorded_at": datetime.now(timezone.utc).isoformat(), "as_of": summary["as_of"],
        "status": "in_progress" if counts["pending"] else "all_items_reviewed",
        "total": len(queue), "counts": counts, "chapters": chapter_rows,
        "all_targets_visited": counts["pending"] == 0,
        "all_targets_released": counts["released"] == len(queue) and not correspondence,
        "target_correspondence_recheck_count": len(correspondence),
        "live_model_validation": summary["live_natural_language_model_validation"],
        "warning": "A held review is not approval. Code tests do not validate live-model accuracy.",
        "items": queue,
    }
    lines = [f"전체 {len(queue)}문항 | 승인 {counts['released']} | 검토 후 보류 {counts['reviewed_held']} | 대기 {counts['pending']}"]
    for subject in ("S1", "S2", "S3"):
        lines.append(f"├─ {subject[1]}과목")
        for row in chapter_rows:
            if row["id"].startswith(subject):
                lines.append(f"│  ├─ {row['name']}: {row['released']}/{row['total']} 승인; "
                             f"보류 {row['reviewed_held']}; 대기 {row['pending']}")
    lines.append(f"├─ TARGET 원문 충실성 추가 재검토: {len(correspondence)}문항 (위 승인수와 중복 가능)")
    lines.append("└─ 실모델 채점 검증: " + summary["live_natural_language_model_validation"])
    for filename, content in (
        ("parallel_progress.json", json.dumps(progress, ensure_ascii=False, indent=2) + "\n"),
        ("progress_tree.txt", "\n".join(lines) + "\n"),
    ):
        path = ROOT / filename
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(path)
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
