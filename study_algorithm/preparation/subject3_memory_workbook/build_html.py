"""Convert the complete outline workbook to the user's fixed ledger HTML."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

import build_workbook as workbook
from reportlab.platypus import Paragraph, Spacer, Table

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
HTML_PATH = ROOT / "output" / "3과목_목차암기_공부법과_반복학습_문제집.html"
TOC_PAGES = {1: 3, 2: 59, 3: 161, 4: 203, 5: 251, 6: 309, 7: 369, 8: 401, 9: 433}
FONTS = '''<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Gowun+Batang:wght@400;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">'''


def fmt(text: str) -> str:
    """Escape prose and mark every numeric value with the required font class."""
    text = html.escape(text)
    text = re.sub(
        r'\(\s*([①②③④⑤⑥⑦⑧⑨])?\s*\)',
        lambda match: f'({match[1] or ""}<span class="blank s" aria-label="답안 빈칸"></span>)',
        text,
    )
    text = re.sub(r"\d+(?:[.,]\d+)*", lambda match: f'<span class="num">{match[0]}</span>', text)
    text = re.sub(r"_{3,}", '<span class="blank w" aria-label="답안 빈칸"></span>', text)
    return text.replace("\n", "<br>")


def plain(item: object) -> str:
    """Read the preserved text from a ReportLab flowable."""
    if isinstance(item, Paragraph):
        return html.unescape(item.text.replace("<br/>", "\n"))
    return str(item)


def section_head(label: str, title: str) -> str:
    """Use the exact section skeleton requested by the user."""
    return f'<div class="sechead"><span class="step">{html.escape(label)}</span><h2>{fmt(title)}</h2></div>'


def data_table(headers: list[str], rows: list[list[str]], footer: list[str] | None = None) -> str:
    """Wrap a small indivisible data table in the required figure container."""
    result = '<div class="scroll fig"><table><thead><tr>'
    result += ''.join(f'<th scope="col">{fmt(value)}</th>' for value in headers)
    result += '</tr></thead><tbody>'
    result += ''.join('<tr>' + ''.join(f'<td>{fmt(value)}</td>' for value in row) + '</tr>' for row in rows)
    result += '</tbody>'
    if footer:
        result += '<tfoot><tr>' + ''.join(f'<td>{fmt(value)}</td>' for value in footer) + '</tr></tfoot>'
    return result + '</table></div>'


def term(title: str, body: str, application: str, label: str = "") -> str:
    """Connect every conceptual card to actual chapter or topic data."""
    return (
        '<article class="term fig"><div class="term-head">'
        f'<h3 class="term-word">{fmt(title)}</h3>'
        f'<span class="term-eng">{html.escape(label)}</span></div>'
        f'<div class="term-body">{body}<div class="deal"><b>이 학습에서:</b> '
        f'{fmt(application)}</div></div></article>'
    )


def render_item(item: object) -> str:
    """Preserve existing prose and exercises while replacing their visual form."""
    if isinstance(item, Spacer):
        return ''
    if isinstance(item, Paragraph):
        tag = 'h3' if item.style.name == 'heading' else 'p'
        return f'<{tag}>{fmt(plain(item))}</{tag}>'
    if isinstance(item, Table):
        rows = [[plain(cell) for cell in row] for row in item._cellvalues]
        if all(not cell for row in rows for cell in row):
            return '<p>' + '<br>'.join('<span class="blank w" aria-label="답안 빈칸"></span>' for _ in rows) + '</p>'
        if len(rows) == 1 and len(rows[0]) == 1:
            return '<div class="note fig"><strong>확인할 기준</strong><p>' + fmt(rows[0][0]) + '</p></div>'
        return data_table(rows[0], rows[1:])
    raise TypeError(f'Unsupported flowable: {type(item)}')


def exercise_blocks(page: workbook.WorkbookPage) -> str:
    """Keep the original question IDs and group each prompt with its answer space."""
    result = ['<div class="ws">']
    introduction = [f'<h3 id="{page.key}">{fmt(page.title)}</h3>']
    opened = False
    for item in page.items:
        if isinstance(item, Paragraph) and item.style.name == 'heading':
            if opened:
                result.append('</div>')
            result.append('<div class="q fig">')
            if not opened:
                result.extend(introduction)
            opened = True
        if opened:
            result.append(render_item(item))
        else:
            introduction.append(render_item(item))
    if opened:
        result.append('</div>')
    result.append('</div>')
    return ''.join(result)


def answer_blocks(page: workbook.WorkbookPage) -> str:
    """Rotate each short answer block, preserving legible page-sized figures."""
    result = [f'<h3>{fmt(page.title)}</h3>']
    items: list[object] = []
    title = ''

    def flush() -> None:
        if not items:
            return
        result.append('<div class="answers fig">')
        if title:
            result.append(f'<p><strong>{fmt(title)}</strong></p>')
        result.append('<div class="ans-body">')
        result.extend(render_item(item) for item in items)
        result.append('</div></div>')

    for item in page.items:
        if isinstance(item, Paragraph) and item.style.name == 'heading':
            flush()
            items = []
            title = plain(item)
        else:
            items.append(item)
    flush()
    return ''.join(result)


def build_html() -> str:
    """Compose a single HTML with unmodified embedded CSS and all workbook content."""
    chapters = json.loads((HERE / "content.json").read_text(encoding="utf-8"))["chapters"]
    original_pages = workbook.build_pages(chapters, TOC_PAGES)
    original = {page.key: page for page in original_pages}
    css = (HERE / "ledger.css").read_text(encoding="utf-8")
    parts = [f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>3과목 목차 암기 · 공부법과 반복학습 문제집</title>
<meta name="description" content="3과목 9개 장과 152개 TOPIC의 구조를 익히는 공부법, 빈칸·순서·분류 문제, 정답 및 반복 기록표.">
{FONTS}
<style>
{css}</style></head><body><main class="sheet">
<header class="head"><div class="eyebrow">STUDY LEDGER · 3과목 목차 학습자료</div>
<h1><span class="num">3</span>과목, <span class="mark">목차를 꺼내는</span> 공부</h1>
<p class="sub">큰 흐름을 이해하고 묶어서 기억한 뒤, 가리고 복원하는 공부법과 반복 문제지</p>
<div class="meta fig"><div><span>학습 범위</span><b><span class="num">1~9</span>장</b></div>
<div><span>세부 목차</span><b><span class="num">152</span> TOPIC</b></div>
<div><span>첫 학습</span><b><span class="num">25</span>분</b></div>
<div><span>최종 확인</span><b><span class="num">27 / 27</span>점</b></div></div></header>
<div class="note fig"><strong>인쇄 안내</strong><p>인쇄 시 '배경 그래픽' 켜기, 크롬 여백은 '없음'. A4 용지와 배율 <span class="num">100%</span>로 인쇄하세요. 정답은 요청하신 서식대로 <span class="num">180</span>도 회전되어 있습니다.</p></div>
<nav aria-label="문서 목차"><p>바로 가기: <a class="term-eng" href="#overview">전체 지도</a> · <a class="term-eng" href="#method">공부법</a> · <a class="term-eng" href="#chapter-1">장별 설명</a> · <a class="term-eng" href="#worksheet">반복 문제</a> · <a class="term-eng" href="#final-check">최종 점검</a> · <a class="term-eng" href="#tracking">반복 기록</a> · <a class="term-eng" href="#answers">정답</a></p></nav>''']

    parts.append('<section id="overview">' + section_head('PART 01', '9개 장을 3개 묶음으로 기억하기'))
    parts.append('<p class="lead">목표는 책을 덮고 장 이름을 순서대로 말하며, 각 장 아래에 어떤 내용이 들어가는지 떠올리는 것입니다. 앞선 답변과 PDF의 공부법·장별 설명·반복 문제를 모두 담았습니다.</p>')
    categories = ['지켜야 할 기준', '투자대상별 운용', '결과·환경·배분']
    questions = ['어떤 태도로 일하는가?', '어떤 법과 규정을 지키는가?', '협회규정은 무엇인가?', '주식을 어떻게 운용하는가?', '채권을 어떻게 운용하는가?', '파생상품을 어떻게 운용하는가?', '운용결과를 어떻게 평가하는가?', '경제환경을 어떻게 보는가?', '자산을 어떻게 나누어 투자하는가?']
    parts.append(data_table(['암기 묶음', '실제 목차', '떠올릴 질문'], [[categories[i // 3], f"{chapter['number']}장 {chapter['name']}", questions[i]] for i, chapter in enumerate(chapters)]))
    parts.append(term('전체 목차의 연결문장', '<p>윤리·법·협회 규정을 지키며, 주식·채권·파생상품을 운용하고, 결과를 평가하고 경제를 살피며 분산한다.</p><p>처음에는 “윤리·법·협회 / 주식·채권·파생 / 결과·경제·분산”으로 꺼낸 뒤, 실제 장 이름으로 풀어서 말합니다. 마지막 세 장의 연결은 교재 순서를 기억하기 위한 문장입니다.</p>', '9개 장을 3개씩 묶으면 3묶음입니다. 5장은 채권, 협회규정 다음은 4장 주식, 결과분석 앞뒤는 6장 파생상품과 8장 거시경제입니다.', '3 × 3'))
    parts.append(term('암기할 때의 세 가지 기준', '<p>순서대로 장 이름을 말하기, 임의의 장 번호에 답하기, 공부한 장의 세부 목차를 꺼내기를 구별해 확인하세요. 읽은 횟수보다 가렸을 때 떠올린 내용을 기준으로 진도를 잡습니다.</p>', '전체 9장과 각 장의 TOPIC을 연결합니다. 1장의 경우 기초 4개·지킬 내용 7개·통제 2개로 13개 TOPIC을 복원합니다.', 'RECALL'))
    parts.append('</section><section id="method">' + section_head('STEP 01', '공부를 실제 행동으로 바꾸기'))
    method_cards = [
        ('목차를 보며 묶음과 위치 확인하기', '각 장이 어떤 질문에 답하는지 한마디로 설명합니다. 장을 낱개로 나열하기 전에 큰 흐름과 상하 관계를 잡으세요.', '1~3장은 기준, 4~6장은 투자대상별 운용, 7~9장은 결과·환경·배분으로 묶습니다.'),
        ('가리고 큰 묶음부터 말하기', '묶음 이름을 먼저 말하고, 그 안에서 장 이름을 꺼냅니다. 막히면 해당 묶음만 확인한 뒤 다시 가립니다.', '5장이 떠오르지 않으면 4장 주식 → 5장 채권 → 6장 파생상품을 다시 말합니다.'),
        ('장 이름에 세부 목차 붙이기', '전체 장의 위치가 잡히면 한 장씩 내려갑니다. 관련 제목을 묶고 그 묶음에 이름과 질문을 붙입니다.', '1장은 기초 4개 + 지킬 내용 7개 + 통제 2개, 2장은 6묶음·37개 TOPIC입니다.'),
        ('질문 순서를 바꿔 확인하기', '처음부터 순서대로 말할 때만 기억나는 부분을 찾아냅니다. 장 번호, 앞뒤 장, 부모 묶음, 하위 제목을 번갈아 묻습니다.', '“5장은?”, “협회규정 다음 장은?”, “7장 앞뒤 장은?”에 답하고 실제 9장 목차와 대조합니다.'),
    ]
    for title, body, application in method_cards:
        parts.append(term(title, f'<p>{body}</p>', application))
    parts.append(data_table(['시간', '오늘 할 행동'], [['0~5분', '9개 장을 읽고 세 묶음의 의미 설명하기'], ['5~10분', '가리고 9개 장 말하기 → 빠진 장만 확인하기'], ['10~20분', '1장 세부 목차를 기초·지킬 내용·통제로 연결하기'], ['20~25분', '책을 덮고 9개 장과 1장 세부 목차 복원하기']], ['합계 25분', '시간 배분은 이번 목표에 맞춘 제안입니다.']))
    parts.append(term('정답이 나올 때까지의 한 바퀴', '<ol class="rule-list"><li>먼저 답합니다.</li><li>원문 또는 정답과 대조합니다.</li><li>막힌 부분이 왜 그 묶음에 속하는지 설명합니다.</li><li>다시 가립니다.</li><li>다른 문제를 푼 뒤 돌아와 재확인합니다.</li></ol>', '빈칸에서 10~20초 생각한 뒤 막히면 해당 묶음만 확인합니다. 다른 문제 2~3개 후 돌아와 재답변합니다. 바로 보고 쓴 답은 독립 정답으로 세지 않습니다.', 'FEEDBACK'))
    parts.append(term('단서를 줄이고, 간격을 두고 확인하기', '<p>보기 있는 문제 → 묶음 이름만 있는 복원 → 자료를 덮은 최종 점검 순서로 갑니다. 오늘 마칠 때, 내일 시작할 때, 이후에도 먼저 가리고 확인합니다. 계속 맞히면 간격을 늘리고 막힌 묶음은 다음 날 다시 확인합니다.</p>', '최종 점검 27/27점을 두 번, 그중 한 번은 다음 날 이후에 달성하면 이번 목표의 완료로 표시합니다. 이후 3일 뒤 다시 확인하세요. 152개 제목 전체의 독립 복원은 확장 목표입니다.', 'DELAYED CHECK'))
    parts.append('<div class="note fig"><strong>채점할 때 구별할 것</strong><p>필기는 짧은 키워드 중심으로 합니다. 말로 복원해도 되지만, 정답을 읽은 직후 따라 말한 답과 도움 없이 꺼낸 답은 따로 표시하세요. 학습용 묶음 이름·시간·복습 간격·완료 기준은 이번 목표를 위해 구성한 제안입니다.</p></div></section>')

    for chapter in chapters:
        number = chapter['number']
        count = len(chapter['topics'])
        parts.append(f'<section id="chapter-{number}"><div class="fig">' + section_head(f'CHAPTER {number:02}', chapter['name']))
        parts.append(f'<p class="lead">{fmt(chapter["cue"])}</p>')
        for group_index, (name, start, end, explanation) in enumerate(chapter['groups'], 1):
            rows = [[f'{i:02}', chapter['topics'][i - 1]] for i in range(start, end + 1)]
            group_table = data_table(['TOPIC', '암기용 축약 제목'], rows)
            body = group_table + f'<p>{fmt(explanation)}</p>'
            application = f'{number}장 TOPIC {start:02}~{end:02}, 총 {end - start + 1}개입니다. 전체 {count}개 중 {group_index}번째 묶음으로 복원합니다.'
            parts.append(term(name, body, application, f'GROUP {group_index:02}'))
            if group_index == 1:
                parts.append('</div>')
        parts.append(term('이렇게 말하면 됩니다', f'<p>{fmt(chapter["story"])}</p>', chapter['tip'], 'SPOKEN RECALL'))
        parts.append(f'<div class="note fig"><strong>원문 대조</strong><p>{fmt(f"3과목.pdf PDF {TOC_PAGES[number]}쪽 목차와 확인하세요. TOPIC 번호와 순서는 원문을 유지하고 긴 제목은 줄였습니다. 위 묶음은 암기용 구성입니다.")}</p></div>')
        parts.append('</section>')

    parts.append('<section id="source">' + section_head('REFERENCE', '참조 자료와 범위 확인'))
    for item in original['sources'].items:
        parts.append(render_item(item))
    parts.append(data_table(['원문 목차 검산', 'TOPIC 수'], [[f"{c['number']}장", str(len(c['topics']))] for c in chapters], ['합계', '152']))
    parts.append('<p class="ok">✓ 원문의 <span class="num">9</span>장·<span class="num">152</span>개 TOPIC 번호를 누락·중복 없이 배치했습니다.</p></section>')

    parts.append('<section id="worksheet">' + section_head('STEP 02', '반복학습 문제지'))
    parts.append('<div class="note fig"><strong>먼저 풀고, 뒤에서 확인</strong><p>설명과 정답을 가리세요. 독립 정답 O, 도움을 본 답 H, 오류 X로 표시합니다. 빈칸에는 핵심어를 쓰고, 뜻이 같으면 인정하되 다른 장·묶음으로 옮겨 적은 답은 고칩니다.</p></div>')
    parts.append(exercise_blocks(original['exercise-a']))
    parts.append(exercise_blocks(original['exercise-b']))
    for chapter in chapters:
        number = chapter['number']
        parts.append('<div class="ws">')
        for group_index, (name, start, end, _) in enumerate(chapter['groups']):
            parts.append('<div class="q fig">')
            if group_index == 0:
                parts.append(f'<h3 id="practice-{number}">{fmt(f"{number}장 목차 복원 · {chapter['name']}")}</h3>')
                parts.append('<p>날짜: <span class="blank"></span> 시도: <span class="blank s"></span>회 / 틀린 번호: <span class="blank w"></span></p>')
            parts.append(f'<strong>{fmt(name)}</strong><p>이 묶음의 TOPIC을 원문 순서대로 쓰세요.</p>')
            parts.append('<p>' + '<br>'.join(f'<span class="num">{i:02}</span> <span class="blank w" data-topic-blank="{number}-{i}" aria-label="{number}장 TOPIC {i} 답안"></span>' for i in range(start, end + 1)) + '</p></div>')
        for index, (question, _) in enumerate(chapter['questions'], 1):
            parts.append(f'<div class="q fig"><span class="num">C{number}-{index}</span> {fmt(question)}<p><span class="blank w"></span></p></div>')
        parts.append('</div><p>틀린 이유: □ 누락 □ 순서 □ 다른 묶음과 혼동 / 해당 묶음을 확인한 뒤 연결 이유를 말하고, 다시 가려 재답변하세요.</p>')
    parts.append('</section>')

    parts.append('<section id="final-check">' + section_head('STEP 03', '자료를 덮고 최종 점검'))
    for key in ['final-1', 'final-2-1', 'final-2-2']:
        parts.append(exercise_blocks(original[key]))
    parts.append('</section><section id="tracking">' + section_head('STEP 04', '목표를 달성할 때까지 반복 기록'))
    parts.extend(render_item(item) for item in original['tracking'].items)
    parts.append('</section><section id="answers">' + section_head('ANSWER KEY', '정답 · 먼저 푼 다음 확인'))
    parts.append('<p class="lead">정답은 각 묶음별로 <span class="num">180</span>도 회전되어 있습니다. 제목과 문제 ID를 기준으로 대조하세요. 빈칸 전체 정답도 아래에 제공합니다.</p>')
    parts.append(answer_blocks(original['answer-ab']))
    for chapter in chapters:
        number = chapter['number']
        parts.append(f'<h3>{fmt(f"{number}장 TOPIC 빈칸 정답")}</h3>')
        for name, start, end, _ in chapter['groups']:
            parts.append(f'<div class="answers fig"><p><strong>{fmt(name)}</strong></p><div class="ans-body">')
            parts.append('<p>' + '<br>'.join(f'<span data-topic-answer="{number}-{i}">{fmt(f"{i:02} {chapter['topics'][i - 1]}")}</span>' for i in range(start, end + 1)) + '</p></div></div>')
    for key in ['answer-c-1', 'answer-c-4', 'answer-c-7', 'answer-final']:
        parts.append(answer_blocks(original[key]))
    parts.append('</section><footer><span>STUDY LEDGER · 3과목 목차 파악</span><span>읽기 → 회상 → 확인 → 재연습</span></footer></main></body></html>')
    result = '\n'.join(parts)
    # Page numbers from the former fixed PDF do not apply to a flowing HTML print.
    result = result.replace('각 장 설명 페이지에', '각 장 설명 부분에').replace('같은 번호끼리 대조하면', '같은 TOPIC 번호끼리 대조하면')
    assert result.count('data-topic-blank=') == 152
    assert result.count('data-topic-answer=') == 152
    assert css in result
    return result


def main() -> None:
    """Write the standalone HTML without changing the existing PDF."""
    HTML_PATH.write_text(build_html(), encoding="utf-8")
    print(str(HTML_PATH))
    print(f'Bytes: {HTML_PATH.stat().st_size:,}')


if __name__ == '__main__':
    main()
