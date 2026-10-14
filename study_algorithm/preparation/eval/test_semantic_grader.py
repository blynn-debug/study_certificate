"""Protocol/security regressions with labelled fixtures, not empirical model accuracy."""

import copy
import json
from pathlib import Path

import pytest

from llm_provider import ProviderUnavailable, ResponsesProvider
from release_policy import fingerprint, variant_fingerprint
from semantic_grader import Corpus, InvalidAssessment, digest, grade, validate_assessment, validate_rubric

FIXTURE_PROMPT = "국세 공시송달 기간이 30일이라는 ④는 옳은가?"


class FixtureProvider:
    """A deterministic queued fixture: it never claims to understand natural language."""

    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.payloads = []

    def complete(self, **kwargs):
        self.payloads.append(kwargs["payload"])
        value = self.outputs.pop(0)
        if isinstance(value, Exception):
            raise value
        return {"data": copy.deepcopy(value), "metadata": {"origin": "test_fixture_not_model"}}


class SmallCorpus:
    """Minimal local evidence makes failure modes inspectable."""

    def __init__(self, *, released=True):
        self.released = released

    def context(self, item_id, mode):
        return {
            "item_id": item_id, "mode": mode, "as_of": "2026-10-13",
            "source_frame": "adjudicated_current" if self.released else "publisher_provisional",
            "references": {"law:L005": "공시송달의 기간은 14일이며 30일이 아니다."},
            "release": {
                "state": "adjudicated_current", "as_of": "2026-10-13", "answer": "④",
                "evidence": ["L005"], "prompt_correspondence_reviewed": True,
                "clean_prompt": FIXTURE_PROMPT,
            } if self.released else {},
            "study_methods": {"branches": [{"method": f"method{i}", "rules": ["R14"]} for i in range(1, 9)]},
        }


@pytest.fixture
def rubric():
    return {
        "item_id": "test-item", "source_consistency": "consistent",
        "source_limit": "법정 요건을 충족한 국세 공시송달", "conditions": ["국세 공시송달"],
        "criteria": [
            {"id": "C1", "dimension": "reason", "expected": "14일과 30일을 구별",
             "critical": True, "evidence": [{"reference_id": "law:L005", "quote": "공시송달의 기간은 14일"}]},
        ],
    }


@pytest.fixture
def assessment():
    return {
        "item_id": "test-item",
        "judgments": [{"criterion_id": "C1", "status": "supported", "response_quote": "14일",
                       "reason": "현재 조문과 기간이 일치한다.", "reference_ids": ["law:L005"]}],
        "selected_option": "4", "selection_quote": "④",
        "diagnosis": "기간을 정확히 구별했다.",
        "explanation": "공시송달은 요건을 충족한 공고 후 14일이 지나 효력이 생긴다.",
        "worked_example": "예시: 30일이라고 쓴 선지는 기간에서 틀렸다.",
        "next_probe": "공시송달의 기간을 30일로 설명한 문장을 어떻게 고칠까요?",
        "feedback_reference_ids": ["law:L005"], "method_index": None, "method_reason": "",
    }


def run_grade(rubric, assessment, *, released=True, response="④, 공시송달은 14일", reviewer=None, mode="explain"):
    return grade(SmallCorpus(released=released), FixtureProvider([rubric, assessment]),
                 item_id="test-item", response=response, mode=mode, review_provider=reviewer,
                 history={"assistance": "native_prompt_only"},
                 prompt_sha256=digest(FIXTURE_PROMPT))


def test_all_2292_items_have_private_contexts():
    corpus = Corpus()
    assert len(corpus.packets) == 2292
    for item_id, packet in corpus.packets.items():
        context = corpus.context(item_id, "explain")
        assert context["references"]["publisher:rationale"]
        assert f"page:{packet['document']}:{packet['question_page']}" in context["references"]
    # This is coverage, not a claim that all question texts are clean or legally verified.


def test_fixtures_are_explicitly_not_live_model_results(rubric, assessment):
    result = run_grade(rubric, assessment)
    assert result["semantic_status"] == "supported"
    assert result["exam_status"] == "correct"
    assert result["mastery"] == "not_established_by_one_response"
    assert all(x["metadata"]["origin"] == "test_fixture_not_model" for x in result["audit"]["calls"])
    assert result["audit"]["semantic_accuracy_empirically_established"] is False


