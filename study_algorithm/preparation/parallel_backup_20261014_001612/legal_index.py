"""Index current article bodies separately from historical supplementary provisions."""

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARTICLE = re.compile(r"(?m)^(제\s*\d+(?:-\d+)?조(?:의\d+)?)\s*\(")
SUPPLEMENT = re.compile(r"(?m)^부\s*칙(?:\s|[<(（])")


def parse_articles(source_id, text):
    """Retain positions in the exact cached text; do not conflate old addenda."""
    boundary = SUPPLEMENT.search(text)
    current_end = boundary.start() if boundary else len(text)
    body = text[:current_end]
    matches = list(ARTICLE.finditer(body))
    articles = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else current_end
        value = text[match.start():end].strip()
        label = re.sub(r"\s", "", match.group(1))
        articles.append({
            "id": f"{source_id}:{label}", "source_id": source_id, "article": label,
            "heading": value.splitlines()[0].split(")")[0] + ")",
            "text": value, "start": match.start(), "end": end,
            "sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(),
        })
    return {
        "source_id": source_id, "header": text[:matches[0].start()] if matches else "",
        "current_body_end": current_end,
        "supplementary_provisions": text[current_end:],
        "count": len(articles), "items": articles,
        "warning": "별표·별지는 별도 파일일 수 있다. 본문 인덱스 존재는 검증 완료를 뜻하지 않는다.",
    }


def build():
    """Index complete statutory/rule sources, retaining version metadata."""
    output = ROOT / "articles"
    output.mkdir(exist_ok=True)
    rows = []
    for name in ("source_registry.json", "kofia_registry.json"):
        registry = json.loads((ROOT / name).read_text(encoding="utf-8"))
        for metadata in registry["items"]:
            if not metadata["http_complete"]:
                continue
            source_id = metadata["id"]
            text = (ROOT / "sources" / f"{source_id}.txt").read_text(encoding="utf-8")
            parsed = parse_articles(source_id, text)
            parsed["source_metadata"] = metadata
            (output / f"{source_id}.json").write_text(
                json.dumps(parsed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
            )
            rows.append({"id": source_id, "articles": parsed["count"], "header": parsed["header"]})
    (ROOT / "article_index.json").write_text(
        json.dumps({"count": len(rows), "items": rows}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return rows


def read_article(source_id, article):
    """Load one uniquely identified current article; fail on ambiguous IDs."""
    article_path = ROOT / "articles" / f"{source_id}.json"
    if not article_path.exists():
        metadata = json.loads((ROOT / "sources" / f"{source_id}.json").read_text(encoding="utf-8"))
        if metadata.get("evidence_unit") != article or not metadata.get("http_complete"):
            raise ValueError("Unregistered or incomplete non-article evidence")
        text = (ROOT / "sources" / f"{source_id}.txt").read_text(encoding="utf-8")
        return {"id": f"{source_id}:{article}", "text": text,
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
    data = json.loads(article_path.read_text(encoding="utf-8"))
    matches = [row for row in data["items"] if row["article"] == article]
    if len(matches) != 1:
        raise ValueError(f"Expected one current article: {source_id}:{article}, got {len(matches)}")
    return matches[0]


def main():
    """Show exact articles or concise search matches for human adjudication."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--source")
    parser.add_argument("--article")
    parser.add_argument("--search")
    args = parser.parse_args()
    if args.build:
        rows = build()
        print(f"Indexed {len(rows)} complete sources, {sum(x['articles'] for x in rows)} articles.")
    elif args.article:
        print(read_article(args.source, args.article)["text"])
    else:
        data = json.loads((ROOT / "articles" / f"{args.source}.json").read_text(encoding="utf-8"))
        for row in data["items"]:
            if args.search in row["text"]:
                print(row["id"], row["heading"])


if __name__ == "__main__":
    main()
