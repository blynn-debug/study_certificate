"""Guard offline study routes against stale questions and unapproved checks."""

import hashlib
from copy import deepcopy
from types import SimpleNamespace

import pytest

from build_learning_guide import check_embedded_examples
from semantic_grader import digest


@pytest.fixture
def reviewed_example():
    """Use an isolated release store; no corpus files or APIs are required."""
    release = {
        "clean_prompt": "A unit costs 100 and pays 110. What is its return?",
        "answer": "10%",
        "as_of": "2026-10-13",
    }
    corpus = SimpleNamespace(
        releases={"APPROVED": release, "RECHECK_REQUIRED": deepcopy(release)}
    )
    embedded = {
        "item_id": "APPROVED",
        "prompt": release["clean_prompt"],
        "reviewed_answer": release["answer"],
        "prompt_sha256": digest(release["clean_prompt"]),
        "release_sha256": digest(release),
    }
    return corpus, {"APPROVED"}, embedded


@pytest.mark.parametrize("hash_convention", ["json", "raw_utf8"])
def test_matching_reviewed_example_accepts_retained_hash_conventions(
    reviewed_example, hash_convention
):
    corpus, usable, embedded = reviewed_example
    if hash_convention == "raw_utf8":
        embedded["prompt_sha256"] = hashlib.sha256(
            embedded["prompt"].encode("utf-8")
        ).hexdigest()
    route = {"id": "HELD_ORIGINAL", "next_check": embedded}

    assert check_embedded_examples(route, corpus, usable, "HELD_ORIGINAL") == []


@pytest.mark.parametrize(
    ("field", "replacement", "expected_check"),
    [
        ("prompt", "The cost is now 200. What is its return?", "embedded_example_stale"),
        ("clean_prompt", "A different question", "embedded_example_stale"),
        ("answer", "20%", "embedded_example_stale"),
        ("reviewed_answer", "20%", "embedded_example_stale"),
        ("prompt_sha256", "0" * 64, "embedded_prompt_hash"),
        ("release_sha256", "0" * 64, "embedded_release_hash"),
    ],
)
def test_nested_check_rejects_changed_question_answer_or_hash(
    reviewed_example, field, replacement, expected_check
):
    corpus, usable, original = reviewed_example
    changed = deepcopy(original)
    changed[field] = replacement
    route = {"steps": [{"example": original}, {"next_check": changed}]}

    errors = check_embedded_examples(route, corpus, usable, "HELD_ORIGINAL")

    assert any(
        error["check"] == expected_check
        and error["id"] == "APPROVED"
        and error["owner"] == "HELD_ORIGINAL"
        for error in errors
    )


@pytest.mark.parametrize("item_id", ["UNKNOWN", "UNRELEASED", "RECHECK_REQUIRED"])
@pytest.mark.parametrize("include_snapshot", [False, True])
def test_explicit_check_rejects_unusable_id_even_without_question(
    reviewed_example, item_id, include_snapshot
):
    corpus, usable, embedded = reviewed_example
    check = deepcopy(embedded) if include_snapshot else {}
    check["item_id"] = item_id
    route = {"id": "HELD_ORIGINAL", "steps": [{"next_check": check}]}

    errors = check_embedded_examples(route, corpus, usable, "HELD_ORIGINAL")

    assert any(
        error["check"] == "explicit_check_item_unusable"
        and error["id"] == item_id
        for error in errors
    )


def test_updated_release_rejects_previously_valid_stored_check(reviewed_example):
    corpus, usable, embedded = reviewed_example
    corpus.releases["APPROVED"]["clean_prompt"] = "The payment is now 120. Return?"
    corpus.releases["APPROVED"]["answer"] = "20%"

    errors = check_embedded_examples(
        {"next_check": embedded}, corpus, usable, "HELD_ORIGINAL"
    )

    stale_fields = {
        error.get("field")
        for error in errors
        if error["check"] == "embedded_example_stale"
    }
    assert {"prompt", "reviewed_answer"} <= stale_fields