def test_rubric_is_created_without_seeing_learner_response(rubric, assessment):
    provider = FixtureProvider([rubric, assessment])
    grade(SmallCorpus(), provider, item_id="test-item", response="④, 공시송달은 14일")
    assert "learner_response" not in provider.payloads[0]
    assert provider.payloads[1]["learner_response"] == "④, 공시송달은 14일"


def test_unverified_publisher_key_cannot_enter_pass_score(rubric, assessment):
    result = run_grade(rubric, assessment, released=False)
    assert result["exam_status"] == "held"
    assert result["semantic_frame"] == "provisional_reference_frame"


def test_wrong_reason_does_not_cancel_correct_mcq_credit(rubric, assessment):
    assessment["judgments"][0].update(status="contradicted", response_quote="30일",
                                     reason="학습자가 기간을 30일로 잘못 설명했다.")
    result = run_grade(rubric, assessment, response="④, 공시송달은 30일")
    assert result["exam_status"] == "correct"
    assert result["semantic_status"] == "repair_required"


@pytest.mark.parametrize("consistency", ["conflicting", "insufficient"])
def test_source_problem_prevents_definitive_grade(rubric, assessment, consistency):
    rubric["source_consistency"] = consistency
    result = run_grade(rubric, assessment)
    assert result["exam_status"] == "held"
    assert result["semantic_status"] == "held_source"
    assert result["feedback"] is None
    assert result["study_method"] is None


@pytest.mark.parametrize("prompt_hash", [None, digest("A different original question")])
def test_exam_credit_needs_the_actual_reviewed_prompt(rubric, assessment, prompt_hash):
    result = grade(SmallCorpus(), FixtureProvider([rubric, assessment]),
                   item_id="test-item", response="④, 공시송달은 14일",
                   prompt_sha256=prompt_hash)
    assert result["exam_status"] == "held"
    assert result["prompt_correspondence"] == "not_confirmed_exam_credit_held"


def test_confirmed_source_error_does_not_become_a_learner_mistake():
    provider = FixtureProvider([])
    result = grade(Corpus(), provider, item_id="S1C1T03-SUP-02", response="①도 틀렸습니다.")
    assert result["semantic_status"] == "held_source"
    assert result["learner_error_recorded"] is False
    assert result["provider_calls"] == 0
    assert provider.payloads == []


class CorrectedCorpus(SmallCorpus):
    """A reviewed replacement fixture, preserving the erroneous original as evidence."""

    def __init__(self, mutation=None):
        super().__init__()
        self.mutation = mutation

    def context(self, item_id, mode):
        context = super().context(item_id, mode)
        correction = {"id": "C-test", "item_ids": [item_id], "finding": "Old key incorrectly used 30 days"}
        context["source_corrections"] = [correction]
        release = context["release"]
        release.update({
            "prompt_variant": "corrected_reviewed_prompt",
            "correction_resolution": {"C-test": {
                "reviewed_correction_sha256": fingerprint(correction),
                "resolution_note": "The replacement asks the verified 14-day condition explicitly.",
            }},
        })
        release["corrected_variant_sha256"] = variant_fingerprint(release)
        if self.mutation:
            self.mutation(context)
        return context


def test_reviewed_correction_can_be_graded_only_as_the_delivered_replacement(rubric, assessment):
    provider = FixtureProvider([rubric, assessment])
    result = grade(CorrectedCorpus(), provider, item_id="test-item", response="④, 공시송달은 14일",
                   prompt_sha256=digest(FIXTURE_PROMPT))
    assert result["exam_status"] == "correct"
    assert result["prompt_variant"] == "corrected_reviewed_prompt"
    assert result["original_source_corrections_preserved"] == ["C-test"]
    assert provider.payloads[0]["source_corrections"][0]["id"] == "C-test"


