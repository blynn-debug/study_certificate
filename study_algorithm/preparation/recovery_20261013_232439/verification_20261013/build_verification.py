"""Assemble scoped evidence, per-item status, and outstanding work without inflated counts."""

import json
import sys
from collections import Counter
from pathlib import Path

from claim_reviews import CLAIMS
from legal_index import read_article

ROOT = Path(__file__).resolve().parent
EVAL = ROOT.parent / "eval"
ANALYSIS = ROOT.parent / "target_analysis"
sys.path.insert(0, str(EVAL))
from release_policy import is_current_release
from correction_links import correction_candidates


def load(path):
    """Read UTF-8 JSON."""
    return json.loads(path.read_text(encoding="utf-8"))


def save(name, value):
    """Write a derived artifact deterministically."""
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    """Keep collection, claim verification, item release, and live testing separate."""
    topics = {x["id"] for x in load(ANALYSIS / "topic_learning_routes.json")["items"]}
    issues = load(ANALYSIS / "quality_issues.json")["items"]
    issue_ids = {x["id"] for x in issues}
    verified = []
    for record in CLAIMS:
        row = dict(record)
        if not set(row["topic_ids"]) <= topics or not set(row["issue_ids"]) <= issue_ids:
            raise ValueError(f"Unknown topic or issue in {row['id']}")
        evidence = []
        for reference in row["article_refs"]:
            source_id, article = reference.split(":", 1)
            selected = read_article(source_id, article)
            metadata = load(ROOT / "sources" / f"{source_id}.json")
            if not metadata["http_complete"]:
                raise ValueError("Incomplete source cannot support a verified claim")
            evidence.append({
                "id": reference, "url": metadata["retrieved_url"],
                "source_content_sha256": metadata["content_sha256"],
                "article_sha256": selected["sha256"], "text": selected["text"],
            })
        row["evidence"] = evidence
        verified.append(row)
    save("verified_claims.json", {
        "as_of": "2026-10-13", "count": len(verified), "items": verified,
        "unit": "scoped claim; not a whole question, page, topic, or law",
    })
    releases_path = ROOT / "item_releases.json"
    releases = load(releases_path)["items"] if releases_path.exists() else {}
    corrections_path = ROOT / "source_corrections.json"
    corrections = load(corrections_path)["items"] if corrections_path.exists() else []
    contracts = load(EVAL / "item_contracts.json")["items"]
    packets = {x["id"]: x for x in load(EVAL / "answer_packets.json")["items"]}
    rows = []
    claim_map = {row["id"]: row for row in verified}
    math_path = ROOT / "verified_math_cases.json"
    math_cases = {row["id"]: row for row in load(math_path)["items"]} if math_path.exists() else {}
    for item in contracts:
        relevant = [x["id"] for x in verified if set(x["topic_ids"]) & set(item["topic_ids"])]
        item_corrections = [x for x in corrections if item["id"] in x["item_ids"]]
        correction_ids = [x["id"] for x in item_corrections]
        released = is_current_release(releases.get(item["id"], {}), item_corrections)
        rows.append({
            "id": item["id"], "chapter_id": item["chapter_id"], "kind": item["kind"],
            "topic_ids": item["topic_ids"],
            "publisher_answer": item["publisher_answer"],
            "claim_candidates": relevant,
            "issue_candidates": item["page_review_candidates"],
            "source_state": "adjudicated_current" if released else
                            "held_source_correction" if correction_ids else "whole_item_review_pending",
            "confirmed_correction_ids": correction_ids,
            "related_correction_candidates": [
                {key: value for key, value in candidate.items() if key != "record"}
                for candidate in correction_candidates(packets[item["id"]], corrections, claim_map, math_cases)
            ],
            "unresolved_correction_ids": [] if released else correction_ids,
            "original_source_state": "held_source_correction" if correction_ids else "not_asserted_faulty",
            "prompt_variant": releases.get(item["id"], {}).get("prompt_variant", "source_compatible"),
            "clean_prompt_state": "reviewed" if released else "not_released",
            "question_private_context": "fragment_and_source_pages" if packets[item["id"]]["question_text"] else "source_pages",
            "semantic_backend": "implemented; live_provider_validation_pending",
            "candidate_mapping_is_not_verification": True,
        })
    if set(releases) - set(packets):
        raise ValueError("Item release points outside the original corpus")
    save("item_verification_registry.json", {"count": len(rows), "items": rows})
    issue_rows = []
    for issue in issues:
        linked = [x["id"] for x in verified if issue["id"] in x["issue_ids"]]
        issue_rows.append({
            **issue, "verified_claim_ids": linked,
            "recomputed_math_case_ids": [row["id"] for row in math_cases.values() if issue["id"] in row["issue_ids"]],
            "adjudication_state": "scoped_claims_added_item_impact_review_needed" if linked else "further_adjudication_required",
            "affected_item_candidates": [
                item["id"] for item in rows if issue["id"] in item["issue_candidates"]
            ],
            "warning": "Same-page links alone do not establish a faulty question.",
        })
    save("issue_adjudication_registry.json", {"count": len(issue_rows), "items": issue_rows})
    summary = {
        "as_of": "2026-10-13", "status": "in_progress",
        "original_items": len(rows), "existing_issue_notes": len(issue_rows),
        "scoped_verified_claims": len(verified),
        "recomputed_mathematical_prompt_variants": len(math_cases),
        "individually_reasoned_concept_variants": sum(bool(row.get("concept_review")) for row in releases.values()),
        "individually_released_items": sum(x["source_state"] == "adjudicated_current" for x in rows),
        "confirmed_correction_records": len(corrections),
        "items_held_for_confirmed_correction": sum(x["source_state"] == "held_source_correction" for x in rows),
        "items_with_original_source_corrections": sum(bool(x["confirmed_correction_ids"]) for x in rows),
        "released_corrected_variants": sum(x["source_state"] == "adjudicated_current" and bool(x["confirmed_correction_ids"]) for x in rows),
        "items_with_related_correction_candidates": sum(bool(x["related_correction_candidates"]) for x in rows),
        "item_states": dict(Counter(x["source_state"] for x in rows)),
        "live_natural_language_model_validation": "not_run_no_configured_provider",
        "complete_current_law_item_verification": False,
        "do_not_report": "Full claim verification or 2292 validated semantic grades.",
    }
    save("verification_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
