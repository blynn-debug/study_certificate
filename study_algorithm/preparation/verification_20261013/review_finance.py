"""Individually reviewed financial-rule prompts, with explicit scope and dates."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ITEMS = []


def reviewed(item_id, answer, prompt, claims, note, answer_kind="free_response"):
    """Record one read question; a shared page never authorizes its neighbours."""
    ITEMS.append({
        "id": item_id, "answer": answer, "clean_prompt": prompt,
        "claim_ids": claims.split(), "review_note": note, "answer_kind": answer_kind,
    })


reviewed("S1C2T24-SUP-02", "④",
         "원화 MMF의 운용대상으로 적절하지 않은 것은? 회사채는 주권관련사채·사모사채를 제외하고 신용등급 요건을 충족한다고 가정한다.\n① 남은 만기 6개월 이내 CD\n② 남은 만기 1년 이내 회사채\n③ 법정 금융기관에 대한 30일 이내 단기대출\n④ 만기 1년인 금융기관 예치",
         "L093 L094", "예치 만기는 6개월 이내다. 상한을 묻는 교재 의도를 유지하고 회사채의 법정 제외대상을 명시했다.", "choice")
reviewed("NOTE-S1C2-Q049", "40%",
         "외국환평형기금·국가재정법상 통합운용의 예외에 해당하지 않는 원화 MMF는 집합투자재산의 몇 % 이상을 법정 채무증권에 운용해야 하는가?",
         "L094", "원화·적용 예외를 명시했다. RP 매수액을 이 채무증권 40% 산정에 포함하지 않는다.")
reviewed("NOTE-S1C2-Q051", "X",
         "O/X: 원화 MMF가 다른 집합투자기구의 집합투자증권에 투자하는 경우, 주식형펀드나 일반 채권형펀드에도 투자할 수 있다.",
         "L094", "시행령 제241조는 다른 MMF의 집합투자증권을 열거한다. 일반 주식형·채권형으로 확대하지 않는다.")
reviewed("NOTE-S3C3-Q002", "핵심설명서",
         "법정 수령거부·간이투자설명서 대체 등 예외가 없는 일반투자자에게 고난도상품 또는 비고난도 공모 파생결합증권(ELW·ETN·금적립계좌등 제외), 신용융자·FX마진 거래의 법정 경우 추가로 교부하여 충분히 설명하는 서류는?",
         "L098", "핵심설명서와 일반사모 핵심상품설명서 명칭을 구별한다. 각 대상·예외를 유지한 재서술이다.")
reviewed("NOTE-S3C3-Q003", "O",
         "O/X: 일반투자자가 ELW나 ETN을 최초로 매매하려면, 기존 위탁매매거래 여부와 별개로 서명 등으로 매매의사를 별도 확인한다.",
         "L098", "영업규정 제2-5조제5항의 최초 매매 확인이다. 모든 상품에 매 거래마다 적용하지 않는다.")
reviewed("NOTE-S3C3-Q004", "O",
         "O/X: 영업규정의 법인·외국인·일임 등 교육 예외가 없는 일반투자자가 ELW나 1배 초과 배율 연동 레버리지 ETF·ETN을 매매하려면 협회가 인정하는 사전교육을 이수해야 한다.",
         "L103", "모든 ETN으로 확대하지 않고 해외 상장 포함 및 별도 단일종목 규정을 설명한다.")
reviewed("NOTE-S3C3-Q005", "1시간 이상 / 3시간 이상",
         "사전이수 예외가 없는 일반개인투자자가 한국거래소 선물·옵션을 거래하려면 파생상품 교육과 모의거래를 각각 최소 몇 시간 이수해야 하는가?",
         "L103", "교육과 모의거래를 별도 요건으로 평가한다. 자격시험 합격을 양쪽 모두의 자동 면제로 설명하지 않는다.")
reviewed("NOTE-S3C3-Q014", "2회 이상",
         "법정 예외를 제외하고 IPO 대표주관회사는 최초 매매거래일부터 1년간 해당 주식의 조사분석자료를 최소 몇 회 공표하고 무료 열람을 제공해야 하는가?",
         "L072", "최초 1년간 의무다. 영구히 매년 2회라는 뜻으로 확대하지 않는다.")
reviewed("NOTE-S3C3-Q015", "24시간 / 7일",
         "조사분석자료를 공표한 상품에 대한 금융투자분석사의 법정 예외적 매매에서 공표 후 최소 대기시간은? 공표일부터 며칠이 지나기 전까지는 공표 내용과 같은 방향이어야 하는가?",
         "L073", "24시간 경과와 7일 방향 제한은 누적 조건이다. 매수의견이면 반드시 매수하라는 의무가 아니다.")
reviewed("NOTE-S3C3-Q021", "1년 / 100억원",
         "세제상품 등 법정 예외를 제외한 개별 집합투자기구의 일반 운용실적 광고는 설정·설립 후 몇 년 이상, 순자산총액 얼마 이상을 기본 요건으로 하는가?",
         "L083", "세제펀드 50억원 및 유형별 500억원과 분리한 일반 조건이다.")
reviewed("NOTE-S3C3-Q022", "5만원 / 20만원",
         "협회 영업규정의 재산상 이익 범위에서 제외되는 물품·식사의 경제적 가치 상한과 경조비·조화·화환의 상한은 각각 얼마인가? 현금·백화점상품권 전부를 물품으로 취급하지 않는다.",
         "L084", "각 금액 이하가 경계다. 원문 노트의 2026년 개정 표시는 그대로 반복하지 않는다.")
reviewed("NOTE-S3C3-Q024", "X",
         "O/X: FX마진 거래는 금융투자회사의 명의와 금융투자회사의 계산으로 이루어진다.",
         "L102", "회사 명의·투자자 계산이다. 명의와 손익 귀속을 따로 평가한다.")
reviewed("NOTE-S3C3-Q027", "5% 이상",
         "동일인이 주관회사와 발행회사의 주식등을 각각 일정 비율 이상 보유하면 이해관계에 따른 주관제한이 생긴다. 동일인이 정부·기관투자자인 예외를 제외할 때 이 비율은?",
         "L087", "각각 5% 이상이다. 두 회사 지분을 합해 5%로 해석하지 않는다.")
reviewed("NOTE-S3C3-Q029", "20% / 25% 이상 / 5% 이상",
         "법정 배정 예외가 없는 국내 유가증권시장 IPO에서 우리사주조합, 일반청약자, 요건을 갖춘 15일 이상 의무보유확약 고위험고수익투자신탁등의 배정비율을 차례로 말하라.",
         "L088 L089", "시장과 자격을 명시했다. 잔여 기관 물량에도 별도 확약 우선배정 조건이 있다는 점은 후속 설명에서 유지한다.")
reviewed("NOTE-S3C3-Q032", "O",
         "O/X: 협회 위원회가 불성실 수요예측 참여자에게 법정 요건 아래 제재금 또는 금전 납부를 부과하는 경우, 그 자의 고유재산에 대해 수요예측 참여제한을 병과할 수 있다.",
         "L091 L092", "제17조의2제5항의 고유재산 범위를 명시한다. 언제나 병과해야 한다는 의무로 바꾸지 않는다.")
reviewed("NOTE-S3C3-Q034", "7일",
         "개별약관을 제정하거나 변경한 후 협회에 보고하는 원칙적 기한은? 사전신고 대상은 별도로 구분한다.",
         "L086", "제정·변경 후 7일이며 영업일이 아니다. 시행 후 7일과 혼동하지 않는다.")


def main():
    """Merge these explicit prompt decisions while preserving other reviews."""
    path = ROOT / "item_releases.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    packets = {x["id"]: x for x in json.loads(
        (ROOT.parent / "eval/answer_packets.json").read_text(encoding="utf-8"))["items"]}
    claim_ids = {x["id"] for x in json.loads(
        (ROOT / "verified_claims.json").read_text(encoding="utf-8"))["items"]}
    for review in ITEMS:
        packet = packets[review["id"]]
        if not set(review["claim_ids"]) <= claim_ids:
            raise ValueError(f"Missing claim for {review['id']}")
        data["items"][review["id"]] = {
            "state": "adjudicated_current", "as_of": "2026-10-13",
            "answer": review["answer"], "answer_kind": review["answer_kind"],
            "prompt_correspondence_reviewed": True, "clean_prompt": review["clean_prompt"],
            "evidence": [f"{packet['document']}:{packet['question_page']}", *review["claim_ids"]],
            "review_note": review["review_note"],
            "original_publisher_answer": packet["publisher_answer"],
            "scope": "Only this reviewed prompt; no approval of neighbouring questions or entire source pages.",
        }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Recorded {len(ITEMS)} individual financial-rule prompts.")


if __name__ == "__main__":
    main()
