"""Compile traceable EVAL contracts, demonstrations, and a local reading report."""

import csv
import hashlib
import html
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

from build_benchmarks import main as build_benchmarks
from evaluator import evaluate_exam

ROOT = Path(__file__).resolve().parent
PREP = ROOT.parent
TARGET = PREP / "target_analysis"
WORKSPACE = PREP.parent


def read(path: Path) -> Any:
    """Read UTF-8 JSON."""
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    """Write stable readable JSON."""
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def numeric_case(
    cid: str, source: str, prompt: str, value: str, units: dict[str, str],
    tolerance: str, atoms: list[tuple[str, str]], explanation: str,
    contrast: str, next_prompt: str, next_answer: str,
) -> dict[str, Any]:
    """Define a manually written, independently recalculable diagnostic case."""
    return {
        "id": cid, "source_question_ids": [source], "origin": "reviewer_authored_clean_restatement_or_variant",
        "prompt": prompt, "prompt_reviewed": True, "response_format": "수치와 단위를 별도 입력",
        "answer": {"type": "numeric", "value": value, "accepted_units": units, "absolute_tolerance": tolerance},
        "release": {
            "state": "adjudicated_under_explicit_assumptions",
            "reason": "명시 조건에서 독립 산술 검증",
            "evidence": explanation,
        },
        "criteria": [
            {"id": f"{cid}-{i:02}", "dimension": dimension, "required_relation": atom,
             "critical": dimension in {"conditions", "procedure"}, "evidence": explanation}
            for i, (dimension, atom) in enumerate(atoms, 1)
        ],
        "repair": {
            "actual_explanation": explanation, "contrast": contrast,
            "memory_card": "공식 이름만 외우지 말고, 이 사례에서 조건→분모·시점→출력의 연결을 회상한다.",
            "next_probe": {"prompt": next_prompt, "withheld_answer": next_answer},
            "sequence": "비서가 설명과 대비를 제공→한 단계 확인→답을 숨긴 확인→노출 시각을 기록한 지연 확인",
        },
    }


