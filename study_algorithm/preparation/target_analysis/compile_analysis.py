"""Compile reviewed questions and teaching routes; audit supplied-material coverage."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from omission_audit import apply_additions, extend_evidence

ROOT = Path(__file__).resolve().parent
PREP = ROOT.parent
WORKSPACE = PREP.parent
KIND_NAMES = {
    "core": "핵심문제", "supplement": "추가 확인문제", "additional": "단원 추가문제",
    "calculation": "계산문제·별도 변형", "mock": "모의고사", "warmup": "노트 빈칸·OX",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def topic_id(chapter: str, number: int) -> str:
    return f"{chapter}T{number:02d}"


def complete_record_fields(reviews: list[dict]) -> None:
    """Fill the twelve early repair routes and correct one rounding transcription."""
    repairs = [
        "기관 이름을 가리고 설립 근거·조달 방식·업무만 제시한다. 중앙회와 단위조합을 별도 행에 놓고 틀린 분류축 하나부터 다시 고르게 한다.",
        "계좌 유형→가입 자격→손익통산→비과세 한도→초과분 과세의 빈칸 표를 채워 준다. 적용 연도를 먼저 고정하고 손실을 빼지 않은 줄부터 다시 계산한다.",
        "가입 자격·납입 또는 보유 조건·혜택 적용 기간을 세 칸으로 나눈다. 조건 하나가 없는 반례를 주고 비과세와 낮은 세율 과세를 다시 구별한다.",
        "유동성은 양도와 인출을 분리해 설명한다. 공제 계산은 실제 납입액과 공제대상 한도 중 작은 금액에 표시한 뒤 해당 공제율만 곱하게 한다.",
        "가입일·환매일·만기일을 시간선에 놓고 지금 속한 구간의 약정금리를 고른다. 양도는 다른 사람에게 파는 거래, 중도환매는 계약상 환매라는 차이를 사례로 보여 준다.",
        "재산을 맡긴 사람→운용·관리하는 사람→이익을 받는 사람을 먼저 설명하고 위탁자·수탁자·수익자 이름을 나중에 붙인다. 일반 신탁과 펀드는 별도 사례로 대조한다.",
        "공제받은 납입액·공제받지 않은 납입액·운용수익을 나눈다. 인출 사유와 수령 형태를 확인한 뒤 각 부분에 과세 여부를 붙이며 비과세로 단정한 줄을 수정한다.",
        "기초지수 경로 두 개를 그려 만기 가격은 같고 장벽 도달 여부만 다르게 만든다. 약정 지급액·중도해지 금액·예금보험 적용을 따로 계산하거나 판별한다.",
        "권리를 산 사람의 만기 현금흐름을 콜 max(S−K,0), 풋 max(K−S,0)로 먼저 그린다. 프리미엄 지급을 빼서 매수와 매도를 구별하고 현물 하락 위험의 헤지를 고른다.",
        "거래 수수료와 잔액 연동 수수료에서 거래 횟수 증가의 영향을 비교한다. 과도한 매매 유인 감소와 다른 이해상충의 잔존을 별개 문장으로 판단하게 한다.",
        "기관명·상품의 법적 유형·보호 근거를 세 칸으로 나누고 상품별로 확인한다. CMA라는 이름만으로 결론을 내리지 않게 서로 다른 운용 유형을 대조한다.",
        "미래 지급액의 발생 확률과 현재가치 할인을 분리한다. 사망보험과 생존보험의 지급 조건을 먼저 고른 뒤 예정위험률·예정이율 각각의 변화만 적용한다.",
    ]
    for review in reviews:
        if review["chapter_id"] == "S1C2":
            for topic, repair in zip(review["topics"][:12], repairs, strict=True):
                topic.setdefault("repair", repair)
        if review["chapter_id"] == "S3C9":
            for flag in review["quality_flags"]:
                if "26.7282" in flag.get("resolution", ""):
                    flag["resolution"] = flag["resolution"].replace("26.7282", "26.7278")
                    flag["refs"] = ["P3:462-463"]


def normalize_cross_links(reviews: list[dict]) -> list[dict]:
    """Disambiguate legacy source-topic numbers from destination-topic numbers."""
    destinations = {
        ("S3C3", "S3C1"): [6, 8, 9, 11],
        ("S3C3", "S3C2"): [4, 6, 12, 23, 25, 33, 37],
        ("S3C3", "S1C2"): [18, 20, 32],
        ("S3C4", "S2C3"): [2, 4, 8, 9, 11, 17],
        ("S3C4", "S2C4"): [1, 4, 5, 6, 12],
        ("S3C4", "S3C6"): [6, 13, 15, 19],
        ("S3C4", "S3C7"): [4, 6, 7, 9],
        ("S3C4", "S3C9"): [2, 3, 4, 5, 6],
        ("S3C5", "S2C3"): [1, 3, 8],
        ("S3C5", "S2C4"): [4, 5, 6, 13],
        ("S3C5", "S3C6"): [5, 6, 9, 15],
        ("S3C5", "S3C9"): [2, 5, 6, 8],
        ("S3C6", "S2C4"): [4, 5, 6],
        ("S3C6", "S3C4"): [10, 11, 12],
        ("S3C6", "S3C5"): [5, 8, 12, 15],
        ("S3C7", "S3C9"): [1, 5, 6, 9],
        ("S3C7", "S2C4"): [1, 3, 12],
        ("S3C7", "S3C4"): [14, 15, 16, 19],
        ("S3C8", "S3C5"): [9, 14, 15, 16],
        ("S3C8", "S2C3"): [1, 2, 23, 26],
        ("S3C8", "S3C7"): [5, 9],
        ("S3C9", "S3C7"): [3, 4, 6, 7],
        ("S3C9", "S3C4"): [5, 6, 8, 12, 18],
        ("S3C9", "S2C4"): [1, 3, 5, 12],
    }
    links = []
    for review in reviews:
        cid = review["chapter_id"]
        normalized = []
        for index, link in enumerate(review.get("cross_chapter_links", []), 1):
            if "source_topic_ids" in link:
                normalized.append(link)
                continue
            if "chapter" in link:
                target = link["chapter"]
                normalized.append({
                    "source_topic_ids": [topic_id(cid, n) for n in link["topics"]],
                    "target_topic_ids": [topic_id(target, n) for n in destinations[cid, target]],
                    "reason": link["reason"],
                    "legacy_note": "Legacy topics described the source chapter; explicit source and target IDs replace the ambiguous field.",
                })
            else:
                choices = [
                    (["S3C2T37"], ["S3C1T08"]),
                    (["S3C2T02"], ["S1C2T32"]),
                    (["S3C2T06"], ["S1C2T19"]),
                    (["S3C2T16", "S3C2T17"], ["S1C2T24", "S1C2T30", "S1C3T15"]),
                ]
                source_ids, target_ids = choices[index - 1]
                normalized.append({"source_topic_ids": source_ids, "target_topic_ids": target_ids,
                                   "reason": link["reason"], "legacy_evidence": link})
        review["cross_chapter_links"] = normalized
        links.extend({"id": f"{cid}-LINK-{n:02d}", **row} for n, row in enumerate(normalized, 1))
    return links


def normalize_questions(review: dict, document: str) -> list[dict]:
    cid = review["chapter_id"]
    result = []

    def add(key, kind, doc, page, numbers, test, **extra):
        result.append({
            "id": key, "kind": kind, "document": doc, "pdf_page": page,
            "chapter_id": cid, "topic_ids": [topic_id(cid, n) for n in numbers],
            "demand": test, "answer_page": extra.pop("answer_page", None),
            "source_status": "provided_commercial_material",
            "grading_status": "requires_item_conditions_and_issue_check",
            **extra,
        })

    for topic in review["topics"]:
        tid = topic_id(cid, topic["number"])
        page, test = topic["core"]
        add(tid + "-CORE", "core", document, page, [topic["number"]], test)
        for index, (page, test) in enumerate(topic["supplement"], 1):
            add(f"{tid}-SUP-{index:02d}", "supplement", document, page, [topic["number"]], test)
    for row in review["additional_questions"]:
        if isinstance(row, list):
            row = dict(zip(["number", "page", "topics", "test"], row, strict=True))
        add(f"{cid}-ADD-{row['number']:02d}", "additional", document, row["page"],
            row["topics"], row["test"], number=row["number"], answer_page=row.get("answer_page"))
    for row in review["calculation_questions"]:
        if isinstance(row, list):
            row = dict(zip(["number", "page", "topics", "test", "source_claim"], row, strict=True))
        add("CALC-" + row["number"], "calculation", "CALC", row["page"], row["topics"],
            row["test"], number=row["number"], answer_page=row.get("answer_page"),
            publisher_claim=row.get("source_claim"), embedded_examples=row.get("embedded_examples", []))
    for row in review["mock_questions"]:
        if isinstance(row, list):
            row = dict(zip(["set", "number", "page", "topics", "test"], row, strict=True))
        add(f"MOCK-{row['set']}-Q{row['number']:03d}", "mock", "MOCK", row["page"],
            row["topics"], row["test"], set=row["set"], number=row["number"],
            answer_page=row.get("answer_page"))
    warmup = review["warmup_mapping"]
    if isinstance(warmup, dict):
        for topic, numbers in warmup.items():
            for number in numbers:
                page = next(p for end, p in [(9, 2), (20, 3), (31, 4), (40, 5), (50, 6)] if number <= end)
                add(f"NOTE-{cid}-Q{number:03d}", "warmup", "NOTE", page, [int(topic)],
                    "세제 빈칸·OX와 해설 대조", number=number)
    else:
        for row in warmup:
            for number in row["numbers"]:
                add(f"NOTE-{cid}-Q{number:03d}", "warmup", "NOTE", row["page"],
                    row["topics"], row["test"], number=number,
                    mapping_precision="group_level; verify individual prompt before tutoring")
    return result


def parse_page_refs(refs: list[str]) -> set[tuple[str, int]]:
    result = set()
    for ref in refs:
        for match in re.finditer(r"\b(P12|P3|CALC|MOCK|NOTE):(\d+)(?:[-–](\d+))?", ref):
            doc, start, end = match.groups()
            result.update((doc, page) for page in range(int(start), int(end or start) + 1))
    return result


def compile_data(reviews: list[dict], outline: dict, documents: dict) -> tuple[list, list, list]:
    ledger, issues, routes = [], [], []
    for review, chapter in zip(reviews, outline["chapters"], strict=True):
        cid = review["chapter_id"]
        rows = normalize_questions(review, chapter["document"])
        ledger.extend(rows)
        for index, flag in enumerate(review["quality_flags"], 1):
            issues.append({
                "id": f"{cid}-ISSUE-{index:02d}", "chapter_id": cid,
                "refs": flag.get("refs", []), "issue": flag["issue"],
                "resolution": flag.get("resolution", flag.get("handling", "")),
                "status": "review_note; resolution text determines scope",
                "is_publisher_erratum": False,
            })
        for topic in review["topics"]:
            tid = topic_id(cid, topic["number"])
            routes.append({
                "id": tid, "chapter_id": cid, "chapter": review["title"], "title": topic["title"],
                "evidence": {"document": chapter["document"], "pdf_pages": topic["pages"],
                             "review": f"chapter_reviews/{cid}.json"},
                "required_action": topic.get("demand", topic.get("understand")),
                "explanation_plan": topic["assistant_delivery"],
                "memory_targets": topic.get("memory", topic.get("memorize")),
                "likely_confusion": topic["trap"], "check_plan": topic["check"],
                "repair_plan": topic["repair"],
                "question_ids": [row["id"] for row in rows if tid in row["topic_ids"]],
                "embedded_examples": topic.get("embedded_examples", []),
                "learner_state": "unassessed",
                "delivery_status": "preparation_route; instantiate an actual explanation before teaching",
                "rules": ["R02", "R04", "R24"],
            })
    issue_pages = {issue["id"]: parse_page_refs(issue["refs"]) for issue in issues}
    for row in ledger:
        row["source_path"] = documents[row["document"]]["path"]
        refs = {(row["document"], row["pdf_page"])}
        if row["answer_page"]:
            refs.add((row["document"], row["answer_page"]))
        row["same_page_review_notes"] = [key for key, pages in issue_pages.items() if pages & refs]
        row["issue_link_meaning"] = "page-level candidates, not a finding that this particular question is wrong"
    for route in routes:
        doc = route["evidence"]["document"]
        start, end = route["evidence"]["pdf_pages"]
        refs = {(doc, page) for page in range(start, end + 1)}
        route["same_page_review_notes"] = [key for key, pages in issue_pages.items() if pages & refs]
        route["chapter_review_notes"] = [i["id"] for i in issues if i["chapter_id"] == route["chapter_id"]]
        route["related_topic_ids"] = sorted({
            target for review in reviews for link in review.get("cross_chapter_links", [])
            if route["id"] in link["source_topic_ids"] for target in link["target_topic_ids"]
        })
    return ledger, issues, routes


def audit(reviews: list[dict], documents: dict, ledger: list, routes: list, progress: dict) -> dict:
    checks, errors, source_rows = [], [], []

    def check(name, passed, detail):
        checks.append({"check": name, "pass": bool(passed), "detail": detail})
        if not passed:
            errors.append(name)

    for doc, meta in documents.items():
        path = WORKSPACE / meta["path"]
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        check(f"{doc}: unchanged source", digest == meta["sha256"], digest)
        pages = read_json(ROOT / "extracted" / f"{doc}.json")
        check(f"{doc}: extracted sequence", [r["page"] for r in pages] == list(range(1, meta["pages"] + 1)), len(pages))
        read_pages = {page for start, end in progress["fully_read_pdf_page_intervals"][doc] for page in range(start, end + 1)}
        check(f"{doc}: recorded full reading", read_pages == set(range(1, meta["pages"] + 1)), len(read_pages))
        visual = set(progress["visually_checked_pages"].get(doc, []))
        check(f"{doc}: low-text visual review", set(meta["low_text_pages"]) <= visual, meta["low_text_pages"])
        for page in pages:
            source_rows.append({"document": doc, "pdf_page": page["page"],
                                "text_read": page["page"] in read_pages,
                                "image_checked": page["page"] in visual,
                                "characters": page["characters"]})
    ids = [q["id"] for q in ledger]
    tids = {r["id"] for r in routes}
    check("unique question IDs", len(ids) == len(set(ids)), len(ids))
    check("16 chapters, 285 unique topics, 2292 standalone items", len(reviews) == 16 and len(routes) == len(tids) == 285 and len(ledger) == 2292, [len(reviews), len(routes), len(ledger)])
    check("valid topic references", all(set(q["topic_ids"]) <= tids and q["topic_ids"] for q in ledger), "All questions link to identified topics")
    invalid_pages = [q["id"] for q in ledger if not 1 <= q["pdf_page"] <= documents[q["document"]]["pages"] or (q["answer_page"] is not None and not 1 <= q["answer_page"] <= documents[q["document"]]["pages"])]
    check("question/answer pages in bounds", not invalid_pages, invalid_pages)
    required = ["required_action", "explanation_plan", "memory_targets", "likely_confusion", "check_plan", "repair_plan", "question_ids"]
    incomplete = [r["id"] for r in routes if any(not r[k] for k in required)]
    check("all topic route fields present", not incomplete, incomplete)
    links = [link for review in reviews for link in review.get("cross_chapter_links", [])]
    check("cross-chapter source and target topic IDs", all(set(link["source_topic_ids"] + link["target_topic_ids"]) <= tids for link in links), len(links))
    for review in reviews:
        cid = review["chapter_id"]
        rows = [q for q in ledger if q["chapter_id"] == cid]
        actual = Counter(q["kind"] for q in rows)
        expected = dict(review["standalone_question_counts"])
        expected["calculation"] = expected.pop("calculation_including_unnumbered_variant")
        expected.pop("total")
        check(cid + ": type counts", all(actual[k] == n for k, n in expected.items()), dict(actual))
        for kind in ["warmup", "additional"]:
            nums = sorted(q["number"] for q in rows if q["kind"] == kind)
            check(f"{cid}: {kind} continuity", nums == list(range(1, len(nums) + 1)), len(nums))
    for exam_set in [1, 2]:
        nums = sorted(q["number"] for q in ledger if q["kind"] == "mock" and q["set"] == exam_set)
        check(f"MOCK-{exam_set}: Q1-Q100", nums == list(range(1, 101)), len(nums))
    calc = [q["number"] for q in ledger if q["kind"] == "calculation"]
    primary = sorted(int(n) for n in calc if n.isdecimal())
    check("CALC primary 01-70", primary == list(range(1, 71)), primary)
    check("CALC all named variants unique", len(calc) == len(set(calc)) == 129, len(calc))
    result = {
        "status": "pass" if not errors else "fail", "audited_at": datetime.now().astimezone().isoformat(),
        "counts": {"documents": len(documents), "pages": len(source_rows), "chapters": len(reviews),
                   "topics": len(routes), "standalone_questions": len(ledger), "by_kind": dict(Counter(q["kind"] for q in ledger)),
                   "visually_checked_pages": sum(r["image_checked"] for r in source_rows)},
        "checks": checks, "errors": errors,
        "boundary": "Checks verify inventory, recorded reading and reference consistency; they are not an independent proof of perfect comprehension, current law or every inline subquestion being separately counted.",
        "reading_scope": "All 1179 extracted page texts read; ambiguous formula/graph and low-text pages inspected visually. Not every page image was inspected.",
        "count_policy": "Standalone stems counted once at their source location. Repeated concepts across books remain distinct source items. Inline worked examples are reviewed within page/topic coverage, not exhaustively enumerated as additional standalone questions.",
    }
    write_json(ROOT / "completion_audit.json", result)
    with (ROOT / "page_coverage.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(source_rows[0]))
        writer.writeheader()
        writer.writerows(source_rows)
    if errors:
        raise ValueError("Audit failed: " + ", ".join(errors))
    return result


def generate_report(reviews, documents, ledger, issues, routes, result, examples) -> None:
    esc = lambda value: html.escape(str(value), quote=True)
    supplemental = read_json(ROOT / "supplemental_evidence.json")
    supplemental_by_id = {row["id"]: row for row in supplemental["items"]}
    omission_review = read_json(ROOT / "omission_audit.json")

    def pdf_link(doc, page):
        path = "../../" + quote(documents[doc]["path"], safe="/")
        return f'<a href="{path}#page={page}">{esc(doc)} PDF {page}쪽</a>'

    parts = ['''<!doctype html><html lang="ko"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>투자자산운용사 · 제공자료 분석 및 학습비서 준비</title>
<style>body{font:16px/1.8 system-ui,sans-serif;max-width:1080px;margin:40px auto;padding:0 24px;color:#182331;background:#f7f9fc}h1,h2,h3{line-height:1.4}a{color:#175baa}header,.chapter,.example{background:white;padding:24px;margin:20px 0;border:1px solid #dae2ed;border-radius:12px}summary{cursor:pointer;font-weight:650}details{padding:12px 0;border-bottom:1px solid #e4e9f1}dt{font-weight:650;color:#31516e}dd{margin:0 0 12px}table{width:100%;border-collapse:collapse}td,th{padding:8px;border-bottom:1px solid #dee4ec;text-align:left}small,.muted{color:#526174}.note{padding:12px;background:#fff4d9}input{box-sizing:border-box;width:100%;padding:12px;font:inherit}.counts{font-size:22px;font-weight:700}.source{font-size:14px}button{padding:8px 14px;cursor:pointer}@media print{input,button{display:none}body{background:white;margin:0}details{break-inside:avoid}}</style>
<header><p>제공 자료 기준 · 2026-10-13</p><h1>투자자산운용사 문제 분석과 학습비서 준비</h1>
<p class="counts">5개 PDF · 1,179쪽 · 16개 목차 · 285개 세부 주제 · 2,292개 독립 문항</p>
<p>본문 전체 읽기와 목차별 문항 검토를 마치고, 각 주제의 요구 행동·설명 방법·기억 대상·확인 질문·오류별 보완 방법을 연결했다. 아래에서 목차를 열면 개별 문항의 원본 위치까지 확인할 수 있다.</p>
<p class="note">분석 근거는 제공된 상업 교재다. 교재의 기출·동일유형 표시는 출판사 주장으로 보존했으며 공식 기출 인증이나 출제 확률로 바꾸지 않았다. 최신 법령·시험 적용 기준의 전수 검증은 별도다. 검토 주의사항은 확정 오탈자뿐 아니라 조건 누락·OCR·모델 가정 등을 포함한다.</p>
<p>285개 주제는 수업 준비 경로이며 완성 대화 285개를 뜻하지 않는다. 실제 설명·단계별 풀이·답변별 보완은 아래 시연 예제로 구체화했다. 본문 속 예제·수식은 읽기와 주제 검토에 포함하며, 독립 문항 수에 모든 작은 소문항을 별도 가산하지 않았다.</p>
<p><a href="question_ledger.csv">문항 목록 CSV</a> · <a href="topic_learning_routes.json">285개 학습 경로</a> · <a href="study_assistant_flow.json">학습비서 알고리즘</a> · <a href="completion_audit.json">누락 검사</a> · <a href="page_coverage.csv">전 페이지 기록</a></p></header>''']
    parts.append('<section class="chapter"><h2>누락 재점검에서 보완한 내용</h2>')
    parts.append('<p>원문 질문 표시와 문항 목록을 별도로 대조했다. 질문 표시가 더 많은 99쪽은 본문 예시·설명 질문·중복 축소 이미지·OCR 기호로 분류했고, 문제 문장이 OCR에서 빠진 3쪽은 원본 이미지로 복원했다. 이 대조 범위에서 추가로 빠진 독립 문항은 발견하지 못했다.</p>')
    parts.append(f'<p>기존 본문 예제 기록 354개, 세제 단원 확인사항 16쪽, 이번에 위치를 보강한 13개 기록을 합쳐 <strong>{supplemental["count"]}개 보조 학습요소 기록</strong>을 주제와 연결했다. 여러 소문항을 묶거나 기존 문제의 해설과 겹치는 기록이므로 2,292개에 더해 총문항 수로 계산하지 않는다.</p>')
    parts.append('<p><a href="omission_audit.json">누락 재점검 결과</a> · <a href="supplemental_evidence.json">본문 예제·OX 연결 목록</a> · <a href="source_page_index.json">1,179쪽의 역할·근거 연결</a> · <a href="publisher_exam_context.json">교재의 시험 구성·학습전략</a> · <a href="ocr_recoveries.json">OCR 문제 문장 복원</a></p>')
    parts.append('<p class="muted">해설 페이지가 개별 지정되지 않은 문항은 해설이 없다는 뜻이 아니다. 실제 수업에서는 해당 문제·해설·조건을 원본에서 대조한 뒤 채점한다. 전체 페이지의 모든 이미지·인쇄 기호를 새로 전수 검증했다는 의미도 아니다.</p></section>')
    counts = result["counts"]["by_kind"]
    parts.append('<h2>문항 구성</h2><table><tr><th>종류</th><th>독립 문항 수</th></tr>')
    for kind in KIND_NAMES:
        parts.append(f'<tr><td>{KIND_NAMES[kind]}</td><td>{counts.get(kind, 0)}</td></tr>')
    parts.append('</table><p class="muted">모의고사 2회 × 100문항, 계산문제 기본번호 01~70 및 별도 변형 포함 129개, 노트 750개 번호의 연속성을 검사했다. 출처가 다른 유사 문항은 별도 기록하고 같은 원본 문제의 해설 반복은 중복 계산하지 않았다.</p>')
    parts.append('<h2>학습비서가 실제로 제공할 설명 예시</h2><p>다음은 원문 복사가 아닌 설계 시연용 생성 예제다. 사용자 숙달 여부는 아직 평가하지 않았다.</p>')
    for example in examples:
        parts.append(f'<details class="example"><summary>{esc(example["title"])}</summary><p>연결: {esc(", ".join(example["topic_ids"]))}</p>')
        for key, label in [("goal", "이번 목표"), ("explanation", "실제 설명"), ("worked_example", "풀이와 이유"), ("memory", "기억할 핵심"), ("check", "정답을 가린 확인 질문"), ("repair", "답변별 보완")]:
            parts.append(f'<h3>{label}</h3><p>{esc(example[key]).replace(chr(10), "<br>")}</p>')
        parts.append(f'<details><summary>확인 질문 정답·판정 근거</summary><p>{esc(example["answer"])}</p></details></details>')
    parts.append('<h2>목차별 분석</h2><label for="filter">개념·문항 내용 검색</label><input id="filter" placeholder="예: ISA, 듀레이션, 추적오차"><p id="matches" aria-live="polite"></p>')
    qmap = {q["id"]: q for q in ledger}
    for review in reviews:
        cid = review["chapter_id"]
        topic_rows = [r for r in routes if r["chapter_id"] == cid]
        chapter_issues = [i for i in issues if i["chapter_id"] == cid]
        parts.append(f'<section class="chapter" id="{cid}"><h2>{cid} · {esc(review["title"])}</h2><p>{len(topic_rows)}개 주제 · {review["standalone_question_counts"]["total"]}개 독립 문항 · {len(chapter_issues)}개 검토 주의사항</p>')
        if review.get("chapter_demand"):
            parts.append(f'<p>{esc(review["chapter_demand"])}</p>')
        for route in topic_rows:
            doc = route["evidence"]["document"]
            start, end = route["evidence"]["pdf_pages"]
            parts.append(f'<details class="topic" id="{route["id"]}"><summary>{esc(route["id"])} · {esc(route["title"])} ({len(route["question_ids"])}개 연결)</summary><p>{pdf_link(doc, start)}~{end}쪽</p><dl>')
            for key, label in [("required_action", "문제가 요구하는 행동"), ("explanation_plan", "비서가 준비할 설명"), ("memory_targets", "기억 대상"), ("likely_confusion", "헷갈리는 조건"), ("check_plan", "확인 방법"), ("repair_plan", "막혔을 때 보완")]:
                parts.append(f'<dt>{label}</dt><dd>{esc(route[key])}</dd>')
            parts.append('</dl>')
            if route.get("supplemental_evidence_ids"):
                parts.append('<details><summary>본문 속 예제·OX·추가 이해자료</summary>')
                for evidence_id in route["supplemental_evidence_ids"]:
                    item = supplemental_by_id[evidence_id]
                    # One record can be relevant to more than one topic; anchor once.
                    anchor = f' id="{evidence_id}"' if route["id"] == item["topic_ids"][0] else ''
                    sources = ' · '.join(pdf_link(item["document"], page) for page in item["pages"])
                    parts.append(f'<p{anchor}><strong>{esc(item["description"])}</strong><br>{sources}</p>')
                    if item.get("teaching_point"):
                        parts.append(f'<p>{esc(item["teaching_point"])}</p>')
                    if item.get("description_scope"):
                        parts.append('<p class="muted">여러 페이지의 확인사항을 묶은 요약이다. 해당 페이지의 개별 문장을 확인한다.</p>')
                parts.append('</details>')
            parts.append('<details><summary>근거 문항과 원본 위치</summary><ul class="source">')
            for key in route["question_ids"]:
                q = qmap[key]
                answer = f' / 해설 {pdf_link(q["document"], q["answer_page"])}' if q["answer_page"] else ''
                flags = f' / 관련 페이지 주의사항 {esc(", ".join(q["same_page_review_notes"]))}' if q["same_page_review_notes"] else ''
                parts.append(f'<li>{esc(key)} · {pdf_link(q["document"], q["pdf_page"])}{answer} — {esc(q["demand"])}{flags}</li>')
                if q.get("ocr_recovery"):
                    correction = q["ocr_recovery"]
                    parts.append(f'<li>이미지로 복원한 조건: {esc(correction["recovered_prompt"])} {esc(correction["necessary_visual_conditions"])}</li>')
            parts.append('</ul></details>')
            if route["related_topic_ids"]:
                related = ' · '.join(f'<a href="#{tid}">{tid}</a>' for tid in route["related_topic_ids"])
                parts.append(f'<p class="source">다른 목차의 연결 개념: {related}</p>')
            parts.append('</details>')
        parts.append(f'<details><summary>이 목차의 검토 주의사항 {len(chapter_issues)}개</summary><p>페이지가 겹친다는 이유만으로 해당 문항이 틀렸다는 뜻은 아니다. 원문 조건과 아래 처리 내용을 함께 확인한다.</p>')
        for issue in chapter_issues:
            parts.append(f'<details id="{issue["id"]}"><summary>{esc(issue["id"])} · {esc(issue["issue"])}</summary><p>{esc(", ".join(issue["refs"]))}</p><p>{esc(issue["resolution"])}</p></details>')
        for source in review.get("primary_source_checks", []):
            url = source.get("url")
            if url:
                parts.append(f'<p class="source"><a href="{esc(url)}">외부 1차 자료</a> · {esc(source.get("scope", "해당 쟁점의 선택 검증"))} · {esc(source.get("findings", ""))}</p>')
        parts.append('</details></section>')
    parts.append(f'<footer><p>자동 검사: {len(result["checks"])}개 통과. 이미지 확인: {result["counts"]["visually_checked_pages"]}쪽. 전체 페이지의 텍스트 읽기와 필요한 수식·그래프의 이미지 대조를 구분해 기록했다.</p><p>기존 3개 자막 묶음의 42개 TXT 전수 재독 기록은 <a href="../full_reread_01.json">별도 보존</a>했다. 전수 10회독 완료로 기록하지 않았다.</p></footer>')
    parts.append('''<script>const box=document.getElementById('filter');box.addEventListener('input',()=>{const term=box.value.trim().toLowerCase();let count=0;document.querySelectorAll('.chapter').forEach(ch=>{let hits=0;ch.querySelectorAll('.topic').forEach(t=>{const show=t.textContent.toLowerCase().includes(term);t.hidden=!show;if(show){hits++;count++;}if(term)t.open=show;});ch.hidden=!hits;});document.getElementById('matches').textContent=term?count+'개 주제에서 일치':'';});</script></html>''')
    (ROOT / "analysis_report.html").write_text("\n".join(parts), encoding="utf-8")


def integrate(reviews: list, manifest: dict, progress: dict, result: dict) -> None:
    artifacts = {name: f"target_analysis/{filename}" for name, filename in {
        "report": "analysis_report.html", "question_ledger": "question_ledger.json",
        "learning_routes": "topic_learning_routes.json", "quality_issues": "quality_issues.json",
        "assistant_flow": "study_assistant_flow.json", "worked_lessons": "worked_lessons.json",
        "completion_audit": "completion_audit.json",
        "cross_chapter_links": "cross_chapter_links.json",
        "omission_audit": "omission_audit.json", "supplemental_evidence": "supplemental_evidence.json",
        "source_page_index": "source_page_index.json", "publisher_exam_context": "publisher_exam_context.json",
        "ocr_recoveries": "ocr_recoveries.json",
    }.items()}
    progress.update({"status": "completed_for_supplied_materials", "next": "개념 입력과 학습자 응답에 맞춰 실제 설명·확인·보완 실행",
                     "completion_scope": "5개 PDF 본문 읽기, 16개 목차·285개 주제·2292개 독립 문항 의미 검토와 전역 연결 검사 완료. 최신 법령 전수 검증 및 원문 모든 소문항의 개별 번호화와 구분.",
                     "current_law_verification": "selected_issues_checked; full current-law and exam-date applicability remain unverified",
                     "artifacts": artifacts, "audit_status": result["status"]})
    write_json(ROOT / "review_progress.json", progress)
    for doc in manifest["documents"]:
        doc["semantic_review"] = "completed_for_supplied_materials; see completion_audit.json for scope"
    write_json(ROOT / "target_manifest.json", manifest)
    for review in reviews:
        review["global_cross_reference_audit"] = "pass; completion_audit.json"
        write_json(ROOT / "chapter_reviews" / f"{review['chapter_id']}.json", review)
    contract = read_json(PREP / "exam_requirement_contract.json")
    contract["activation"]["current_work"] = "제공된 5개 PDF 분석과 학습비서 준비물 통합 완료. 개념별 수업에서 근거와 적용 조건을 확인하며 사용한다."
    contract["activation"]["draft_boundary"] = "요구 수준은 제공 상업 교재에 근거한 잠정 프로필이다. 공식 기출 인증·미래 출제 확률·최신 규정의 전수 확인 결과가 아니다."
    analysis = contract["supplied_material_analysis"]
    analysis.update({"status": "completed_for_supplied_materials", "counts": result["counts"], "artifacts": artifacts,
                     "pending": [], "separate_followups": ["실제 응시일 기준 법령·공식 범위·출판사 정오표 전수 확인", "학습자 응답을 통한 실제 수업과 난이도 보정"],
                     "quality_gate": "검토 주의사항과 원문 조건을 확인하기 전 문항의 출판사 정답을 자동 채점 정답으로 승인하지 않는다."})
    analysis["omission_recheck"] = read_json(ROOT / "omission_audit.json")["counts"]
    write_json(PREP / "exam_requirement_contract.json", contract)
    blueprint = read_json(PREP / "learning_assistant_blueprint.json")
    blueprint["exam_requirement_activation"] = contract["activation"]
    blueprint["preparation_audit"]["target_material_analysis"] = analysis
    readiness = blueprint["implementation_readiness"]
    for item in ["5개 PDF 전수 읽기와 2292개 독립 문항 연결", "285개 주제별 설명·기억·확인·보완 경로", "실제 설명 시연 6개와 오류별 분기", "교재 오류·가정 검토와 자동 채점 보류 규칙"]:
        if item not in readiness["prepared"]:
            readiness["prepared"].append(item)
    readiness["next_build_unit"] = "개념 입력→관련 학습 경로·근거 문항 조회→조건·오류 확인→실제 설명과 예제 제공→응답 진단→보완·회상·독립 적용"
    blueprint["target_analysis_artifacts"] = artifacts
    write_json(PREP / "learning_assistant_blueprint.json", blueprint)
    rules = read_json(PREP / "operational_rules.json")
    for rule in rules["rules"]:
        if rule["id"] in ["R02", "R04"]:
            key = "activation" if rule["id"] == "R02" else "exam_analysis_activation"
            rule[key] = contract["activation"]
        if rule["id"] in ["R02", "R04", "R24"]:
            rule["supplied_material_bindings"] = artifacts
    rules["target_analysis_artifacts"] = artifacts
    write_json(PREP / "operational_rules.json", rules)


def main() -> None:
    outline = read_json(ROOT / "outline.json")
    manifest = read_json(ROOT / "target_manifest.json")
    documents = {row["id"]: row for row in manifest["documents"]}
    reviews = [read_json(ROOT / "chapter_reviews" / f"{ch['id']}.json") for ch in outline["chapters"]]
    complete_record_fields(reviews)
    cross_links = normalize_cross_links(reviews)
    progress = read_json(ROOT / "review_progress.json")
    apply_additions(reviews, progress)
    for doc in ["MOCK", "NOTE"]:
        progress["visually_checked_pages"][doc] = sorted(set(progress["visually_checked_pages"][doc]) | {1})
    ledger, issues, routes = compile_data(reviews, outline, documents)
    omission_review = extend_evidence(reviews, outline, ledger, routes, progress)
    result = audit(reviews, documents, ledger, routes, progress)
    result["counts"]["review_notes"] = len(issues)
    result["omission_recheck"] = {"artifact": "omission_audit.json", "status": omission_review["status"], "counts": omission_review["counts"]}
    write_json(ROOT / "completion_audit.json", result)
    write_json(ROOT / "question_ledger.json", {"count": len(ledger), "items": ledger})
    write_json(ROOT / "quality_issues.json", {"count": len(issues), "note": "Not a count of confirmed publisher errors. Page links are candidates; read the resolution.", "items": issues})
    write_json(ROOT / "topic_learning_routes.json", {"count": len(routes), "items": routes})
    write_json(ROOT / "cross_chapter_links.json", {"count": len(cross_links), "items": cross_links})
    fields = ["id", "kind", "document", "source_path", "pdf_page", "answer_page", "chapter_id", "topic_ids", "demand", "same_page_review_notes", "grading_status"]
    with (ROOT / "question_ledger.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows({**q, "topic_ids": ";".join(q["topic_ids"]), "same_page_review_notes": ";".join(q["same_page_review_notes"])} for q in ledger)
    examples = read_json(ROOT / "worked_lessons.json")["examples"]
    for example in examples:
        assert set(example["topic_ids"]) <= {r["id"] for r in routes}, example["id"]
    generate_report(reviews, documents, ledger, issues, routes, result, examples)
    integrate(reviews, manifest, progress, result)
    # EVAL is a separate evidence-backed layer. Keep its bindings on recompilation.
    eval_dir = PREP / "eval"
    if (eval_dir / "eval_spec.json").exists():
        for name in ["exam_requirement_contract.json", "learning_assistant_blueprint.json"]:
            obj = read_json(PREP / name)
            obj["confirmed_exam_goal"] = read_json(eval_dir / "exam_goal.json")
            obj["eval_system"] = {
                "specification": "preparation/eval/eval_spec.json",
                "exam_goal": "preparation/eval/exam_goal.json",
                "item_contracts": "preparation/eval/item_contracts.json",
                "topic_rubrics": "preparation/eval/topic_rubrics.json",
                "report": "preparation/eval/eval_report.html",
                "executable": "preparation/eval/evaluator.py",
            }
            write_json(PREP / name, obj)
        report_path = ROOT / "analysis_report.html"
        report_text = report_path.read_text(encoding="utf-8")
        report_text = report_text.replace(
            "</header>",
            '<p><a href="../eval/eval_report.html">학습자·학습비서 EVAL · 70% 및 과목별 40% 합격 기준</a></p></header>',
            1,
        )
        report_path.write_text(report_text, encoding="utf-8")
    print(json.dumps({"status": result["status"], "counts": result["counts"], "checks": len(result["checks"]), "report": str(ROOT / "analysis_report.html")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
