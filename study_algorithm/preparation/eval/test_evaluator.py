"""Behavior tests for pass boundaries, source gates, units, and evidence claims."""

import copy
import json
from pathlib import Path

import pytest

from evaluator import (
    classify_evidence,
    evaluate_exam,
    learner_prompt,
    load_json,
    normalize_choice,
    score_case,
    validate_judgments,
)

ROOT = Path(__file__).resolve().parent


@pytest.fixture
def cases():
    """Read the reviewed cases used by the same CLI as actual users."""
    return {x["id"]: x for x in load_json("calibration_cases.json")["items"]}


def exam_rows(correct_counts):
    """Make a full synthetic exam; every incorrect slot can later become held/blank."""
    return [
        {"id": f"{subject}-{i+1}", "subject": subject, "status": "correct" if i < correct else "incorrect"}
        for subject, total, correct in zip(["S1", "S2", "S3"], [20, 30, 50], correct_counts)
        for i in range(total)
    ]


@pytest.mark.parametrize(
    "counts,expected",
    [
        ((8, 12, 50), "pass"),   # Exactly 70, and two subjects exactly 40%.
        ((20, 30, 20), "pass"),  # Third subject exactly 40%.
        ((7, 30, 50), "fail"),  # High total cannot mask subject 1.
        ((20, 11, 50), "fail"),
        ((20, 30, 19), "fail"),
        ((20, 29, 20), "fail"), # 69, all subjects meet their floors.
        ((8, 12, 20), "fail"),  # Passing each floor is not passing overall.
        ((20, 30, 50), "pass"),
    ],
)
def test_pass_requires_both_total_and_every_subject(counts, expected):
    result = evaluate_exam(exam_rows(counts), closed=True, elapsed_seconds=7200)
    assert result["threshold_status"] == expected
    assert result["timed_independent_status"] == expected


def test_held_item_is_not_removed_to_inflate_score():
    rows = exam_rows((20, 29, 20))
    rows[49]["status"] = "held"
    result = evaluate_exam(rows, closed=True, elapsed_seconds=7000)
    assert result["original_total"] == 100
    assert (result["lower_correct"], result["upper_correct"]) == (69, 70)
    assert result["threshold_status"] == "indeterminate"
    assert result["bounds"] == {"all_unknown_wrong_passes": False, "all_unknown_correct_passes": True}


def test_held_subject_floor_remains_visible_even_with_high_total():
    rows = exam_rows((7, 30, 50))
    rows[7]["status"] = "held"
    result = evaluate_exam(rows, closed=True, elapsed_seconds=7000)
    assert result["subjects"]["S1"]["lower_correct"] == 7
    assert result["subjects"]["S1"]["upper_correct"] == 8
    assert result["priority_subjects"] == ["S1"]
    assert result["threshold_status"] == "indeterminate"


def test_submitted_blank_counts_in_denominator():
    rows = exam_rows((20, 29, 20))
    rows[49]["status"] = "unanswered"
    result = evaluate_exam(rows, closed=True, elapsed_seconds=7200)
    assert result["lower_correct"] == result["upper_correct"] == 69
    assert result["subjects"]["S2"]["unanswered"] == 1
    assert result["threshold_status"] == "fail"


@pytest.mark.parametrize("closed,remove", [(False, False), (True, True), (False, True)])
def test_incomplete_or_open_exam_cannot_claim_pass(closed, remove):
    rows = exam_rows((20, 30, 50))
    result = evaluate_exam(rows[:-1] if remove else rows, closed=closed, elapsed_seconds=100)
    assert result["threshold_status"] == "indeterminate"
    assert result["timed_independent_status"] == "not_established"


@pytest.mark.parametrize(
    "time,help_level,reason",
    [
        (7201, "native_prompt_only", "over_120_minutes"),
        (None, "native_prompt_only", "timing_not_observed"),
        (5000, "concept_hint", "assisted_session"),
        (5000, "worked_answer_visible", "assisted_session"),
    ],
)
def test_score_is_separate_from_exam_conditions(time, help_level, reason):
    result = evaluate_exam(exam_rows((8, 12, 50)), closed=True, elapsed_seconds=time, assistance=help_level)
    assert result["threshold_status"] == "pass"
    assert result["timed_independent_status"] == "not_established"
    assert reason in result["qualification_notes"]


