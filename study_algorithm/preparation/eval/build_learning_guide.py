"""Join retained TARGET evidence to concrete offline study routes, without API calls."""

import html
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from learning_patterns import PATTERNS
from release_policy import is_current_release
from semantic_grader import Corpus, digest

ROOT = Path(__file__).resolve().parent
VERIFICATION = ROOT.parent / "verification_20261013"
OUTPUT = ROOT.parent / "learning_integration_20261014"


def read(path: Path) -> Any:
    """Read a local artifact without modifying its source."""
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(name: str, content: Any) -> None:
    """Publish one complete artifact by atomic replacement."""
    path = OUTPUT / name
    temporary = path.with_suffix(path.suffix + ".tmp")
    text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False, indent=2) + "\n"
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def pattern_ids(packet: dict[str, Any], release: dict[str, Any]) -> list[str]:
    """Suggest study routes from structural metadata, not a validated semantic classifier."""
    chapter = packet["chapter_id"]
    result = ["LP10"]
    if release.get("answer_kind") == "multiple_choice":
        result.append("LP03")
    if chapter in {"S1C1", "S1C2", "S3C1", "S3C2", "S3C3"}:
        result += ["LP01", "LP02"]
    if chapter in {"S2C1", "S2C3", "S3C5"}:
        result += ["LP04", "LP06"]
    if chapter in {"S2C4", "S3C9"}:
        result += ["LP06", "LP07"]
    if chapter == "S3C6":
        result += ["LP05", "LP06"]
    if chapter == "S3C7":
        result += ["LP06", "LP08"]
    if chapter == "S3C8":
        result.append("LP09")
    return list(dict.fromkeys(result))


def example(corpus: Corpus, item_id: str) -> dict[str, Any]:
    """Preserve a reviewed example and its exact scope; never synthesize an answer key."""
    packet, release = corpus.packets[item_id], corpus.releases[item_id]
    return {
        "item_id": item_id, "prompt": release["clean_prompt"], "answer": release["answer"],
        "explanation": release["review_note"], "evidence": release["evidence"],
        "scope": release.get("scope", "Only the explicitly reviewed prompt and conditions."),
        "concept_assumptions": (release.get("concept_review") or {}).get("assumptions"),
        "as_of": release["as_of"], "release_sha256": digest(release),
        "original_target": {key: packet[key] for key in (
            "document", "question_page", "source_pages", "question_text", "publisher_answer", "explanation_text"
        )},
        "use": "Assistant-private explanation and answer; show the question before revealing this answer.",
    }


def check_embedded_examples(value: Any, corpus: Corpus, usable: set[str], owner: str) -> list[dict[str, Any]]:
    """Reject stale embedded questions and keys, including historical hash conventions."""
    errors = []
    if isinstance(value, dict):
        key = value.get("item_id", value.get("id"))
        if "item_id" in value and key not in usable:
            errors.append({"check": "explicit_check_item_unusable", "owner": owner, "id": key})
        if key in corpus.releases and any(field in value for field in ("prompt", "clean_prompt")):
            release = corpus.releases[key]
            if key not in usable:
                errors.append({"check": "embedded_example_unusable", "owner": owner, "id": key})
            for embedded, current in (("prompt", "clean_prompt"), ("clean_prompt", "clean_prompt"),
                                      ("answer", "answer"), ("reviewed_answer", "answer")):
                if embedded in value and value[embedded] != release[current]:
                    errors.append({"check": "embedded_example_stale", "owner": owner, "id": key, "field": embedded})
            if "release_sha256" in value and value["release_sha256"] != digest(release):
                errors.append({"check": "embedded_release_hash", "owner": owner, "id": key})
            hashes = {digest(release["clean_prompt"]), hashlib.sha256(release["clean_prompt"].encode()).hexdigest()}
            if "prompt_sha256" in value and value["prompt_sha256"] not in hashes:
                errors.append({"check": "embedded_prompt_hash", "owner": owner, "id": key})
        for child in value.values():
            errors.extend(check_embedded_examples(child, corpus, usable, owner))
    elif isinstance(value, list):
        for child in value:
            errors.extend(check_embedded_examples(child, corpus, usable, owner))
    return errors


