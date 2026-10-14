"""Shared release gates for original and explicitly repaired question variants."""

import hashlib
import json


def fingerprint(value):
    """Bind decisions to exact Unicode data, rather than an item ID alone."""
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def variant_fingerprint(release):
    """Require renewed review when the corrected prompt, answer, or date changes."""
    return fingerprint({key: release.get(key) for key in ("clean_prompt", "answer", "as_of")})


def is_current_release(release, corrections=(), *, as_of="2026-10-13"):
    """Accept a corrected variant only if every current source defect is explicitly resolved.

    A release is authorization to assess that exact prompt, never a retroactive repair of
    the publisher's original question. The caller must separately bind the delivered prompt.
    """
    if not (
        release.get("state") == "adjudicated_current"
        and release.get("as_of") == as_of
        and isinstance(release.get("clean_prompt"), str)
        and release["clean_prompt"].strip()
        and release.get("evidence")
        and release.get("answer")
        and release.get("prompt_correspondence_reviewed") is True
    ):
        return False
    concept = release.get("concept_review")
    if concept is not None and not (
        isinstance(concept, dict)
        and isinstance(concept.get("derivation"), str)
        and concept["derivation"].strip()
        and isinstance(concept.get("assumptions"), str)
        and concept["assumptions"].strip()
        and concept.get("basis") == "explicit_conditions_and_independent_reasoning"
        and concept.get("current_law_claim") is False
        and release.get("reviewed_concept_sha256") == fingerprint(concept)
        and release.get("reviewed_prompt_sha256") == variant_fingerprint(release)
    ):
        return False
    if not corrections:
        return True
    resolutions = release.get("correction_resolution", {})
    if not (
        release.get("prompt_variant") == "corrected_reviewed_prompt"
        and isinstance(resolutions, dict)
        and set(resolutions) == {row["id"] for row in corrections}
        and release.get("corrected_variant_sha256") == variant_fingerprint(release)
    ):
        return False
    return all(
        isinstance(resolutions[row["id"]], dict)
        and resolutions[row["id"]].get("reviewed_correction_sha256") == fingerprint(row)
        and isinstance(resolutions[row["id"]].get("resolution_note"), str)
        and resolutions[row["id"]]["resolution_note"].strip()
        for row in corrections
    )
