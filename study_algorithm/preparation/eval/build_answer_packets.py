"""Locate publisher answers and explanations for item-by-item EVAL review.

Extraction is a locator, not an endorsement. Review is recorded separately.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
ANALYSIS = ROOT.parent / "target_analysis"
CHOICES = "①②③④"
ANSWER_LINE = re.compile(r"^[ \t]*(?:[^\n가-힣①②③④]{0,12}|(?:정답|답)[ :：]*)[①②③④][ \t]*$", re.MULTILINE)
NUMBER_LINE = re.compile(r"^[ \t]*(?:[^ \t\n]{1,5}[ \t]+)?([0-9IOl〇]{2,3}|\d|이)[ \t]+([^\n]+)", re.MULTILINE)


def read_json(path: Path) -> Any:
    """Read an existing UTF-8 artifact."""
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    """Save a review artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def numbered_lines(text: str) -> list[dict]:
    """Locate number-prefixed lines, excluding obvious page footers."""
    result = []
    for match in NUMBER_LINE.finditer(text):
        if re.search(r"제\d과목|부록 최종|워밍업|제\d장", match[2]):
            continue
        token = match[1]
        number = 1 if token == "이" else int(token.translate(str.maketrans({"O": "0", "〇": "0", "I": "1", "l": "1"})))
        result.append({"number": number, "offset": match.start(), "line": match[0]})
    return result


def source_span(pages: dict, doc: str, start: int, end: int) -> list[dict]:
    """Preserve page boundaries for fallback inspection."""
    return [{"page": page, "text": pages[doc][page]} for page in range(start, end + 1)]


def create_packet(question: dict) -> dict:
    """Construct a neutral record, separate from a trusted grading key."""
    return {
        "id": question["id"], "kind": question["kind"], "chapter_id": question["chapter_id"],
        "topic_ids": question["topic_ids"], "document": question["document"],
        "question_page": question["pdf_page"], "demand": question["demand"],
        "publisher_answer": None, "explanation_text": "", "question_text": "",
        "answer_pages": [], "review_status": "unreviewed", "locator_status": "unlocated",
        "source_page_review_notes": question["same_page_review_notes"],
        "ocr_recovery": question.get("ocr_recovery"), "trusted_gold_status": "not_adjudicated",
    }


def locate_note(packets: dict, questions: list[dict], pages: dict) -> None:
    """Split note pages at their repeated question-number sequence."""
    groups = defaultdict(list)
    for question in questions:
        if question["kind"] == "warmup":
            groups[question["pdf_page"]].append(question)
    for page, group in groups.items():
        text = pages["NOTE"][page]
        group.sort(key=lambda q: q["number"])
        wanted = [q["number"] for q in group]
        lines = numbered_lines(text)
        first = [line for line in lines if line["number"] == wanted[0]]
        split = first[-1]["offset"] if len(first) >= 2 else len(text) // 2
        for index, question in enumerate(group):
            packet = packets[question["id"]]
            number = question["number"]
            starts = [line for line in lines if line["number"] == number and line["offset"] >= split]
            prompts = [line for line in lines if line["number"] == number and line["offset"] < split]
            if starts:
                start = starts[0]["offset"]
                following = [line["offset"] for line in lines if line["offset"] > start and line["number"] in wanted[index + 1:]]
                answer = text[start:min(following, default=len(text))].strip()
                answer = re.sub(r"\n\s*\d+\s+워밍업.*$", "", answer, flags=re.DOTALL)
                packet.update({"publisher_answer": answer.splitlines()[0].strip(), "explanation_text": answer,
                               "answer_pages": [page], "locator_status": "heuristic_answer_sequence; requires_review"})
            if prompts:
                start = prompts[0]["offset"]
                following = [line["offset"] for line in lines if start < line["offset"] < split and line["number"] in wanted[index + 1:]]
                packet["question_text"] = text[start:min(following, default=split)].strip()
            packet["source_pages"] = [page]


