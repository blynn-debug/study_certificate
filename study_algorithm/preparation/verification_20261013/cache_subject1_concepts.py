"""Index the reviewed SEC text and archived IVSC concepts without altering shared caches."""

import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent


def index(source_id: str, article: str, begin: str, finish: str, *, append: bool = False) -> None:
    """Save one exact text span from the preserved source text."""
    text = (BASE / "sources" / f"{source_id}.txt").read_text(encoding="utf-8")
    start = text.index(begin)
    end = text.index(finish, start)
    span = text[start:end].strip()
    end = start + len(span)
    metadata = json.loads((BASE / "sources" / f"{source_id}.json").read_text(encoding="utf-8"))
    result = {
        "source_id": source_id,
        "source_metadata": metadata,
        "items": [{"id": f"{source_id}:{article}", "source_id": source_id,
                   "article": article, "heading": article, "text": span,
                   "start": start, "end": end,
                   "sha256": hashlib.sha256(span.encode()).hexdigest()}],
    }
    output = BASE / "articles" / f"{source_id}.json"
    if append and output.exists():
        previous = json.loads(output.read_text(encoding="utf-8"))
        result["items"] = [item for item in previous["items"] if item["article"] != article] + result["items"]
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    source = BASE / "sources" / "s1_ivsc_concepts6"
    url = "https://www.icjce.es/images/pdfs/TECNICA/C02%20-%20IASB/C210%20-%20IVSC%20-%20Normas/03-valuation_concepts.pdf"
    metadata = {
        "id": source.name, "requested_url": url, "retrieved_url": url,
        "as_of": "2026-10-13", "title": "International Valuation Standards, Sixth Edition: General Valuation Concepts and Principles",
        "scope": "Archived conceptual definition only; not a claim about the currently effective standard or Korean law",
        "content_sha256": hashlib.sha256(source.with_suffix('.txt').read_bytes()).hexdigest(),
        "pdf_sha256": hashlib.sha256(source.with_suffix('.pdf').read_bytes()).hexdigest(),
        "text_extraction": "PyMuPDF digital PDF text, not a reviewer paraphrase",
    }
    if source.with_suffix('.json').exists():
        previous_metadata = json.loads(source.with_suffix('.json').read_text(encoding="utf-8"))
        for key in ("http_complete", "http_status", "http_content_length", "downloaded_bytes", "download_verification", "retrieved_at"):
            if key in previous_metadata:
                metadata[key] = previous_metadata[key]
    source.with_suffix('.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    index("s1_ivsc_concepts6", "최유효이용", "6.3\nHighest and best use is defined as:", "7.0 Utility")
    index("s1_sec_mbs", "MBS구조와위험", "Mortgage-backed securities (MBS)", "Featured Content")
    index("s1_appraisal_practice", "최유효이용", '8. "최유효이용"', '9. "일시적인 이용"')
    index("s1_appraisal_practice", "감가수정", "3.2.1.3 감가수정", "3.2.2 적산법", append=True)
    index("s1_kofia_fund_manual", "일부환매분리", "❏ 일부환매 (", "❏ 환매청구에 응하지 않을 수 있는 경우")
    index("s1_court_title2022", "등기공신력", "담보권의 실체적 하자는", "(2) 종래 대법원은")
    index("s1_worldbank_green_pf", "PF위험구조", "5.3.3. PROJECT FINANCE", "Cast Study Summary:")
    index("s1_ifrs10_overview", "연결원칙", "IFRS 10 establishes", "Standard history")
    index("s1_fed_riskretention", "외부지원", "Securitizers of ABCP conduits generally", "ABCP can be classified", append=True)
    index("s1_money_stats2022", "입출금분류", "□항목별 정의(통화 및 유동성)", "○광의통화(M2)")
    index("s1_money_stats2022", "CMA구조", "8) CMA :", "9) 2년미만 금융채", append=True)
    index("s1_kb_subscription", "적립방법", "적립 방법 및 금액", "일부해지")
