"""Publish explicitly reviewed mathematical variants and preserve source defects."""

import hashlib
import json
import sys
from pathlib import Path

from math_reviews import CASES

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "eval"))
from release_policy import fingerprint, is_current_release, variant_fingerprint


def read(path):
    """Read project UTF-8 JSON."""
    return json.loads(path.read_text(encoding="utf-8"))


def write(name, value):
    """Keep Unicode proof notes and exact hashes."""
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    """Validate all arithmetic before writing any approvals."""
    if len(CASES) != len({row["id"] for row in CASES}):
        raise ValueError("Duplicate mathematical case")
    packets = {row["id"]: row for row in read(ROOT.parent / "eval/answer_packets.json")["items"]}
    pages = {row["page"]: row["text"] for row in read(ROOT.parent / "target_analysis/extracted/CALC.json")}
    issue_ids = {row["id"] for row in read(ROOT.parent / "target_analysis/quality_issues.json")["items"]}
    claims = {row["id"]: row for row in read(ROOT / "verified_claims.json")["items"]}
    rows = []
    corrections = read(ROOT / "source_corrections.json")
    findings = {row["id"]: row for row in corrections["items"]}
    for case in CASES:
        packet = packets[case["id"]]
        if packet["document"] != "CALC" or packet["question_page"] not in case["pages"]:
            raise ValueError("Mathematical review refers to another source")
        if not set(case["issue_ids"]) <= issue_ids:
            raise ValueError("Unknown mathematical issue note")
        if not set(case["claim_ids"]) <= set(claims):
            raise ValueError("Tax calculation requires registered official claims")
        if any(claims[key]["as_of"] != case["as_of"] for key in case["claim_ids"]):
            raise ValueError("Calculation and official claim dates differ")
        row = {**case, "document": "CALC", "topic_ids": packet["topic_ids"],
               "original_publisher_answer": packet["publisher_answer"],
               "source_page_evidence": [
                   {"ref": f"CALC:{page}", "text_sha256": hashlib.sha256(pages[page].encode("utf-8")).hexdigest()}
                   for page in case["pages"]
               ],
               "method": "source_conditions_read_then_arithmetic_recomputed",
               "scope": "Only the explicit prompt and its stated assumptions; not every theory sentence on the source page."}
        rows.append(row)
        if case["source_finding"]:
            key = f"M-{case['id']}"
            findings[key] = {
                "id": key, "item_ids": case["item_ids"],
                "refs": [f"CALC:{page}" for page in case["pages"]],
                "claim_ids": case["claim_ids"], "math_case_ids": [case["id"]],
                "issue_ids": case["issue_ids"], "classification": case["finding_classification"],
                "finding": case["source_finding"],
                "learner_treatment": "오류는 학습자 책임으로 돌리지 않는다. 조건을 명시한 수정 문항과 다시 계산한 풀이에 한해 채점한다.",
                "original_exam_answer_impact": "explicit_variant_required_original_explanation_not_approved",
            }
    corrections["items"] = list(findings.values())
    releases = read(ROOT / "item_releases.json")
    for row in rows:
        matched = [finding for finding in corrections["items"] if row["id"] in finding["item_ids"]]
        note = "원문 조건과 정답·해설을 읽고 산술 결과를 다시 계산했다. 조건을 명시한 이 변형의 정답만 승인한다. " + row["conditions"]
        release = {
            "state": "adjudicated_current", "as_of": "2026-10-13",
            "answer": row["answer"], "answer_kind": row["answer_kind"],
            "clean_prompt": row["clean_prompt"], "prompt_correspondence_reviewed": True,
            "original_publisher_answer": row["original_publisher_answer"],
            "evidence": [*[source["ref"] for source in row["source_page_evidence"]],
                         f"math:{row['id']}", *row["claim_ids"]],
            "review_note": note,
            "scope": "Explicit prompt assumptions only. Current tax rules are supported only by the listed official claim IDs.",
        }
        if matched:
            release["prompt_variant"] = "corrected_reviewed_prompt"
            release["correction_resolution"] = {
                finding["id"]: {"reviewed_correction_sha256": fingerprint(finding), "resolution_note": note}
                for finding in matched
            }
            release["corrected_variant_sha256"] = variant_fingerprint(release)
        if not is_current_release(release, matched):
            raise ValueError("Invalid mathematical release")
        releases["items"][row["id"]] = release
    write("verified_math_cases.json", {"count": len(rows), "items": rows,
                                     "unit": "explicit mathematical prompt variant; tax variants have separately linked current-law claims"})
    write("source_corrections.json", corrections)
    write("item_releases.json", releases)
    print(f"Recomputed and published {len(rows)} individually reviewed mathematical prompts.")


if __name__ == "__main__":
    main()