@pytest.mark.parametrize("mutation", [
    lambda c: c["release"].pop("correction_resolution"),
    lambda c: c["release"].update(as_of="2026-10-12"),
    lambda c: c["release"].update(clean_prompt="Changed but not re-reviewed"),
    lambda c: c["release"].update(answer="③"),
    lambda c: c["source_corrections"][0].update(finding="Additional fault was found"),
    lambda c: c["source_corrections"].append({"id": "C-new", "item_ids": ["test-item"]}),
    lambda c: c["release"].update(prompt_variant="source_compatible"),
])
def test_stale_or_incomplete_correction_review_stays_held_before_api(mutation):
    provider = FixtureProvider([])
    result = grade(CorrectedCorpus(mutation), provider, item_id="test-item", response="④",
                   prompt_sha256=digest(FIXTURE_PROMPT))
    assert result["semantic_status"] == "held_source"
    assert result["learner_error_recorded"] is False
    assert provider.payloads == []


@pytest.mark.parametrize("prompt_hash", [None, digest("The old original prompt")])
def test_repair_never_relabels_an_attempt_on_the_original(prompt_hash):
    provider = FixtureProvider([])
    result = grade(CorrectedCorpus(), provider, item_id="test-item", response="④",
                   prompt_sha256=prompt_hash)
    assert result["semantic_status"] == "held_source"
    assert provider.payloads == []


def test_stale_release_is_not_served_to_a_learner():
    corpus = Corpus()
    corpus.releases["S1C1T01-SUP-01"]["as_of"] = "2026-10-12"
    with pytest.raises(ValueError):
        corpus.learner_prompt("S1C1T01-SUP-01")


def test_learner_prompt_is_reviewed_and_contains_no_private_answer_fields():
    prompt = Corpus().learner_prompt("S1C1T01-SUP-01")
    assert set(prompt) == {"item_id", "as_of", "prompt", "prompt_sha256"}
    assert prompt["prompt_sha256"] == digest(prompt["prompt"])
    assert "정답" not in prompt["prompt"]
    corrected = Corpus().learner_prompt("S1C1T03-SUP-02")
    assert set(corrected) == set(prompt)
    corpus = Corpus()
    corpus.releases["S1C1T03-SUP-02"].pop("correction_resolution")
    with pytest.raises(ValueError):
        corpus.learner_prompt("S1C1T03-SUP-02")


def test_official_articles_are_shared_without_losing_explicit_release_evidence():
    corpus = Corpus()
    # An explicit review can cite evidence from a different topic.
    corpus.claims["L140"]["topic_ids"] = []
    context = corpus.context("S1C2T21-CORE", "solve")
    assert "verified:L140" in context["references"]
    assert "official:capital:제189조" in context["references"]
    cited = json.loads(context["references"]["verified:L140"])
    assert all("text" not in row and row["reference_id"] in context["references"] for row in cited["evidence"])
    context = corpus.context("S3C2T16-CORE", "solve")
    assert "verified:L162" in context["references"]
    assert "verified:L163" in context["references"]
    assert list(context["references"]).count("official:capital:제81조") == 1


def test_conflicting_official_versions_fail_before_judging():
    corpus = Corpus()
    corpus.claims["L163"]["evidence"][0]["text"] += " contradictory revision"
    with pytest.raises(ValueError, match="Conflicting official"):
        corpus.context("S3C2T16-CORE", "solve")


def test_theory_only_correction_reaches_related_items_without_approving_them():
    corpus = Corpus()
    correction = next(row for row in corpus.corrections if row["id"] == "C023")
    assert correction["item_ids"] == []
    related_claims = [corpus.claims[key] for key in correction["claim_ids"]]
    topic_ids = {topic for row in related_claims for topic in row["topic_ids"]}
    packet = next(row for row in corpus.packets.values()
                  if topic_ids & set(row["topic_ids"]) and row["id"] not in corpus.releases)
    context = corpus.context(packet["id"], "explain")
    candidate = json.loads(context["references"]["correction_candidate:C023"])
    assert candidate["whole_item_fault_confirmed"] is False
    assert candidate["status"] == "applicability_review_required"
    assert "C023" not in {row["id"] for row in context["source_corrections"]}
    assert context["reviewed_prompt_released"] is False


