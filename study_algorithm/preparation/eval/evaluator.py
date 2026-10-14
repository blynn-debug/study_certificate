"""Deterministic study evaluation; model-based prose assessment is in semantic_grader.py."""

import argparse
import json
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SUBJECT_SIZES = {"S1": 20, "S2": 30, "S3": 50}
SUBJECT_MINIMUMS = {"S1": 8, "S2": 12, "S3": 20}
OBSERVATIONS = {"supported", "partial", "contradicted", "not_observed", "not_applicable", "held"}


def load_json(name: str) -> Any:
    """Read an evaluation artifact relative to this module."""
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def evaluate_exam(
    rows: list[dict[str, Any]],
    *,
    closed: bool,
    elapsed_seconds: float | None,
    assistance: str = "native_prompt_only",
    familiar_items: int = 0,
) -> dict[str, Any]:
    """Evaluate a 20/30/50, 100-slot mock without dropping held or blank slots.

    Rows are already adjudicated observations, not raw answer strings.
    A result describes this practice session, never a predicted official result.
    """
    if not 0 <= familiar_items <= 100:
        raise ValueError("familiar_items must be between 0 and 100")
    if assistance not in load_json("eval_spec.json")["assistance_record"]["levels"]:
        raise ValueError("Unknown assistance level")
    if elapsed_seconds is not None and (not 0 <= elapsed_seconds < float("inf")):
        raise ValueError("Elapsed time must be finite and nonnegative")
    seen: set[str] = set()
    counts = {s: dict(correct=0, incorrect=0, unanswered=0, held=0) for s in SUBJECT_SIZES}
    for row in rows:
        qid, subject, status = row["id"], row["subject"], row["status"]
        if not isinstance(qid, str) or not qid or qid in seen:
            raise ValueError("Every exam slot must have a unique nonempty ID")
        if subject not in counts or status not in counts[subject]:
            raise ValueError("Unknown subject or exam status")
        seen.add(qid)
        counts[subject][status] += 1
    for subject, values in counts.items():
        if sum(values.values()) > SUBJECT_SIZES[subject]:
            raise ValueError(f"Too many slots in {subject}")
    complete = all(sum(counts[s].values()) == n for s, n in SUBJECT_SIZES.items())
    subject_results = {}
    for subject, n in SUBJECT_SIZES.items():
        values = counts[subject]
        pending = n - sum(values.values())
        lower = values["correct"]
        upper = lower + values["held"] + pending
        subject_results[subject] = {
            **values, "total": n, "pending_slots": pending, "minimum": SUBJECT_MINIMUMS[subject],
            "lower_correct": lower, "upper_correct": upper,
            "lower_percent": lower * 100 / n, "upper_percent": upper * 100 / n,
            "minimum_deficit": max(0, SUBJECT_MINIMUMS[subject] - lower),
        }
    lower_total = sum(v["lower_correct"] for v in subject_results.values())
    upper_total = sum(v["upper_correct"] for v in subject_results.values())
    lower_pass = lower_total >= 70 and all(
        v["lower_correct"] >= v["minimum"] for v in subject_results.values()
    )
    upper_pass = upper_total >= 70 and all(
        v["upper_correct"] >= v["minimum"] for v in subject_results.values()
    )
    held = sum(v["held"] for v in counts.values())
    threshold_status = "indeterminate"
    if closed and complete and not held:
        threshold_status = "pass" if lower_pass else "fail"
    reasons = []
    if not closed or not complete:
        reasons.append("session_not_closed_or_missing_slots")
    if held:
        reasons.append("held_items_keep_original_denominators")
    if assistance != "native_prompt_only":
        reasons.append("assisted_session")
    if elapsed_seconds is None:
        reasons.append("timing_not_observed")
    elif elapsed_seconds > 7200:
        reasons.append("over_120_minutes")
    return {
        "scope": "practice_session_only; officially_cross_checked_70_and_40_rule_and_20_30_50_format",
        "threshold_status": threshold_status,
        "timed_independent_status": threshold_status if not reasons else "not_established",
        "original_total": 100, "lower_correct": lower_total, "upper_correct": upper_total,
        "overall_minimum": 70, "overall_deficit": max(0, 70 - lower_total),
        "held_count": held, "subjects": subject_results, "qualification_notes": reasons,
        "bounds": {"all_unknown_wrong_passes": lower_pass, "all_unknown_correct_passes": upper_pass},
        "priority_subjects": sorted(
            [s for s, v in subject_results.items() if v["minimum_deficit"] > 0],
            key=lambda s: (-subject_results[s]["minimum_deficit"], s),
        ),
        "familiar_items": familiar_items,
        "generalization": "Familiar-item performance does not establish unseen-item transfer or pass probability.",
    }


def normalize_choice(value: Any) -> str:
    """Normalize only an unambiguous single option; do not search prose for digits."""
    text = str(value).strip()
    circles = {"①": "1", "②": "2", "③": "3", "④": "4", "⑤": "5"}
    if text in circles:
        return circles[text]
    if re.fullmatch(r"[1-5](?:번)?", text):
        return text[0]
    raise ValueError("Submit one option, for example ③ or 3")