def calibration_cases() -> list[dict[str, Any]]:
    """Return reviewed examples that cover distinct explanation and scoring failures."""
    cases = [
        numeric_case(
            "E01", "CALC-05",
            "최초 투자액은1,000원, 임대수입의 현재가치는300원, 미래 매각대금은1,250원이다. "
            "매각대금의 현재가치계수는0.8이다. 수익성지수PI를 구하라.",
            "1.3", {"ratio": "1", "배": "1"}, "0.000001",
            [("conditions", "300원은 이미 현재가치이므로 다시 할인하지 않는다."),
             ("procedure", "매각 현가1,000과 임대 현가300을 합해 투자액1,000으로 나눈다.")],
            "PI는 오늘 내는 돈1원에 대해 들어올 돈의 현재가치가 얼마인지를 비교한다. "
            "300원은 이미 오늘 가치이고 매각대금만1,250×0.8=1,000원으로 바꾼다. "
            "따라서(300+1,000)/1,000=1.3이다.",
            "(300+1,250)×0.8/1,000=1.24는 임대 현가를 두 번 할인한 오류다.",
            "투자액500원, 임대 현가100원, 매각대금600원, 현재가치계수0.75일 때PI는?", "1.1",
        ),
        numeric_case(
            "E02", "CALC-14",
            "판매량이200에서400으로, 영업이익이10에서50으로 증가했다. "
            "이 구간의 영업레버리지도DOL을 변화율의 비로 구하라.",
            "4", {"ratio": "1", "배": "1"}, "0.000001",
            [("procedure", "영업이익 변화율(50-10)/10과 판매량 변화율(400-200)/200을 나눈다."),
             ("numeric_execution", "400%/100%=4이며 증가량40/200이 아니다.")],
            "민감도는 단위가 다른 증가량을 직접 비교하지 않는다. 영업이익은 처음10의4배만큼 늘었고 "
            "판매량은 처음200의1배만큼 늘었다. 비율끼리 비교하면4/1=4다.",
            "40/200=0.2는 이익과 판매량의 단위가 섞인다.",
            "판매량100→120, 영업이익20→28이면 변화율 기준DOL은?", "2",
        ),
        numeric_case(
            "E03", "CALC-21",
            "시장점유율이 같은5개 기업의 HHI를 구하라. 0~1 척도 또는0~10,000 척도를 단위로 명시하라.",
            "0.2", {"0_to_1": "1", "0_to_10000": "0.0001"}, "0.000001",
            [("procedure", "각 점유율을 제곱해서 합한다."),
             ("numeric_execution", "5×0.2²=0.2와5×20²=2,000의 척도를 구별한다.")],
            "HHI는 큰 기업의 비중을 더 크게 반영하려고 각 점유율을 제곱한 뒤 더한다. "
            "점유율20%를0.2로 쓰면5×0.04=0.2다. 20으로 쓰면5×400=2,000이다. "
            "두 값은 척도만 다르므로 단위까지 보고 채점한다.",
            "0.2와2,000을 단위 없이 비교하면 같은 집중도를 다른 답으로 오판한다.",
            "동일 점유율10개 기업의 HHI를0~1척도로 구하라.", "0.1",
        ),
        numeric_case(
            "E04", "CALC-32",
            "현재 자산110억원, 1년 뒤 보호할 금액100억원, 1년 무위험수익률2%, "
            "CPPI 승수3이다. 현재 위험자산 투자액을 구하라. 중간 반올림을 하지 말고 억원 단위로 답하라.",
            str(3 * (110 - 100 / 1.02)), {"억원": "1", "원": "0.00000001"}, "0.00001",
            [("conditions", "만기 보호금액100을 현재Floor100/1.02로 할인한다."),
             ("procedure", "현재 자산에서 현재Floor를 뺀 쿠션에 승수3을 곱한다.")],
            "만기에100억원을 만들려면 오늘은100/1.02≈98.039216억원이면 된다. "
            "현재 쿠션은110-98.039216≈11.960784억원이다. 교재의 CPPI 규칙에 따라 "
            "위험투자액은 쿠션의3배, 약35.882353억원이다. 이 계산이 모든 시장에서 원금 보장을 뜻하지는 않는다.",
            "(110-100)×3=30은 오늘 자산과 미래Floor를 섞었다.",
            "현재 자산100억원, 만기Floor90억원, 금리0%, 승수2일 때 위험투자액은?", "20억원",
        ),
        numeric_case(
            "E05", "CALC-63-1",
            "X 표준편차0.1, Y 표준편차0.2, 상관계수0이다. 두 자산의 합계비중은1이다. "
            "최소분산 포트폴리오의 X비중을 구하라.",
            "0.8", {"ratio": "1", "%": "0.01"}, "0.000001",
            [("conditions", "상관0으로 공분산항이 사라지지만 각 자산 분산은 남는다."),
             ("procedure", "X비중의 분자는Y분산이며0.04/(0.01+0.04)=0.8이다.")],
            "X가 덜 흔들리므로 최소분산 조합에서는X비중이 더 높다. "
            "V(w)=0.01w²+0.04(1-w)²를 최소화하면0.02w-0.08(1-w)=0, w=0.8이다. "
            "교재 첫줄60%와 달리 뒤의 계산과 정답은80%다.",
            "표준편차0.2를 분산0.04 대신 쓰거나 X·Y분자를 바꾸면 다른 비중이 나온다.",
            "상관0이고 두 표준편차가 모두0.2이면X비중은?", "0.5",
        ),
        numeric_case(
            "E06", "CALC-67-1",
            "무위험수익률2%, 시장 기대수익률6%, 시장 표준편차0.4, "
            "주식과 시장 수익률의 공분산0.20이다. CAPM의 요구수익률을 구하라.",
            "0.07", {"ratio": "1", "%": "0.01"}, "0.000001",
            [("procedure", "β분모는 시장분산0.4²이며β=1.25이다."),
             ("conditions", "시장수익률6% 전체가 아니라 위험프리미엄6%-2%에β를 곱한다.")],
            "베타는 시장과 함께 움직이는 정도인 공분산을 시장 자체의 분산으로 나눈다. "
            "따라서0.20/0.16=1.25다. 기본 보상2%에 시장 위험보상4%의1.25배를 더하면7%다.",
            "0.20/0.4는 표준편차를 분모로 잘못 썼다. 2%+1.25×6%도 시장프리미엄을 혼동했다.",
            "무위험2%, 시장6%, 베타0.5이면 요구수익률은?", "4%",
        ),
        numeric_case(
            "E07", "CALC-59",
            "취업자20명, 실업자5명, 비경제활동인구25명이다. 실업률을 구하라.",
            "0.2", {"ratio": "1", "%": "0.01"}, "0.000001",
            [("conditions", "실업률 분모는 경제활동인구20+5이다."),
             ("concept_reason", "비경제활동인구25명을 실업률 분모에 넣지 않는다.")],
            "실업률은 일하고 있거나 일을 구하는 사람 중 실업자의 비중이다. "
            "경제활동인구는20+5=25명이고 그중5명이 실업자이므로5/25=20%다. "
            "50명을 분모로 쓰는 경제활동참가율은25/50=50%로 다른 질문이다.",
            "5/50=10%는 생산가능인구 대비 실업자 비율이지 여기서 묻는 실업률이 아니다.",
            "취업자18명, 실업자2명, 비경제활동인구30명이면 실업률은?", "10%",
        ),
        numeric_case(
            "E08", "CALC-60",
            "BSI 조사100명 중 호전40명, 악화30명, 변화없음30명이다. "
            "100+(호전-악화)/전체×100 방식의 BSI를 구하라.",
            "110", {"index": "1", "지수": "1"}, "0",
            [("conditions", "중립 응답이 있으므로 호전비중×200 약식을 사용하지 않는다."),
             ("procedure", "100+(40-30)/100×100=110으로 계산한다.")],
            "BSI는 긍정과 부정이 같을 때100이다. 여기서는 호전이 악화보다10명 더 많고 "
            "전체100명의10%에 해당하므로 기준100에10을 더해110이다. "
            "변화없음30명도 전체응답자 분모에는 들어간다.",
            "40/100×200=80은 중립 응답이 없는 교재 예시의 약식을 잘못 확장했다.",
            "전체100명 중 호전30명, 악화30명, 중립40명이면BSI는?", "100",
        ),
        numeric_case(
            "E09", "MOCK-2-Q089",
            "월간 펀드수익률12%, 무위험수익률2%, 표준편차20%이다. "
            "수익률은12배, 표준편차는√12배로 연율화한다는 가정에서 연간 샤프비율을 구하라. 중간 반올림 금지.",
            str(0.5 * 12 ** 0.5), {"ratio": "1"}, "0.00001",
            [("conditions", "월간 초과수익률과 월간 표준편차의 기간을 일치시킨다."),
             ("numeric_execution", "0.5×√12≈1.7320508로 마지막에 반올림한다.")],
            "월간 초과수익률은12%-2%=10%, 월간 샤프는10%/20%=0.5다. "
            "명시한 연율화에서는 분자가12배, 분모가√12배여서 전체는√12배, 약1.732051이다. "
            "교재의1.74는 분모를0.69로 먼저 반올림해서 생긴 차이다.",
            "연율화 가정은 수익률 자기상관 등 실제 조건과 따로 검토해야 한다.",
            "같은 연율화 가정에서 월간 샤프가1이면 연간 샤프는?", "sqrt(12)≈3.464102",
        ),
    ]
    for case in cases:
        case["response_format"] = "수치와 단위를 별도 필드로 입력. 이해 진단 모드에서는 풀이를 별도로 받는다."
        case["release"]["reason"] = "명시한 조건에서 직접 재계산한 수치·관계. 실제 법령이나 투자 권고가 아니다."
    cases.append({
        "id": "E10", "source_question_ids": ["S3C9T06-CORE"],
        "origin": "source_conflict_control", "prompt_reviewed": True,
        "prompt": "출판사 정답④와 별개로③의 '베타=최적 위험보상비율'도 부적절하다는 이의가 있다. "
                  "이 원문 문항의 단일 정답을 학습자 자동 채점에 사용할 수 있는가?",
        "response_format": "비서 품질 진단용. 채점 보류 사유를 서술한다.",
        "answer": {"type": "choice", "value": "④"},
        "release": {"state": "conflicting_or_ambiguous", "reason": "단일정답 전제가 해결되지 않았다.",
                    "evidence": "P3 PDF452; review_log.json S3C9"},
        "criteria": [{"id": "E10-01", "dimension": "source_issue", "critical": True,
                      "required_relation": "출판사 의도와 검증된 단일정답을 구별하고 학습자 점수 판정을 보류한다."}],
        "repair": {"actual_explanation": "베타는 시장수익률 변화에 대한 민감도다. 위험보상비율과 동일하지 않다.",
                   "next_probe": {"prompt": "공분산0.02, 시장분산0.01이면베타는?", "withheld_answer": "2"}},
    })
    choice = json.loads(json.dumps(cases[4], ensure_ascii=False))
    choice.update({
        "id": "E11",
        "prompt": cases[4]["prompt"] + " ①0.2 ②0.4 ③0.6 ④0.8",
        "response_format": "선택지 번호 하나",
        "answer": {"type": "choice", "value": "④"},
        "criteria": [{"id": "E11-01", "dimension": "exam_answer",
                      "required_relation": "④를 선택한다. 이유 미제출은 이해 미관측이며 시험점수 감점이 아니다."}],
    })
    cases.append(choice)
    cases.append(numeric_case(
        "E12", "CALC-43-2",
        "개시증거금120억원, 유지증거금80억원, 일일정산 후 잔액90억원이다. "
        "잔액이 유지증거금 미만일 때만 개시증거금까지 보충하는 규칙이다. 추가 납부액은?",
        "0", {"억원": "1", "원": "0.00000001"}, "0",
        [("conditions", "90이80보다 작지 않으므로 마진콜 조건이 성립하지 않는다."),
         ("procedure", "조건이 거짓이면 개시액과 차이30을 계산해 납부시키지 않는다.")],
        "개시증거금은 처음 맡기는 기준이고 유지증거금은 추가 납부가 발생하는 문턱이다. "
        "현재90은 유지80보다 높아 문턱을 넘지 않았다. 따라서 추가 납부는0이다. "
        "개시120과의 차이30은 마진콜이 발생한 경우에만 보충액이 될 수 있다.",
        "개시액에 못 미치면 항상 보충한다고 생각하면30억원을 잘못 납부시킨다.",
        "같은 개시120·유지80에서 잔액이70이면 추가 납부액은?", "50억원",
    ))
    return cases


