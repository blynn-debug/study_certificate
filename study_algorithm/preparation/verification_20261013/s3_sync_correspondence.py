"""Update owned audit metadata after explicit item-level restorations."""

import json
from pathlib import Path

from subject3_restorations import RESTORATIONS, WITHDRAWALS

BASE = Path(__file__).parent
audit_path = BASE / "subject3_correspondence_audit.json"
audit = json.loads(audit_path.read_text(encoding="utf-8"))
for item in audit["items"]:
    item_id = item["id"]
    if item_id in RESTORATIONS:
        item["status"] = "resolved"
        item["audit_status"] = "resolved"
        item["resolution"] = RESTORATIONS[item_id]["review_note"]
        item["correction_details"] = RESTORATIONS[item_id]["source_finding"]
        item["previous_review_history"] = "s3_correspondence_previous_reviews.json"
    elif item_id in WITHDRAWALS:
        item["status"] = "held"
        item["audit_status"] = "held_original_scope"
        item["resolution"] = WITHDRAWALS[item_id]
        item["previous_review_history"] = "s3_correspondence_previous_reviews.json"
audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
holds_path = BASE / "subject3_holds.json"
holds = json.loads(holds_path.read_text(encoding="utf-8"))
held_ids = {item["id"] for item in holds["items"]}
for item in audit["items"]:
    if item["id"] in WITHDRAWALS and item["id"] not in held_ids:
        holds["items"].append({
            "id": item["id"],
            "reason": WITHDRAWALS[item["id"]],
            "evidence_checked": [
                f"TARGET {item['document']}:{item['question_page']} 전체보기·출판정답·해설",
                "s3_correspondence_previous_reviews.json 이전교정판 및 원문대응 재검토",
            ],
        })
holds_path.write_text(json.dumps(holds, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(BASE / "s3_correspondence_withdrawals.json").write_text(
    json.dumps({"items": [{"id": key, "reason": reason} for key, reason in WITHDRAWALS.items()]}, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print({"restored": len(RESTORATIONS), "withdrawn": len(WITHDRAWALS)})