def test_duplicate_and_overfull_exam_rejected():
    rows = exam_rows((20, 30, 50))
    with pytest.raises(ValueError):
        evaluate_exam(rows + [rows[0]], closed=True, elapsed_seconds=1)
    with pytest.raises(ValueError):
        evaluate_exam(rows + [{"id": "extra", "subject": "S1", "status": "correct"}],
                      closed=True, elapsed_seconds=1)


@pytest.mark.parametrize("time", [-1, float("nan"), float("inf")])
def test_invalid_time_rejected(time):
    with pytest.raises(ValueError):
        evaluate_exam(exam_rows((20, 30, 50)), closed=True, elapsed_seconds=time)


def test_user_confirmed_contract_matches_exam_engine():
    goal = load_json("exam_goal.json")
    assert goal["overall_minimum_correct_ratio"] == 0.7
    assert goal["each_subject_minimum_correct_ratio"] == 0.4
    assert goal["publisher_exam_format"]["minimum_correct_counts"] == {
        "overall": 70, "S1": 8, "S2": 12, "S3": 20,
    }


@pytest.mark.parametrize(
    "cid,response,unit",
    [
        ("E01", "1.3", "ratio"), ("E02", "4", "배"),
        ("E03", "0.2", "0_to_1"), ("E03", "2000", "0_to_10000"),
        ("E04", "35.882353", "억원"), ("E05", "80", "%"),
        ("E05", "0.8", "ratio"), ("E06", "7", "%"), ("E07", "20", "%"),
        ("E08", "110", "index"), ("E09", "1.732051", "ratio"),
        ("E11", "④", None), ("E11", "4번", None), ("E12", "0", "억원"),
    ],
)
def test_recalculated_answers_and_equivalent_units(cases, cid, response, unit):
    result = score_case(cases[cid], response, unit)
    assert result["status"] == "supported"
    assert result["understanding"] == "not_observed"


@pytest.mark.parametrize(
    "cid,response,unit",
    [
        ("E01", "1.24", "ratio"), ("E02", "0.2", "ratio"),
        ("E03", "2000", "0_to_1"), ("E04", "30", "억원"),
        ("E05", "60", "%"), ("E06", "4", "%"),
        ("E07", "10", "%"), ("E08", "80", "index"),
        ("E09", "1.74", "ratio"), ("E11", "3", None), ("E12", "30", "억원"),
    ],
)
def test_concept_condition_and_unit_traps_get_actual_repair(cases, cid, response, unit):
    result = score_case(cases[cid], response, unit)
    assert result["status"] == "contradicted"
    assert result["repair"]["actual_explanation"]
    assert result["repair"]["next_probe"]["withheld_answer"]


def test_missing_unit_is_not_invented(cases):
    assert score_case(cases["E05"], "80")["status"] == "partial"
    assert score_case(cases["E05"], "80", "원")["numeric_correct"] is None


@pytest.mark.parametrize("response", ["nan", "Infinity", "-Infinity", "not a number"])
def test_nonfinite_or_invalid_number_is_not_a_correct_answer(cases, response):
    with pytest.raises(ValueError):
        score_case(cases["E05"], response, "ratio")


def test_source_conflict_cannot_be_overridden_by_publisher_key(cases):
    assert score_case(cases["E10"], "④")["status"] == "held"


def test_missing_release_evidence_holds_score(cases):
    case = copy.deepcopy(cases["E05"])
    case["release"]["evidence"] = ""
    assert score_case(case, ".8", "ratio")["status"] == "held"


def test_blank_does_not_mean_observed_concept_failure(cases):
    result = score_case(cases["E05"], "", "ratio")
    assert result == {"status": "not_observed", "exam_on_closed_session": "unanswered"}


