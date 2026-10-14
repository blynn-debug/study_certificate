"""Store explicitly labelled review notes for the visually read BNK RP PDF."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_ID = "s1_bnk_rp2025"
metadata_path = ROOT / "sources" / f"{SOURCE_ID}.json"
metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
metadata.update(
    title="BNK투자증권 RP 핵심·상품설명서 검토필2026-193호",
    document_date="2026-05-26",
    image_read_pages=[1, 2, 3, 4],
    note="검색결과는2025판이었으나 실제 PDF는2026-05-26 심의판. 스캔이미지를 직접 읽었으며 아래본문은 추출문이나 직접인용이 아닌 검토자 요약이다.",
)
summary = (
    "[검토자 이미지 독해 요약, 원문 직접인용 아님] BNK투자증권2026-05-26심의 RP설명서1·3·4쪽은"
    "회사가 미래에 원금과 약정이자를 지급하여 다시 사는 조건으로 채권을 고객에게 매도하는 구조와 예금비보호를 설명한다."
    "3쪽은 중도환매시 약정이율의 절반, 약정기간초과시 약정기간에는 약정이율, 초과기간에는 약정이율의 절반을 적용한다고 설명한다."
    "3쪽은 거래내용을 통장·매도확인서 등으로 통지하고 조건부매도 거래시 고객에게 통장을 교부한다고 설명한다."
    "1·4쪽은 회사 및 담보채권의 신용위험과 담보처분시 가격변동에 따른 원금손실 가능성을 명시한다."
)
unit = {
    "id": f"{SOURCE_ID}:RP구조와이율", "source_id": SOURCE_ID,
    "article": "RP구조와이율", "heading": "RP구조와이율(이미지 직접 독해 요약)",
    "text": summary, "sha256": hashlib.sha256(summary.encode()).hexdigest(),
    "start": 0, "end": len(summary), "pages": [1, 3, 4],
    "evidence_kind": "reviewer_paraphrase_of_visually_read_pdf",
    "exact_span_verified": False, "reviewer": "codex_assistant_visual_read",
    "pdf_sha256": metadata["pdf_sha256"],
    "image_paths": [f"preparation/verification_20261013/sources/{SOURCE_ID}_page{i}.png" for i in [1, 3, 4]],
}
metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(ROOT / "articles" / f"{SOURCE_ID}.json").write_text(
    json.dumps({"source_id": SOURCE_ID, "source_metadata": metadata, "items": [unit]}, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
