"""Connect individually documented TARGET holds to verified learning examples."""

import hashlib
import json
import math
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build() -> None:
    """Write a preparation artifact; never release or grade a held question."""
    inventory = read(BASE / "s3_remediation_inventory.json")["items"]
    focused_findings = {row["id"]: row for row in read(BASE / "s3_focused_followup_findings.json")["items"]}
    packets = {row["id"]: row for row in read(ROOT / "preparation/eval/answer_packets.json")["items"]}
    releases = read(BASE / "item_releases.json")["items"]
    unresolved_audit = set()
    for audit_path in BASE.glob("*correspondence*audit*.json"):
        audit = read(audit_path)
        rows = audit.get("items", []) if isinstance(audit, dict) else audit
        for row in rows:
            if isinstance(row, dict) and row.get("status", row.get("audit_status")) not in ("resolved", "verified", "approved"):
                unresolved_audit.add(row.get("id"))
    concepts = {
        "S3C1": "윤리상 의무의 내용과 교재의 이해관계자별 분류, 법적 책임 성립요건을 구별한다.",
        "S3C2": "규제 주체·행위·대상·예외·시행시점을 먼저 고정하고 조문상의 조치와 절차를 나눈다.",
        "S3C3": "발행·인수·청약의 참여자와 단계별 의무를 구분하고 공동주관과 공동평가를 혼동하지 않는다.",
        "S3C4": "벤치마크·위험척도·운용제약을 고정한 뒤 자산배분과 보험전략의 조건부 결과를 비교한다.",
        "S3C5": "채권의 발행주체·만기·이자방식·거래시장을 나누고 시장의 비중은 날짜와 분모를 확인한다.",
        "S3C6": "계약 현금흐름과 권리·의무에서 출발해 가격식·헤지방향·민감도와 예외조건을 도출한다.",
        "S3C7": "성과비율의 분모가 총위험·베타·하방위험 중 무엇인지 고정하고 서로 다른 순위를 허용한다.",
        "S3C8": "지표 정의·회계항등식과 인과모형·경험적 예측력을 구분하고 비교정태의 고정조건을 밝힌다.",
        "S3C9": "분산·공분산과 위험분해를 식으로 확인하고 추정치의 적용범위를 분리한다.",
    }
    demonstrations = {}

    def demonstration(ids: list[str], title: str, assumptions: str, reasoning: str, memory: str, numbers: dict) -> None:
        for item_id in ids:
            demonstrations[item_id] = {"title": title, "assumptions": assumptions, "reasoning": reasoning,
                "memory_core": memory, "computed_values": numbers,
                "result": "보편명제의 반례 확정; 원문 전체의 단일정답 승인은 별개로 보류"}

    carry = 100 * math.exp(0.05)
    demonstration(["S3C6T07-CORE", "S3C6-ADD-05", "NOTE-S3C6-Q014"],
        "콘탱고와 현물매수·선물매도 차익거래는 조건이 다르다",
        "현물100, 연속복리금리5%, 배당0, 만기1년, 거래비용0, 공매도·차입 가능",
        "선물102는 현물100보다 높지만 공정선물105.127보다 낮다. 100 차입해 현물을 사고 선물102에 매도하면 만기에 102-105.127=-3.127이다. 콘탱고만으로 매수차익이 생기지 않는다.",
        "현물과 비교하면 시장형태, 보유비용 반영 공정가격과 비교하면 차익거래 방향.",
        {"spot": 100, "futures": 102, "fair_futures": carry, "cash_carry_profit": 102-carry})
    demonstration(["MOCK-2-Q072"], "총위험의 순위로 추적오차의 순위를 정할 수 없다",
        "벤치마크 표준편차20%, A 표준편차30%·상관1, B 표준편차15%·상관0",
        "TE²=σp²+σb²-2ρσpσb. A의 TE=10%, B의 TE=25%이다. 총위험 A>B여도 추적오차 A<B이다.",
        "추적오차는 수익률 차이의 표준편차; 두 분산뿐 아니라 공분산이 필요하다.",
        {"sigma_a": .3, "sigma_b": .15, "benchmark_sigma": .2, "te_a": .1, "te_b": .25})
    demonstration(["MOCK-2-Q091"], "샤프와 트레이너의 순위가 반대일 수 있다",
        "A 초과수익10%·총위험30%·베타2, B 초과수익5%·총위험20%·베타0.5; 시장표준편차10%이면 두 잔차분산도 비음수가 된다",
        "샤프 A=0.333>B=0.25, 트레이너 A=0.05<B=0.10. 위험척도가 다르므로 역전은 모순이 아니다.",
        "샤프는 σ, 트레이너는 β. 한 순위가 다른 순위를 결정하지 않는다.",
        {"sharpe_a": .1/.3, "sharpe_b": .05/.2, "treynor_a": .1/2, "treynor_b": .05/.5})
    demonstration(["S3C4-ADD-01", "S3C4T04-CORE", "NOTE-S3C4-Q006"],
        "완전히 중복된 자산을 더해도 분산효과는 늘지 않는다",
        "두 자산의 모든 상태별 수익이 동일하고 표준편차20%, 상관계수1, 각50% 투자",
        "분산=.5²·.2²+.5²·.2²+2·.5·.5·1·.2·.2=.04. 기존 한 자산과 똑같이 표준편차20%다. 자산 수 증가만으로 엄격한 위험감소를 보장하지 못한다.",
        "분산투자는 개수가 아니라 공분산과 비중에 달린다.", {"before_sigma": .2, "after_sigma": math.sqrt(.04)})
    normal = lambda x: (1 + math.erf(x / math.sqrt(2))) / 2
    d1 = (.05+.2**2/2)/.2
    demonstration(["S3C6T19-SUP-04", "MOCK-2-Q087"], "현물과 행사가가 같아도 콜 델타는 정확히 0.5가 아니다",
        "유럽형 콜, 블랙숄즈, S=K=100, r=5%, q=0, σ=20%, T=1",
        "d1=[ln(S/K)+(r-q+σ²/2)T]/(σ√T)=0.35, Δ=N(0.35)=0.63683. ATM이라는 말만으로 정확히0.5를 주장할 수 없다.",
        "ATM 델타0.5는 근사; 정확한 델타는 d1과 배당할인으로 계산한다.", {"d1": d1, "call_delta": normal(d1)})
    demonstration(["S3C4T11-CORE", "S3C4T11-SUP-02", "NOTE-S3C4-Q023"],
        "변동성이 커질 때 콜 델타의 방향은 상태에 따라 바뀐다",
        "블랙숄즈, K=100, r=q=0, T=1; 동일한 델타 단위 노출 비교, 고정예산의 옵션 개수 조정 효과는 별도",
        "∂d1/∂σ=-ln(S/K)/σ²+1/2. S=120이면 σ0.2→0.3에서 콜델타가 감소하고 S=80이면 증가한다. 따라서 변동성과대평가→언제나 위험자산과소편입이라는 일반화는 성립하지 않는다.",
        "옵션 가격의 베가는 양수여도 델타의 변동성 민감도는 부호가 고정되지 않는다.",
        {"s120_delta_sigma02": normal(math.log(1.2)/.2+.1), "s120_delta_sigma03": normal(math.log(1.2)/.3+.15),
         "s80_delta_sigma02": normal(math.log(.8)/.2+.1), "s80_delta_sigma03": normal(math.log(.8)/.3+.15)})
    maturity = 20/365
    sigma = .2
    gamma_strike = 100 * math.exp(.5 * sigma**2 * maturity)
    gamma_peak = 1 / (math.sqrt(2*math.pi)*100*sigma*math.sqrt(maturity))
    gamma_atm = gamma_peak * math.exp(-.5*(.5*sigma*math.sqrt(maturity))**2)
    demonstration(["MOCK-1-Q087"], "행사가별 감마의 엄밀한 최대점은 현물 ATM과 조금 다를 수 있다",
        "블랙숄즈, S=100, r=q=0, σ=20%, T=20/365년; 같은 만기·변동성에서 행사가만 변화",
        "Γ=φ(d1)/(Sσ√T)는 d1=0일 때 최대다. 이때 K=S exp(σ²T/2)=100.10965로 현물100과 다르다. ATM 근사가 실무상 유용해도 엄밀한 최대라는 단정과 구별한다.",
        "감마 최대는 d1=0. ATM 근사와 정확한 극값을 구분한다.",
        {"maximum_gamma_strike": gamma_strike, "maximum_gamma": gamma_peak, "atm_gamma": gamma_atm})
    s, k, r, vol, t = 50, 100, .05, .2, 1
    put_d1 = (math.log(s/k)+(r+vol**2/2)*t)/(vol*math.sqrt(t))
    put_d2 = put_d1-vol*math.sqrt(t)
    put_theta = -s*math.exp(-put_d1**2/2)/math.sqrt(2*math.pi)*vol/(2*math.sqrt(t))+r*k*math.exp(-r*t)*normal(-put_d2)
    demonstration(["S3C6T19-SUP-03"], "깊은 내가격 유럽형 풋의 세타는 양수일 수 있다",
        "블랙숄즈, 시간경과에 대한 달력시간 세타, 유럽형 풋 S50 K100 r5% q0 σ20% 잔존1년",
        "Θput=-Sφ(d1)σ/(2√T)+rK exp(-rT)N(-d2)=약4.738. 세타가 언제나 음수라는 주장은 반례로 기각된다. PDE는 Θ+(σ²S²/2)Γ+(r-q)SΔ-rV=0이며 감마와 세타의 단순합이 일정하다는 뜻이 아니다.",
        "시간가치 감소라는 직관만으로 풋 세타 부호를 확정하지 말고 이자효과까지 본다.",
        {"d1": put_d1, "d2": put_d2, "put_calendar_theta": put_theta})
    items = []
    for hold in inventory:
        packet = packets[hold["id"]]
        topic_ids = set(packet["topic_ids"])
        candidates = []
        for item_id, release in releases.items():
            if item_id not in packets or item_id in unresolved_audit or release.get("state") != "adjudicated_current":
                continue
            overlap = topic_ids.intersection(packets[item_id]["topic_ids"])
            if overlap:
                candidates.append((len(overlap), item_id, release, sorted(overlap)))
        candidates.sort(key=lambda row: (-row[0], row[1]))
        examples = [{"id": key, "shared_topic_ids": overlap, "prompt": release["clean_prompt"],
                     "answer": release["answer"], "explanation": release["review_note"], "evidence": release["evidence"],
                     "release_sha256": hashlib.sha256(json.dumps(release, ensure_ascii=False, sort_keys=True).encode()).hexdigest()}
                    for _, key, release, overlap in candidates[:2]]
        demo = demonstrations.get(hold["id"])
        items.append({
            "id": hold["id"], "chapter_id": packet["chapter_id"], "topic_ids": packet["topic_ids"],
            "source": {key: packet.get(key) for key in ["document", "question_page", "source_pages", "demand", "question_text", "publisher_answer", "explanation_text"]},
            "hold_reason": hold["reason"], "evidence_checked": hold.get("evidence_checked", []), "hold_file": hold["hold_file"],
            "connected_concept": concepts[packet["chapter_id"]],
            "why_publisher_answer_not_automatically_valid": hold["reason"],
            "specific_evidence_needed": {"unresolved_proposition": hold["reason"],
                "acceptance_test": "해당 원문 모든 보기의 참거짓을 같은 기준일·대상·모형에서 대조하고 단일 출판정답이 유지되는지 확인한다. 교정하면 원문과 바뀐 어구·이유를 함께 남긴다.",
                "not_sufficient": "관련 개념 하나의 참, 같은 장의 승인, 출판정답 번호, 방법 이름만으로 전체 문항을 승인하지 않는다."},
            "study_method": {"primary_branch": "자료충돌", "secondary_branch": "조건대비" if demo else "절차" if packet["chapter_id"] in ["S3C1", "S3C2", "S3C3"] else "회상",
                "policy": "E10/R22/R24; 조건대비는 E12/R13/R15/R29", "flow": "resolve → calibrate → quality_gate(원문 채점보류) → 검증된 예제 teach → 독립 check 대기",
                "teach": demo or {"worked_example": examples[0] if examples else None, "boundary": hold["reason"]},
                "memory_core": demo["memory_core"] if demo else "원문 요구: " + packet["demand"] + " / 결론을 암기하기 전 확인할 경계: " + hold["reason"],
                "check_instruction": "검증된 예제의 답을 가리고 먼저 대상·조건과 결론을 회상한 뒤 근거와 비교한다. 보류 원문은 정오 채점에 사용하지 않는다.",
                "learner_response_observed": False, "delivery_status": "학습자료 준비; 사용자 응답·지연회상·전이 정확도 미측정"},
            "verified_related_item_ids": [row["id"] for row in examples], "verified_learning_examples": examples,
            "related_example_limit": "동일 topic_ids 교집합만 연결; 예제의 승인이 보류 원문을 승인한다는 뜻은 아님" if examples else "동일 주제 승인 예제 없음; 인접 장 문항으로 임의 대체하지 않음",
            "independent_demonstration": demo,
            "reevaluation": {"current_state": "held", "conflict_analysis": "수치 반례 직접 계산 완료" if demo else "개별 기존 근거 및 보류원인 연결 완료; 추가 1차근거 대기",
                "trigger": "누락 직접근거 확보 또는 원문 전보기 보존한 최소교정 확정", "then": "새 근거·교정본으로 전체 보기를 재심사하고 이전 응답이 있으면 재채점한다. 지연회상·변형문제는 별도로 평가한다.",
                "release_changed": False}
        })
        item = items[-1]
        if hold["id"] in focused_findings:
            finding = focused_findings[hold["id"]]
            item["focused_followup"] = finding
            item["specific_evidence_needed"]["after_followup"] = finding["remaining_evidence"]
        item.update({"status": "held", "reason": hold["reason"],
                     "concept_explanation": demo["reasoning"] if demo else (examples[0]["explanation"] if examples else concepts[packet["chapter_id"]]),
                     "condition_contrast": demo["assumptions"] if demo else hold["reason"],
                     "memory_targets": [item["study_method"]["memory_core"]],
                     "verified_example_ids": item["verified_related_item_ids"],
                     "next_check": item["study_method"]["check_instruction"],
                     "resume_condition": item["reevaluation"]["trigger"]})
        if hold["id"] == "S3C2T13-SUP-02":
            item["additional_review"] = {
                "completed": "현행 법 제446조 전체64호와 443~449조의 제72조 참조 여부, 420·422조, 금융투자업규정4-21조를 재대조했다. 446조55호의 신용공여 벌칙은 342·345조 등의 다른 업종·행위에 관한 것이며 제72조 위반과 같지 않다.",
                "choice_3": "인수대상 회사의 증권 전부가 아니라 그 인수증권을 매수하게 하기 위한 해당 투자자 신용공여가 금지된다.",
                "choice_4": "제72조 위반 자체를 446조의 1년·3천만원 범죄로 열거하지 않는다. 다른 범죄 성립이나 제재명령 위반까지 면책한다는 의미는 아니다.",
                "remaining": "원문① 고유업무/예외허용이라는 업무분류까지 직접근거를 대조하고, ② 현행 증권담보융자 용어 및③ 대상범위의 최소교정을 함께 검토해야 하므로 전체승인 미실행.",
                "official_url": "https://law.go.kr/LSW/lsInfoP.do?ancYnChk=0&chrClsCd=010202&efYd=20261002&lsiSeq=288615&urlMode=lsInfoP",
                "article_refs": ["capital:제72조", "capital:제420조", "capital:제422조", "capital:제443조", "capital:제444조", "capital:제445조", "capital:제446조", "capital:제447조", "capital:제448조", "capital:제449조", "financial_investment_rule:제4-21조"]}
        if hold["id"] in {"S3C5T01-SUP-02", "MOCK-2-Q055", "S3C6T18-SUP-01"}:
            from subject3_reviews import REVIEWS

            review = next(row for row in REVIEWS if row["id"] == hold["id"])
            item["status"] = "resolved_pending_integration"
            item["reason"] = review["source_finding"]
            item["concept_explanation"] = review["review_note"]
            item["resolution"] = {"review": review, "new_claim_ids": review["claim_ids"], "original_hold_reason": hold["reason"], "official_http_complete": True}
            item["reevaluation"].update({"current_state": "resolved_pending_integration", "conflict_analysis": review["review_note"], "trigger": "루트 통합빌드·원문대응·근거게이트 통과 후 승인상태 확정"})
            item["resume_condition"] = item["reevaluation"]["trigger"]
            item["study_method"]["teach"] = {"worked_example": review["clean_prompt"], "answer": review["answer"], "explanation": review["review_note"]}
            item["memory_targets"] = ["국민주택1종=국채·5년·연단위복리·발행분별고정이율. 5년을중기로보는것은교재분류." if hold["id"] == "S3C5T01-SUP-02" else "회원제명=협회총회. 검사=금감원장. 조치명령·임원해임요구·직원면직요구=금융위. 직접면직과면직요구를구분."]
            item["study_method"]["memory_core"] = item["memory_targets"][0]
            if hold["id"] == "S3C6T18-SUP-01":
                item["memory_targets"] = ["스마일은중앙ATM저점·양끝고점.콜ITM→ATM→OTM이면하락후상승.1987전후S&P500역사와현재모든상품의곡선을혼동하지않는다."]
                item["study_method"]["memory_core"] = item["memory_targets"][0]
    output = {"as_of": "2026-10-14", "api_calls": 0, "kind": "item_specific_remediation_preparation", "count": len(items),
              "numerical_counterexample_count": len(demonstrations), "original_items_released": 0, "resolved_pending_integration": 3,
              "policy_sources": ["preparation/eval/study_method_policy.json", "preparation/target_analysis/study_assistant_flow.json"], "items": items}
    path = BASE / "s3_learning_remediation.json"
    if path.exists():
        prior = path.read_bytes()
        (BASE / ("s3_learning_remediation_history_" + hashlib.sha256(prior).hexdigest()[:12] + ".json")).write_bytes(prior)
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"count": len(items), "counterexamples": len(demonstrations), "with_related_examples": sum(bool(row["verified_related_item_ids"]) for row in items)}))


if __name__ == "__main__":
    build()
