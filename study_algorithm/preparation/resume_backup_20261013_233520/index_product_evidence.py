"""Index only the official product passages actually read for this audit."""

from pathlib import Path

from publication_evidence import register_units

ROOT = Path(__file__).resolve().parent


def text_for(source_id):
    """Read the cached source without refreshing its reviewed version."""
    return (ROOT / "sources" / f"{source_id}.txt").read_text(encoding="utf-8")


def page_span(text, start_page, next_page):
    """Use exact cached PDF page markers, not printed-page guesses."""
    return text.index(f"[PDF page {start_page}]"), text.index(f"[PDF page {next_page}]")


def main():
    """Retain selected units, preserving complete legislation indexes."""
    text = text_for("fsc_financial_map")
    start = text.index("◦ 금융맵은")
    register_units("fsc_financial_map", [("기관분류", start, text.index("◦ 위치", start))])
    text = text_for("kcie_financial_products")
    register_units("kcie_financial_products", [("기관분류표", *page_span(text, 29, 30))])
    text = text_for("krx_elw_overview")
    start = text.index("ELW(Equity")
    register_units("krx_elw_overview", [("상품과상장요건", start, text.index("개인정보처리방침", start))])
    text = text_for("insurance_standard_terms")
    register_units("insurance_standard_terms", [
        ("화재담보범위", *page_span(text, 56, 60)),
        ("화재지급한도", *page_span(text, 60, 62)),
        ("자동차담보분류", *page_span(text, 83, 85)),
    ])
    text = text_for("kofia_isa_managed")
    start = text.index("6. 모델포트폴리오의 구성")
    register_units("kofia_isa_managed", [
        ("모델포트폴리오구성", start, text.index("2)  위험도 분류", start)),
    ])
    text = text_for("kofia_isa_brokerage")
    start = text.index("2. 용어의 정의")
    register_units("kofia_isa_brokerage", [
        ("중개형운용자산", start, text.index("Ⅱ. 가입요건", start)),
    ])
    text = text_for("kofia_isa_trust")
    start = text.index("2. 용어의 정의")
    register_units("kofia_isa_trust", [
        ("신탁형운용자산정의", start, text.index("Ⅱ. 가입요건", start)),
    ])
    text = text_for("klia_life_2026")
    register_units("klia_life_2026", [
        ("보험료산출방식", *page_span(text, 42, 44)),
        ("보험상품분류", *page_span(text, 264, 268)),
        ("종신정기보험", *page_span(text, 270, 271)),
    ])
    text = text_for("kidi_life_insurance")
    start = text.index("생명보험의 보험료 계산")
    register_units("kidi_life_insurance", [
        ("보험료구성", start, text.index("개인정보처리방침", start)),
    ])
    text = text_for("kidi_long_insurance")
    start = text.index("장기손해보험의 개요")
    register_units("kidi_long_insurance", [
        ("장기손해보험구조", start, text.index("31F, Tower", start)),
    ])
    text = text_for("kcie_els_knockin")
    start = text.index("조기상환형 스텝다운")
    end = text.index("그러므로 낙인", start)
    register_units("kcie_els_knockin", [("낙인과상환조건", start, end)])
    text = text_for("kyobo_increasing_benefit")
    start = text.index("‘교보손주사랑포에버종신보험 (무배당)’은")
    register_units("kyobo_increasing_benefit", [
        ("체증설계예시", start, text.index("보험료 납입기간(10년납 미만은 10년)이 지나면", start)),
    ])
    text = text_for("bok_deposit_basics")
    start = text.index("요구불예금{")
    end = text.index('"저축성예금은 요구불예금과 반대', start)
    register_units("bok_deposit_basics", [("예금기본분류", start, end)])
    text = text_for("shinhan_cd_2025")
    register_units("shinhan_cd_2025", [
        ("발행방식과만기", *page_span(text, 1, 5)),
    ])
    text = text_for("shinhan_cover_note")
    register_units("shinhan_cover_note", [
        ("표지어음구조", *page_span(text, 1, 4)),
    ])
    text = text_for("nh_eld_contract")
    start = text.index("□ NH농협은행")
    payout = text.index("※  이자 지급 시기")
    early = text.index("※ 중도해지 수수료")
    register_units("nh_eld_contract", [
        ("만기원금약정예시", start, text.index("□ 이 상품은", start)),
        ("낙아웃이자지급예시", payout, text.index("※ 수취 이자 예시", payout)),
        ("중도해지손실예시", early, text.index("※ 모집 기간 중 해지 시", early)),
    ])
    text = text_for("kcie_cma_structure")
    start = text.index("1 RP는") if "1 RP는" in text else text.index("1\u00a0RP는")
    cma = text.index("RP, MMF, MMW는 모두")
    register_units("kcie_cma_structure", [
        ("RP기본구조", start, text.index("단기 여유 자금", start)),
        ("CMA계좌기능", cma, text.index("삼총사 모두", cma)),
    ])
    text = text_for("ktrust_collateral_contract")
    register_units("ktrust_collateral_contract", [
        ("담보신탁구조예시", *page_span(text, 2, 5)),
    ])
    text = text_for("nh_mmda_2025")
    register_units("nh_mmda_2025", [
        ("입출금과보호", *page_span(text, 1, 3)),
    ])
    text = text_for("fsc_els_offerings")
    start = text.index("원금보장형, 원금비보장형 다 가능한데")
    register_units("fsc_els_offerings", [
        ("공모사모발행사례", start, text.index("DLS는", start)),
    ])
    text = text_for("oic_bull_call")
    start = text.index("Description\nA bull call spread")
    register_units("oic_bull_call", [
        ("불콜스프레드구조", start, text.index("Outlook", start)),
    ])
    text = text_for("kb_housing_savings")
    start = text.index("예금자보호\nX")
    register_units("kb_housing_savings", [
        ("청약저축보호구분", start, text.index("세제혜택", start)),
    ])
    text = text_for("korea_sec_protection")
    start = text.index("보호금융상품등록부\n보호금융상품등록부")
    register_units("korea_sec_protection", [
        ("고객예탁금보호목록", start, text.index("타 금융회사 보호금융상품", start)),
    ])
    print("Indexed twenty-three selected official product sources; not whole-source approval.")


if __name__ == "__main__":
    main()
