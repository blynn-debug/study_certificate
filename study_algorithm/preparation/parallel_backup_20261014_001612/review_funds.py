"""Record individually read fund questions and newly confirmed source defects."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    """Preserve the publisher's answer while releasing an explicit current prompt."""
    def load(path):
        return json.loads(path.read_text(encoding="utf-8"))

    corrections = load(ROOT / "source_corrections.json")
    new_corrections = [
        {"id": "C025", "item_ids": ["S1C2T21-CORE", "S1C2T21-SUP-01", "NOTE-S1C2-Q043"],
         "refs": ["P12:120", "P12:121", "NOTE:11"], "claim_ids": ["L140"],
         "classification": "obsolete_issuance_rule",
         "finding": "원본 이미지에서 예탁결제원을 명의인으로 발행한다는 문구를 확인했다. 현행 법 제189조·제196조는 전자등록 발행이다. 핵심문제 ②와 보충문제 나의 해설, 정리노트 43의 선택지를 함께 교정한다.",
         "learner_treatment": "전자등록기관에 명부작성을 위탁하는 것과 발행 증권의 명의인을 구분한다. 교정 문항에만 교정 정답을 적용한다.",
         "original_exam_answer_impact": "core_and_note_key_not_safe; supplementary_explanation_wrong"},
        {"id": "C026", "item_ids": ["NOTE-S1C2-Q048"],
         "refs": ["NOTE:11", "P12:117", "P12:126"], "claim_ids": ["L019", "L138"],
         "classification": "obsolete_classification_count",
         "finding": "노트 48번은 자본시장법상 집합투자기구를 5가지라고 전제하지만 2026-10-13에는 기업성장집합투자기구를 포함한 6종이다. 혼합자산이라는 답 자체와 구분 수 전제를 구별한다.",
         "learner_treatment": "종류 수 전제를 6종으로 고치고 혼합자산의 정의를 묻는다.",
         "original_exam_answer_impact": "answer_unchanged_but_prompt_premise_obsolete"},
    ]
    existing = {x["id"]: x for x in corrections["items"]}
    existing.update({x["id"]: x for x in new_corrections})
    corrections["items"] = list(existing.values())
    (ROOT / "source_corrections.json").write_text(json.dumps(corrections, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Each of these prompts was compared with its source question and all options.
    reviewed = [
        ("S1C2T19-CORE", "④", "집합투자기구의 법적 형태에 속하지 않는 것은? ① 투자신탁 ② 투자회사 ③ 투자합자회사 ④ 투자합명회사", "L138"),
        ("S1C2T20-CORE", "①", "투자신탁의 3면 관계에 관한 설명 중 틀린 것은? ① 위탁자인 집합투자업자와 수익자인 투자자가 신탁설정계약을 체결한다. ② 집합투자업자는 운용을 지시한다. ③ 신탁업자는 재산을 보관·관리하며 운용지시를 이행한다. ④ 투자자는 수익자로 참여하고 일상적인 운용지시를 직접 하지 않는다.", "L139 L128"),
        ("S1C2T22-CORE", "③", "법정 예외 없는 투자신탁 수익자총회에 관한 설명 중 옳은 것은? ① 원칙적 소집권자는 신탁업자다. ② 각 수익자에게 총회 7일 전 통지하면 된다. ③ 법 또는 신탁계약에서 정한 사항에 대해서만 결의할 수 있다. ④ 반드시 현장에 출석해야 의결권을 행사할 수 있다.", "L141"),
        ("S1C2T25-CORE", "④", "별도 법정 예외가 없는 일반 공모기구이고, ①~③은 시장성 없는 자산에도 투자한다고 하자. 다음 중 제시한 사실만으로 환매금지형 설정·설립 원칙의 대상이 되지 않는 것은? ① 부동산펀드 ② 특별자산펀드 ③ 혼합자산펀드 ④ 시장성 없는 자산 편입 상한이 총자산의 15%이며 다른 환매금지형 사유는 없는 펀드", "L148"),
        ("S1C2T26-CORE", "②", "별도 환매제한·현물지급·지급기간 특례가 없는 일반 펀드의 환매 원칙 중 틀린 것은? ① 투자자는 언제든지 환매를 청구할 수 있다. ② 판매회사가 정상 영업 중이어도 반드시 신탁업자에게 먼저 청구해야 한다. ③ 재산으로 보유하거나 재산 처분으로 조성한 금전으로 지급한다. ④ 청구일부터 15일 이내 규약에서 정한 환매일에 지급한다.", "L143"),
        ("S1C2T27-CORE", "①", "집합투자재산은 원칙적으로 (가)로 평가하고, 신뢰할 수 있는 (가)가 없으면 (나)로 평가한다. 법정 허용 요건을 충족한 MMF에는 (다) 평가를 허용한다. 알맞은 연결은? ① 시가 / 공정가액 / 장부가격 ② 시가 / 공정가액 / 순자산가치 ③ 공정가액 / 시가 / 순자산가치 ④ 공정가액 / 시가 / 장부가격", "L146 L153"),
        ("S1C2T28-CORE", "②", "법정 일반 이익분배 규정에 관하여 틀린 것은? ① 금전 또는 새로 발행한 집합투자증권으로 이익금을 분배한다. ② MMF도 다른 모든 펀드와 동일하게 규약만 정하면 이익금 분배를 유보할 수 있다. ③ 투자회사의 초과분배 한도는 순자산액에서 최저순자산액을 뺀 금액이다. ④ 이익금 초과 금전분배의 뜻과 방법·시기 등을 규약에 미리 정한다.", "L152"),
        ("S1C2T29-CORE", "②", "신탁업자의 법정 운용행위 감시·확인 대상에 해당하지 않는 것은? ① 투자설명서의 법령·규약 부합 여부 ② 시장 전망에 비추어 운용방침 자체가 최선인지에 관한 투자판단 ③ 편입자산 비중의 규약 준수 여부 ④ 자산운용보고서 작성의 적정 여부", "L150"),
        ("S1C2T32-CORE", "②", "투자회사 주식발행·명의개서·재산계산 등 위탁사무를 수행하는 회사와, 펀드를 평가해 투자자에게 제공하는 회사를 순서대로 연결하라. ① 일반사무관리회사 / 채권평가회사 ② 일반사무관리회사 / 집합투자기구평가회사 ③ 채권평가회사 / 집합투자기구평가회사 ④ 채권평가회사 / 일반사무관리회사", "L154"),
    ]
    releases = load(ROOT / "item_releases.json")
    packets = {x["id"]: x for x in load(ROOT.parent / "eval/answer_packets.json")["items"]}
    for item_id, answer, prompt, claims in reviewed:
        packet = packets[item_id]
        releases["items"][item_id] = {
            "state": "adjudicated_current", "as_of": "2026-10-13", "answer": answer,
            "answer_kind": "multiple_choice", "clean_prompt": prompt,
            "prompt_correspondence_reviewed": True,
            "original_publisher_answer": packet["publisher_answer"],
            "evidence": [f"{packet['document']}:{packet['question_page']}", *claims.split()],
            "review_note": "원문의 발문·선지·해설을 읽고 현행 조문으로 개별 대조했다. 적용대상과 생략된 예외 조건을 명시한 이 정제 문항에만 채점 승인을 부여한다.",
        }
    (ROOT / "item_releases.json").write_text(json.dumps(releases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Reviewed {len(reviewed)} fund questions and {len(new_corrections)} source correction records.")


if __name__ == "__main__":
    main()