def make_grounding(spec: dict[str, Any]) -> dict[str, Any]:
    """Bind every operational rule to provenance and explicit EVAL use."""
    rules = read(PREP / "operational_rules.json")["rules"]
    uses = {}
    for section in ["dimensions", "assistant_rubric"]:
        for entry in spec[section]:
            for rid in entry["rules"]:
                uses.setdefault(rid, []).append(f"{section}:{entry['id']}")
    manifest = {x["id"]: x for x in read(PREP / "source_manifest.json")}
    fresh = [
        ("ciMdEAqKH7M", 43, 68, "시험 형식에 맞는 출력; 모든 모드에 긴 설명을 강제하지 않음"),
        ("ciMdEAqKH7M", 116, 142, "답 번호와 이유를 구별; 해설 학습 후 시간 간격을 둔 연습"),
        ("vluEPc2lXaI", 1, 79, "목표에 필요한 기억 수준; 완벽주의를 합격 조건으로 만들지 않음"),
        ("fy0SHDX1Uxk", 97, 124, "인풋·연습·훈련의 오류별 복귀"),
        ("lAdUmpA2I14", 292, 330, "완성 풀이의 각 단계와 공식 이유"),
        ("lAdUmpA2I14", 374, 405, "틀린 선지의 부분과 바른 조건을 연결"),
        ("lAdUmpA2I14", 451, 500, "학습에서는 다른 선지 이유도 확인; 정답을 알고 경로를 학습하는 단계 분리"),
        ("g4QlY3eZP3M", 141, 200, "목차의 전체 구조와 필요한 선행 설명"),
        ("SqOrTT_sJ0E", 1, 126, "일반 원리와 구체 사례의 결정적 조건 구별"),
    ]
    return {
        "source_base": "../full_reread_01.json",
        "scope": "42개 물리 TXT·41개 고유 영상·316개 구간·31개 규칙의 기존 전수 검토를 계승. 이번 EVAL에서 핵심 구간을 재대조.",
        "read_count_claim": "10회 정독 완료라고 주장하지 않는다.",
        "interpretation_boundary": "기억·이해 상태명과 채점 코드·70/40 합격 목표 연결은 설계 확장이다. SRC의 과학적 주장도 실증 검증된 사실로 승격하지 않는다.",
        "rules": [{"id": r["id"], "name": r["name"], "evidence": r["evidence"],
                   "eval_bindings": uses.get(r["id"], []), "source_limits": r.get("limits", [])} for r in rules],
        "fresh_close_reading": [
            {"source_id": vid, "path": manifest[vid]["path"], "lines": [a, b], "eval_interpretation": point}
            for vid, a, b, point in fresh
        ],
    }