def main() -> None:
    """Check full item coverage and create reusable teaching material, not a mastery record."""
    OUTPUT.mkdir(parents=True, exist_ok=True)
    corpus = Corpus()
    progress = read(VERIFICATION / "parallel_progress.json")
    queue = {row["id"]: row for row in progress["items"]}
    rules = read(ROOT.parent / "operational_rules.json")["rules"]
    methods = read(ROOT / "study_method_policy.json")
    errors = []
    study_sources = read(ROOT.parent / "source_manifest.json")
    source_lines = {}
    source_records = {row["id"]: row for row in study_sources}
    for source in study_sources:
        path = ROOT.parents[1] / source["path"]
        source_lines[source["id"]] = path.read_text(encoding="utf-8-sig").splitlines()
        if hashlib.sha256(path.read_bytes()).hexdigest().lower() != source["sha256"].lower():
            errors.append({"check": "study_source_changed", "id": source["id"]})
    for rule in rules:
        excerpts = []
        for ref in rule["evidence"]:
            source_id, span = ref.rsplit(":", 1)
            start, end = map(int, span.split("-"))
            lines = source_lines[source_id]
            if not 1 <= start <= end <= len(lines):
                errors.append({"check": "study_rule_source_span", "rule": rule["id"], "ref": ref})
            excerpts.append({"reference": ref, "path": source_records[source_id]["path"],
                             "source_sha256": source_records[source_id]["sha256"],
                             "text": "\n".join(lines[start - 1:end])})
        rule["retained_source_excerpts"] = excerpts
    stale = set()
    claim_hashes = {key: digest(value) for key, value in corpus.claims.items()}
    for key, release in corpus.releases.items():
        packet_hash = release.get("reviewed_packet_sha256")
        if packet_hash and packet_hash != digest(corpus.packets[key]):
            stale.add(key)
        if any(claim_hashes.get(claim) != expected for claim, expected in release.get("reviewed_claim_sha256", {}).items()):
            stale.add(key)
        if release.get("concept_review") is not None and digest(release["concept_review"]) != release.get("reviewed_concept_sha256"):
            stale.add(key)
    if stale:
        errors.append({"check": "reviewed_evidence_changed", "ids": sorted(stale)})
    corrections: dict[str, list[dict[str, Any]]] = {}
    for row in corpus.corrections:
        for item_id in row["item_ids"]:
            corrections.setdefault(item_id, []).append(row)
    usable = {
        item_id for item_id, release in corpus.releases.items()
        if is_current_release(release, corrections.get(item_id, []))
        and not queue[item_id]["target_correspondence_recheck"]
        and item_id not in stale
    }
    # A retained corrected variant with unresolved original correspondence stays
    # preserved in the source store, but is not used as a completed TARGET route.
    remediation = {}
    for subject in ("s1", "s2", "s3"):
        path = VERIFICATION / f"{subject}_learning_remediation.json"
        if path.exists():
            for row in read(path)["items"]:
                if row["id"] in remediation:
                    raise ValueError(f"Duplicate remediation: {row['id']}")
                remediation[row["id"]] = row
    held = {key for key, row in queue.items() if row["state"] == "reviewed_held"}
    if held - remediation.keys():
        errors.append({"check": "missing_held_learning_route", "ids": sorted(held - remediation.keys())})
    required = {"id", "status", "reason", "study_method", "concept_explanation", "condition_contrast",
                "memory_targets", "verified_example_ids", "next_check", "resume_condition"}
    for key, row in remediation.items():
        if required - row.keys():
            errors.append({"check": "incomplete_remediation", "id": key, "fields": sorted(required - row.keys())})
        invalid = set(row.get("verified_example_ids", [])) - usable
        if invalid:
            errors.append({"check": "unusable_remediation_example", "id": key, "ids": sorted(invalid)})
        errors.extend(check_embedded_examples(row, corpus, usable, key))
    for pattern in PATTERNS:
        if not set(pattern["rules"]) <= {row["id"] for row in rules}:
            errors.append({"check": "unknown_study_rule", "pattern": pattern["id"]})
        if not set(pattern.get("anchor_items", [])) <= usable:
            errors.append({"check": "unusable_pattern_anchor", "pattern": pattern["id"]})

    items = []
    public_questions = []
    for key, packet in corpus.packets.items():
        release = corpus.releases.get(key, {})
        row = {
            "id": key, "topic_ids": packet["topic_ids"], "document": packet["document"],
            "source_pages": packet["source_pages"], "demand": corpus.contracts[key]["demand"],
            "source_state": queue[key]["state"], "target_correspondence": queue[key]["target_correspondence_recheck"],
            "usable_for_reviewed_question_practice": key in usable,
            "proposed_learning_patterns": pattern_ids(packet, release),
            "pattern_classification": "structural_route_suggestions; confirm against the actual prompt",
            "learner_state": "unassessed", "delayed_recall": "not_observed", "new_condition_transfer": "not_observed",
            "source_packet_sha256": digest(packet), "release_sha256": digest(release) if release else None,
            "remediation": remediation.get(key),
        }
        if key in usable:
            public_questions.append({
                "id": key, "as_of": release["as_of"], "prompt": release["clean_prompt"],
                "prompt_sha256": digest(release["clean_prompt"]),
            })
        items.append(row)

    topics = []
    for topic_id, topic in corpus.topics.items():
        ids = [row["id"] for row in items if topic_id in row["topic_ids"]]
        approved = [key for key in ids if key in usable]
        selected = sorted(approved, key=lambda key: (not key.endswith("-CORE"), key.startswith("NOTE"), key))[:3]
        worked_ids = selected[:2] if len(selected) > 2 else selected[:1]
        topics.append({
            "id": topic_id, "title": topic["title"], "all_question_ids": ids,
            "reviewed_question_ids": approved, "held_or_correspondence_unresolved_ids": [key for key in ids if key not in usable],
            "draft_design_only": {key: topic[key] for key in (
                "required_action", "recall_targets", "counterexample_focus", "repair_design"
            )},
            "draft_boundary": "Earlier topic design is not current-law evidence. Use the scoped reviewed examples below.",
            "reviewed_item_examples": [example(corpus, key) for key in worked_ids],
            "first_check_item_id": selected[-1] if len(selected) > 1 else None,
            "check_scope": "Different stored item, not proof of unseen transfer. Record prior answer exposure before assessment.",
            "rules": topic["rules"], "learner_state": "unassessed",
        })
    counts = {
        "target_documents": len({row["document"] for row in items}), "topics": len(topics),
        "items": len(items), "reviewed_releases": len(corpus.releases), "usable_practice_items": len(usable),
        "held_items": len(held), "held_with_learning_route": len(held & remediation.keys()),
        "topics_without_reviewed_example": sum(not row["reviewed_item_examples"] for row in topics),
        "topics_without_separate_check": sum(row["first_check_item_id"] is None for row in topics),
        "study_rules_linked": len(rules), "concrete_pattern_lessons": len(PATTERNS),
        "study_transcripts_checked": len(study_sources),
        "study_rule_evidence_spans_checked": sum(len(rule["retained_source_excerpts"]) for rule in rules),
        "learner_responses_observed": 0, "api_calls": 0,
    }
    if set(queue) != set(corpus.packets) or len(items) != 2292 or len(topics) != 285:
        errors.append({"check": "corpus_coverage"})
    metadata = {
        "created_at": datetime.now(timezone.utc).isoformat(), "as_of": "2026-10-13",
        "mode": "offline_assistant_study_preparation", "counts": counts,
        "structural_checks_passed": not errors, "errors": errors,
        "mastery": "not_established; requires actual independent responses, delayed checks and changed-condition checks",
        "model_training_performed": False, "paid_api_calls": 0,
        "remaining_original_validation": progress["target_correspondence_recheck_count"],
        "input_sha256_method": "sha256 of retained file bytes",
        "input_sha256": {
            str(path.relative_to(ROOT.parent)): hashlib.sha256(path.read_bytes()).hexdigest() for path in (
                VERIFICATION / "item_releases.json", VERIFICATION / "parallel_progress.json",
                ROOT / "item_contracts.json", ROOT / "answer_packets.json", ROOT / "study_method_policy.json",
                ROOT / "topic_rubrics.json", ROOT / "learning_patterns.py", Path(__file__),
                ROOT.parent / "operational_rules.json", VERIFICATION / "source_corrections.json",
                ROOT.parent / "source_manifest.json", ROOT.parent / "source_coverage.json",
                VERIFICATION / "verified_claims.json", OUTPUT / "pattern_validation.json",
                *(VERIFICATION / f"s{subject}_learning_remediation.json" for subject in (1, 2, 3)),
            )
            if path.exists()
        },
    }
    if errors:
        write("learning_build_failure.json", metadata)
        print(json.dumps(metadata, ensure_ascii=False))
        sys.exit(1)
    write("learning_status.json", metadata)
    write("question_learning_routes.json", {"scope": "Assistant-private routes; not a record of learning completed.", "items": items})
    write("topic_teaching_guide.json", {"scope": "Assistant-private reviewed examples and answer keys.", "items": topics})
    write("learner_questions.json", {"scope": "Question-only view; no answer or rationale fields.", "items": public_questions})
    write("pattern_lessons.json", {"scope": "Synthetic worked examples, distinct from TARGET originals.", "items": PATTERNS})
    write("study_method_crosswalk.json", {"rules": rules, "response_driven_policy": methods,
          "provenance": "Rule actions are an operational interpretation of the retained SRC excerpts, not literal quotations or measured learning effects.",
          "routing": "Choose a method from actual response evidence. No response means unassessed, not a memory deficit."})
    e = lambda value: html.escape(str(value), quote=True)
    pattern_html = "".join(
        f"<details><summary>{e(row['id'])} {e(row['name'])}</summary>"
        + "".join(f"<p><b>{label}</b> {e(row[key])}</p>" for key, label in (
            ("explanation", "이해"), ("worked_example", "풀이 예제"), ("memory", "기억 핵심"),
            ("check", "확인 질문"), ("repair", "오류 보완"), ("scope", "적용 조건")
        )) + f"<details><summary>응답 후 답 보기</summary><p>{e(row['answer'])}</p></details></details>"
        for row in PATTERNS
    )
    topic_html = "".join(
        f"<tr><td>{e(row['id'])}</td><td>{e(row['title'])}</td><td>{len(row['reviewed_question_ids'])}</td>"
        f"<td>{len(row['held_or_correspondence_unresolved_ids'])}</td></tr>" for row in topics
    )
    write("learning_report.html", "<!doctype html><html lang='ko'><meta charset='utf-8'><title>공부법과 TARGET 연결</title>"
          "<style>body{font-family:system-ui;max-width:1100px;margin:40px auto;padding:16px;line-height:1.7}"
          "td,th{padding:8px;border-bottom:1px solid #ddd;text-align:left}details{margin:15px 0}summary{cursor:pointer;font-weight:700}</style>"
          "<h1>공부법과 TARGET 연결</h1><p>API 호출 없이 준비한 설명·확인·보완 자료입니다. 숙달이나 학습 완료 기록은 아닙니다.</p>"
          f"<p>285주제 · 2,292문항 · 학습용 검토 문항 {len(usable)}개 · 원문 보류 {len(held)}개</p>"
          "<p><a href='learning_status.json'>검사 결과</a> · <a href='topic_teaching_guide.json'>주제별 설명과 근거</a> · "
          "<a href='question_learning_routes.json'>모든 문항과 보류 학습 경로</a> · <a href='learner_questions.json'>답을 가린 문제</a> · "
          "<a href='study_method_crosswalk.json'>공부법 원문 규칙 연결</a></p>"
          "<h2>구체적 이해·확인 예제</h2>" + pattern_html
          + "<h2>전체 주제</h2><table><tr><th>ID</th><th>주제</th><th>사용 가능</th><th>보류·원문 미해결</th></tr>"
          + topic_html + "</table></html>")
    print(json.dumps(metadata, ensure_ascii=False))


if __name__ == "__main__":
    main()