def locate_book(packets: dict, questions: list[dict], pages: dict, reviews: list[dict], outline: dict) -> None:
    """Locate core/supplement answers inside their original topic spans."""
    docmap = {chapter["id"]: chapter["document"] for chapter in outline["chapters"]}
    for review in reviews:
        cid, doc = review["chapter_id"], docmap[review["chapter_id"]]
        for topic in review["topics"]:
            tid = f"{cid}T{topic['number']:02d}"
            rows = [q for q in questions if q["kind"] in ["core", "supplement"] and tid in q["topic_ids"]]
            starts = []
            for question in rows:
                page = question["pdf_page"]
                if question["kind"] == "core":
                    offset = 0
                else:
                    number = int(question["id"].rsplit("-", 1)[-1])
                    choices = [line for line in numbered_lines(pages[doc][page]) if line["number"] == number]
                    heading = re.search(r"보[충중]문제", pages[doc][page])
                    if heading:
                        choices = [line for line in choices if line["offset"] >= heading.start()]
                    offset = choices[0]["offset"] if choices else None
                starts.append((page, offset, question))
            for index, (page, offset, question) in enumerate(starts):
                packet = packets[question["id"]]
                end_page = starts[index + 1][0] if index + 1 < len(starts) else topic["pages"][1]
                packet["source_pages"] = list(range(page, end_page + 1))
                if offset is None:
                    packet["fallback_pages"] = source_span(pages, doc, page, end_page)
                    continue
                chunks, positions, size = [], [], 0
                for current in range(page, end_page + 1):
                    fragment = pages[doc][current][offset:] if current == page else pages[doc][current]
                    if index + 1 < len(starts) and current == end_page and starts[index + 1][1] is not None:
                        limit = starts[index + 1][1] - (offset if current == page else 0)
                        fragment = fragment[:max(0, limit)]
                    chunks.append(fragment)
                    positions.append((size, current))
                    size += len(fragment) + 1
                text = "\n".join(chunks)
                packet["question_text"] = text
                keys = list(ANSWER_LINE.finditer(text))
                if keys:
                    key = keys[0]
                    lines = text[:key.start()].splitlines()
                    fourth = next((i for i, line in enumerate(lines) if "④" in line), -1)
                    rationale = "\n".join(lines[fourth + 1:])
                    key_page = next(pg for start, pg in reversed(positions) if start <= key.start())
                    packet.update({"publisher_answer": next(char for char in key[0] if char in CHOICES),
                                   "explanation_text": rationale.strip(), "answer_pages": [key_page],
                                   "locator_status": "heuristic_terminal_choice; requires_review",
                                   "question_text": text[:key.end()].strip()})
                else:
                    packet["fallback_pages"] = source_span(pages, doc, page, end_page)


def locate_additional(packets: dict, questions: list[dict], pages: dict, outline: dict) -> None:
    """Find numbered explanations following an answer-section heading."""
    for chapter in outline["chapters"]:
        rows = [q for q in questions if q["kind"] == "additional" and q["chapter_id"] == chapter["id"]]
        doc = chapter["document"]
        for question in rows:
            number, packet = question["number"], packets[question["id"]]
            candidates = []
            for page in range(question["pdf_page"], chapter["pdf_end"] + 1):
                text = pages[doc][page]
                header = re.search(r"정답\s*및\s*해설", text)
                for line in numbered_lines(text):
                    if line["number"] == number and (
                        header and line["offset"] >= header.start()
                        or re.match(r"\s*(?:\d+|이)\s*[①②③④@]", line["line"])
                    ):
                        candidates.append((page, line["offset"]))
            if candidates:
                page, offset = candidates[0]
                text = pages[doc][page]
                following = [line["offset"] for line in numbered_lines(text) if line["offset"] > offset and line["number"] > number]
                excerpt = text[offset:min(following, default=len(text))].strip()
                key = re.search(r"[①②③④@]", excerpt[:35])
                packet.update({"publisher_answer": key[0] if key else None, "explanation_text": excerpt,
                               "answer_pages": [page], "locator_status": "heuristic_numbered_explanation; requires_review"})
            page = question["pdf_page"]
            starts = [line for line in numbered_lines(pages[doc][page]) if line["number"] == number]
            if starts:
                offset = starts[0]["offset"]
                ends = [line["offset"] for line in numbered_lines(pages[doc][page]) if line["offset"] > offset]
                packet["question_text"] = pages[doc][page][offset:min(ends, default=len(pages[doc][page]))]
            packet["source_pages"] = sorted({page, *packet["answer_pages"]})


