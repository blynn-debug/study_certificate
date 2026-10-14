"""Apply individually read KOFIA rules to clarified study prompts."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    """Keep changed explanations auditable alongside preserved publisher keys."""
    def load(path):
        return json.loads(path.read_text(encoding="utf-8"))

    data = load(ROOT / "source_corrections.json")
    new = [
        {"id": "C038", "item_ids": ["S3C3T16-CORE"], "refs": ["P3:197"],
         "claim_ids": ["L136", "L217"], "classification": "standard_terms_reporting_exemption_error",
         "finding": "②는 표준약관을 수정해도 협회 보고를 하지 않아도 된다고 썼다. 현행은 제·변경 후 7일 보고가 원칙이고 사전신고 대상은 10영업일 전 신고다. 외국집합투자증권 표준약관 수정금지도 규정상 대상 투자자 예외가 있다.",
         "learner_treatment": "보고·신고 원칙과 예외를 명시한 수정문항에만 유일한 오답 ③을 적용한다.",
         "original_exam_answer_impact": "single_key_not_safe_without_qualification"},
        {"id": "C039", "item_ids": ["S3C3T11-CORE"], "refs": ["P3:183"],
         "claim_ids": ["L214"], "classification": "excluded_benefit_vs_prohibited_benefit_confusion",
         "finding": "나열한 항목은 규정상 재산상 이익으로 보지 않는 제외목록이다. 5만원 이하 현금이 제외목록에 없다는 사실을 현금·현금유사품의 제공과 수령이 모든 경우 불가능하다는 해설로 바꾸면 안 된다. 허용되는 신유형상품권의 범위도 현행 규정에 있다.",
         "learner_treatment": "제공 허용 여부 대신 산정 제외대상 여부를 묻고 그 후 절차·한도 심사를 별도로 안내한다.",
         "original_exam_answer_impact": "key_unchanged_question_and_explanation_scope_fixed"},
        {"id": "C040", "item_ids": ["S3C3T14-CORE"], "refs": ["P3:189"],
         "claim_ids": ["L216"], "classification": "certificate_vs_registered_personnel_conflation",
         "finding": "해설은 자격증을 취득하면 해당 업무를 수행할 수 있다는 식으로 금융투자전문인력을 정의한다. 협회 규정은 임직원인 주요직무 종사자의 등록·관리 제도이며 교육·등록요건이 별도다. 종전 증권분석사 합격자가 분석사 등록요건을 인정받는 경과조항도 존재한다.",
         "learner_treatment": "등록직무의 명칭을 묻는 정답 ④와 과거 자격을 가진 사람이 등록할 수 있는지를 구분한다.",
         "original_exam_answer_impact": "answer_label_unchanged_explanation_overbroad"},
    ]
    rows = {x["id"]: x for x in data["items"]}
    rows.update({x["id"]: x for x in new})
    data["items"] = list(rows.values())
    (ROOT / "source_corrections.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    reviewed = [
        ("S3C3T01-CORE", "③", "시장 개설·운영 및 이상거래 심리 등을 맡는 기관과, 금융투자회사 회원의 영업행위 자율규제를 맡는 기관을 연결한 것은? ① 협회·거래소 ② 협회·금감원 ③ 거래소·협회 ④ 거래소·금감원", "L205"),
        ("S3C3T02-CORE", "②", "별도 설명서 제공 특례가 없는 일반투자자 대상이다. 협회 핵심설명서 교부대상으로 열거된 범주가 아닌 것은? ① 고난도 금융투자상품 ② 다른 고난도 특성이 없는 일반 ELW ③ 신용융자거래 및 FX마진 ④ 고난도가 아닌 공모형 파생결합증권 중 ELW·ETN·금적립계좌 등의 제외상품에 해당하지 않는 상품", "L098"),
        ("S3C3T03-CORE", "①", "다른 법정 예외가 없다고 할 때 펀드판매 금지행위가 아닌 것은? ① 투자자 이익에 부합한다는 합리적 근거에 따른 차별적 판매노력 ② 판매 대가로 집합투자재산 매매주문 배정 요구 ③ 판매 대가로 유사한 다른 투자자보다 부당하게 높은 거래수수료 요구 ④ 수익률을 확정적으로 보장·단언", "L206"),
        ("S3C3T04-CORE", "③", "펀드투자권유대행인의 허용범위를 고르라. 파생상품등·고난도금전신탁·고난도일임 등 규정상 제외대상은 가~다에서 미리 제외했다. 가. 집합투자증권 나. 투자자문·투자일임계약 다. 신탁계약 라. 파생상품계약. ① 가 ② 가·나 ③ 가·나·다 ④ 가·나·다·라", "L207"),
        ("S3C3T05-CORE", "③", "조사분석 규정 중 틀린 것은? ① 선관주의와 공정성·합리적 근거가 요구된다. ② 외부자료를 인용하면 신뢰도를 검증해야 한다. ③ 보수산정 기준에는 자료의 품질·생산실적과 투자의견 적정성이 포함되면 안 된다. ④ 임원수 제한 등 불가피한 경우 조사분석 담당임원의 겸직 예외가 있다.", "L208"),
        ("S3C3T06-CORE", "④", "다른 금지사유·특례가 없을 때 조사분석 공표가 허용되는 것은? ① 자신이 안정조작 중인 법인의 해당 주식 ② 자산총액 대비 5%를 초과하는 M&A 주선업무의 대상법인 ③ 공개입찰 지분매각 주선업무 대상법인 ④ 부적정 감사의견 법인의 투자의견·목표가격을 하향조정하는 자료", "L209"),
        ("S3C3T07-CORE", "①", "최초상장 대표주관업무의 조사분석 의무공표 설명 중 틀린 것은? ① 거래일부터 1년 동안 1회만 공표하면 된다. ② 법정 예외가 없다면 1년 동안 2회 이상 공표한다. ③ 자료에 대표주관 이해관계를 명시하고 무료 열람하도록 한다. ④ 시장 간 이전상장 대표주관업무는 이 최초상장 의무의 예외다.", "L210"),
        ("S3C3T08-CORE", "④", "금융투자분석사 규정 중 틀린 것은? ① 담당 업종 주식등 매매금지에 기존 보유분 처분 등 예외가 있다. ② 원칙상 공표 후 24시간이 지나야 매매하고 7일이 지나지 않았다면 같은 방향으로 매매한다. ③ 법정 고지대상에는 자기뿐 아니라 배우자의 계산으로 보유한 해당 상품도 포함한다. ④ ELW도 보유가액이 300만원 이하이면 언제나 재산적 이해관계 고지를 면제받는다.", "L211"),
        ("S3C3T09-CORE", "④", "표시특례가 없는 일반 펀드 투자광고의 의무사항을 모두 고르라. 가. 환매수수료 나. 환매금액 수령시기 다. 증권거래비용 발생 가능성과 보수·수수료. ① 가·나 ② 나·다 ③ 가·다 ④ 가·나·다", "L212"),
        ("S3C3T10-CORE", "④", "협회 운용실적 광고규정 중 틀린 것은? ① 세제혜택 특례가 없는 일반 펀드는 설정·설립 1년 이상 및 순자산 100억원 이상이 원칙이다. ② 유형별 운용실적은 동일유형 순자산 500억원 이상이 기준이다. ③ MMF는 과거 1개월 수익률을 표시한다. ④ MMF나 객관적 벤치마크 산정이 어려운 부동산펀드도 벤치마크를 반드시 병기해야 한다.", "L213"),
        ("S3C3T12-CORE", "③", "협회 신상품 보호규정 중 틀린 것은? ① 새 비즈니스 모델 등의 상품·서비스로 국내외 공지·판매 이력이 없어야 한다. ② 배타적 사용권은 일정기간 독점 판매권이다. ③ 침해배제 신청은 접수일부터 10영업일 안에 위원회를 소집·심의한다. ④ 이유 있는 신청이면 침해정지를 명할 수 있다.", "L215"),
        ("S3C3T13-CORE", "③", "협회 FX마진거래 규정의 일반 설명 중 틀린 것은? ① 자본시장법상 장내파생상품 범주에 해당한다. ② 위탁증거금은 미국 달러로 납부한다. ③ 원·달러와 원·엔 거래가 일반적인 거래대상이다. ④ 같은 계좌의 같은 통화쌍에서 반대방향 거래가 생기면 같은 수량의 기존 포지션을 상계한다.", "L102 L127 L137"),
    ]
    data = load(ROOT / "item_releases.json")
    packets = {x["id"]: x for x in load(ROOT.parent / "eval/answer_packets.json")["items"]}
    for item_id, answer, prompt, claims in reviewed:
        packet = packets[item_id]
        data["items"][item_id] = {
            "state": "adjudicated_current", "as_of": "2026-10-13", "answer": answer,
            "answer_kind": "multiple_choice", "clean_prompt": prompt,
            "prompt_correspondence_reviewed": True,
            "original_publisher_answer": packet["publisher_answer"],
            "evidence": [f"{packet['document']}:{packet['question_page']}", *claims.split()],
            "review_note": "원문 문항·해설 및 현행 협회규정을 개별 대조했다. 적용범위를 명시하고 모호한 선지를 정리한 이 문항에 한해 승인한다.",
        }
    (ROOT / "item_releases.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Recorded {len(reviewed)} KOFIA questions and {len(new)} corrections.")


if __name__ == "__main__":
    main()
