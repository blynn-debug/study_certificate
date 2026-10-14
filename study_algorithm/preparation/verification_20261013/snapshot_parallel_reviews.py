"""Freeze independently reviewed batches before updating shared derived artifacts."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from claim_reviews import CLAIMS
from product_followup_reviews import REVIEWS as PRODUCT_REVIEWS
from tax_followup_reviews import REVIEWS as TAX_REVIEWS

ROOT = Path(__file__).resolve().parent
BATCHES = (
    ("fund_remaining_reviews", "REVIEWS"),
    ("fund_remaining_claims", "CLAIMS"),
    ("subject2_reviews", "REVIEWS"),
    ("subject2_claims", "CLAIMS"),
    ("subject3_reviews", "REVIEWS"),
    ("subject3_claims", "CLAIMS"),
    ("final_bond_reviews", "REVIEWS"),
    ("final_bond_claims", "CLAIMS"),
    ("final_derivative_reviews", "REVIEWS"),
    ("final_derivative_claims", "CLAIMS"),
    ("root_final_law_reviews", "REVIEWS"),
    ("root_final_law_claims", "CLAIMS"),
)


def main() -> None:
    """Validate complete records and atomically publish one immutable input snapshot."""
    reviews, claims, files = [], [], []
    for name, field in BATCHES:
        path = ROOT / f"{name}.py"
        if not path.exists():
            continue
        raw = path.read_bytes()
        namespace = {"__file__": str(path), "__name__": name}
        exec(compile(raw, str(path), "exec"), namespace)
        rows = namespace[field]
        if not isinstance(rows, list):
            raise ValueError(f"Expected a list: {name}.{field}")
        (reviews if field == "REVIEWS" else claims).extend(rows)
        files.append({"file": path.name, "sha256": hashlib.sha256(raw).hexdigest(), "records": len(rows)})

    all_reviews = [*TAX_REVIEWS, *PRODUCT_REVIEWS, *reviews]
    all_claims = [*CLAIMS, *claims]
    for filename in (
        "claim_reviews.py", "tax_followup_reviews.py", "product_followup_reviews.py",
        "root_diversification_reviews.py", "root_performance_reviews.py", "root_macro_reviews.py",
        "subject3_restorations.py",
    ):
        path = ROOT / filename
        if path.exists():
            files.append({
                "file": filename, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "role": "review_dependency",
            })
    if len(all_reviews) != len({row["id"] for row in all_reviews}):
        raise ValueError("Duplicate item across review batches")
    if len(all_claims) != len({row["id"] for row in all_claims}):
        raise ValueError("Duplicate claim across review batches")
    packets = json.loads((ROOT.parent / "eval/answer_packets.json").read_text(encoding="utf-8"))
    packet_ids = {row["id"] for row in packets["items"]}
    claim_ids = {row["id"] for row in all_claims}
    for row in reviews:
        for field in ("id", "answer", "clean_prompt", "answer_kind", "review_note", "claim_ids", "source_finding"):
            if field not in row:
                raise ValueError(f"Missing {field} in {row.get('id')}")
        if row["id"] not in packet_ids or not set(row["claim_ids"]) <= claim_ids:
            raise ValueError(f"Unresolved item/claim reference: {row['id']}")
        if not row["clean_prompt"].strip() or not row["answer"] or not row["review_note"].strip():
            raise ValueError(f"Incomplete review: {row['id']}")
        concept = row.get("concept_review")
        if not row["claim_ids"] and not concept:
            raise ValueError(f"No evidence or independent reasoning: {row['id']}")
        if concept and not (
            concept.get("derivation")
            and concept.get("assumptions")
            and concept.get("basis") == "explicit_conditions_and_independent_reasoning"
            and concept.get("current_law_claim") is False
        ):
            raise ValueError(f"Incomplete conceptual evidence: {row['id']}")
    snapshot = {
        "as_of": "2026-10-13",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "files": files,
        "reviews": reviews,
        "claims": claims,
        "scope": "Individual reviewed prompts; snapshot validation is not semantic approval.",
    }
    path = ROOT / "parallel_review_snapshot.json"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    print(json.dumps({"files": files, "reviews": len(reviews), "claims": len(claims)}))


if __name__ == "__main__":
    main()
