"""Build a chapter/topic map from manually checked TOCs and OCR page geometry."""

import json
import re
from pathlib import Path

import pymupdf

BASE = Path(__file__).resolve().parent
CHAPTERS = [
    ("S1C1", "P12", 15, 60, "세제관련 법규/세무전략", [4,7,11,14,17,19,22,25,29,32,35,38,40]),
    ("S1C2", "P12", 61, 172, "금융상품", [50,54,56,58,62,64,68,71,78,83,85,88,90,92,94,98,100,102,104,106,108,110,112,114,118,124,128,130,132,134,136,138,140,145,149]),
    ("S1C3", "P12", 173, 232, "부동산관련 상품", [162,165,167,169,173,175,177,180,184,186,190,192,194,196,198,201,203,206,207]),
    ("S2C1", "P12", 233, 276, "대안투자운용/투자전략", [222,224,226,229,232,234,236,238,241,243,245,248,251,254]),
    ("S2C2", "P12", 277, 304, "해외증권투자운용/투자전략", [266,269,271,274,276,278,280,283,285]),
    ("S2C3", "P12", 305, 404, "투자분석기법", [294,296,298,300,306,312,315,317,319,324,329,331,334,336,340,342,344,350,352,355,357,359,362,364,366,369,372,374,377,379]),
    ("S2C4", "P12", 405, 443, "리스크관리", [394,395,400,402,405,408,410,413,414,415,417,419,421]),
    ("S3C1", "P3", 3, 58, "직무윤리", [4,7,8,10,12,14,18,21,33,37,42,44,50]),
    ("S3C2", "P3", 59, 160, "자본시장과 금융투자업에 관한 법률 및 금융위원회규정", [60,62,65,68,72,74,77,79,81,84,86,88,91,94,97,99,103,105,107,108,109,111,115,117,119,121,123,125,127,130,133,135,137,140,142,144,146]),
    ("S3C3", "P3", 161, 202, "한국금융투자협회규정", [162,163,167,169,171,173,175,177,179,181,183,186,187,189,193,197]),
    ("S3C4", "P3", 203, 250, "주식투자운용/투자전략", [204,206,208,210,212,214,216,217,219,222,224,226,228,231,233,236,238,240,242]),
    ("S3C5", "P3", 251, 308, "채권투자운용/투자전략", [252,254,257,259,262,265,268,270,272,274,276,279,281,287,290,292,298,302]),
    ("S3C6", "P3", 309, 368, "파생상품투자운용/투자전략", [310,312,314,317,319,321,325,327,330,333,337,343,346,348,349,351,354,356,358]),
    ("S3C7", "P3", 369, 400, "투자운용결과분석", [370,371,373,376,379,381,386,389,391,394,395]),
    ("S3C8", "P3", 401, 432, "거시경제", [402,404,407,409,412,415,417,419,422,424]),
    ("S3C9", "P3", 433, 468, "분산투자기법", [434,437,440,444,448,452,455,458,461]),
]


def topic_titles(page: pymupdf.Page, count: int) -> list[str]:
    """Read row titles using right-column page anchors to preserve wrapped text."""
    width, height = page.rect.width, page.rect.height
    words = page.get_text("words")
    anchors = sorted(
        [(word[1] + word[3]) / 2 for word in words if re.match(r"^[Pp][.]", word[4])]
    )
    if len(anchors) != count:
        raise ValueError(f"Expected {count} TOC anchors, observed {len(anchors)}")
    label_words = [word for word in words if word[4] == "TOPIC" and word[1] > anchors[0] - 5]
    title_left = min(word[0] for word in label_words) + width * 0.08
    star_words = [word for word in words if "★" in word[4] and word[1] > anchors[0] - 5]
    title_right = min(word[0] for word in star_words) - width * 0.008
    boundaries = [anchors[0] - (anchors[1] - anchors[0]) / 2]
    boundaries += [(left + right) / 2 for left, right in zip(anchors, anchors[1:])]
    boundaries += [min(height, anchors[-1] + (anchors[-1] - anchors[-2]) / 2)]
    titles = []
    for top, bottom in zip(boundaries, boundaries[1:]):
        selected = [word for word in words if title_left <= word[0] < title_right and top <= (word[1] + word[3]) / 2 < bottom]
        selected.sort(key=lambda word: (round(word[1] / 3), word[0]))
        titles.append(" ".join(word[4] for word in selected))
    return titles


def main() -> None:
    """Save 16 chapter maps with 285 source topic identifiers."""
    manifest = json.loads((BASE / "target_manifest.json").read_text(encoding="utf-8"))
    paths = {item["id"]: BASE.parent.parent / item["path"] for item in manifest["documents"]}
    chapters = []
    for chapter_id, document_id, toc, end, name, starts in CHAPTERS:
        with pymupdf.open(paths[document_id]) as document:
            titles = topic_titles(document[toc - 1], len(starts))
        offset = 12 if document_id == "P12" else 0
        extracted = json.loads((BASE / "extracted" / f"{document_id}.json").read_text(encoding="utf-8"))
        extra_pages = [
            page["page"] for page in extracted[starts[-1] + offset - 1 : end]
            if "추가보충문제" in "".join(page["text"].split())[:180]
        ]
        extra_start = min(extra_pages) if extra_pages else None
        topics = []
        for index, (title, start) in enumerate(zip(titles, starts), start=1):
            next_start = starts[index] + offset if index < len(starts) else (extra_start or end + 1)
            topics.append({
                "id": f"{chapter_id}T{index:02}", "number": index, "title_ocr": title,
                "printed_start": start, "pdf_start": start + offset, "pdf_end": next_start - 1,
                "review_status": "pending", "question_analysis": [],
            })
        chapters.append({
            "id": chapter_id, "document": document_id, "name": name, "toc_page": toc,
            "pdf_end": end, "additional_questions_start": extra_start, "topics": topics,
        })
    output = {"chapter_count": len(chapters), "topic_count": sum(len(ch["topics"]) for ch in chapters), "chapters": chapters}
    (BASE / "outline.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"chapters": len(chapters), "topics": output["topic_count"]}))


if __name__ == "__main__":
    main()
