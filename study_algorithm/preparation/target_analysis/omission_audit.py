"""Reconcile raw page signals with reviewed questions and supplemental evidence."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent

# Pages manually examined for additional natural-language questions. Other excess
# question marks were checked as OCR substitutions for symbols or punctuation.
INLINE_PAGES = {
    "P12": {94, 200, 220, 222, 258, 278, 292, 313, 322, 333, 335, 355, 392, 429, 430, 434},
    "P3": {100, 238, 254, 255, 261, 270, 271, 273, 277, 279, 280, 284, 285, 291, 294, 303,
           313, 314, 323, 328, 342, 344, 360, 383, 385, 420, 423, 438, 439, 441, 448, 454, 461, 462},
    "CALC": {8, 37, 49, 58, 81},
}
FRONTMATTER_ROLES = {
    ("P12", 1): "표지", ("P12", 2): "표제·출판사 인사", ("P12", 3): "머리말·학습체계",
    ("P12", 4): "합격 수기·개인 경험", ("P12", 5): "합격 수기·개인 경험",
    ("P12", 6): "1·2과목 학습전략과 문항 배분", ("P12", 7): "3과목 학습전략과 문항 배분",
    ("P12", 8): "교재 사용법·중요도 표시·기존 문제 축소 이미지",
    ("P12", 9): "교재 사용법·기존 문제 축소 이미지", ("P12", 10): "출판사 4주 계획 예시",
    ("P12", 11): "출판사 8주 계획 예시", ("P12", 12): "교재의 시험 구성·일정 안내",
    ("P12", 13): "권·과목 표제", ("P12", 14): "장 안내·중요도 범례",
    ("P12", 15): "S1C1 목차", ("P12", 60): "S1C2 장 안내", ("P12", 61): "S1C2 목차",
    ("P12", 173): "S1C3 목차", ("P3", 1): "권·과목 표제", ("P3", 2): "3과목 장 안내",
    ("CALC", 1): "표지·교재 내 번호별 분포·화폐유통속도 계산/OX 예시",
    ("MOCK", 1): "모의고사 표지", ("NOTE", 1): "핵심정리노트 표지",
}


def read_json(path: Path) -> Any:
    """Read existing UTF-8 artifacts, including older BOM-prefixed files."""
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(name: str, value: Any) -> None:
    """Save an audit artifact in the analysis directory."""
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def apply_additions(reviews: list[dict], progress: dict) -> None:
    """Attach manually verified additions without duplicating existing issues."""
    additions = read_json(ROOT / "omission_review_additions.json")
    by_id = {review["chapter_id"]: review for review in reviews}
    for item in additions["source_issue_additions"]:
        review = by_id[item["chapter_id"]]
        if not any(flag["issue"] == item["issue"] for flag in review["quality_flags"]):
            review["quality_flags"].append({key: item[key] for key in ["refs", "issue", "resolution"]})
        if item.get("primary_url"):
            sources = review.setdefault("primary_source_checks", [])
            if not any(source.get("url") == item["primary_url"] for source in sources):
                sources.append({"url": item["primary_url"], "scope": "ELW 자본지지점 정의만 선택 검증",
                                "findings": "기초자산의 기대상승률에 관한 기준임을 확인; 전체 도움말의 전수 검증은 아님"})
    for doc, pages in {"P12": [8, 9, 12, 354], "P3": [277, 287, 312], "CALC": [1]}.items():
        progress["visually_checked_pages"][doc] = sorted(set(progress["visually_checked_pages"].get(doc, [])) | set(pages))


def extend_evidence(
    reviews: list[dict], outline: dict, ledger: list[dict], routes: list[dict], progress: dict
) -> dict:
    """Build page accounting and expose all existing embedded review records."""
    additions = read_json(ROOT / "omission_review_additions.json")
    docs = {chapter["id"]: chapter["document"] for chapter in outline["chapters"]}
    tids = {route["id"] for route in routes}
    qids = {row["id"] for row in ledger}
    elements = []
    old_topic_records = old_chapter_pages = 0
    for review in reviews:
        cid = review["chapter_id"]
        for topic in review["topics"]:
            tid = f"{cid}T{topic['number']:02d}"
            for number, entry in enumerate(topic.get("embedded_examples", []), 1):
                elements.append({"id": f"{tid}-INLINE-{number:03d}", "document": docs[cid],
                                 "pages": entry[:-1], "topic_ids": [tid], "description": entry[-1],
                                 "provenance": "existing_topic_review", "relation": "page-based review note; may cover multiple small prompts"})
                old_topic_records += 1
        for group in review.get("embedded_checks_reviewed", []):
            for page in group["pages"]:
                matches = [f"{cid}T{topic['number']:02d}" for topic in review["topics"]
                           if topic["pages"][0] <= page <= topic["pages"][1]]
                assert matches, (cid, page)
                elements.append({"id": f"{cid}-INLINE-P{page:03d}", "document": docs[cid], "pages": [page],
                                 "topic_ids": matches, "description": group["content"],
                                 "provenance": "existing_chapter_review", "description_scope": "shared summary of several pages; open the specified page for the individual check"})
                old_chapter_pages += 1
    for number, item in enumerate(additions["extra_learning_elements"], 1):
        elements.append({"id": f"OMISSION-INLINE-{number:03d}", "provenance": "omission_recheck", **item})
    for item in elements:
        assert set(item["topic_ids"]) <= tids, item["id"]
        assert set(item.get("represented_by_question_ids", [])) <= qids, item["id"]
    for route in routes:
        route["supplemental_evidence_ids"] = [item["id"] for item in elements if route["id"] in item["topic_ids"]]
        route["exam_context_ref"] = "publisher_exam_context.json"
    for question in ledger:
        correction = next((row for row in additions["ocr_recoveries"] if row["question_id"] == question["id"]), None)
        if correction:
            question["ocr_recovery"] = correction
        question["answer_location_status"] = "explicit_page_recorded" if question["answer_page"] else "page_not_individually_recorded; not evidence that no answer exists"
        question["answer_retrieval"] = "문제 페이지와 문항이 이어지는 페이지를 읽고 해설을 찾는다. 모의고사는 해당 회차 해설 구간, 추가문제는 단원 정답·해설 구간을 검색한다. 문항 번호·입력값을 대조하고 정답 충돌을 확인한 뒤에만 채점한다."

    page_rows, signal_checks, unresolved = [], [], []
    qcounts = Counter((row["document"], row["pdf_page"]) for row in ledger)
    recovered_pages = {(row["document"], row["page"]) for row in additions["ocr_recoveries"]}
    for doc in ["P12", "P3", "CALC", "MOCK", "NOTE"]:
        for source in read_json(ROOT / "extracted" / f"{doc}.json"):
            page = source["page"]
            owner_chapters = []
            for review in reviews:
                if any(name.split("_")[0] == doc and any(start <= page <= end for start, end in intervals)
                       for name, intervals in review["reviewed_pages"].items()):
                    owner_chapters.append(review["chapter_id"])
            owners = [route["id"] for route in routes if route["evidence"]["document"] == doc
                      and route["evidence"]["pdf_pages"][0] <= page <= route["evidence"]["pdf_pages"][1]]
            linked_questions = [q["id"] for q in ledger if q["document"] == doc and (q["pdf_page"] == page or q["answer_page"] == page)]
            linked_elements = [item["id"] for item in elements if item["document"] == doc and page in item["pages"]]
            special = FRONTMATTER_ROLES.get((doc, page))
            accounted = bool(owner_chapters or owners or linked_questions or linked_elements or special)
            if not accounted:
                unresolved.append(f"unassigned page {doc}:{page}")
            page_rows.append({"id": f"{doc}:P{page:04d}", "document": doc, "pdf_page": page,
                              "role": special or "chapter_content_or_chapter_frontmatter",
                              "chapter_ids": owner_chapters, "topic_ids": owners,
                              "question_ids": linked_questions, "supplemental_evidence_ids": linked_elements,
                              "text_ref": {"file": f"extracted/{doc}.json", "page": page},
                              "visually_checked": page in progress["visually_checked_pages"].get(doc, []),
                              "accounted": accounted})
            raw_count = len(re.findall(r"[?？]", source["text"]))
            natural_count = len(re.findall(r"[가-힣][ \t]*[?？]", source["text"]))
            indexed = qcounts[doc, page]
            if raw_count > indexed:
                if special:
                    resolution = "frontmatter_or_repeated_illustration"
                elif page in INLINE_PAGES.get(doc, set()):
                    resolution = "inline_example_or_explanatory_question; source location now connected"
                else:
                    resolution = "OCR_question_mark_substitution_in_formula_heading_or_note"
                signal_checks.append({"document": doc, "page": page, "raw_question_marks": raw_count,
                                      "natural_language_question_marks": natural_count, "indexed_standalone_items": indexed,
                                      "resolution": resolution, "supplemental_evidence_ids": linked_elements,
                                      "topic_ids": owners, "chapter_ids": owner_chapters})
            if doc in ["P12", "P3", "MOCK"] and natural_count < indexed:
                if (doc, page) not in recovered_pages:
                    unresolved.append(f"question text deficit {doc}:{page}")
    assert len(page_rows) == 1179
    assert len(signal_checks) == 99, "New signal candidates need manual review"
    assert not unresolved, unresolved
    for route in routes:
        references = set(route["question_ids"])
        supplementary = set(route["supplemental_evidence_ids"])
        route["source_page_ids"] = [row["id"] for row in page_rows if route["id"] in row["topic_ids"]
                                    or references.intersection(row["question_ids"])
                                    or supplementary.intersection(row["supplemental_evidence_ids"])]
    # Arithmetic checks cover newly exposed worked examples, not rote JSON equality.
    pv = [600 / 1.04, 600 / 1.04**2, 10600 / 1.04**3]
    duration = sum((i + 1) * value for i, value in enumerate(pv)) / sum(pv)
    assert 2.8381 < duration < 2.8382
    assert math.isclose((1 + 0.08 / 4)**4 - 1, 0.08243216)
    assert math.isclose((2.33 / 1.65) * math.sqrt(25), 7.0606060606060606)
    assert math.isclose((1.65 / 2.33) * math.sqrt(25), 3.540772532188841)
    assert math.isclose(0.08 - (0.03 + 1.2 * (0.06 - 0.03)), 0.014)
    context = additions["publisher_exam_context"]
    assert sum(context["chapter_question_counts"].values()) == context["total_questions"] == 100
    assert set(context["chapter_question_counts"]) == {review["chapter_id"] for review in reviews}
    result = {
        "status": "pass_with_documented_scope", "date": additions["review_date"],
        "findings_and_repairs": additions["findings"],
        "counts": {"source_pages_accounted": len(page_rows), "unassigned_pages": 0,
                   "raw_signal_candidate_pages_reviewed": len(signal_checks), "OCR_stems_restored": len(recovered_pages),
                   "standalone_items": len(ledger), "new_standalone_items_found_in_this_recheck": 0,
                   "existing_topic_embedded_records_exposed": old_topic_records,
                   "chapter_embedded_pages_routed": old_chapter_pages,
                   "new_explicit_embedded_records": len(additions["extra_learning_elements"]),
                   "supplemental_records_total": len(elements)},
        "candidate_resolutions": signal_checks, "remaining_unresolved_scanned_candidates": unresolved,
        "new_calculations": {"bond_price": sum(pv), "duration": duration, "effective_yield": (1 + .08 / 4)**4 - 1},
        "not_claimed": ["Every sentence independently proven correct", "Every page image re-inspected", "All inline micro-prompts individually numbered", "All current laws or official exam rules verified", "Ten complete rereads", "285 fully written lessons or a running application"],
        "scope": "Raw text signals independently identify candidate pages; visual recovery resolves three missing stems. Signals are not a complete OCR-independent census of all printed symbols. Supplemental records are page/description groups, not an additional exam-question count.",
    }
    write_json("supplemental_evidence.json", {"count": len(elements), "count_policy": "Evidence groups, not standalone question count; may contain several prompts or overlap existing problem explanations.", "items": elements})
    write_json("source_page_index.json", {"count": len(page_rows), "items": page_rows})
    write_json("publisher_exam_context.json", context)
    write_json("ocr_recoveries.json", {"count": len(recovered_pages), "items": additions["ocr_recoveries"]})
    write_json("omission_audit.json", result)
    return result
