"""Validate manual chapter coverage and link reviewed topics to the study contract."""

import json
from pathlib import Path

from integrate_financial_review import read_json, write_json


ROOT = Path(__file__).resolve().parent


def main() -> None:
    """Check unique question mappings without treating unchecked pages as reviewed."""
    outline = read_json(ROOT / "outline.json")
    summaries = []
    for chapter in outline["chapters"]:
        path = ROOT / "chapter_reviews" / f"{chapter['id']}.json"
        if not path.exists():
            continue
        review = read_json(path)
        if not review["status"].startswith("semantic_review_complete"):
            continue
        topics = review["topics"]
        assert [topic["number"] for topic in topics] == list(range(1, len(chapter["topics"]) + 1))
        counts = review["standalone_question_counts"]
        assert counts["core"] == len(topics)
        assert counts["supplement"] == sum(len(topic["supplement"]) for topic in topics)
        assert counts["additional"] == len(review["additional_questions"])
        assert counts["mock"] == len(review["mock_questions"])
        assert counts["calculation_including_unnumbered_variant"] == len(review["calculation_questions"])
        warmup = review["warmup_mapping"]
        numbers = (
            [number for group in warmup.values() for number in group]
            if isinstance(warmup, dict)
            else [number for row in warmup for number in row["numbers"]]
        )
        assert sorted(numbers) == list(range(1, counts["warmup"] + 1))
        assert counts["total"] == sum(value for key, value in counts.items() if key != "total")
        for topic, annotation in zip(chapter["topics"], topics, strict=True):
            topic["review_status"] = "semantic_review_complete_within_identified_ranges"
            topic["title_reviewed"] = annotation["title"]
            topic["question_analysis"] = [{
                "artifact": str(path.relative_to(ROOT)).replace("\\", "/"),
                "topic_number": annotation["number"],
                "cross_document_links": "chapter artifact includes additional, calculation, mock and warmup mappings",
            }]
        summaries.append({"chapter": chapter["id"], "topics": len(topics), "questions": counts["total"]})
    write_json(ROOT / "outline.json", outline)
    progress = read_json(ROOT / "review_progress.json")
    progress["chapter_reviews_complete"] = [row["chapter"] for row in summaries]
    progress["reviewed_topic_count"] = sum(row["topics"] for row in summaries)
    progress["standalone_questions_in_completed_chapter_ranges"] = sum(row["questions"] for row in summaries)
    write_json(ROOT / "review_progress.json", progress)
    contract_path = ROOT.parent / "exam_requirement_contract.json"
    contract = read_json(contract_path)
    analysis = contract["supplied_material_analysis"]
    analysis["chapter_reviews"] = [f"target_analysis/chapter_reviews/{row['chapter']}.json" for row in summaries]
    if analysis.get("pending"):
        analysis["pending"][0] = f"나머지 {len(outline['chapters']) - len(summaries)}개 목차 의미 분석"
    write_json(contract_path, contract)
    result = {
        "status": "pass", "chapters": summaries,
        "boundary": "Mapping and count validation only; not an independent semantic or current-law review.",
    }
    write_json(ROOT / "chapter_coverage_checks.json", result)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