@pytest.mark.parametrize("response", ["1 또는 4", "답은 4인 듯", "6", "14"])
def test_ambiguous_choice_is_not_silently_parsed(response):
    with pytest.raises(ValueError):
        normalize_choice(response)


def test_learner_prompt_allowlist_blocks_metadata_leakage(cases):
    prompt = learner_prompt(cases["E05"])
    assert set(prompt) == {"id", "prompt", "response_format"}
    assert "answer" not in prompt and "release" not in prompt
    case = copy.deepcopy(cases["E05"])
    case["prompt_reviewed"] = False
    with pytest.raises(ValueError):
        learner_prompt(case)


def test_old_exposure_allows_delayed_recall_but_not_novel_transfer():
    result = classify_evidence({
        "assistance": "native_prompt_only", "same_item_seen": True,
        "last_exposure_at": "2026-10-10T12:00:00+09:00",
        "response_at": "2026-10-13T12:00:00+09:00",
        "variant_adjudicated": True, "changed_condition": True,
    })
    assert result["performance"] == "independent_this_attempt"
    assert result["delayed_observation_seconds"] == 3 * 86400
    assert result["novel_transfer_eligible"] is False


def test_current_answer_visibility_blocks_independence():
    result = classify_evidence({
        "assistance": "native_prompt_only", "answer_visible_during_attempt": True,
        "same_item_seen": False, "variant_adjudicated": True, "changed_condition": True,
    })
    assert result["performance"] == "assisted"
    assert not result["novel_transfer_eligible"]


def test_reviewed_new_condition_is_transfer_eligible_not_mastery():
    result = classify_evidence({
        "assistance": "native_prompt_only", "same_item_seen": False,
        "variant_adjudicated": True, "changed_condition": True,
    })
    assert result["novel_transfer_eligible"]
    assert result["mastery"] == "not_inferred_from_one_attempt"


def test_no_timestamp_no_long_term_memory_claim():
    result = classify_evidence({"assistance": "native_prompt_only"})
    assert result["delayed_observation_seconds"] is None


def test_semantic_judgment_requires_real_response_quote(cases):
    criteria = cases["E05"]["criteria"]
    judgment = {"criterion_id": criteria[0]["id"], "status": "supported",
                "response_quote": "공분산0", "reason": "조건 확인", "criterion_evidence": "E05"}
    with pytest.raises(ValueError):
        validate_judgments("답80%만 알고 있습니다", criteria, [judgment])
    result = validate_judgments("공분산0", criteria, [judgment])
    assert result["judgments"][criteria[1]["id"]]["status"] == "not_observed"
    assert result["release_status"] == "not_established"


def test_assistant_critical_error_is_not_averaged_away():
    criteria = load_json("eval_spec.json")["assistant_rubric"]
    judgments = [
        {"criterion_id": c["id"], "status": "contradicted" if c["id"] == "A03" else "supported",
         "response_quote": "잔액90이므로30추가납부", "reason": "검토자 판정 사례",
         "criterion_evidence": "E12"}
        for c in criteria
    ]
    result = validate_judgments("잔액90이므로30추가납부", criteria, judgments)
    assert result["critical_failures"] == ["A03"]
    assert result["release_status"] == "correction_required"


def test_mandatory_critical_criterion_cannot_be_marked_not_applicable():
    criteria = [{"id": "A03", "critical": True}]
    with pytest.raises(ValueError):
        validate_judgments("", criteria, [
            {"criterion_id": "A03", "status": "not_applicable", "reason": "검사 생략"},
        ])


def test_artifact_coverage_is_exact_not_just_equal_counts():
    items = load_json("item_contracts.json")["items"]
    ledger = json.loads((ROOT.parent / "target_analysis/question_ledger.json").read_text(encoding="utf-8"))["items"]
    assert {x["id"] for x in items} == {x["id"] for x in ledger}
    assert len(items) == 2292
    assert all(x["rationale_evidence"] and x["topic_ids"] for x in items)
    assert len(load_json("topic_rubrics.json")["items"]) == 285
    assert len(load_json("embedded_evidence_coverage.json")["items"]) == 383
    assert all(load_json("coverage_audit.json")["checks"].values())