def integrate_existing() -> None:
    """Persist EVAL bindings without replacing prior evidence or user edits."""
    refs = {
        "specification": "preparation/eval/eval_spec.json", "exam_goal": "preparation/eval/exam_goal.json",
        "item_contracts": "preparation/eval/item_contracts.json", "topic_rubrics": "preparation/eval/topic_rubrics.json",
        "report": "preparation/eval/eval_report.html", "executable": "preparation/eval/evaluator.py",
        "semantic_grader": "preparation/eval/semantic_grader.py",
        "assistant_grader": "preparation/eval/assistant_grader.py",
        "verification": "preparation/verification_20261013/verification_summary.json",
        "current_claims": "preparation/verification_20261013/verified_claims.json",
        "item_releases": "preparation/verification_20261013/item_releases.json",
    }
    flow_path = TARGET / "study_assistant_flow.json"
    flow = read(flow_path)
    flow["evaluation"] = {
        "artifacts_from_workspace": refs, "target": ["learner", "assistant"],
        "pass_rule": "overall>=70% AND each_subject>=40%",
        "priority": "과락 위험을 먼저 확인하고 총점 부족분·회복 가능 점수·학습시간을 함께 판단한다.",
        "boundary": "이해 설명은 진단이다. timed_mock에서 설명 미제출을 시험 오답으로 처리하지 않는다.",
        "runtime_scope": "정형 채점·모의점수와 전체 문항용 모델 기반 자연어 채점 모듈 구현. 실제 모델 성능은 API 연결 후 측정하며, 법령·문항별 승인 상태는 verification 산출물에 따른다.",
    }
    for state in flow["algorithm"]:
        if state["state"] == "diagnose":
            state["eval_contract"] = "../eval/item_contracts.json"
            state["mode_policy"] = "실제 응답·도움·노출 시각·평가 모드를 기록하고 시험 정답과 학습 차원을 별도 판정한다."
        elif state["state"] == "calibrate":
            state["exam_goal"] = "../eval/exam_goal.json"
        elif state["state"] == "check":
            state["eval_gate"] = "raw question_text에 답·해설이 섞이므로 검토된 학습자용 문항만 제시한다."
    write(flow_path, flow)
    for filename in ["learning_assistant_blueprint.json", "exam_requirement_contract.json"]:
        obj = read(PREP / filename)
        obj["eval_system"] = refs
        obj["confirmed_exam_goal"] = read(ROOT / "exam_goal.json")
        write(PREP / filename, obj)
    rules = read(PREP / "operational_rules.json")
    rules["eval_system"] = refs
    write(PREP / "operational_rules.json", rules)


