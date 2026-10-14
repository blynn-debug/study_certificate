"""Find related source findings without declaring another question defective."""

from typing import Any


def correction_candidates(
    packet: dict[str, Any],
    corrections: list[dict[str, Any]],
    claims: dict[str, dict[str, Any]],
    math_cases: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return page/topic leads; direct findings are handled by the release policy."""
    pages = {packet["question_page"], *packet.get("source_pages", [])}
    page_refs = {f"{packet['document']}:{page}" for page in pages}
    topics = set(packet["topic_ids"])
    candidates = []
    for row in corrections:
        if packet["id"] in row["item_ids"]:
            continue
        matched_pages = sorted(page_refs & set(row.get("refs", [])))
        linked_topics = {
            topic for key in row.get("claim_ids", [])
            for topic in claims.get(key, {}).get("topic_ids", [])
        }
        linked_topics.update(
            topic for key in row.get("math_case_ids", [])
            for topic in (math_cases or {}).get(key, {}).get("topic_ids", [])
        )
        matched_topics = sorted(topics & linked_topics)
        if matched_pages or matched_topics:
            candidates.append({
                "correction_id": row["id"], "matched_pages": matched_pages,
                "matched_topics": matched_topics, "record": row,
                "status": "applicability_review_required",
                "whole_item_fault_confirmed": False,
            })
    return candidates
