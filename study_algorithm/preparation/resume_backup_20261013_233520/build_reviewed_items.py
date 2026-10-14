"""Publish hand-reviewed item records with source and legal-evidence bindings."""

import json
import sys
from pathlib import Path

from tax_followup_reviews import REVIEWS as TAX_REVIEWS
from product_followup_reviews import REVIEWS as PRODUCT_REVIEWS

REVIEWS = [*TAX_REVIEWS, *PRODUCT_REVIEWS]

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "eval"))
from release_policy import fingerprint, is_current_release, variant_fingerprint


def load(path):
    """Read the exact locally reviewed artifact."""
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    """Validate a complete review batch before publishing any of its records."""
    packets = {row["id"]: row for row in load(ROOT.parent / "eval/answer_packets.json")["items"]}
    claims = {row["id"]: row for row in load(ROOT / "verified_claims.json")["items"]}
    corrections = load(ROOT / "source_corrections.json")
    findings = {row["id"]: row for row in corrections["items"]}
    releases = load(ROOT / "item_releases.json")
    if len(REVIEWS) != len({row["id"] for row in REVIEWS}):
        raise ValueError("Duplicate individually reviewed item")
    for row in REVIEWS:
        packet = packets[row["id"]]
        concept_review = row.get("concept_review")
        if concept_review and not all(concept_review.get(key) for key in ("derivation", "assumptions")):
            raise ValueError("A conceptual review needs its reasoning and assumptions")
        if ((not row["claim_ids"] and not concept_review)
                or not set(row["claim_ids"]) <= set(claims)):
            raise ValueError("Missing official claim for individually reviewed item")
        if any(claims[key]["as_of"] != "2026-10-13" for key in row["claim_ids"]):
            raise ValueError("Official claim date does not match the reviewed item")
        source_ref = f"{packet['document']}:{packet['question_page']}"
        if row["source_finding"]:
            key = f"R-{row['id']}"
            findings[key] = {
                "id": key, "item_ids": [row["id"]], "refs": [source_ref],
                "claim_ids": row["claim_ids"], "classification": "individually_reviewed_source_correction",
                "finding": row["source_finding"],
                "learner_treatment": "원문의 오류는 학습자에게 감점하지 않는다. 조건과 정답을 검토한 수정 문항에 한해 채점한다.",
                "original_exam_answer_impact": "corrected_variant_only_original_not_retroactively_approved",
            }
        matched = [finding for finding in findings.values() if row["id"] in finding["item_ids"]]
        release = {
            "state": "adjudicated_current", "as_of": "2026-10-13",
            "clean_prompt": row["clean_prompt"], "answer": row["answer"],
            "answer_kind": row["answer_kind"], "prompt_correspondence_reviewed": True,
            "evidence": [source_ref, *row["claim_ids"]],
            "original_publisher_answer": packet["publisher_answer"],
            "review_note": row["review_note"],
            "reviewed_claim_sha256": {key: fingerprint(claims[key]) for key in row["claim_ids"]},
            "reviewed_packet_sha256": fingerprint(packet),
            "scope": "Only this explicitly worded prompt; not every statement on its source page.",
        }
        if concept_review:
            release["concept_review"] = concept_review
            release["reviewed_concept_sha256"] = fingerprint(concept_review)
            release["reviewed_prompt_sha256"] = variant_fingerprint(release)
            release["evidence"].append(f"concept:{row['id']}")
        if matched:
            release["prompt_variant"] = "corrected_reviewed_prompt"
            release["correction_resolution"] = {
                finding["id"]: {"reviewed_correction_sha256": fingerprint(finding),
                                 "resolution_note": row["review_note"]}
                for finding in matched
            }
            release["corrected_variant_sha256"] = variant_fingerprint(release)
        if not is_current_release(release, matched):
            raise ValueError("Invalid individually reviewed release")
        releases["items"][row["id"]] = release
    corrections["items"] = list(findings.values())
    for name, data in (("source_corrections.json", corrections), ("item_releases.json", releases)):
        (ROOT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Published {len(REVIEWS)} individually reviewed follow-up prompts.")


if __name__ == "__main__":
    main()
