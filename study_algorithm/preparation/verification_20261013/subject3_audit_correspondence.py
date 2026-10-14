"""Record scope-review candidates without changing any approved release."""

import json
import re
from pathlib import Path

from subject3_reviews import REVIEWS


def main():
    """Keep the original question and the edited question side by side."""
    folder = Path(__file__).resolve().parent
    packets = json.loads(
        (folder.parent / "eval" / "answer_packets.json").read_text(encoding="utf-8")
    )["items"]
    originals = {item["id"]: item for item in packets}
    items = []
    comparison_question = re.compile("잘못|틀린|옳지|가장|거리가|아닌|속하지")
    for review in REVIEWS:
        original = originals[review["id"]]
        question = original.get("question_text", "")
        edited = review["clean_prompt"]
        original_choices = len(set(re.findall("[①②③④]", question)))
        edited_choices = len(set(re.findall("[①②③④]", edited)))
        if original_choices < 3 or edited_choices >= 3:
            continue
        if not comparison_question.search(question[:900]):
            continue
        items.append({
            "id": review["id"],
            "original_intent": "TARGET의 복수 선택지를 비교하여 정오 또는 해당 여부를 판단하는 문항: "
            + " ".join(question.split())[:450],
            "changed_scope": "현재 교정판은 선택지 일부 또는 특정 명제로 질문을 바꾸어 원문 전체 보기 판정 범위와 다를 수 있다: "
            + edited,
            "resolution_needed": "원문 네 보기와 교정판을 항목별로 대조하여 생략된 보기 근거를 검증하고, 원문 의도·보기 순서·정답번호를 유지하는 최소교정판을 작성한다. 복수 오류는 TARGET 오류로 별도 기록한다. 현재 교정판 승인을 원문 전체검토 완료로 간주하지 않는다.",
            "audit_status": "scope_review_candidate_not_final_mismatch_judgment",
            "original_question": question,
            "publisher_answer": original.get("publisher_answer"),
            "publisher_explanation": original.get("explanation_text", ""),
            "document": original.get("document"),
            "question_page": original.get("question_page"),
            "source_pages": original.get("source_pages"),
            "existing_source_finding": review.get("source_finding", ""),
        })
    result = {
        "as_of": "2026-10-13",
        "method": "Original multiple-choice comparison questions whose edited prompt omits the original choice structure; conservative audit candidates, not automatic rejection.",
        "limitations": "Blank OCR questions and pure blank-fill questions require a separate page-level audit. This candidate list is not a declaration that every listed item has a substantive mismatch or that every unlisted item is faithful.",
        "preserve_existing_releases": True,
        "review_count": len(REVIEWS),
        "items": items,
    }
    output = folder / "subject3_correspondence_audit.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Scope review candidates: {len(items)} / {len(REVIEWS)}")


if __name__ == "__main__":
    main()
