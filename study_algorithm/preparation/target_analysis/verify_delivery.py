"""Verify report navigation, integration references and worked-example arithmetic."""

from __future__ import annotations

import json
import math
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent


class ReportParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links = []
        self.ids = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if "id" in values:
            self.ids.append(values["id"])
        if tag == "a" and "href" in values:
            self.links.append(values["href"])


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    parser = ReportParser()
    parser.feed((ROOT / "analysis_report.html").read_text(encoding="utf-8"))
    assert len(parser.ids) == len(set(parser.ids)), "Duplicate report anchors"
    missing = []
    for href in parser.links:
        link = urlsplit(href)
        if link.scheme:
            continue
        if link.path and not (ROOT / unquote(link.path)).exists():
            missing.append(href)
        if not link.path and link.fragment not in parser.ids:
            missing.append(href)
    assert not missing, missing
    flow = load(ROOT / "study_assistant_flow.json")
    for ref in flow["basis"].values():
        assert (ROOT / ref).exists(), ref
    topics = load(ROOT / "topic_learning_routes.json")["items"]
    tids = {r["id"] for r in topics}
    examples = load(ROOT / "worked_lessons.json")["examples"]
    assert len(examples) == 6
    for lesson in examples:
        assert set(lesson["topic_ids"]) <= tids, lesson["id"]
        for field in ["goal", "explanation", "worked_example", "memory", "check", "answer", "repair"]:
            assert lesson[field].strip(), (lesson["id"], field)
    calc = {
        "bond_two_year_yield_10pct": 5 / 1.1 + 105 / 1.1**2,
        "bond_two_year_yield_5pct": 5 / 1.05 + 105 / 1.05**2,
        "forward_check_price": 200 * 1.04,
        "forward_check_profit": 215 - 200 * 1.04,
        "tracking_error": math.sqrt((1.5 - 1)**2 * 0.2**2 + 0.06**2),
        "portfolio_mean": 0.5 * 0.08 + 0.5 * 0.04,
        "portfolio_sigma_rho_0": math.sqrt(0.5**2 * 0.2**2 + 0.5**2 * 0.1**2),
        "portfolio_sigma_rho_minus_1": abs(0.5 * 0.2 - 0.5 * 0.1),
        "corrected_irr": (-1.1 + math.sqrt(1.21 + 12)) / 2 - 1,
    }
    expected = [91.32231404958677, 100, 208, 7, 0.11661903789690602, 0.06, 0.1118033988749895, 0.05, 0.26727818453862473]
    assert all(math.isclose(value, reference, rel_tol=1e-10) for value, reference in zip(calc.values(), expected, strict=True))
    for filename in ["exam_requirement_contract.json", "learning_assistant_blueprint.json", "operational_rules.json"]:
        data = load(ROOT.parent / filename)
        if filename == "exam_requirement_contract.json":
            assert data["supplied_material_analysis"]["status"] == "completed_for_supplied_materials"
            refs = data["supplied_material_analysis"]["artifacts"]
        else:
            refs = data["target_analysis_artifacts"]
        for ref in refs.values():
            assert (ROOT.parent / ref).exists(), ref
    result = {
        "status": "pass", "report_links_checked": len(parser.links),
        "report_anchors_checked": len(parser.ids), "worked_examples": len(examples),
        "numeric_results": calc, "integration_files": 3,
        "boundary": "Local link existence, anchor validity, reference integration and stated example arithmetic. No browser interaction or empirical learning-effect evaluation.",
    }
    (ROOT / "delivery_checks.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
