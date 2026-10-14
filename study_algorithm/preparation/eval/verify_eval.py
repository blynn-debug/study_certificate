"""Verify release artifacts and record test results without asserting semantic mastery."""

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
PREP = ROOT.parent
WORKSPACE = PREP.parent


def read(path):
    """Read local JSON."""
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    """Write review results."""
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class ReportLinks(HTMLParser):
    """Collect local links and IDs without opening a browser."""

    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])


def main():
    """Fail visibly on missing evidence, changed sources, or broken integration."""
    test_xml = ET.parse(ROOT / "test_results.xml").getroot()
    suites = list(test_xml.iter("testsuite"))
    totals = {k: sum(int(s.attrib.get(k, 0)) for s in suites) for k in ["tests", "failures", "errors", "skipped"]}
    test_result = {
        "status": "pass" if totals["tests"] and not (totals["failures"] or totals["errors"]) else "fail",
        **totals, "command": "python -m pytest preparation/eval/test_evaluator.py -q",
        "scope": "70/40 경계·과락·미응답·보류·시간·도움·단위·노출·판정 근거·누락 연결 코드 검증",
        "not_measured": ["자연어 의미 판정의 정확도", "실제 학습자 효과", "실제 합격확률", "평가자간 일치도"],
        "test_case_names": [x.attrib["name"] for x in test_xml.iter("testcase")],
        "code_sha256": {
            f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in ["evaluator.py", "test_evaluator.py"]
        },
    }
    write(ROOT / "test_results.json", test_result)
    errors = []
    manifest = read(PREP / "source_manifest.json")
    physical_count = 0
    for row in manifest:
        for source in [row, *row.get("copies", [])]:
            physical_count += 1
            digest = hashlib.sha256((WORKSPACE / source["path"]).read_bytes()).hexdigest()
            if digest.lower() != source["sha256"].lower():
                errors.append(f"SRC changed: {source['path']}")
    if physical_count != 42:
        errors.append(f"Expected 42 physical SRC files, found {physical_count}")
    indexed = {r["id"]: r for r in manifest}
    citations_checked = 0
    for rule in read(ROOT / "source_grounding.json")["rules"]:
        for reference in rule["evidence"]:
            match = re.fullmatch(r"([^:]+):(\d+)-(\d+)", reference)
            if match is None:
                errors.append(f"Unparsed SRC citation: {reference}")
                continue
            vid, start, end = match.groups()
            if vid not in indexed or not 1 <= int(start) <= int(end) <= indexed[vid]["lines"]:
                errors.append(f"Invalid SRC citation: {reference}")
            citations_checked += 1
    parser = ReportLinks()
    parser.feed((ROOT / "eval_report.html").read_text(encoding="utf-8"))
    duplicate_ids = [name for name, count in Counter(parser.ids).items() if count > 1]
    if duplicate_ids:
        errors.append(f"Duplicate report IDs: {duplicate_ids}")
    for href in parser.links:
        parsed = urlsplit(href)
        if parsed.scheme:
            errors.append(f"Unexpected nonlocal report link: {href}")
            continue
        if parsed.path and not (ROOT / unquote(parsed.path)).resolve().is_file():
            errors.append(f"Missing report file: {href}")
        if not parsed.path and parsed.fragment and unquote(parsed.fragment) not in parser.ids:
            errors.append(f"Missing report anchor: {href}")
    for filename in ["learning_assistant_blueprint.json", "exam_requirement_contract.json"]:
        data = read(PREP / filename)
        if data.get("confirmed_exam_goal") != read(ROOT / "exam_goal.json"):
            errors.append(f"Goal not integrated: {filename}")
        for ref in data.get("eval_system", {}).values():
            if not (WORKSPACE / ref).is_file():
                errors.append(f"Missing integrated artifact: {ref}")
    flow = read(PREP / "target_analysis/study_assistant_flow.json")
    if flow["evaluation"]["pass_rule"] != "overall>=70% AND each_subject>=40%":
        errors.append("Flow lost pass rule")
    report = (PREP / "target_analysis/analysis_report.html").read_text(encoding="utf-8")
    if "../eval/eval_report.html" not in report:
        errors.append("Original report lost EVAL navigation")
    coverage = read(ROOT / "coverage_audit.json")
    if coverage["status"] != "pass":
        errors.append("Coverage audit failed")
    if test_result["status"] != "pass":
        errors.append("Behavior tests failed")
    benchmark = read(ROOT / "assistant_benchmark.json")
    if {x["target_criterion"] for x in benchmark["items"]} != {f"A{i:02}" for i in range(1, 13)}:
        errors.append("Assistant criteria not covered")
    result = {
        "status": "pass" if not errors else "fail",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "errors": errors, "source_files_hash_checked": physical_count, "source_citations_checked": citations_checked,
        "report_links_checked": len(parser.links), "report_ids_checked": len(parser.ids),
        "behavior_tests": totals, "coverage": coverage["counts"],
        "boundary": "원본 보존·참조·코드 검증. 별도 전 문항 정답 승인이나 실제 학습 성과 측정이 아니다.",
    }
    write(ROOT / "delivery_checks.json", result)
    if errors:
        raise ValueError(json.dumps(result, ensure_ascii=False))
    progress = read(ROOT / "progress.json")
    progress.update({
        "status": "foundation_verified_current_law_and_live_model_followup_in_progress",
        "completed_scope": "2292문항 답·해설 EVAL 검토, 285주제 기준, 383본문 근거 연결, SRC31규칙, 학습자·비서 평가, 합격70/40 판정 코드와 검증",
        "validation": "delivery_checks.json",
        "separate_runtime_requirements": [
            "전체 문항을 실제 자동 채점에 투입하기 전 문항별 gold·원문 조건·학습자용 문항 승인",
            "구현된 자연어 평가 모듈의 API 공급자·모델 설정과 실모델 보정",
            "2026-10-13 시행 기준 법령·규정의 문항별 검증 계속",
            "실제 응답 기반 진단·평가자 일치도·학습효과 측정",
        ],
        "followup_artifacts": {
            "learner_runtime": "semantic_grader.py",
            "assistant_runtime": "assistant_grader.py",
            "current_source_review": "../verification_20261013/verification_report.html",
            "current_source_counts": "../verification_20261013/verification_summary.json",
        },
    })
    write(ROOT / "progress.json", progress)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
