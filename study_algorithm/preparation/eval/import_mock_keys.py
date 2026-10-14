"""Import publisher tables visually checked on MOCK PDF pages 55 and 67."""

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
ROWS = {
    1: [
        "③②③②④①③②①②③②②①③②②④④②",
        "③①②②②④①④②②③④③③③④②③③②",
        "①①③③①③①④④③①③②①②④④①③④",
        "③③①①③①②③②②③②③④④③④②④①",
        "②④④④④③④④③②④④②④③②②①③③",
    ],
    2: [
        "②①③②①②③①④④①②②③④③②①②②",
        "④①④②④①②③④③②③①③②②②④②④",
        "①①②④①④④②③④③②④②②②①④③④",
        "②②④④②③④②③③④①①④③④②③②③",
        "④①②①②④③④④③④①④①②②③②①①",
    ],
}


def main() -> None:
    """Retain other manual corrections while installing these 200 keys."""
    path = ROOT / "answer_overrides.json"
    changes = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    for exam_set, rows in ROWS.items():
        assert all(len(row) == 20 for row in rows)
        for number, answer in enumerate("".join(rows), 1):
            record = changes.setdefault(f"MOCK-{exam_set}-Q{number:03d}", {})
            record.update({
                "publisher_answer": answer,
                "key_source": {"document": "MOCK", "page": 55 if exam_set == 1 else 67},
                "key_review": "visual_table_checked_2026-10-13",
            })
    path.write_text(json.dumps(changes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("200 publisher keys saved. This does not adjudicate disputed answers.")


if __name__ == "__main__":
    main()
