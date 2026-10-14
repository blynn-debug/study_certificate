"""Integrate the manually read financial-products chapter and check its coverage."""

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent


def read_json(path: Path) -> Any:
    """Read a UTF-8 analysis artifact."""
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    """Write a review artifact with readable Korean text."""
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    """Merge manual annotations; do not infer semantic review from extraction."""
    chapter_path = ROOT / "chapter_reviews/S1C2.json"
    chapter = read_json(chapter_path)
    update = read_json(ROOT / "review_updates/s1c2_topics13_35.json")
    chapter["topics"] = [topic for topic in chapter["topics"] if topic["number"] <= 12] + update["topics"]
    assert [topic["number"] for topic in chapter["topics"]] == list(range(1, 36))
    for key in ("additional_questions", "mock_questions", "calculation_questions", "warmup_mapping"):
        chapter[key] = update[key]
    previous_flags = [flag for flag in chapter["quality_flags"] if flag not in update["quality_flags"]]
    chapter["quality_flags"] = previous_flags + update["quality_flags"]
    chapter["status"] = "semantic_review_complete_within_identified_chapter_ranges"
    chapter["global_cross_reference_audit"] = "pending_until_all_five_documents_reviewed"
    chapter["current_law_validation"] = "pending; disputed questions excluded from authoritative grading"
    chapter["reviewed_pages"] = {
        "P12": [[62, 172]], "NOTE": [[7, 13]], "CALC": [[8, 8]],
        "MOCK": [[4, 6], [30, 32], [56, 57], [68, 68]],
    }
    warmup_numbers = [number for row in chapter["warmup_mapping"] for number in row["numbers"]]
    assert sorted(warmup_numbers) == list(range(1, 69))
    assert [row["number"] for row in chapter["additional_questions"]] == list(range(1, 26))
    assert {(row["set"], row["number"]) for row in chapter["mock_questions"]} == {
        (exam_set, number) for exam_set in (1, 2) for number in range(8, 16)
    }
    supplement_count = sum(len(topic["supplement"]) for topic in chapter["topics"])
    counts = {
        "core": len(chapter["topics"]), "supplement": supplement_count,
        "additional": 25, "calculation_including_unnumbered_variant": 1, "mock": 16, "warmup": 68,
    }
    counts["total"] = sum(counts.values())
    chapter["standalone_question_counts"] = counts
    chapter.pop("standalone_questions_reviewed_so_far", None)
    chapter.pop("next", None)
    chapter["count_policy"] = (
        "독립 문항의 물리적 등장 횟수. 풀이 재인쇄는 중복 집계하지 않는다. "
        "본문 OX·빈칸·계산 예시는 읽고 별도 기록하되 이 합계에 포함하지 않는다. "
        "다른 목차에서 다시 등장하는 관련 문항은 전체 자료 검토 후 연결한다."
    )
    chapter["algorithm_rules"] = ["R02", "R04", "R24"]
    chapter["chapter_demand"] = (
        "금융기관·상품·계약·세제·보호제도의 분류축을 분리하고 조건을 함께 판단한다. "
        "자금흐름·주체·시간·분모를 먼저 설명한 다음 정확한 예외와 수치를 회상한다. "
        "구조적 이해와 규정의 정확한 기억을 별도로 확인하며 충돌 문항은 정답 암기로 넘기지 않는다."
    )
    write_json(chapter_path, chapter)

    tax_path = ROOT / "chapter_reviews/S1C1.json"
    tax = read_json(tax_path)
    if not any(row[0] == "03-추가빈칸" for row in tax["calculation_questions"]):
        tax["calculation_questions"].append([
            "03-추가빈칸", 7, [10], "주주·기업규모·보유기간별 세율 세 개를 회상해 합산",
            "세제 단원 끝의 번호 없는 독립 선택형 문항; 재검토로 추가",
        ])
    tax["reviewed_pages"]["CALC"] = [[2, 7]]
    tax_counts = tax["standalone_question_counts"]
    tax_counts["calculation_including_unnumbered_variant"] = len(tax["calculation_questions"])
    tax_counts["total"] = sum(value for key, value in tax_counts.items() if key != "total")
    tax["count_policy"] = chapter["count_policy"]
    tax["status"] = "semantic_review_complete_within_identified_chapter_ranges"
    tax["global_cross_reference_audit"] = "pending_until_all_five_documents_reviewed"
    tax["current_law_validation"] = "pending"
    tax["coverage_correction"] = "CALC 7쪽 번호 없는 추가문항 1개를 발견해 137→138개로 정정."
    write_json(tax_path, tax)

    progress = read_json(ROOT / "review_progress.json")
    progress["fully_read_pdf_page_intervals"]["P12"] = [[1, 173], [233, 233], [277, 277], [305, 305], [405, 405]]
    progress["fully_read_pdf_page_intervals"]["NOTE"] = [[1, 13]]
    progress["fully_read_pdf_page_intervals"]["CALC"] = [[1, 12]]
    progress["fully_read_pdf_page_intervals"]["MOCK"] = [[1, 6], [28, 32], [55, 57], [67, 68]]
    progress["visually_checked_pages"]["P12"] = [17, 74, 88, 109, 147, 164, 167]
    progress["chapter_reviews_complete"] = ["S1C1", "S1C2"]
    progress["completion_scope"] = (
        "완료 목차는 확인된 해당 목차 범위의 문항별 의미 분석 완료를 뜻한다. "
        "5개 문서 전체 분석·다른 목차의 관련 문항 교차검사·현행 규정 검증은 진행 중이다."
    )
    progress["next"] = (
        "S1C3 부동산: P12 174-232, NOTE 14-18, CALC 9-11 (이미 읽음), "
        "MOCK 1회16-20·2회16-20와 해설. 이후 남은 목차를 같은 방식으로 진행."
    )
    write_json(ROOT / "review_progress.json", progress)

    contract_path = ROOT.parent / "exam_requirement_contract.json"
    contract = read_json(contract_path)
    activation = contract["activation"]
    historical = {key: activation.pop(key) for key in ("deferred_work", "resume_condition", "while_deferred") if key in activation}
    if historical:
        activation["previous_deferral_history"] = historical
    activation["draft_boundary"] = (
        "일반 분류와 비례관계 예시는 설계 초안이다. 실제 제공자료 분석 결과는 "
        "supplied_material_analysis의 목차별 파일을 참조한다. 공식 기출 인증이나 현행 규정 검증과 구분한다."
    )
    contract["supplied_material_analysis"] = {
        "status": "in_progress", "manifest": "target_analysis/target_manifest.json",
        "outline": "target_analysis/outline.json", "progress": "target_analysis/review_progress.json",
        "chapter_reviews": ["target_analysis/chapter_reviews/S1C1.json", "target_analysis/chapter_reviews/S1C2.json"],
        "integration": (
            "개념을 받으면 목차·세부주제와 실제 문항의 demand/test를 찾고 assistant_delivery를 실제 설명으로 구현한다. "
            "memory/memorize는 기억 대상으로, check는 확인 문제로, repair는 실패 원인별 재설명으로 사용한다. "
            "공식성·시점·정답 충돌이 미확인인 항목은 권위 있는 채점 기준으로 사용하지 않는다."
        ),
        "pending": ["나머지 14개 목차 의미 분석", "5개 문서 전체 교차참조 검사", "규정·정오표 검증", "주제별 실제 설명 예제 보강"],
    }
    write_json(contract_path, contract)
    print(json.dumps({"S1C2": counts, "S1C1": tax_counts, "coverage_checks": "pass"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
