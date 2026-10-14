"""Assistant evaluation protocol tests; fixture verdicts are not model accuracy."""

import copy

import pytest

from assistant_grader import assess, benchmark, make_context
from llm_provider import ProviderUnavailable
from test_semantic_grader import FixtureProvider


@pytest.fixture
def context():
    return make_context(case_id="quality-test", task_context="실제 설명을 제공해야 한다.",
                        target_ids=["A02", "A03"])


@pytest.fixture
def verdict():
    return {
        "case_id": "quality-test",
        "judgments": [
            {"criterion_id": "A02", "status": "contradicted",
             "response_quote": "그냥 외우세요.", "reason": "설명 대신 지시만 했다.",
             "reference_ids": ["A02"]},
            {"criterion_id": "A03", "status": "not_observed", "response_quote": "",
             "reason": "사실 설명이 없어 정확성은 관측하지 못했다.", "reference_ids": ["A03"]},
        ],
        "required_repair": "대상 개념의 뜻과 짧은 예제를 실제로 제공해야 한다.",
        "repair_reference_ids": ["A02"],
    }


def test_actual_output_and_all_selected_criteria_are_evaluated(context, verdict):
    provider = FixtureProvider([verdict])
    result = assess(provider, context=context, assistant_output="그냥 외우세요.")
    assert result["status"] == "assessed"
    assert result["critical_failures"] == ["A02"]
    assert result["critical_unobserved_or_held"] == ["A03"]
    assert result["quality_status"] == "repair_required"
    assert provider.payloads[0]["assistant_output"] == "그냥 외우세요."
    assert result["audit"]["provider"]["origin"] == "test_fixture_not_model"


@pytest.mark.parametrize("mutation", [
    "invented_quote", "invented_reference", "missing_criterion",
    "duplicate_criterion", "wrong_case", "missing_repair", "invented_repair_reference",
    "wrong_type", "extra_field",
])
def test_invalid_assistant_assessments_are_held(context, verdict, mutation):
    if mutation == "invented_quote":
        verdict["judgments"][0]["response_quote"] = "제출하지 않은 문장"
    elif mutation == "invented_reference":
        verdict["judgments"][0]["reference_ids"] = ["invented"]
    elif mutation == "missing_criterion":
        verdict["judgments"].pop()
    elif mutation == "duplicate_criterion":
        verdict["judgments"].append(copy.deepcopy(verdict["judgments"][0]))
    elif mutation == "wrong_case":
        verdict["case_id"] = "a-different-output"
    elif mutation == "missing_repair":
        verdict["required_repair"] = ""
    elif mutation == "invented_repair_reference":
        verdict["repair_reference_ids"] = ["not-a-source"]
    elif mutation == "wrong_type":
        verdict["judgments"][0]["reason"] = {"guess": True}
    else:
        verdict["all_assistants_are_correct"] = True
    result = assess(FixtureProvider([verdict]), context=context, assistant_output="그냥 외우세요.")
    assert result["status"] == "held"
    assert "critical_failures" not in result


def test_unobserved_critical_quality_is_not_a_pass(context, verdict):
    verdict["judgments"][0].update(status="not_observed", response_quote="",
                                    reason="설명을 요구하지 않은 대화라 관측할 수 없다.")
    verdict["required_repair"] = ""
    verdict["repair_reference_ids"] = []
    result = assess(FixtureProvider([verdict]), context=context, assistant_output="확인했습니다.")
    assert result["quality_status"] == "not_established"
    assert result["critical_unobserved_or_held"] == ["A02", "A03"]


def test_provider_unavailable_is_not_a_quality_verdict(context):
    result = assess(FixtureProvider([ProviderUnavailable("not configured")]),
                    context=context, assistant_output="제출된 설명")
    assert result["status"] == "held"
    assert "judgments" not in result


def test_all_twelve_criteria_are_available_without_authored_answer_labels():
    value = make_context(case_id="all", task_context="실제 대화를 평가한다.")
    assert len(value["criteria"]) == 12
    assert len({x["id"] for x in value["criteria"]}) == 12
    assert "expected_status" not in value
    with pytest.raises(ValueError):
        make_context(case_id="bad", task_context="", target_ids=["not-a-criterion"])


def test_benchmark_hides_expected_labels_from_the_provider():
    result = {
        "case_id": "A01-P",
        "judgments": [{"criterion_id": "A01", "status": "held", "response_quote": "",
                       "reason": "이 시험은 실제 모델 판정이 아닌 프로토콜 검증이다.",
                       "reference_ids": ["A01"]}],
        "required_repair": "", "repair_reference_ids": [],
    }
    provider = FixtureProvider([result])
    report = benchmark(provider, limit=1)
    assert "expected_status" not in provider.payloads[0]
    assert "expected_reason" not in provider.payloads[0]
    assert report["holds_or_unobserved"] == 1
    assert report["incorrect_acceptances"] == 0
    assert report["exact_agreement_including_holds"] == 0


@pytest.mark.parametrize("limit", [0, 25, -1, True])
def test_benchmark_refuses_ambiguous_or_unbounded_limits(limit):
    with pytest.raises(ValueError):
        benchmark(FixtureProvider([]), limit=limit)