def test_direct_correction_is_not_duplicated_as_topic_candidate():
    context = Corpus().context("S1C2T08-CORE", "explain")
    assert "correction:C042" in context["references"]
    assert "correction_candidate:C042" not in context["references"]


def test_recomputed_math_proof_supersedes_bad_original_explanation():
    corpus = Corpus()
    context = corpus.context("CALC-18-2", "solve")
    proof = json.loads(context["references"]["math:CALC-18-2"])
    assert proof["result"] == 500
    assert proof["unit"] == "원/주"
    assert proof["current_law_claim"] is False
    assert context["reviewed_prompt_released"] is True
    assert context["prompt_variant"] == "corrected_reviewed_prompt"
    assert "math:CALC-18-2" in context["release"]["evidence"]


def test_math_review_detects_changed_source_before_model_call():
    corpus = Corpus()
    corpus.pages["CALC"][28] += " changed assumptions"
    with pytest.raises(ValueError, match="source page changed"):
        corpus.context("CALC-18-2", "solve")


def test_individual_tax_review_detects_changed_source_packet():
    corpus = Corpus()
    corpus.packets["NOTE-S1C1-Q001"]["question_text"] += " altered tax category"
    with pytest.raises(ValueError, match="packet changed after individual review"):
        corpus.context("NOTE-S1C1-Q001", "recall")


@pytest.mark.parametrize("alteration", ["changed", "missing"])
def test_individual_tax_review_detects_changed_official_claim(alteration):
    corpus = Corpus()
    if alteration == "changed":
        corpus.claims["L231"]["verified_statement"] += " unreviewed exception"
    else:
        del corpus.claims["L231"]
    with pytest.raises(ValueError, match="Official claim changed after individual review"):
        corpus.context("NOTE-S1C1-Q001", "recall")


def test_second_judge_disagreement_holds_feedback_and_exam(rubric, assessment):
    second = copy.deepcopy(assessment)
    second["judgments"][0]["status"] = "partial"
    reviewer = FixtureProvider([second])
    result = run_grade(rubric, assessment, reviewer=reviewer)
    assert result["semantic_status"] == "held_reviewer_disagreement"
    assert result["exam_status"] == "held"
    assert result["feedback"] is None
    assert "assessment" not in reviewer.payloads[0]


def test_no_response_means_no_provider_call(rubric, assessment):
    provider = FixtureProvider([])
    result = grade(SmallCorpus(), provider, item_id="test-item", response=" ")
    assert result["exam_status"] == "unanswered"
    assert provider.payloads == []


@pytest.mark.parametrize("alteration", [
    "fake_quote", "fake_reference", "missing_criterion", "duplicate_criterion",
    "wrong_item", "wrong_type", "new_field", "wrong_option_quote", "missing_feedback",
])
def test_malformed_or_untraceable_judgments_are_held(rubric, assessment, alteration):
    if alteration == "fake_quote":
        assessment["judgments"][0]["response_quote"] = "존재하지 않는 응답"
    elif alteration == "fake_reference":
        assessment["judgments"][0]["reference_ids"] = ["made-up"]
    elif alteration == "missing_criterion":
        assessment["judgments"] = []
    elif alteration == "duplicate_criterion":
        assessment["judgments"] *= 2
    elif alteration == "wrong_item":
        assessment["item_id"] = "another-item"
    elif alteration == "wrong_type":
        assessment["judgments"][0]["status"] = ["supported"]
    elif alteration == "new_field":
        assessment["confidence_is_truth"] = True
    elif alteration == "wrong_option_quote":
        assessment["selected_option"] = "3"
    elif alteration == "missing_feedback":
        assessment["explanation"] = ""
    result = run_grade(rubric, assessment)
    assert result["exam_status"] == "held"
    assert result["audit"]["protocol_valid"] is False


def test_not_observed_is_not_implicitly_wrong(rubric, assessment):
    assessment["judgments"][0].update(status="not_observed", response_quote="", reason="이유를 말하지 않았다.")
    result = run_grade(rubric, assessment, response="④")
    assert result["exam_status"] == "correct"
    assert result["semantic_status"] == "not_established"


