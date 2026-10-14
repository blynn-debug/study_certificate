"""Audit integrated files and actual EVAL inputs without claiming model accuracy."""

import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
EVAL = ROOT.parent / "eval"
sys.path.insert(0, str(EVAL))

from semantic_grader import Corpus


def read(path: Path) -> Any:
    """Read one persisted artifact using the project's UTF-8 convention."""
    return json.loads(path.read_text(encoding="utf-8-sig"))


def source_body_matches(source_id: str, expected: str) -> bool:
    """Check retained bytes, allowing Windows text newline serialization only."""
    for extension in (".pdf", ".html", ".txt", ".hwp", ".json.raw"):
        path = ROOT / "sources" / f"{source_id}{extension}"
        if not path.exists():
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() == expected:
            return True
        if extension in (".html", ".txt"):
            content = path.read_text(encoding="utf-8")
            for serialized in (content, content.replace("\n", "\r\n")):
                if hashlib.sha256(serialized.encode("utf-8")).hexdigest() == expected:
                    return True
    return False


def main() -> None:
    """Check every private evidence context, preserved release, and frozen batch."""
    corpus = Corpus()
    errors = []
    context_sizes = []
    for key, packet in corpus.packets.items():
        try:
            references = corpus.context(key, "explain")["references"]
            expected = {
                "publisher:answer": str(packet["publisher_answer"]),
                "publisher:rationale": packet["explanation_text"],
            }
            if packet["question_text"]:
                expected["publisher:question_fragment"] = packet["question_text"]
            for page in {packet["question_page"], *packet.get("source_pages", [])}:
                expected[f"page:{packet['document']}:{page}"] = corpus.pages[packet["document"]][page]
            for ref, value in expected.items():
                if not value or references.get(ref) != value:
                    errors.append({"id": key, "check": "target_evidence", "reference": ref})
            for claim_id in corpus.releases.get(key, {}).get("evidence", []):
                if claim_id in corpus.claims and f"verified:{claim_id}" not in references:
                    errors.append({"id": key, "check": "explicit_claim_missing", "claim": claim_id})
            context_sizes.append(sum(map(len, references.values())))
        except (KeyError, ValueError) as exc:
            errors.append({"id": key, "check": "eval_context", "error": str(exc)})

    baseline = read(ROOT.parent / "parallel_backup_20261014_001612/item_releases.json")["items"]
    changed = [key for key, value in baseline.items() if corpus.releases.get(key) != value]
    if changed:
        errors.append({"check": "baseline_releases_changed", "ids": changed})

    snapshot = read(ROOT / "parallel_review_snapshot.json")
    stale = []
    for row in snapshot["files"]:
        if hashlib.sha256((ROOT / row["file"]).read_bytes()).hexdigest() != row["sha256"]:
            stale.append(row["file"])
    if stale:
        errors.append({"check": "snapshot_outdated", "files": stale})

    registry = read(ROOT / "item_verification_registry.json")["items"]
    progress = read(ROOT / "parallel_progress.json")
    registry_ids = [row["id"] for row in registry]
    if len(registry_ids) != len(set(registry_ids)) or set(registry_ids) != set(corpus.packets):
        errors.append({"check": "registry_coverage"})
    if sum(progress["counts"].values()) != len(corpus.packets):
        errors.append({"check": "progress_total"})

    referenced_sources = {}
    for claim in corpus.claims.values():
        for evidence in claim["evidence"]:
            actual = hashlib.sha256(evidence["text"].encode("utf-8")).hexdigest()
            if actual != evidence["article_sha256"]:
                errors.append({"check": "evidence_hash", "claim": claim["id"], "ref": evidence["id"]})
            source = evidence["id"].split(":", 1)[0]
            if source not in referenced_sources:
                metadata = read(ROOT / "sources" / f"{source}.json")
                referenced_sources[source] = metadata
            metadata = referenced_sources[source]
            if not metadata.get("http_complete") or metadata["content_sha256"] != evidence["source_content_sha256"]:
                errors.append({"check": "source_completeness_or_hash", "claim": claim["id"], "source": source})

    for source, metadata in referenced_sources.items():
        if not source_body_matches(source, metadata["content_sha256"]):
            errors.append({"check": "retained_source_body_hash", "source": source})

    provider_configured = bool(os.getenv("OPENAI_API_KEY") and os.getenv("STUDY_EVAL_MODEL"))
    test_path = ROOT / "integration_test_results.xml"
    test_result = {"status": "not_run"}
    if test_path.exists():
        suites = list(ET.parse(test_path).getroot().iter("testsuite"))
        test_result = {
            "tests": sum(int(row.get("tests", "0")) for row in suites),
            "failures": sum(int(row.get("failures", "0")) for row in suites),
            "errors": sum(int(row.get("errors", "0")) for row in suites),
            "skipped": sum(int(row.get("skipped", "0")) for row in suites),
            "timestamps": [row.get("timestamp") for row in suites],
        }
        test_result["status"] = "passed" if not (test_result["failures"] or test_result["errors"]) else "failed"
    if test_result["status"] != "passed":
        errors.append({"check": "local_test_suite", "result": test_result})
    learning_root = ROOT.parent / "learning_integration_20261014"
    learning_status = None
    if (learning_root / "learning_status.json").exists():
        learning_status = read(learning_root / "learning_status.json")
        if not learning_status["structural_checks_passed"]:
            errors.append({"check": "learning_integration_failed"})
        if learning_status["counts"]["items"] != len(corpus.packets):
            errors.append({"check": "learning_item_coverage"})
        if learning_status["counts"]["held_items"] != progress["counts"]["reviewed_held"]:
            errors.append({"check": "learning_hold_coverage"})
        for name, expected in learning_status["input_sha256"].items():
            if hashlib.sha256((ROOT.parent / name).read_bytes()).hexdigest() != expected:
                errors.append({"check": "learning_inputs_changed", "file": name})
        for question in read(learning_root / "learner_questions.json")["items"]:
            if set(question) != {"id", "as_of", "prompt", "prompt_sha256"}:
                errors.append({"check": "learner_question_unexpected_fields", "id": question.get("id")})
            release = corpus.releases.get(question["id"], {})
            if question["prompt"] != release.get("clean_prompt"):
                errors.append({"check": "learning_question_changed", "id": question["id"]})
    manifest_paths = [
        ROOT / "parallel_review_snapshot.json", ROOT / "item_releases.json",
        ROOT / "verified_claims.json", ROOT / "source_corrections.json",
        ROOT / "parallel_progress.json", EVAL / "answer_packets.json",
        EVAL / "item_contracts.json", EVAL / "semantic_grader.py",
        ROOT / "item_verification_registry.json", ROOT / "verification_summary.json",
        ROOT / "verification_report.html", ROOT / "progress_tree.txt", test_path,
    ]
    manifest_paths.extend(
        ROOT.parent / "target_analysis" / "extracted" / f"{document}.json"
        for document in sorted(corpus.pages)
    )
    if learning_status:
        manifest_paths.extend(learning_root / name for name in (
            "learning_status.json", "learner_questions.json", "topic_teaching_guide.json",
            "question_learning_routes.json", "pattern_lessons.json", "study_method_crosswalk.json",
            "pattern_validation.json", "learning_report.html",
        ))
    target_files = sorted((ROOT.parents[1] / "src/target").glob("*.pdf"))
    if len(target_files) != 5:
        errors.append({"check": "target_pdf_coverage", "files_found": len(target_files)})
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "as_of": "2026-10-13",
        "integration_checks_passed": not errors,
        "full_task_complete": False,
        "items_checked": len(corpus.packets),
        "preserved_baseline_releases": len(baseline) - len(changed),
        "target_answer_rationale_and_source_page_checked": len(corpus.packets),
        "all_linked_target_pages_checked": True,
        "largest_private_context_characters": max(context_sizes, default=0),
        "claims_checked": len(corpus.claims),
        "local_test_suite": test_result,
        "sources_checked": len(referenced_sources),
        "retained_source_bodies_checked": len(referenced_sources),
        "progress": progress["counts"],
        "target_correspondence_recheck_count": progress["target_correspondence_recheck_count"],
        "provider_configured": provider_configured,
        "live_model_validation": read(ROOT / "verification_summary.json")["live_natural_language_model_validation"],
        "offline_learning": learning_status["counts"] if learning_status else None,
        "limitations": [
            "Successful file and context checks do not establish correctness of every answer.",
            "Held items and unresolved original-question correspondence are not completed validation.",
            "A live semantic grading run is separate from local protocol tests.",
        ],
        "errors": errors,
        "artifact_sha256": {
            str(path.relative_to(ROOT.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in manifest_paths
        },
        "target_pdf_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in target_files
        },
    }
    path = ROOT / "integration_audit.json"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    print(json.dumps({key: value for key, value in report.items() if key != "artifact_sha256"}, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
