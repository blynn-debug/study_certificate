"""Display complete answer/explanation packets within a bounded character budget."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    """Print a review batch without silently truncating individual explanations."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind")
    parser.add_argument("--chapter")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--max-chars", type=int, default=6500)
    parser.add_argument("--include-question", action="store_true")
    args = parser.parse_args()
    records = json.loads((ROOT / "answer_packets.json").read_text(encoding="utf-8"))["items"]
    records = [row for row in records if (not args.kind or row["kind"] == args.kind)
               and (not args.chapter or row["chapter_id"] == args.chapter)]
    length = 0
    ids = []
    end = args.start
    for index in range(args.start, len(records)):
        row = records[index]
        explanation = re.sub(r"\s+", " ", row["explanation_text"]).strip()
        key_label = f' 답 {row["publisher_answer"]}' if row["kind"] != "warmup" else ""
        body = f'{index} {row["id"]} | {row["document"]}:{row["question_page"]}{key_label}\n'
        body += f'요구: {row["demand"]}\n해설: {explanation or "[미추출 — 원본 확인 필요]"}\n'
        if args.include_question:
            body += "문제: " + re.sub(r"\s+", " ", row["question_text"]).strip() + "\n"
        if length and length + len(body) > args.max_chars:
            break
        print(body)
        length += len(body)
        ids.append(row["id"])
        end = index + 1
    print(json.dumps({"displayed_count": len(ids), "next_start": end, "total_filtered": len(records)}, ensure_ascii=False))
    receipt = {"kind": args.kind, "chapter": args.chapter, "start": args.start, "next_start": end,
               "displayed_ids": ids, "characters": length, "review_status": "displayed_only_not_yet_semantically_reviewed"}
    receipt_name = f"{args.kind or 'all'}_{args.chapter or 'all'}_{args.start:04d}.json"
    (ROOT / "display_receipts").mkdir(exist_ok=True)
    (ROOT / "display_receipts" / receipt_name).write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
