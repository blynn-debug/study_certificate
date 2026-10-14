"""Verify the manual subtitle reread ledger and link it to existing source rules."""

import hashlib
import json
from datetime import datetime
from pathlib import Path

PREPARATION = Path(__file__).resolve().parent.parent
ROOT = PREPARATION.parent


def read_json(name: str) -> object:
    """Read a preparation artifact including optional UTF-8 BOM."""
    return json.loads((PREPARATION / name).read_text(encoding="utf-8-sig"))


def write_json(name: str, value: object) -> None:
    """Save an updated preparation artifact."""
    (PREPARATION / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    """Validate paths, read intervals, source hashes, counts and rule references."""
    manifest = read_json("source_manifest.json")
    ledger = read_json("full_reread_01.json")
    coverage = read_json("source_coverage.json")
    rules = read_json("operational_rules.json")
    expected = {}
    for entry in manifest:
        expected[entry["path"]] = entry
        for copy in entry.get("copies", []):
            expected[copy["path"]] = {**copy, "id": entry["id"]}
    observed = ledger["completed"]
    assert len(observed) == len({entry["path"] for entry in observed}) == 42
    assert set(expected) == {entry["path"] for entry in observed}
    valid_rules = {rule["id"] for rule in rules["rules"]}
    source_rules = {
        source["id"]: sorted({rule for segment in source["segments"] for rule in segment["rule_ids"]})
        for source in coverage["sources"]
    }
    for entry in observed:
        source = expected[entry["path"]]
        assert entry["id"] == source["id"]
        assert entry["lines"] == source["lines"]
        intervals = entry["read_ranges"]
        if isinstance(intervals[0], int):
            intervals = [intervals]
        cursor = 1
        for start, end in intervals:
            assert start == cursor and end >= start
            cursor = end + 1
        assert cursor == source["lines"] + 1
        assert entry["note"].strip()
        digest = hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest()
        assert digest.lower() == source["sha256"].lower()
        entry["rule_ids"] = source_rules[entry["id"]]
        assert set(entry["rule_ids"]) <= valid_rules
    ledger["status"] = "complete"
    ledger["verification"] = {
        "checked_at": datetime.now().astimezone().isoformat(),
        "physical_files": len(observed),
        "unique_videos": len({entry["id"] for entry in observed}),
        "read_lines_including_duplicate": sum(entry["lines"] for entry in observed),
        "missing_files": 0,
        "missing_read_intervals": 0,
        "hash_mismatches": 0,
        "basis": "Manual full-text reading recorded in this session; code validates ledger completeness and source identity, not comprehension.",
        "scope": "The three subtitle folders. Newly supplied src/target exam PDFs have a separate analysis ledger.",
    }
    write_json("full_reread_01.json", ledger)
    blueprint = read_json("learning_assistant_blueprint.json")
    provenance = blueprint["review_provenance"]
    provenance.setdefault("previous_three_folder_audit", provenance["current_work"])
    provenance["current_work"] = "Fresh complete reread of all 42 physical subtitle TXT files across the three folders, including the duplicate: 10805 lines, 41 unique videos. See full_reread_01.json."
    provenance["limitation"] = "This records one fresh complete reread, not ten. Exam PDF analysis is tracked separately."
    blueprint["preparation_audit"]["reading_boundary"] = provenance["current_work"]
    blueprint["preparation_audit"]["artifacts"]["full_reread_verifier"] = "preparation/target_analysis/finalize_source_review.py"
    write_json("learning_assistant_blueprint.json", blueprint)
    print(json.dumps(ledger["verification"], ensure_ascii=False))


if __name__ == "__main__":
    main()