def locate_mock(packets: dict, questions: list[dict], pages: dict) -> None:
    """Locate explanation paragraphs; key tables are reviewed separately."""
    for exam_set, start_page, end_page in [(1, 55, 66), (2, 67, 76)]:
        starts = []
        for page in range(start_page, end_page + 1):
            for line in numbered_lines(pages["MOCK"][page]):
                if 1 <= line["number"] <= 100 and re.search(r"[가-힣]", line["line"].strip().split(maxsplit=1)[-1]):
                    starts.append((line["number"], page, line["offset"]))
        for question in questions:
            if question["kind"] != "mock" or question["set"] != exam_set:
                continue
            packet, number = packets[question["id"]], question["number"]
            match = next((row for row in starts if row[0] == number), None)
            if match:
                _, page, offset = match
                after = [row for row in starts if row[0] == number + 1 and (row[1], row[2]) > (page, offset)]
                if not after:
                    after = [row for row in starts if number < row[0] <= number + 3
                             and (row[1], row[2]) > (page, offset)]
                    packet["boundary_review"] = "next_header_OCR_missing; adjacent_explanation_may_be_included"
                stop_page, stop_offset = (after[0][1], after[0][2]) if after else (min(page + 1, end_page), len(pages["MOCK"][min(page + 1, end_page)]))
                fragments = [pages["MOCK"][current][offset if current == page else 0:stop_offset if current == stop_page else len(pages["MOCK"][current])]
                             for current in range(page, stop_page + 1)]
                packet.update({"explanation_text": "\n".join(fragments).strip(), "answer_pages": list(range(page, stop_page + 1)),
                               "locator_status": "heuristic_mock_explanation; table_key_pending"})
            packet["source_pages"] = sorted({question["pdf_page"], *packet["answer_pages"]})


def locate_calculation(packets: dict, questions: list[dict], pages: dict) -> None:
    """Keep whole calculation pages so formula context remains available."""
    for question in questions:
        if question["kind"] == "calculation":
            packet = packets[question["id"]]
            start, end = question["pdf_page"], question["answer_page"] or question["pdf_page"]
            packet["source_pages"] = list(range(start, max(start, end) + 1))
            packet["fallback_pages"] = source_span(pages, "CALC", start, max(start, end))
            packet["locator_status"] = "full_calculation_pages_for_manual_review"


def main() -> None:
    """Produce unreviewed answer packets and extraction diagnostics."""
    questions = read_json(ANALYSIS / "question_ledger.json")["items"]
    outline = read_json(ANALYSIS / "outline.json")
    reviews = [read_json(ANALYSIS / "chapter_reviews" / f"{chapter['id']}.json") for chapter in outline["chapters"]]
    pages = {doc: {row["page"]: row["text"] for row in read_json(ANALYSIS / "extracted" / f"{doc}.json")}
             for doc in ["P12", "P3", "CALC", "MOCK", "NOTE"]}
    packets = {question["id"]: create_packet(question) for question in questions}
    locate_note(packets, questions, pages)
    locate_book(packets, questions, pages, reviews, outline)
    locate_additional(packets, questions, pages, outline)
    locate_mock(packets, questions, pages)
    locate_calculation(packets, questions, pages)
    if (ROOT / "answer_overrides.json").exists():
        for key, changes in read_json(ROOT / "answer_overrides.json").items():
            packets[key].update(changes)
    if (ROOT / "review_log.json").exists():
        reviewed_chapters = read_json(ROOT / "review_log.json")["chapters"]
        for packet in packets.values():
            if packet["chapter_id"] in reviewed_chapters:
                packet["review_status"] = "explanation_reviewed_for_eval; not_independent_gold_validation"
    write_json(ROOT / "answer_packets.json", {"count": len(packets), "items": list(packets.values())})
    unresolved = [{"id": p["id"], "page": p["question_page"], "locator_status": p["locator_status"]}
                  for p in packets.values() if not p["explanation_text"] or p["publisher_answer"] in [None, "@"]]
    result = {"counts": dict(Counter(p["locator_status"] for p in packets.values())), "needs_key_or_explanation": unresolved,
              "scope": "Extraction only. Item-level EVAL review is never inferred from running this script."}
    write_json(ROOT / "locator_diagnostics.json", result)
    print(json.dumps({"packets": len(packets), "locator_counts": result["counts"], "needs_key_or_explanation": len(unresolved)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