def test_timed_mock_forbids_mid_attempt_explanation(rubric, assessment):
    result = run_grade(rubric, assessment, mode="timed_mock")
    assert result["exam_status"] == "held"
    for key in ("diagnosis", "explanation", "worked_example", "next_probe"):
        assessment[key] = ""
    result = run_grade(rubric, assessment, mode="timed_mock")
    assert result["exam_status"] == "correct"
    assert result["feedback"] is None


def test_invented_rubric_quote_prevents_judge_call(rubric):
    rubric["criteria"][0]["evidence"][0]["quote"] = "31일"
    provider = FixtureProvider([rubric])
    result = grade(SmallCorpus(), provider, item_id="test-item", response="④")
    assert result["exam_status"] == "held"
    assert len(provider.payloads) == 1


def test_transport_failure_is_held_without_fake_judgment():
    result = grade(SmallCorpus(), FixtureProvider([ProviderUnavailable("timeout")]),
                   item_id="test-item", response="④")
    assert result["exam_status"] == "held"
    assert result["feedback"] is None


def test_provider_key_is_not_in_repr():
    provider = ResponsesProvider(api_key="secret-fixture", model="configured-model")
    assert "secret-fixture" not in repr(provider)


def test_conditional_reasoning_is_available_without_claiming_current_law():
    corpus = Corpus()
    context = corpus.context("S1C2T08-SUP-07", "explain")
    reasoning = json.loads(context["references"]["concept:S1C2T08-SUP-07"])
    assert reasoning["current_law_claim"] is False
    assert "15%" in reasoning["derivation"]
    assert corpus.learner_prompt("S1C2T08-SUP-07")


def test_changed_reasoning_cannot_reuse_an_individual_review():
    corpus = Corpus()
    corpus.releases["S1C2T08-SUP-07"]["concept_review"]["derivation"] = "130%×50%=65%"
    with pytest.raises(ValueError, match="Conceptual reasoning changed"):
        corpus.context("S1C2T08-SUP-07", "explain")


def test_changed_assumptions_or_prompt_are_not_served_as_reviewed():
    corpus = Corpus()
    corpus.releases["S1C2T08-SUP-07"]["clean_prompt"] = "배리어를 이미 넘었다."
    with pytest.raises(ValueError):
        corpus.learner_prompt("S1C2T08-SUP-07")


@pytest.mark.parametrize("url", ["http://example.com/v1", "https://key@example.com/v1", "https://example.com/v1?key=x"])
def test_provider_rejects_unsafe_credential_transport(url):
    with pytest.raises(ValueError):
        ResponsesProvider(api_key="fixture", model="configured-model", base_url=url)


class HttpFixture:
    def __init__(self, envelope):
        self.raw = json.dumps(envelope).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit):
        return self.raw[:limit]


@pytest.mark.parametrize("envelope", [
    {"status": "incomplete", "output": []},
    {"status": "completed", "output": [{"type": "message", "content": [{"type": "refusal", "refusal": "no"}]}]},
    {"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": "not json"}]}]},
])
def test_incomplete_refusal_and_bad_json_never_become_grades(monkeypatch, envelope):
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: HttpFixture(envelope))
    provider = ResponsesProvider(api_key="fixture", model="configured-model")
    with pytest.raises(ProviderUnavailable):
        provider.complete(instructions="fixture", payload={}, schema={}, name="fixture")


def test_live_request_uses_strict_schema_and_disables_storage(monkeypatch):
    observed = {}

    def open_fixture(request, **kwargs):
        observed.update(json.loads(request.data))
        return HttpFixture({"status": "completed", "model": "configured-model", "id": "fixture",
                            "output": [{"type": "message", "content": [{"type": "output_text", "text": '{"ok":true}'}]}]})

    monkeypatch.setattr("urllib.request.urlopen", open_fixture)
    provider = ResponsesProvider(api_key="fixture", model="configured-model")
    result = provider.complete(instructions="fixture", payload={"answer": "응답"}, schema={}, name="fixture")
    assert result["data"] == {"ok": True}
    assert observed["store"] is False
    assert observed["text"]["format"]["strict"] is True
