"""Apply individually authored replacements while retaining prior review records."""

import ast
import json
from pathlib import Path
from pprint import pformat

ROOT = Path(__file__).resolve().parent


def apply(updates: list[dict]) -> None:
    """Replace only explicitly supplied IDs and append immutable old review snapshots."""
    import root_diversification_reviews

    path = ROOT / "root_diversification_reviews.py"
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)
    current = {row["id"]: row for row in root_diversification_reviews.REVIEWS}
    history_path = ROOT / "root_diversification_review_history.json"
    history = json.loads(history_path.read_text(encoding="utf-8")) if history_path.exists() else {"items": []}
    audit_path = ROOT / "root_diversification_correspondence_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    entries = {row["id"]: row for row in audit["items"]}
    locations = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            args = node.value.args
            if args and isinstance(args[0], ast.Constant) and isinstance(args[0].value, str):
                locations[args[0].value] = (node.lineno - 1, node.end_lineno)
    replacements = []
    for update in updates:
        item_id = update["id"]
        old = current[item_id]
        revised = dict(old)
        revised.update(update["review"])
        if "concept_review" in revised:
            revised["concept_review"] = dict(revised["concept_review"])
            revised["concept_review"]["derivation"] = revised["review_note"]
        history["items"].append({"id": item_id, "reason": "Restore all TARGET choice topics", "review": old})
        start, end = locations[item_id]
        replacements.append((start, end, "REVIEWS.append(" + pformat(revised, width=110, sort_dicts=False) + ")\n"))
        entries[item_id].update(status="resolved", resolution=update["resolution"],
                                reviewed_original_pages=[entries[item_id]["original_page"]],
                                prior_review_preserved_in=history_path.name)
    for start, end, replacement in sorted(replacements, reverse=True):
        lines[start:end] = [replacement]
    result = "".join(lines)
    ast.parse(result)
    for target, value in [(history_path, history), (audit_path, audit)]:
        target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    path.write_text(result, encoding="utf-8")


if __name__ == "__main__":
    import sys
    apply(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
