"""Build a local review report from actual evidence and item-level decisions."""

import html
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(name):
    """Read a generated UTF-8 artifact."""
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def esc(value):
    """Escape source text before inserting it in report markup."""
    return html.escape(str(value), quote=True)


def main():
    """Keep collection, reviewed claims, released prompts and runtime validation distinct."""
    summary = read("verification_summary.json")
    claims = read("verified_claims.json")["items"]
    math_path = ROOT / "verified_math_cases.json"
    math_cases = read("verified_math_cases.json")["items"] if math_path.exists() else []
    corrections = read("source_corrections.json")["items"]
    items = read("item_verification_registry.json")["items"]
    progress_path = ROOT / "parallel_progress.json"
    progress = read("parallel_progress.json") if progress_path.exists() else None
    progress_notice = ""
    if progress and progress["counts"]["released"] == summary["individually_released_items"]:
        progress_notice = (
            '<p class="notice">최신 개별 검토 집계: '
            f'검토 발문 {progress["counts"]["released"]}개 · '
            f'개별 사유가 있는 보류 {progress["counts"]["reviewed_held"]}개 · '
            f'검토 대기 {progress["counts"]["pending"]}개. '
            f'TARGET 원문 대응 재확인 {progress["target_correspondence_recheck_count"]}개는 '
            '검토 발문 수와 중복될 수 있으며 원문 검증 완료로 집계하지 않는다. '
            '<a href="progress_tree.txt">전체 진행 트리</a> · '
            '<a href="parallel_progress.json">문항별 보류 사유와 재검토 기록</a> · '
            '<a href="integration_audit.json">통합 검사 결과와 검사 시각</a> · '
            '<a href="../learning_integration_20261014/learning_report.html">공부법·문제 패턴·보류 학습 경로</a></p>'
        )
    versions = read("source_version_reviews.json")["items"]
    sources = [*read("source_registry.json")["items"], *read("kofia_registry.json")["items"]]
    states = {
        "adjudicated_current": "검토된 발문 사용 가능",
        "held_source_correction": "확인된 원문 오류로 보류",
        "whole_item_review_pending": "문항 전체의 독립 검증 필요",
    }
    totals = Counter(row["chapter_id"] for row in items)
    chapter_rows = []
    for chapter, total in sorted(totals.items()):
        count = Counter(row["source_state"] for row in items if row["chapter_id"] == chapter)
        chapter_rows.append(
            f"<tr><td>{esc(chapter)}</td><td>{total}</td>"
            + "".join(f"<td>{count[state]}</td>" for state in states) + "</tr>"
        )
    correction_cards = []
    for row in corrections:
        correction_cards.append(
            f'<article id="{esc(row["id"])}"><h3>{esc(row["id"])} · '
            f'{esc(", ".join(row["refs"]))}</h3><p>{esc(row["finding"])}</p>'
            f'<p class="action">학습자 처리: {esc(row["learner_treatment"])}</p>'
            f'<p class="meta">직접 연결 문항: {esc(", ".join(row["item_ids"]) or "본문 설명 정정; 이웃 문항까지 오류로 간주하지 않음")}</p>'
            f'<p>근거: {" · ".join(f"<a href=\"#{esc(cid)}\">{esc(cid)}</a>" for cid in row["claim_ids"])}</p>'
            f'<p>{" · ".join(f"<a href=\"#math-{esc(cid)}\">재계산 {esc(cid)}</a>" for cid in row.get("math_case_ids", []))}</p></article>'
        )
    claim_cards = []
    for row in claims:
        links = " · ".join(
            f'<a href="{esc(source["url"])}" rel="noreferrer">{esc(source["id"])}</a>'
            for source in row["evidence"]
        )
        claim_cards.append(
            f'<details id="{esc(row["id"])}"><summary>{esc(row["id"])} · '
            f'{esc(" / ".join(row["topic_ids"]))} · {esc(row["verified_statement"])}</summary>'
            f'<p>{esc(row["scope_limit"])}</p><p>공식 근거: {links}</p>'
            '<p class="meta">확인 단위는 위 명제와 조건이다. 연결된 주제·문항 전체의 승인과 다르다.</p></details>'
        )
    version_cards = "".join(
        f'<li>{esc(row["id"])}: {esc(row["reason"])}</li>' for row in versions
    )
    math_cards = "".join(
        f'<details id="math-{esc(row["id"])}"><summary>{esc(row["id"])} · '
        f'{esc(row["result"])} {esc(row["unit"])}</summary>'
        f'<p>{esc(row["clean_prompt"])}</p><p>검토 답: {esc(row["answer"])}</p>'
        f'<p>{esc(row["derivation"])}</p><p class="meta">{esc(row["conditions"])}</p>'
        f'<p>원문: {esc(", ".join(x["ref"] for x in row["source_page_evidence"]))}</p></details>'
        for row in math_cases
    )
    item_rows = "".join(
        f'<tr data-chapter="{esc(row["chapter_id"])}" data-state="{esc(row["source_state"])}">'
        f'<td>{esc(row["id"])}</td><td>{esc(row["chapter_id"])}</td>'
        f'<td>{esc(states[row["source_state"]])}{" · 교정 문항" if row.get("prompt_variant") == "corrected_reviewed_prompt" else ""}</td>'
        f'<td>{esc(", ".join(row["claim_candidates"]))}</td>'
        f'<td>{" · ".join(f"<a href=\"#{esc(cid)}\">{esc(cid)}</a>" for cid in row["confirmed_correction_ids"])}</td>'
        f'<td>{" · ".join(f"<a href=\"#{esc(x["correction_id"])}\">{esc(x["correction_id"])}</a>" for x in row.get("related_correction_candidates", []))}</td></tr>'
        for row in items
    )
    chapter_options = "".join(f'<option>{esc(chapter)}</option>' for chapter in sorted(totals))
    state_options = "".join(f'<option value="{esc(key)}">{esc(label)}</option>' for key, label in states.items())
    template = """<!doctype html>
<html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>2026-10-13 기준 검증과 자연어 EVAL</title>
<style>
:root{color-scheme:light;--ink:#1f2937;--accent:#185b51}*{box-sizing:border-box}
body{font:16px/1.65 system-ui,sans-serif;color:var(--ink);max-width:1320px;margin:auto;padding:30px 24px;background:#f7f8f6}
h1{font-size:1.8rem}h2{margin-top:2.4rem}h3{font-size:1.03rem}a{color:#125e83}
.notice{background:#fff3d8;border-left:5px solid #aa7020;padding:18px}.stats{display:flex;flex-wrap:wrap;gap:12px}
.stat{background:white;border:1px solid #d5ded8;border-radius:8px;padding:16px;min-width:180px}.stat b{display:block;font-size:1.7rem;color:var(--accent)}
article,details{background:white;border:1px solid #dbe2dc;border-radius:6px;padding:14px 18px;margin:12px 0}summary{cursor:pointer}
.meta{font-size:.88rem;color:#59645f}.action{border-left:3px solid #387f73;padding-left:12px}
.scroll{overflow:auto;max-height:650px}table{border-collapse:collapse;width:100%;background:white;font-size:.9rem}
td,th{text-align:left;padding:9px 12px;border-bottom:1px solid #dde2dc;vertical-align:top}thead{position:sticky;top:0;background:#e8efea}
select,input{font:inherit;padding:8px;max-width:100%;margin:4px 8px 10px 0}code{overflow-wrap:anywhere}nav a{margin-right:18px}
</style>
<h1>현행 기준 검증 · 학습자와 학습비서 EVAL</h1>
<p>기준일 <strong>2026-10-13</strong> · 합격은 <strong>전체 70% 이상과 매 과목 40% 이상을 동시에 충족</strong>해야 한다.</p>
<nav><a href="../eval/eval_report.html">EVAL 전체 보고서</a><a href="../target_analysis/analysis_report.html">5개 자료 분석</a><a href="#corrections">확인된 교정</a><a href="#claims">공식 근거</a><a href="#items">전체 문항 상태</a></nav>
<p class="notice">작업 중이다. 전체 자료의 읽기·연결, 특정 명제의 공식 검증, 문항별 승인, 실제 모델의 채점 성능은 서로 다른 단계다. 아래 수치는 각 단계를 구분한다. 문항 전체의 현행 검증과 실모델 채점 정확도 검증을 완료했다고 보고하지 않는다.</p>
<div class="stats">
<div class="stat"><b>__TOTAL__</b>등록된 전체 문항</div><div class="stat"><b>__SOURCES__</b>수집한 법령·규정 본문</div>
<div class="stat"><b>__CLAIMS__</b>조건을 정해 검증한 명제</div><div class="stat"><b>__RELEASES__</b>개별 검토한 학습자용 발문</div>
<div class="stat"><b>__CORRECTIONS__</b>확인된 교정 기록</div>
<div class="stat"><b>__MATH_COUNT__</b>조건을 명시해 재계산한 발문</div></div>
__PROGRESS_NOTICE__
<h2>시험 점수와 이해 진단</h2>
<p>공식 시험은 100문항·120분, 과목별 20·30·50문항이다. 따라서 총 70문항 이상을 맞히고, 각 과목에서 최소 8·12·20문항을 맞혀야 한다. 과목별 득점을 동일 가중치로 평균하지 않는다.</p>
<p>선택지가 맞아도 이유가 틀렸다면 시험 정답과 이해 보완을 따로 기록한다. 정답만 제출한 경우 설명을 관측하지 못했으므로 이해했다고 확정하지 않는다. 풀이 중 처음 틀어진 조건·분모·단위·관계를 찾아 SRC 공부법과 구체적 설명·예시·재확인 질문을 연결한다. 단 한 번의 정답으로 장기 암기나 합격 확률을 확정하지 않는다.</p>
<p>시험 점수로 승인하려면 검토된 답과 실제 전달한 발문의 지문 해시가 일치해야 한다. 원문 오류는 학습자 오답으로 기록하지 않는다. 모든 오류를 공식 근거로 교정하고 검토한 별도 발문은 채점할 수 있지만, 그 교정 발문을 실제로 전달했다는 확인이 필요하다. 원문과 교정 문항의 정답을 섞지 않는다. 시간 제한 모의고사 진행 중에는 해설과 정답을 숨긴다.</p>
<h2>자연어 채점 실행 상태</h2>
<p>학습자 응답과 학습비서 출력을 평가하는 실행 모듈을 구현했다. 2,292개 문항은 근거 문맥 생성 범위다. API 공급자·모델이 설정되지 않아 실제 모델 채점, 자동 채점의 정답 인정 오류율, 평가자 일치도와 학습 효과는 아직 측정하지 않았다. 모의 응답을 이용한 코드 검증을 실제 의미 판단 정확도로 표시하지 않는다.</p>
<p><a href="../eval/semantic_grader.py">학습자 채점 모듈</a> · <a href="../eval/assistant_grader.py">비서 품질 평가 모듈</a> · <a href="usage_examples.json">실행 예시</a> · <a href="verification_summary.json">기계 판독 요약</a></p>
<h2>목차별 문항 상태</h2><div class="scroll"><table><thead><tr><th>목차</th><th>전체</th><th>검토 발문</th><th>확인 오류 보류</th><th>독립 검증 필요</th></tr></thead><tbody>__CHAPTER_ROWS__</tbody></table></div>
<h2 id="corrections">확인된 교정과 학습자 처리</h2>__CORRECTION_CARDS__
<h2>시행일·적용례 확인</h2><ul>__VERSIONS__</ul><p>아직 해결되지 않은 연동 시행일도 그대로 표시한다. 현재 날짜 이전 공포라는 이유만으로 시행 중이라고 판단하지 않는다.</p>
<h2 id="claims">공식 근거와 검증한 범위</h2>__CLAIM_CARDS__
<h2 id="math">계산문항의 조건과 재계산</h2>
<p>수치는 명시한 조건의 계산 결과다. 예시 세율은 현행 세법을 검증한 값이라는 뜻이 아니다. 원문 오류, OCR 손실, 중간 반올림을 구분한다.</p>__MATH_CARDS__
<h2 id="items">전체 문항: 누락과 보류 확인</h2>
<p>명제·관련 교정 후보 연결은 같은 주제나 쪽의 근거를 제공한다는 뜻이다. 해당 문항의 오류 확정이나 모든 선지·해설 검증을 뜻하지 않는다. 직접 교정과 관련 후보를 구별한다.</p>
<label>목차 <select id="chapter"><option value="">전체</option>__CHAPTER_OPTIONS__</select></label>
<label>상태 <select id="state"><option value="">전체</option>__STATE_OPTIONS__</select></label>
<label>문항 번호 <input id="query" placeholder="예: S3C3T15"></label><p id="count" aria-live="polite"></p>
<div class="scroll"><table id="item-table"><thead><tr><th>문항</th><th>목차</th><th>상태</th><th>관련 명제 후보</th><th>직접 교정</th><th>관련 교정 후보</th></tr></thead><tbody>__ITEM_ROWS__</tbody></table></div>
<script>
const rows=[...document.querySelectorAll('#item-table tbody tr')];
function filter(){const c=document.getElementById('chapter').value,s=document.getElementById('state').value,q=document.getElementById('query').value.trim().toUpperCase();let n=0;for(const r of rows){const ok=(!c||r.dataset.chapter===c)&&(!s||r.dataset.state===s)&&(!q||r.cells[0].textContent.toUpperCase().includes(q));r.hidden=!ok;if(ok)n++}document.getElementById('count').textContent=n+' / '+rows.length+'문항 표시';}
for(const id of ['chapter','state','query'])document.getElementById(id).addEventListener('input',filter);filter();
</script></html>"""
    replacements = {
        "TOTAL": len(items), "SOURCES": sum(x["http_complete"] for x in sources),
        "CLAIMS": len(claims), "RELEASES": summary["individually_released_items"],
        "CORRECTIONS": len(corrections), "CHAPTER_ROWS": "".join(chapter_rows),
        "CORRECTION_CARDS": "".join(correction_cards), "VERSIONS": version_cards,
        "CLAIM_CARDS": "".join(claim_cards), "CHAPTER_OPTIONS": chapter_options,
        "STATE_OPTIONS": state_options, "ITEM_ROWS": item_rows,
        "MATH_COUNT": len(math_cases), "MATH_CARDS": math_cards,
        "PROGRESS_NOTICE": progress_notice,
    }
    for key, value in replacements.items():
        template = template.replace(f"__{key}__", str(value))
    (ROOT / "verification_report.html").write_text(template, encoding="utf-8")
    print(f"Built report: {len(items)} items, {len(claims)} scoped claims.")


if __name__ == "__main__":
    main()
