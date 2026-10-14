"""Record reviewed insurance, trust and retirement prompt variants."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    """Preserve source findings separately from newly approved prompts."""
    def read(path):
        return json.loads(path.read_text(encoding="utf-8"))

    data = read(ROOT / "source_corrections.json")
    additions = [
        {"id": "C041", "item_ids": ["S1C2T06-CORE"], "refs": ["P12:76"],
         "claim_ids": ["L218"], "classification": "trust_exception_scope_needs_qualification",
         "finding": "④의 금전신탁 설명을 신탁 전체의 예외 없는 겸임금지로 일반화하면 신탁법의 자기신탁 및 공동수익자 예외와 충돌한다. 일반 신탁법의 예외가 개별 금융기관 금전신탁 상품에 적용되는지까지 이 문항만으로 확정할 수는 없다. ②의 수익자에게 재산권 이전이라는 오답은 명백하다.",
         "learner_treatment": "기존 ②의 학습목표를 보존하되 통상적 위탁자·수탁자·수익자 역할을 명확히 묻는 변형만 채점한다. 원문 ④를 예외 없는 법칙으로 암기시키지 않는다.",
         "original_exam_answer_impact": "publisher_key_preserved_only_after_scope_clarification"},
        {"id": "C042", "item_ids": ["S1C2T08-CORE"], "refs": ["P12:83"],
         "claim_ids": ["L219"], "classification": "conditional_payoff_misrepresented_as_guarantee",
         "finding": "해설의 ELS 원리금 확실 지급보장은 틀리다. 사전에 정한 지급조건·산식과 확정된 수익·지급보장은 별개다. ELS의 원금손실과 ELB의 발행사·중도상환 위험을 누락해서는 안 된다.",
         "learner_treatment": "수익산식의 사전설정과 실제 지급조건·신용위험을 분리하여 설명·채점한다. 원문의 보장 표현을 되풀이하면 학습비서 평가에서 근거 오류로 판정한다.",
         "original_exam_answer_impact": "publisher_key_preserved_in_rewritten_risk_question"},
        {"id": "C043", "item_ids": ["S1C2T14-CORE"], "refs": ["P12:104"],
         "claim_ids": ["L221"], "classification": "accident_insurance_subrogation_exception_omitted",
         "finding": "보험자대위가 손해보험에서만 인정된다는 해설은 상법 제729조 단서의 상해보험 약정대위 예외를 누락했다. 잔존물대위와 청구권대위를 뒤바꾼 ④가 틀렸다는 핵심은 유지된다.",
         "learner_treatment": "잔존물·청구권 대위의 대상과 요건을 구별하고 상해보험 예외를 포함한 수정 해설을 사용한다.",
         "original_exam_answer_impact": "key_unchanged_explanation_corrected"},
    ]
    rows = {row["id"]: row for row in data["items"]}
    rows.update({row["id"]: row for row in additions})
    data["items"] = list(rows.values())
    (ROOT / "source_corrections.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    reviewed = [
        ("S1C2T12-CORE", "③", "보험에 관한 설명 중 틀린 것은? ① 다수 동질적 위험을 모으면 통계적 위험 추정이 가능해진다. ② 보험은 계약상 사고 발생 시 급여를 제공하는 구조다. ③ 정액 사망보험은 사망으로 생긴 재산상 실제 손해액을 계산하여 그 금액만 지급하는 실손보험이다. ④ 보험은 질병·사망 등의 경제적 위험에 대비하는 수단이 될 수 있다.", "L220"),
        ("S1C2T33-CORE", "②", "다음은 자산유동화법이 허용하는 여러 구조 중 양도형 SPC 구조를 설명한 것이다. 자산보유자가 채권 등 자산을 유동화전문회사에 양도하고 이를 바탕으로 증권을 발행하는 것은? ① 특정한 부동산담보대출만을 뜻하는 MBS ② 자산유동화증권인 ABS ③ 주가연계증권인 ELS ④ 주식형 상장지수펀드인 ETF. 모든 ABS가 SPC 양도형이라는 뜻은 아니다.", "L225"),
        ("S1C2T35-CORE", "②", "DB와 DC의 설명 중 틀린 것은? ① DB는 받을 급여수준을, DC는 사용자 부담금 수준을 미리 정한다. ② DB의 운용성과에 따른 부담은 근로자가, DC의 운용지시는 기업이 담당한다. ③ DC 급여는 운용결과에 따라 달라질 수 있다. ④ DC 사외적립과 원금·수익률 보장은 서로 다른 개념이다.", "L223 L224"),
    ]
    releases = read(ROOT / "item_releases.json")
    packets = {row["id"]: row for row in read(ROOT.parent / "eval/answer_packets.json")["items"]}
    for item_id, answer, prompt, claims in reviewed:
        packet = packets[item_id]
        releases["items"][item_id] = {
            "state": "adjudicated_current", "as_of": "2026-10-13", "answer": answer,
            "answer_kind": "multiple_choice", "clean_prompt": prompt,
            "prompt_correspondence_reviewed": True,
            "original_publisher_answer": packet["publisher_answer"],
            "evidence": [f"{packet['document']}:{packet['question_page']}", *claims.split()],
            "review_note": "교재 문항·해설과 현행 법률을 대조했다. 여기 명시된 변형의 문항 범위와 단일 정답을 승인하며 기존 원문의 모든 부가설명까지 승인한 것으로 보지 않는다.",
        }
    (ROOT / "item_releases.json").write_text(json.dumps(releases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Recorded {len(reviewed)} product prompts and {len(additions)} source findings.")


if __name__ == "__main__":
    main()