def score_case(case: dict[str, Any], response: Any, unit: str | None = None) -> dict[str, Any]:
    """Score an explicitly released choice or numeric case under its assumptions."""
    release = case["release"]
    if release["state"] != "adjudicated_under_explicit_assumptions":
        return {"status": "held", "reason": release["reason"]}
    if not release.get("evidence") or not case.get("prompt_reviewed"):
        return {"status": "held", "reason": "Missing adjudication or clean-prompt review"}
    if response is None or str(response).strip() == "":
        return {"status": "not_observed", "exam_on_closed_session": "unanswered"}
    expected = case["answer"]
    if expected["type"] == "choice":
        correct = normalize_choice(response) == normalize_choice(expected["value"])
    elif expected["type"] == "numeric":
        units = expected["accepted_units"]
        if unit not in units:
            return {"status": "partial", "reason": "unit_missing_or_not_accepted", "numeric_correct": None}
        try:
            value = Decimal(str(response)) * Decimal(str(units[unit]))
            target = Decimal(str(expected["value"]))
            tolerance = Decimal(str(expected["absolute_tolerance"]))
        except InvalidOperation as exc:
            raise ValueError("Numeric response must be a finite number") from exc
        if not all(x.is_finite() for x in [value, target, tolerance]) or tolerance < 0:
            raise ValueError("Numeric values and tolerances must be finite")
        correct = abs(value - target) <= tolerance
    else:
        return {"status": "held", "reason": "Semantic judgment requires an evidence-bearing reviewer"}
    return {
        "status": "supported" if correct else "contradicted", "exam_correct": correct,
        "understanding": "not_observed", "source_frame": release["state"],
        "repair": None if correct else case["repair"],
    }


def validate_judgments(
    response: str, criteria: list[dict[str, Any]], judgments: list[dict[str, Any]]
) -> dict[str, Any]:
    """Validate reviewer evidence structure, not the truth of semantic judgments."""
    expected = {c["id"]: c for c in criteria}
    results: dict[str, Any] = {}
    for judgment in judgments:
        cid, status = judgment["criterion_id"], judgment["status"]
        if cid not in expected or cid in results or status not in OBSERVATIONS:
            raise ValueError("Invalid, duplicate, or unknown criterion judgment")
        if status in {"supported", "partial", "contradicted"}:
            quote = judgment.get("response_quote", "")
            if not quote or quote not in response:
                raise ValueError("Observed judgments require an exact quote from the actual response")
            if not judgment.get("reason") or not judgment.get("criterion_evidence"):
                raise ValueError("Observed judgments require reasoning and source/criterion evidence")
        if status == "not_applicable":
            if not expected[cid].get("allow_not_applicable") or not judgment.get("reason"):
                raise ValueError("Not-applicable judgments require an explicitly optional criterion and a reason")
        results[cid] = judgment
    for cid in expected.keys() - results.keys():
        results[cid] = {"criterion_id": cid, "status": "not_observed"}
    critical_failures = [
        cid for cid, c in expected.items()
        if c.get("critical") and results[cid]["status"] in {"contradicted", "partial"}
    ]
    critical_unknowns = [
        cid for cid, c in expected.items()
        if c.get("critical") and results[cid]["status"] in {"held", "not_observed"}
    ]
    return {
        "judgments": results, "critical_failures": critical_failures, "critical_unknowns": critical_unknowns,
        "release_status": "correction_required" if critical_failures else (
            "not_established" if critical_unknowns else "reviewer_supported"
        ),
        "limit": "Protocol validation only; a human or separately calibrated semantic reviewer must verify meaning.",
    }


def classify_evidence(history: dict[str, Any]) -> dict[str, Any]:
    """Separate current assistance, delayed retrieval, and genuinely new conditions."""
    assisted = history.get("assistance", "unknown") not in {"native_prompt_only", "neutral_clarification"}
    assisted = assisted or history.get("answer_visible_during_attempt", False)
    delay = None
    if history.get("last_exposure_at") and history.get("response_at"):
        start = datetime.fromisoformat(history["last_exposure_at"])
        end = datetime.fromisoformat(history["response_at"])
        if start.tzinfo is None or end.tzinfo is None or end < start:
            raise ValueError("Exposure and response timestamps must be timezone-aware and ordered")
        delay = (end - start).total_seconds()
    return {
        "performance": "assisted" if assisted else "independent_this_attempt",
        "delayed_observation_seconds": delay if not assisted and delay and not history.get("intervening_study") else None,
        "novel_transfer_eligible": bool(
            not assisted and history.get("variant_adjudicated")
            and history.get("changed_condition") and not history.get("same_item_seen", True)
        ),
        "mastery": "not_inferred_from_one_attempt",
    }


def learner_prompt(case: dict[str, Any]) -> dict[str, Any]:
    """Return an allowlisted prompt without answer, explanation, or source metadata."""
    if not case.get("prompt_reviewed"):
        raise ValueError("Raw extraction is not an approved learner prompt")
    return {"id": case["id"], "prompt": case["prompt"], "response_format": case["response_format"]}


def main() -> None:
    """Provide reproducible local CLI entry points."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    exam = sub.add_parser("exam")
    exam.add_argument("--input", type=Path, required=True)
    for name in ["prompt", "score"]:
        command = sub.add_parser(name)
        command.add_argument("--case", required=True)
        if name == "score":
            command.add_argument("--response", required=True)
            command.add_argument("--unit")
    topic = sub.add_parser("topic")
    topic.add_argument("--id", required=True)
    args = parser.parse_args()
    if args.command == "exam":
        payload = json.loads(args.input.read_text(encoding="utf-8-sig"))
        result = evaluate_exam(**payload)
    elif args.command == "topic":
        result = next(x for x in load_json("topic_rubrics.json")["items"] if x["id"] == args.id)
    else:
        case = next(x for x in load_json("calibration_cases.json")["items"] if x["id"] == args.case)
        result = learner_prompt(case) if args.command == "prompt" else score_case(case, args.response, args.unit)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