def generate_report(
    topics: list[dict[str, Any]], contracts: list[dict[str, Any]],
    spec: dict[str, Any], cases: list[dict[str, Any]], audit: dict[str, Any],
) -> None:
    """Create a navigable local report; instructor materials are explicitly labeled."""
    esc = html.escape
    manifest = {d["id"]: d for d in read(TARGET / "target_manifest.json")["documents"]}

    def pdf_link(doc: str, page: int) -> str:
        path = manifest[doc].get("path", manifest[doc].get("source_path", ""))
        if not path:
            names = {"P12": "1과목_2과목.pdf", "P3": "3과목.pdf", "CALC": "계산문제.pdf",
                     "MOCK": "모의고사.pdf", "NOTE": "핵심정리노트.pdf"}
            path = f"src/target/{names[doc]}"
        resolved = Path(path)
        if resolved.is_absolute():
            path = resolved.relative_to(WORKSPACE).as_posix()
        return f'<a href="../../{quote(path.replace(chr(92), "/"))}#page={page}">{doc} PDF {page}</a>'

    parts = ['''<!doctype html><html lang="ko"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>투자자산운용사 EVAL — 학습자와 학습비서</title>
<style>
body{font:16px/1.75 system-ui,sans-serif;max-width:1100px;margin:auto;padding:24px;background:#f5f7fa;color:#17283a}
header,section,article{background:white;padding:22px;margin:18px 0;border-radius:12px}
h1{font-size:30px}h2{font-size:23px}h3{font-size:19px}a{color:#175dab}
table{border-collapse:collapse;width:100%}th,td{border:1px solid #d9e2ec;padding:8px;text-align:left}
details{border-top:1px solid #d9e2ec;padding:12px 0}summary{cursor:pointer;font-weight:650}
pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px;background:#edf2f7;padding:12px}
.badge{background:#e0f2e9;padding:6px 12px;border-radius:16px}.warn{background:#fff3d6;padding:14px}
input{padding:10px;width:95%;font-size:16px}.muted{color:#53677a}nav a{margin-right:16px}
</style><header><h1>합격을 위한 학습자·학습비서 EVAL</h1>
<p class="badge">전체 70% 이상 ∧ 각 과목 40% 이상</p>
<p>제공 자료를 근거로 무엇을 맞혀야 하는지 정하고, 막힌 이유에 맞춰 비서가 설명·예제·회상·재확인을 준비한다.
이해 평가는 점수 향상을 위한 진단이며 별도의 합격 장벽이 아니다.</p>
<nav><a href="#coverage">검토 범위</a><a href="#pass">합격 판정</a><a href="#learner">학습자</a>
<a href="#assistant">비서</a><a href="#cases">실제 평가 예시</a><a href="#topics">285개 목차</a>
<a href="#items">2,292개 문항</a><a href="#run">실행</a></nav></header>''']
    parts.append(f'''<section id="coverage"><h2>검토 범위와 한계</h2>
<p>5개 PDF · 16개 장 · 285개 주제 · 2,292개 독립 문항의 답·해설 검토.
본문 예제·OX 등 383개 근거 묶음은 기존 전 페이지 검토를 계승하며, 별도 383문항으로 더하지 않는다.</p>
<p>정답표 대조·추출 보완 {audit["counts"]["override_records"]}문항
(해설 수동 복원 {audit["counts"]["manual_rationale_recoveries"]}건). <a href="review_log.json">장별 검토 기록</a>,
<a href="source_grounding.json">SRC 근거와 설계 구분</a>, <a href="coverage_audit.json">연결 검사</a>,
<a href="../target_analysis/analysis_report.html">원본 목차 분석</a>.</p>
<p><a href="../verification_20261013/verification_report.html">2026-10-13 법령 대조·교재 교정·자연어 채점 진행 현황</a>.
모든 문항에 대한 모델 채점용 근거 연결을 구현했다. 실제 모델 정확도와 문항별 현행 정답 승인은 별도로 검증한다.</p>
<p class="warn">이 보고서는 답·해설이 있는 비서/검토자용이다. 학습자 시험 화면으로 사용하지 않는다.
전체 문항의 독립 정답 검증·최신 법령 전수 검증·자동 자연어 채점 완성을 의미하지 않는다.
교재의 기출 표기는 공식 기출 인증이 아니다. 10회독 완료 또는 실제 합격확률을 주장하지 않는다.</p></section>''')
    parts.append('''<section id="pass"><h2>점수와 다음 공부의 우선순위</h2>
<table><tr><th>구분</th><th>공식 확인 형식</th><th>최소 정답수</th></tr>
<tr><td>전체</td><td>100문항</td><td>70개</td></tr><tr><td>1과목</td><td>20문항</td><td>8개</td></tr>
<tr><td>2과목</td><td>30문항</td><td>12개</td></tr><tr><td>3과목</td><td>50문항</td><td>20개</td></tr></table>
<p>합격선·과락·문항 배분·120분은 2026-10-13 협회 자격시험센터 공식 데이터로 대조했다.
70점·과목40%는 기준을 충족한다. 1과목7/20, 나머지30/30·50/50이면87점이어도 과락이다.</p>
<p>미완료 세트는 합격 판정을 내리지 않는다. 종료한 시험의 미응답은 정답수가 늘지 않는다.
보류 문항은100문항 분모에 남기고 가능한 최소·최대 점수와 판정 보류를 표시한다.
힌트·시간 초과·기존 문항 노출 여부를 함께 보고한다.</p>
<p>과락 미달 과목의 기본 조건·반복 오개념을 우선 복구하고 총점 부족분도 함께 본다.
그다음 실제 오류 이력과 소요시간으로 회복 가능한 점수를 비교한다.
교재 빈도만으로 출제확률이나 임의의 80·90점 안정합격선을 만들지 않는다.</p></section>''')
    parts.append('<section id="learner"><h2>학습자 평가</h2><table><tr><th>관측 대상</th><th>질문</th><th>판정의 한계</th></tr>')
    for dim in spec["dimensions"]:
        parts.append(f'<tr><td>{esc(dim["id"])}</td><td>{esc(dim["question"])}</td><td>{esc(dim["limit"])}</td></tr>')
    parts.append('</table><p>상태: supported / partial / contradicted / not_observed / not_applicable / held.'
                 ' 문체나 글자 수로 이해를 채점하지 않고, 실제 응답 인용과 필수 관계·조건을 대조한다.</p>'
                 '<p>학습에서는 정답을 먼저 보고 풀이 경로를 배울 수 있다. 독립 확인에서는 답을 숨긴다.'
                 ' 과거에 본 문항의 지연 회상은 가능하지만 처음 보는 문제의 전이와 구별한다.</p></section>')
    parts.append('<section id="assistant"><h2>학습비서 평가</h2><table><tr><th>항목</th><th>기준</th><th>중대 항목</th></tr>')
    for item in spec["assistant_rubric"]:
        parts.append(f'<tr><td>{item["id"]}</td><td>{esc(item["test"])}</td><td>{"예" if item["critical"] else "아니오"}</td></tr>')
    parts.append('</table><p>오답을 가르침, 출처 왜곡, 답 노출을 독립 수행으로 처리함, 관측하지 않은 숙달 주장은'
                 ' 친절함·표현력 점수로 상쇄하지 않는다. 중대 항목이 미관측이면 검증 완료로 표시하지 않는다.</p>'
                 '<p><a href="assistant_benchmark.json">12개 기준의 좋은/나쁜 출력 24개와 평가자 보정 절차</a> · '
                 '<a href="study_method_policy.json">오류에 맞춘 8개 공부법 선택·설명 제공 분기</a></p></section>')
    parts.append('<section id="cases"><h2>실제 설명·오류·재확인 예시</h2>'
                 '<p>아래는 비서가 실제로 제공할 내용의 시연이다. 원문 정답을 무조건 승인한 예시가 아니다.</p>')
    for case in cases:
        repair = case["repair"]
        parts.append(f'<details id="{case["id"]}"><summary>{case["id"]} · {esc(case["source_question_ids"][0])}</summary>'
                     f'<p>{esc(case["prompt"])}</p><p><b>설명:</b> {esc(repair["actual_explanation"])}</p>')
        if repair.get("contrast"):
            parts.append(f'<p><b>오류 대비:</b> {esc(repair["contrast"])}</p>')
        parts.append(f'<p><b>다음 확인:</b> {esc(repair["next_probe"]["prompt"])}</p>'
                     f'<details><summary>검토자용 다음 답</summary>{esc(repair["next_probe"]["withheld_answer"])}</details></details>')
    parts.append('</section><section id="topics"><h2>목차별 평가 기준</h2>'
                 '<input id="search" placeholder="목차·개념·문항 ID 검색" aria-label="목차 검색">')
    for topic in topics:
        parts.append(f'<details class="topic" id="{topic["id"]}"><summary>{topic["id"]} · {esc(topic["title"])} '
                     f'({len(topic["question_ids"])}개 연결)</summary>')
        for label, key in [("시험이 요구하는 구별", "required_action"), ("이해 확인", "understanding_probe"),
                           ("기억 대상", "recall_targets"), ("주요 혼동", "counterexample_focus"),
                           ("비서의 보완", "repair_design")]:
            parts.append(f'<p><b>{label}:</b> {esc(topic[key])}</p>')
        parts.append('<p>근거 문항: ' + ' · '.join(f'<a href="#{qid}">{qid}</a>' for qid in topic["question_ids"]) + '</p></details>')
    parts.append('</section><section id="items"><h2>문항별 정답·해설과 평가 계약</h2>'
                 '<p>출판사 답은 출판사 의도이며, 자동 채점 gold와 분리되어 있다. 원문 위치·검토 주의사항을 먼저 확인한다.</p>')
    for c in contracts:
        parts.append(f'<details id="{c["id"]}"><summary>{c["id"]} · {esc(c["demand"])}</summary>'
                     f'<p>출판사 답: {esc(str(c["publisher_answer"]))} / '
                     + ' · '.join(pdf_link(c["document"], p) for p in c["source_pages"])
                     + f'</p><p>{esc(c["rationale_evidence"])}</p>'
                     + f'<p>주제 기준: ' + ' · '.join(f'<a href="#{tid}">{tid}</a>' for tid in c["topic_ids"])
                     + f'</p><p>정답 상태: {esc(c["gold_status"])}. 페이지 주의사항: {esc(", ".join(c["page_review_candidates"]) or "없음")}</p>'
                     '</details>')
    parts.append('''</section><section id="run"><h2>실행과 검증</h2>
<p>워크스페이스 루트에서 다음 명령을 실행한다. Python 외부 API 호출 없이 동작한다.</p>
<pre>preparation/target_analysis/.venv/Scripts/python.exe preparation/eval/evaluator.py topic --id S3C9T02
preparation/target_analysis/.venv/Scripts/python.exe preparation/eval/evaluator.py prompt --case E05
preparation/target_analysis/.venv/Scripts/python.exe preparation/eval/evaluator.py score --case E05 --response 80 --unit "%"
preparation/target_analysis/.venv/Scripts/python.exe preparation/eval/evaluator.py exam --input preparation/eval/example_exam.json
preparation/target_analysis/.venv/Scripts/python.exe -m pytest preparation/eval/test_evaluator.py -q</pre>
<p><a href="eval_spec.json">평가 명세</a> · <a href="item_contracts.csv">문항 CSV</a> ·
<a href="topic_rubrics.json">주제 기준 JSON</a> · <a href="calibration_cases.json">검증 예시</a> ·
<a href="example_exam_result.json">합격 경계 예시 결과</a> · <a href="test_results.json">코드 검증 결과</a></p>
<p>evaluator.py는 선택·수치·시험점수와 판정 근거 형식을 검사한다.
semantic_grader.py는 모든 원본 문항의 근거를 이용해 실제 모델에 원자 기준 작성과 자연어 판정을 요청하고,
assistant_grader.py는 실제 비서 출력을 12개 기준으로 평가한다. 공급자 설정과 실제 모델 보정 검증이 필요하다.
실제 학습자 데이터에 대한 평가자 일치도·학습효과·합격예측력은 아직 측정하지 않았다.</p></section>
<script>document.getElementById('search').addEventListener('input',e=>{
const q=e.target.value.toLowerCase();document.querySelectorAll('.topic').forEach(x=>{
x.hidden=!x.textContent.toLowerCase().includes(q);});});</script></html>''')
    (ROOT / "eval_report.html").write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    """Build artifacts from completed answer review and existing topic-specific routes."""
    build_benchmarks()
    packets = read(ROOT / "answer_packets.json")["items"]
    routes = read(TARGET / "topic_learning_routes.json")["items"]
    embedded = read(TARGET / "supplemental_evidence.json")["items"]
    log = read(ROOT / "review_log.json")
    spec = read(ROOT / "eval_spec.json")
    spec["version"] = "1.1-semantic-backend-and-current-source-review"
    spec["source_adjudication"]["states"]["withdrawn"] = "수정 전 채점 불가. 원래 시험 슬롯은 보류로 유지한다."
    spec["source_adjudication"]["policy"][-1] = (
        "합격선70%·과목40% 및20/30/50문항·120분은 2026-10-13 협회 공식 데이터로 대조했다. "
        "모의시험 형식이 다르면 이 판정기를 그대로 적용하지 않는다."
    )
    spec["execution"] = {
        "module": "evaluator.py", "full_corpus": "item_contracts.json",
        "released_examples": "calibration_cases.json",
        "semantic_grader": "semantic_grader.py: 전체 문항 근거 연결·실제 모델 요청·응답 인용 검증·출처 충돌 보류 구현. 실제 모델 정확도는 미측정.",
        "assistant_grader": "assistant_grader.py",
        "provider_configuration": "llm_provider.py; OPENAI_API_KEY and STUDY_EVAL_MODEL",
        "current_verification": "../verification_20261013/verification_summary.json",
        "criterion_release": "주제 기준은 문항별 명시 조건·각 선지의 이유로 구체화하고 원본과 대조한 후 실제 수업에 투입한다.",
        "assistant_benchmark": "assistant_benchmark.json",
        "study_method_decisions": "study_method_policy.json",
    }
    write(ROOT / "eval_spec.json", spec)
    cases = calibration_cases()
    qmap = {p["id"]: p for p in packets}
    for case in cases:
        assert set(case["source_question_ids"]) <= qmap.keys()
        case["source_locations"] = [
            {"id": qid, "document": qmap[qid]["document"], "pages": qmap[qid]["source_pages"]}
            for qid in case["source_question_ids"]
        ]
    write(ROOT / "calibration_cases.json", {"count": len(cases), "items": cases})
    contracts = []
    current_ledger = {x["id"]: x for x in read(TARGET / "question_ledger.json")["items"]}
    for packet in packets:
        p = {**packet, "demand": current_ledger[packet["id"]]["demand"]}
        contracts.append({
            "id": p["id"], "chapter_id": p["chapter_id"], "subject_id": p["chapter_id"][:2],
            "topic_ids": p["topic_ids"], "kind": p["kind"], "document": p["document"],
            "source_pages": p["source_pages"], "demand": p["demand"], "publisher_answer": p["publisher_answer"],
            "rationale_evidence": p["explanation_text"], "locator_status": p["locator_status"],
            "review": "publisher_frame_reviewed_for_eval", "gold_status": "item_level_release_required",
            "page_review_candidates": p["source_page_review_notes"],
            "chapter_findings": f"review_log.json#/chapters/{p['chapter_id']}",
            "criteria": [
                {"dimension": "exam_answer", "criterion": "명시된 발문·선택지와 대응하는 답. 교재 의도와 승인 gold를 구별.",
                 "evidence": "publisher_answer + release_review"},
                {"dimension": "concept_reason", "criterion": p["demand"],
                 "evidence": "이 문항의 rationale_evidence + 연결 topic_rubrics.required_action"},
                {"dimension": "conditions", "criterion": "위 해설에서 정답을 바꾸는 조건·시점·분모·예외를 실제 응답과 대조.",
                 "evidence": "해당 문항 원본 + topic_rubrics.counterexample_focus"},
            ],
            "semantic_criterion_state": "grounded_contract; instantiate atomic criteria before scoring free text",
            "mode_policy": "timed_mock는 정답만 요구 가능. 학습 모드는 필요한 이유·선지·단계를 관측.",
            "learner_prompt": {"state": "needs_clean_extraction_review",
                               "forbidden_input": "answer_packets.question_text may contain answers"},
            "release_gate": ["원본 문항·선지·해설의 대응", "원문/교정 답과 가정 분리",
                             "같은 페이지 주의사항의 실제 적용 여부 판정", "시점 민감 사실 적용일 확인",
                             "도표·수식·단위 복원", "답을 숨긴 학습자용 문항 검토"],
            "repair_reference": [f"topic_rubrics.json#{tid}" for tid in p["topic_ids"]],
            "illustrated_by": [c["id"] for c in cases if p["id"] in c["source_question_ids"]],
        })
    write(ROOT / "item_contracts.json", {"count": len(contracts), "items": contracts})
    topics = [{
        "id": r["id"], "chapter_id": r["chapter_id"], "title": r["title"],
        "required_action": r["required_action"], "understanding_probe": r["check_plan"],
        "recall_targets": r["memory_targets"], "counterexample_focus": r["likely_confusion"],
        "repair_design": r["repair_plan"], "explanation_design": r["explanation_plan"],
        "question_ids": r["question_ids"], "supplemental_evidence_ids": r["supplemental_evidence_ids"],
        "rules": sorted(set(r["rules"] + ["R03", "R14", "R17", "R22", "R24", "R30"])),
        "review_findings": log["chapters"][r["chapter_id"]]["eval_findings"],
        "rubric_state": "topic_specific_design; no learner assessed",
        "response_protocol": {
            "required": ["mode", "prompt", "response", "assistance", "item_exposures", "response_at",
                         "criterion_id", "response_quote", "criterion_evidence", "reason", "status"],
            "alternative_solutions": "정당한 동치 풀이와 쉬운 표현을 허용. 해설 문장 복사 여부로 판정하지 않음",
            "diagnosis": "틀린 응답만으로 암기 부족을 추측하지 않고 짧은 조건·절차 확인으로 첫 오류를 찾음",
            "next_delivery": "repair_design을 실제 설명·예시·비교·회상 카드로 구체화한 뒤 학습자에게 제시",
        },
    } for r in routes]
    write(ROOT / "topic_rubrics.json", {"count": len(topics), "items": topics})
    write(ROOT / "embedded_evidence_coverage.json", {
        "count": len(embedded), "unit": "evidence_group_not_individual_question",
        "review_basis": "../target_analysis/omission_audit.json and source_page_index.json; prior full-page review carried forward",
        "items": [{**e, "eval_topic_refs": e["topic_ids"],
                   "release_policy": "개별 OX·예제의 원문 조건·답을 추출 검토한 뒤 평가 문항으로 사용"} for e in embedded],
    })
    grounding = make_grounding(spec)
    write(ROOT / "source_grounding.json", grounding)
    with (ROOT / "item_contracts.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        fields = ["id", "chapter_id", "kind", "demand", "publisher_answer", "gold_status", "topic_ids"]
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows({**c, "topic_ids": ";".join(c["topic_ids"])} for c in contracts)
    ledger_ids = {x["id"] for x in read(TARGET / "question_ledger.json")["items"]}
    reviewed = set(read(ROOT / "progress.json")["answer_review"]["reviewed_ids"])
    receipts = {
        cid: {
            qid for name in record["packet_receipts"]
            for qid in read(ROOT / "display_receipts" / name)["displayed_ids"]
        }
        for cid, record in log["chapters"].items()
    }
    checks = {
        "2292_unique_packets": len(packets) == len(qmap) == 2292,
        "ledger_and_review_exact_set": set(qmap) == ledger_ids == reviewed,
        "every_answer_and_rationale_present": all(p["publisher_answer"] and p["explanation_text"] for p in packets),
        "16_chapters_logged": len(log["chapters"]) == 16,
        "chapter_receipts_match_exact_question_sets": all(
            receipts[cid] == {p["id"] for p in packets if p["chapter_id"] == cid}
            and record["reviewed_question_count"] == len(receipts[cid])
            for cid, record in log["chapters"].items()
        ),
        "285_unique_topics": len(topics) == len({t["id"] for t in topics}) == 285,
        "all_questions_in_topics": {qid for t in topics for qid in t["question_ids"]} == ledger_ids,
        "all_contract_topics_exist": all(set(c["topic_ids"]) <= {t["id"] for t in topics} for c in contracts),
        "383_embedded_groups": len(embedded) == len({e["id"] for e in embedded}) == 383,
        "every_embedded_group_linked": {eid for t in topics for eid in t["supplemental_evidence_ids"]} == {e["id"] for e in embedded},
        "31_SRC_rules_bound": len(grounding["rules"]) == 31 and all(r["eval_bindings"] for r in grounding["rules"]),
        "no_raw_prompt_auto_release": all(c["learner_prompt"]["state"] == "needs_clean_extraction_review" for c in contracts),
    }
    audit = {
        "status": "pass" if all(checks.values()) else "fail", "checks": checks,
        "meaning": "전수 검토 기록·집합·근거 연결의 검사. 전 문항 gold 승인이나 의미 정확성의 자동 증명이 아니다.",
        "counts": {"questions": len(contracts), "topics": len(topics), "chapters": len(log["chapters"]),
                   "embedded_groups": len(embedded), "override_records": len(read(ROOT / "answer_overrides.json")),
                   "manual_rationale_recoveries": sum(p["locator_status"] == "manual_source_recovery" for p in packets),
                   "calibration_cases": len(cases)},
        "input_sha256": {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in ["answer_packets.json", "review_log.json", "exam_goal.json"]
        },
    }
    write(ROOT / "coverage_audit.json", audit)
    if not all(checks.values()):
        raise ValueError(f"EVAL coverage failed: {checks}")
    rows = []
    for subject, total, correct in [("S1", 20, 8), ("S2", 30, 12), ("S3", 50, 50)]:
        rows.extend({"id": f"{subject}-EXAMPLE-{i+1}", "subject": subject,
                     "status": "correct" if i < correct else "incorrect"} for i in range(total))
    example = {"rows": rows, "closed": True, "elapsed_seconds": 7200,
               "assistance": "native_prompt_only", "familiar_items": 0}
    write(ROOT / "example_exam.json", example)
    write(ROOT / "example_exam_result.json", {"data_origin": "synthetic_boundary_example_not_user_score",
                                             **evaluate_exam(**example)})
    generate_report(topics, contracts, spec, cases, audit)
    integrate_existing()
    progress = read(ROOT / "progress.json")
    progress["status"] = "eval_artifacts_built; validation_pending"
    progress["artifacts"] = ["eval_report.html", "eval_spec.json", "exam_goal.json", "source_grounding.json",
                             "item_contracts.json", "topic_rubrics.json", "calibration_cases.json",
                             "embedded_evidence_coverage.json", "evaluator.py", "coverage_audit.json"]
    write(ROOT / "progress.json", progress)
    print(json.dumps({"status": audit["status"], "counts": audit["counts"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
