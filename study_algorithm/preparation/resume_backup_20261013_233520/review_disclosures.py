"""Record reviewed disclosure/regulation questions, preserving original defects."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

CORRECTIONS = [
    {"id": "C030", "item_ids": ["S3C2T14-CORE"], "refs": ["P3:94"],
     "claim_ids": ["L180"], "classification": "overbroad_trustee_option",
     "finding": "②는 일반 투자매매·중개업자도 모든 신탁업자에게 예탁금을 신탁할 수 있는 것처럼 썼다. 법 제74조제1항은 증권금융회사에 예치 또는 신탁이며 다른 신탁업자 허용은 법정 겸영업자의 특례다. ③의 자기계약 전면금지도 틀리므로 단일 오답키를 그대로 사용하지 않는다.",
     "learner_treatment": "②에 원칙상 예치기관을 명시하고 ③에 자기계약 허용요건을 명시한 수정문항으로 평가한다.",
     "original_exam_answer_impact": "single_key_not_safe_without_qualification"},
    {"id": "C031", "item_ids": ["S3C2T24-CORE"], "refs": ["P3:117"],
     "claim_ids": ["L182", "L183"], "classification": "offering_filing_requirements_conflated",
     "finding": "①은 청약권유 50인 이상이면 금액·증권종류에 관계없이 신고의무가 자동 발생한다고 썼다. 공모 판정과 신고서 제출요건은 따로 판단한다. ③의 전매기간 6개월도 틀리므로 원문을 유일한 ③ 오답으로 채점하지 않는다.",
     "learner_treatment": "공모 인원, 과거 인원합산, 전매기간, 신고금액을 서로 다른 기준으로 설명한다.",
     "original_exam_answer_impact": "single_key_not_safe_without_qualification"},
    {"id": "C032", "item_ids": ["NOTE-S3C2-Q073"], "refs": ["NOTE:49", "P3:115", "P3:116"],
     "claim_ids": ["L183"], "classification": "obsolete_small_offering_threshold",
     "finding": "노트 정답의 일반 소액공모 기준 10억원은 2026-07-28 개정 이후 30억원이다. 현 공모와 법정 과거 1년 금액 합산, 금액과 무관하게 신고하는 특수 증권을 별도로 판단한다.",
     "learner_treatment": "30억원 기준이 적용되는 일반 증권이라는 조건을 문제에 명시한다.",
     "original_exam_answer_impact": "answer_changes_to_30억원"},
    {"id": "C033", "item_ids": ["S3C2T35-CORE", "NOTE-S3C2-Q103"],
     "refs": ["P3:142", "P3:143", "NOTE:53"], "claim_ids": ["L193"],
     "classification": "obsolete_inspection_classification",
     "finding": "검사 종류가 종합검사·부문검사라는 교재 분류는 2022-03-03 개정 전 표현이다. 현행은 정기검사·수시검사이고 현장·서면은 실시방법이다. 정리노트의 대부분이라는 경험적 빈도는 현재 근거 없이 정답화하지 않는다.",
     "learner_treatment": "법정 종류와 방법을 분리한 문항으로 교체한다. 핵심문제 정답번호 유지와 낡은 해설 교정을 구분한다.",
     "original_exam_answer_impact": "core_key_unchanged_explanation_outdated; note_rewritten"},
    {"id": "C034", "item_ids": ["S3C2T12-CORE"], "refs": ["P3:88", "P3:89"],
     "claim_ids": ["L196"], "classification": "missing_decision_authority_condition",
     "finding": "④는 내부통제업무 위탁을 전면 금지한다고 썼으나 법 제42조는 의사결정권한까지 위탁하는 경우로 제한한다. ①도 별도 인허가 업무와 사후보고 대상 겸영업무를 구별해야 한다.",
     "learner_treatment": "보고대상 겸영업무와 내부통제 의사결정권한이라는 조건을 명시하고 ③의 일률적 위탁보고기한을 오답으로 평가한다.",
     "original_exam_answer_impact": "single_key_not_safe_without_qualification"},
]

REVIEWED = [
    ("S3C2T11-CORE", "③", "일반 금융투자업자가 사업연도 개시일부터 3·6·9·12개월간의 업무보고서를 금융위에 제출하는 기한은 해당 기간 경과 후 며칠 이내인가? 역외업자 특례는 제외한다. ① 7일 ② 1개월 ③ 45일 ④ 90일", "L178"),
    ("S3C2T13-CORE", "①", "금융투자업자가 주문을 받기 전에 거래의 상대방인 투자매매업자인지, 중개수수료를 받는 투자중개업자인지를 투자자에게 밝히는 의무는? ① 매매형태의 명시의무 ② 자기계약의 금지 ③ 최선집행의무 ④ 임의매매의 금지", "L179"),
    ("S3C2T22-CORE", "②", "법정 별도 예외를 제외한 투자일임업 규정 중 옳은 것은? ① 일반 투자일임보고서의 작성 주기는 2개월마다 1회 이상이다. ② 역외투자일임업자는 월 1회 이상 보고서를 제공한다. ③ 투자일임업자라는 자격만으로 고객 금전·증권을 보관할 수 있다. ④ 이해관계인이 되기 3개월 전 체결한 계약이면 그 이해관계인 고유재산과의 거래가 기존계약 예외에 해당한다.", "L181"),
    ("S3C2T26-CORE", "①", "법정 예외가 없는 증권분석기관의 평가제한 기준을 설명했다. 법정 최소 출자율을 잘못 쓴 것은? ① 기관과 발행인이 상대방에 출자한 최소 비율은 5%다. ② 동일 주주가 두 기관에 각각 출자한 최소 비율은 5%다. ③ 기관의 임원이 발행인에 출자한 최소 비율은 1%다. ④ 주요주주의 특수관계 및 주요 경영사항에 대한 사실상 영향력도 별도 제한사유다.", "L184"),
    ("S3C2T27-CORE", "②", "법정 특례·면제가 없는 경우 사업보고서 제출은 사업연도 후 (가), 반기·분기보고서는 기간 후 (나), 통상의 제출기간 밖에 처음 제출대상이 된 법인의 직전연도 사업보고서는 대상이 된 날부터 (다) 이내다. 어느 빈칸에도 들어가지 않는 것은? ① 5일 ② 10일 ③ 45일 ④ 90일", "L185"),
    ("S3C2T28-CORE", "②", "사업보고서 제출대상법인의 주요사항보고서 제출사유에 해당하지 않는 것은? ① 발행어음 부도 ② 중요하지 않은 일부 영업의 정지만 발생했고 다른 보고사유도 없음 ③ 법정 보고대상 자본변동에 관한 이사회 결정 ④ 자기주식 취득·처분 결의", "L186"),
    ("S3C2T29-CORE", "③", "법정 공개매수 면제사유가 없는 경우의 요건이다. 고쳐야 할 표현은? ① 증권시장 밖에서 ② 과거 6개월간 10명 이상으로부터 법정 주식등을 유상취득하고 ③ 본인과 특수관계인만 합산하여 공동보유자를 제외한 결과 ④ 주식등 총수의 5% 이상을 보유하게 되는 경우 공개매수를 해야 한다.", "L187"),
    ("S3C2T30-CORE", "②", "상장법인의 5% 대량보유 보고에 관한 일반 원칙이다. 다른 변경사유가 없는 경우 보고의무가 자동 발생하는 사유가 아닌 것은? ① 본인·특별관계자 합계가 처음 5%에 도달 ② 합계 보유 5%인 자의 1주 변동으로 변동폭이 총수의 1%포인트에 미달 ③ 단순투자에서 경영참가로 목적 변경 ④ 경영참가에서 단순투자로 목적 변경", "L188"),
    ("S3C2T31-CORE", "①", "공공적 법인의 상장 당시 10% 이상 주주도 아니고 별도 금융위 승인도 없는 자의 일반 소유한도는 의결권 주식총수의 얼마 이내에서 정관이 정한 비율인가? ① 3% ② 5% ③ 7% ④ 10%", "L189"),
    ("S3C2T32-CORE", "①", "협회를 통해 불특정 다수에게 호가·수량을 공표하고, 호가가 일치하는 경우 그 가격에 체결하며 발행인 재무상황 등을 공시하는 거래를 설명했다. 해당하는 것은? ① 비상장주권 장외거래 ② 증권대차거래 ③ 환매조건부매매 ④ 기업어음 장외거래", "L190"),
    ("S3C2T33-CORE", "③", "미공개중요정보 이용규제에 관한 설명 중 틀린 것은? ① 상장법인 외에 6개월 내 상장되는 법인도 포함한다. ② 법정 요건을 충족한 정보수령자도 포함한다. ③ 주요주주가 주주권 행사 과정에서 안 정보는 내부자에 관한 규정의 적용대상이 아니다. ④ 법인에 대한 인허가·감독권을 행사하는 과정에서 안 미공개중요정보도 규제될 수 있다.", "L191"),
    ("S3C2T34-CORE", "②", "성황인 듯 오인시키는 등의 목적으로 권리이전 목적 없이 거짓으로 꾸민 상장증권·장내파생상품 매매는? ① 통정매매 ② 가장매매 ③ 가격고정 ④ 법정 안정조작", "L192"),
    ("S3C2T36-CORE", "④", "자본시장 조사업무규정에 관한 설명 중 틀린 것은? ① 금융위·금감원 업무 중 발견한 위법 혐의는 조사사유가 될 수 있다. ② 거래소가 이첩한 혐의도 조사할 수 있다. ③ 익명 제보는 조사를 하지 않을 수 있는 사유지만 반드시 조사면제되는 것은 아니다. ④ 조사결과 과징금은 가능하나 법정 요건을 갖춰도 과태료는 부과할 수 없다.", "L194"),
    ("S3C2T37-CORE", "④", "금융소비자보호법 제3조가 정한 네 가지 상품유형의 명칭이 아닌 것은? ① 예금성 상품 ② 투자성 상품 ③ 보장성 상품 ④ 연금성 상품", "L195"),
]


def main():
    """Upsert only the records whose individual texts were reviewed."""
    def load(path):
        return json.loads(path.read_text(encoding="utf-8"))

    corrections = load(ROOT / "source_corrections.json")
    rows = {x["id"]: x for x in corrections["items"]}
    rows.update({x["id"]: x for x in CORRECTIONS})
    corrections["items"] = list(rows.values())
    (ROOT / "source_corrections.json").write_text(
        json.dumps(corrections, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    packets = {x["id"]: x for x in load(ROOT.parent / "eval/answer_packets.json")["items"]}
    releases = load(ROOT / "item_releases.json")
    for item_id, answer, prompt, claims in REVIEWED:
        packet = packets[item_id]
        releases["items"][item_id] = {
            "state": "adjudicated_current", "as_of": "2026-10-13",
            "answer": answer, "answer_kind": "multiple_choice", "clean_prompt": prompt,
            "prompt_correspondence_reviewed": True,
            "original_publisher_answer": packet["publisher_answer"],
            "evidence": [f"{packet['document']}:{packet['question_page']}", *claims.split()],
            "review_note": "원문의 발문·선지·해설과 현행 조문을 대조했다. 빠진 적용조건을 명시하고 중의성을 제거한 이 문항에 한해서 평가한다. 원문 응답에 수정 키를 소급 적용하지 않는다.",
        }
    (ROOT / "item_releases.json").write_text(
        json.dumps(releases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    print(f"Recorded {len(REVIEWED)} reviewed questions and {len(CORRECTIONS)} corrections.")


if __name__ == "__main__":
    main()
