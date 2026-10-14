"""Record current ethics claims applied to individually inspected questions."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    """Retain distinct statuses for an original explanation and a revised prompt."""
    def load(path):
        return json.loads(path.read_text(encoding="utf-8"))

    data = load(ROOT / "source_corrections.json")
    additions = [
        {"id": "C035", "item_ids": ["S3C1T05-CORE"], "refs": ["P3:12"],
         "claim_ids": ["L197"], "classification": "fiduciary_duty_legal_overstatement",
         "finding": "해설의 신임의무는 법률상의 의무가 아니라는 전면적 단정은 민법상 선관주의·상법상 충실의무와 맞지 않는다. 포괄개념의 설명과 법적 구체화를 구분해야 한다.",
         "learner_treatment": "교재가 제시한 학습용 두 축은 보존하되 신임의무가 전혀 법적 의무가 아니라는 해설은 사용하지 않는다.",
         "original_exam_answer_impact": "key_unchanged_explanation_correction"},
        {"id": "C036", "item_ids": ["S3C1T11-CORE"], "refs": ["P3:42"],
         "claim_ids": ["L199"], "classification": "unlimited_market_abuse_overstatement",
         "finding": "①·②의 모든 시장질서 교란행위 제재 및 목적성 불필요라는 표현은 법 제178조의2의 개별 구성요건·정보의 중요성·비공개성·인식·부당한 시세영향 등을 생략했다. 손익이전·조세회피 목적을 요구하는 유형도 있다.",
         "learner_treatment": "수령차수 제한 철폐와 구성요건 없는 무제한 제재를 구분하는 수정문항으로 평가한다.",
         "original_exam_answer_impact": "single_key_not_safe_without_qualification"},
        {"id": "C037", "item_ids": ["S3C1T04-CORE"], "refs": ["P3:10"],
         "claim_ids": ["L198"], "classification": "incorrect_article_number",
         "finding": "원본 이미지에서 핵심해설의 고객우선 제3조를 확인했다. 같은 쪽 본문과 협회 준칙은 제2조다. 제3조는 법규준수다.",
         "learner_treatment": "정답인 고객우선·신의성실은 유지하고 조문번호를 제2조·제4조로 교정한다.",
         "original_exam_answer_impact": "answer_unchanged_citation_wrong"},
    ]
    rows = {x["id"]: x for x in data["items"]}
    rows.update({x["id"]: x for x in additions})
    data["items"] = list(rows.values())
    (ROOT / "source_corrections.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    reviewed = [
        ("S3C1T03-CORE", "②", "고객의 입장에서 서비스를 제공하고 정직·신뢰에 따라 맡은 업무를 충실히 수행한다는 두 준칙은? 가. 고객우선 나. 신의성실 다. 법규준수 라. 시장질서존중. ① 가 ② 가·나 ③ 다·라 ④ 가·나·다·라", "L198"),
        ("S3C1T07-CORE", "④", "협회 금융소비자보호 내부통제기준상 위원회의 조정·의결사항을 모두 고르라. 경미한 사항의 보고 특례는 제외한다. 가. 소비자보호 주요 제도변경 나. 금융상품 개발·영업방식·정보공시 다. 보호기준 적정성·준수실태 점검조치. ① 가·나 ② 나·다 ③ 가·다 ④ 가·나·다", "L200"),
        ("S3C1T10-CORE", "④", "다음 설명 중 틀린 것은? ① 회사는 임직원의 자율·창의를 존중하고 임직원은 상호 협조한다. ② 회사의 경영진은 올바른 윤리문화 정착을 위해 노력한다. ③ 회사재산의 부당한 사용과 사적이익 추구는 금지한다. ④ 사용자를 대신해 사무를 감독하는 자는 민법 제756조제2항의 요건을 충족해도 같은 조의 사용자책임을 지지 않는다.", "L198 L204"),
        ("S3C1T12-CORE", "②", "지배구조법이 적용되고 별도 특례가 없는 금융회사의 내부통제 규정 중 틀린 것은? ① 내부통제위원회는 내부통제기준 제·개정을 심의·의결한다. ② 위원회의 대표는 사외이사가 아니라 준법감시인이 맡아야 한다. ③ 준법감시인은 내부통제기준 준수 여부를 점검한다. ④ 위원회 위원 과반수는 사외이사여야 한다.", "L201"),
        ("S3C1T13-CORE", "③", "자본시장법의 제재상한을 틀리게 쓴 것은? ① 금융투자업자의 업무정지는 6개월 이내다. ② 법정 사유에 따라 시정·중지명령을 할 수 있다. ③ 임원의 직무정지는 1년 이내다. ④ 직원 정직은 6개월 이내 조치를 회사에 요구할 수 있다.", "L203"),
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
            "review_note": "원문의 발문·선지·해설과 현행 공식 규정의 범위를 확인했다. 이 정제 문항의 답에만 적용하며 모든 윤리의무를 곧바로 법적 제재와 동일시하지 않는다.",
        }
    (ROOT / "item_releases.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Recorded {len(reviewed)} ethics questions and {len(additions)} corrections.")


if __name__ == "__main__":
    main()
