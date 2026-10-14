"""Build and validate a Korean subject-three outline study workbook."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "preparation" / "pdf_tools"))

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Flowable, Frame, Paragraph, Spacer, Table, TableStyle

HERE = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"
PDF_PATH = OUTPUT / "3과목_목차암기_공부법과_반복학습_문제집.pdf"
PAGE_WIDTH, PAGE_HEIGHT = A4
WIDTH = PAGE_WIDTH - 84
NAVY = colors.HexColor("#16324F")
TEAL = colors.HexColor("#147D83")
PALE = colors.HexColor("#EEF6F6")
GRAY = colors.HexColor("#536371")
LINE = colors.HexColor("#D8E2E9")

pdfmetrics.registerFont(TTFont("Malgun", "C:/Windows/Fonts/malgun.ttf"))
pdfmetrics.registerFont(TTFont("MalgunBold", "C:/Windows/Fonts/malgunbd.ttf"))
pdfmetrics.registerFontFamily("Malgun", normal="Malgun", bold="MalgunBold")
STYLES = {
    "body": ParagraphStyle("body", fontName="Malgun", fontSize=10, leading=15.2, spaceAfter=7, wordWrap="CJK", textColor=NAVY),
    "small": ParagraphStyle("small", fontName="Malgun", fontSize=8.7, leading=13, spaceAfter=5, wordWrap="CJK", textColor=GRAY),
    "heading": ParagraphStyle("heading", fontName="MalgunBold", fontSize=11.2, leading=16.5, spaceBefore=8, spaceAfter=5, wordWrap="CJK", textColor=TEAL),
    "quote": ParagraphStyle("quote", fontName="MalgunBold", fontSize=10.3, leading=16.2, wordWrap="CJK", textColor=NAVY),
    "cell": ParagraphStyle("cell", fontName="Malgun", fontSize=9.2, leading=13.5, wordWrap="CJK", textColor=NAVY),
    "cell_small": ParagraphStyle("cell_small", fontName="Malgun", fontSize=8.5, leading=12.3, wordWrap="CJK", textColor=NAVY),
    "cover": ParagraphStyle("cover", fontName="MalgunBold", fontSize=30, leading=43, wordWrap="CJK", textColor=NAVY),
    "center": ParagraphStyle("center", fontName="MalgunBold", fontSize=12, leading=19, alignment=TA_CENTER, wordWrap="CJK", textColor=TEAL),
}


@dataclass
class WorkbookPage:
    """One deliberately bounded workbook page."""

    title: str
    subtitle: str
    key: str
    items: list[Flowable]


def paragraph(text: str, style: str = "body") -> Paragraph:
    """Create a plain-text paragraph with safe line breaks."""
    return Paragraph(escape(text).replace("\n", "<br/>"), STYLES[style])


def heading(text: str) -> Paragraph:
    """Create a small section heading."""
    return paragraph(text, "heading")


def callout(text: str) -> Table:
    """Place an important statement in a lightly shaded box."""
    result = Table([[paragraph(text, "quote")]], colWidths=[WIDTH])
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    result.spaceAfter = 8
    return result


def table(rows: list[list[str]], widths: list[float], small: bool = False, header: bool = True) -> Table:
    """Build a table that wraps Korean text inside each cell."""
    result = Table(
        [[paragraph(cell, "cell_small" if small else "cell") for cell in row] for row in rows],
        colWidths=widths,
        hAlign="LEFT",
    )
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]
    if header:
        commands.append(("BACKGROUND", (0, 0), (-1, 0), PALE))
    result.setStyle(TableStyle(commands))
    result.spaceAfter = 9
    return result


def answer_lines(count: int = 1, height: int = 23) -> Table:
    """Create writing lines with enough vertical room for handwriting."""
    result = Table([[""] for _ in range(count)], colWidths=[WIDTH], rowHeights=height)
    result.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.45, LINE)]))
    result.spaceAfter = 6
    return result


def topic_text(chapter: dict, start: int, end: int) -> str:
    """Format every topic in an inclusive original-number range."""
    return "  /  ".join(f"{i:02d} {chapter['topics'][i - 1]}" for i in range(start, end + 1))


def group_block(chapter: dict, group: list) -> list[Flowable]:
    """Explain a memory group without changing its original topic order."""
    name, start, end, explanation = group
    count = end - start + 1
    return [
        heading(f"{name}  |  TOPIC {start:02d}~{end:02d} · {count}개"),
        paragraph(topic_text(chapter, start, end), "body"),
        paragraph(explanation, "small"),
    ]


def add_page(pages: list[WorkbookPage], title: str, subtitle: str, key: str, items: list[Flowable]) -> None:
    """Append a page with a stable internal destination."""
    pages.append(WorkbookPage(title, subtitle, key, items))


def build_pages(chapters: list[dict], toc_pages: dict[int, int]) -> list[WorkbookPage]:
    """Compose explanations, graded exercises, answers, and progress records."""
    pages: list[WorkbookPage] = []
    add_page(pages, "3과목 목차 암기", "공부법 + 1~9장 연결 설명 + 반복학습 문제지", "cover", [
        Spacer(1, 22),
        paragraph("3과목의 지도를\n머릿속에 만드는 공부", "cover"),
        Spacer(1, 16),
        callout("목표: 9개 장의 순서와 역할을 알고, 각 장의 세부 목차가 어디에 속하는지 설명한다."),
        paragraph("앞선 답변의 공부법과 1장 예시를 포함하고, 같은 방식의 설명을 2~9장까지 확장했습니다. 9개 장·152개 TOPIC의 위치를 확인하며 연습할 수 있습니다."),
        heading("이 책의 사용 순서"),
        table([
            ["단계", "할 일"],
            ["1. 전체 지도", "9개 장을 세 묶음으로 기억하고 연결문장을 말합니다."],
            ["2. 장별 설명", "각 장의 묶음과 이유를 읽고 세부 제목을 연결합니다."],
            ["3. 반복 문제", "빈칸·짝짓기·순서 배열·오류 교정·목차 복원을 풉니다."],
            ["4. 지연 확인", "다음 날 자료를 덮고 다시 확인하고, 막힌 부분을 재연습합니다."],
        ], [92, WIDTH - 92]),
        heading("읽기보다 실제로 꺼내기"),
        paragraph("‘읽으면 아는 느낌’과 ‘가렸을 때 말할 수 있음’을 구별하세요. 먼저 답하고, 확인하고, 틀린 부분을 연결해 다시 말하는 행동을 반복합니다."),
        paragraph("자료 기준: src/target/3과목.pdf 및 src의 공부법 자막. 묶음 이름·연결문장·문제·시간 배분·완료 기준은 이번 목표에 맞게 구성한 학습 설계입니다. 세부 제목은 암기용 축약이며 원문 TOPIC 순서와 번호를 유지했습니다.", "small"),
    ])

    overview_rows = [["묶음", "실제 목차", "떠올릴 질문"]]
    questions = ["어떤 태도로 일하는가?", "어떤 법과 규정을 지키는가?", "협회규정은 무엇인가?", "주식을 어떻게 운용하는가?", "채권을 어떻게 운용하는가?", "파생상품을 어떻게 운용하는가?", "운용결과를 어떻게 평가하는가?", "경제환경을 어떻게 보는가?", "자산을 어떻게 나누어 투자하는가?"]
    for index, chapter in enumerate(chapters):
        category = ["① 지켜야 할 기준", "② 투자대상별 운용", "③ 결과·환경·배분"][index // 3] if index % 3 == 0 else ""
        overview_rows.append([category, f"{index + 1}장 {chapter['name']}", questions[index]])
    add_page(pages, "9개 장을 3개 묶음으로", "전체 지도 | 큰 흐름 → 묶음 → 실제 장 이름", "overview", [
        table(overview_rows, [95, 247, WIDTH - 342], small=True),
        heading("소리 내어 말할 연결문장"),
        callout("윤리·법·협회 규정을 지키며, 주식·채권·파생상품을 운용하고, 결과를 평가하고 경제를 살피며 분산한다."),
        paragraph("처음에는 ‘윤리·법·협회 / 주식·채권·파생 / 결과·경제·분산’으로 꺼내고, 그다음 실제 장 이름으로 풀어서 말합니다. 마지막 세 장의 연결은 교재 순서를 기억하기 위한 문장입니다."),
        heading("위치까지 기억하기"),
        paragraph("묶음 세 개를 위에서 아래로 배치한 모습을 떠올립니다. ‘5장은 채권’, ‘협회 다음은 주식’, ‘결과분석 앞은 파생, 뒤는 거시경제’처럼 앞뒤 위치도 말해 보세요."),
        paragraph("정확한 제목을 말하는 최종 확인은 원문 목차와 대조합니다. 학습 중에는 핵심어로 복원해도 되지만 다른 장과 혼동되는 표현은 고칩니다.", "small"),
    ])

    add_page(pages, "오늘 25분, 이후에는 가리고 복원", "실행법 | 시간과 완료 기준은 이번 목표를 위한 제안", "method", [
        heading("공부할 때의 네 행동"),
        paragraph("1. 목차를 보며 묶음과 위치를 확인하고, 각 장이 어떤 질문에 답하는지 설명합니다.\n2. 목차를 가리고 세 묶음을 말한 뒤, 각 묶음에서 장 이름 세 개를 꺼냅니다.\n3. 장의 위치가 잡히면 세부 목차를 의미 있는 묶음으로 붙입니다.\n4. ‘몇 장인가? 앞뒤 장은? 이 장의 하위 목차는?’처럼 질문 순서를 바꿉니다."),
        table([
            ["시간", "오늘 할 행동"],
            ["0~5분", "9개 장을 읽고 세 묶음의 의미를 설명하기"],
            ["5~10분", "가리고 9개 장 말하기 → 빠진 장만 확인하기"],
            ["10~20분", "1장 세부 목차를 기초·지킬 내용·통제로 연결하기"],
            ["20~25분", "책을 덮고 9개 장과 1장 세부 목차 복원하기"],
        ], [84, WIDTH - 84]),
        heading("정답이 나올 때까지의 한 바퀴"),
        callout("먼저 답하기 → 확인하기 → 막힌 연결 고치기 → 다시 가리기 → 다른 문제 뒤에 재확인하기"),
        paragraph("빈칸은 10~20초 정도 생각한 뒤, 안 떠오르면 해당 묶음만 봅니다. 왜 그 위치인지 한 문장으로 말하고 다시 가립니다. 다른 문제 2~3개를 푼 뒤 틀렸던 항목으로 돌아옵니다. 바로 보고 쓴 답은 독립 정답으로 세지 않습니다."),
        heading("단서를 점점 줄이기"),
        paragraph("보기 있는 문제 → 묶음 이름만 있는 복원 → 아무 목차도 보지 않는 최종 점검 순서로 갑니다. 필기는 답을 확인하기 위한 짧은 키워드 중심으로 하고, 말로 복원한 경우도 기록합니다."),
        heading("복습과 완료"),
        paragraph("오늘 마칠 때, 내일 시작할 때, 3일 뒤에 먼저 가리고 확인합니다. 계속 맞히면 간격을 늘리고, 막힌 묶음은 다음 날 다시 확인합니다. 9개 장의 순서·위치·하위 관계를 말할 수 있는지가 기준입니다. 최종 점검 27/27을 두 번, 그중 한 번은 다음 날 이후에 달성하면 이번 목표의 완료로 표시하세요."),
        paragraph("152개 제목을 모두 독립적으로 복원하는 것은 확장 목표입니다. 목차 파악 단계에서는 장의 위치와 묶음의 의미를 우선하되, 빈칸 문제지로 전체 TOPIC까지 점검할 수 있습니다.", "small"),
    ])

    for chapter in chapters:
        number = chapter["number"]
        groups = chapter["groups"]
        parts = [groups[:3], groups[3:]] if number == 2 else [groups]
        for part_index, part in enumerate(parts):
            suffix = f" ({part_index + 1}/2)" if number == 2 else ""
            title = f"{number}장 {chapter['name']}{suffix}"
            items = [callout(chapter["cue"])]
            if number == 2:
                items.append(paragraph("37개 제목을 한 줄로 외우지 말고 여섯 묶음부터 기억합니다. 이 페이지는 " + ("기초·회사관리·영업행위" if part_index == 0 else "공시·소유와 거래·감독과 보호") + "를 다룹니다.", "small"))
            for group in part:
                items.extend(group_block(chapter, group))
            if part_index == len(parts) - 1:
                items.extend([heading("이렇게 말하면 됩니다"), paragraph(chapter["story"]), heading("누락을 찾는 단서"), paragraph(chapter["tip"], "small")])
            else:
                items.extend([heading("여기까지의 연결문장"), paragraph("법의 방향·기관·대상을 알고, 회사의 진입과 건전성을 관리한다. 다음으로 공통규칙에서 매매·중개, 집합투자, 자문·일임의 영업규칙으로 내려간다.")])
            items.append(paragraph(f"원문 확인: 3과목.pdf PDF {toc_pages[number]}쪽 목차. 번호는 원문 TOPIC 번호이며 제목은 암기용으로 줄였습니다. 묶음은 이 문제집의 학습용 분류입니다.", "small"))
            add_page(pages, title, f"장별 설명 | 세부 목차 {len(chapter['topics'])}개", f"chapter-{number}-{part_index}", items)

    add_page(pages, "연습 A · 보기와 함께 전체 지도 만들기", "유형: 빈칸 채우기 · 짝짓기 | 정답표를 가리고 먼저 답하세요", "exercise-a", [
        paragraph("이름: __________  날짜: __________  시도: ____회  /  도움 없이 맞힌 수: ____ / 15", "small"),
        heading("A1. 연결문장 빈칸 채우기 · 빈칸당 1점"),
        paragraph("보기: 경제 / 협회 / 파생 / 윤리 / 분산 / 채권 / 결과 / 법 / 주식"),
        callout("( ①        )·( ②        )·( ③        ) 규정을 지키며,\n( ④        )·( ⑤        )·( ⑥        )상품을 운용하고,\n( ⑦        )를 평가하고 ( ⑧        )를 살피며 ( ⑨        )한다."),
        heading("A2. 장과 역할 짝짓기 · 문항당 1점"),
        paragraph("보기: 가. 한국금융투자협회규정  나. 투자운용결과분석  다. 거시경제  라. 직무윤리  마. 분산투자기법  바. 파생상품투자운용/투자전략"),
        table([
            ["질문", "보기 기호"],
            ["1. 운용결과를 어떻게 평가하는가?", "________"],
            ["2. 어떤 태도로 일해야 하는가?", "________"],
            ["3. 투자에 영향을 주는 경제환경은 어떠한가?", "________"],
            ["4. 자산을 어떻게 나누어 투자하는가?", "________"],
            ["5. 협회의 규정은 무엇인가?", "________"],
            ["6. 선물·옵션을 어떻게 운용하는가?", "________"],
        ], [WIDTH - 100, 100]),
        heading("답을 확인한 뒤"),
        paragraph("틀린 칸을 그대로 베끼지 말고 그 칸이 속한 세 장 묶음을 말하세요. 예: 5장을 틀렸다면 ‘주식 → 채권 → 파생’을 다시 꺼냅니다. 다른 문제 뒤에 해당 칸을 다시 풀어 모두 맞힐 때까지 반복합니다."),
        paragraph("재시도할 항목 번호: ______________________________________________"),
    ])

    add_page(pages, "연습 B · 순서와 경계 구별하기", "유형: 순서 배열 · 선택 · 잘못된 분류 고치기", "exercise-b", [
        heading("B1. 전체 목차를 교재 순서로 배열하세요"),
        paragraph("가 거시경제 / 나 주식 / 다 직무윤리 / 라 분산투자 / 마 협회규정 / 바 채권 / 사 자본시장법·금융위규정 / 아 운용결과분석 / 자 파생상품"),
        paragraph("답: (    ) → (    ) → (    ) → (    ) → (    ) → (    ) → (    ) → (    ) → (    )"),
        heading("B2. 각 묶음 안에서 제목을 순서대로 배열하세요"),
        paragraph("1. 2장 영업행위: 가 집합투자 / 나 공통규칙 / 다 자문·일임 / 라 매매·중개\n답: (    ) → (    ) → (    ) → (    )"),
        paragraph("2. 5장: 가 금리구조 / 나 종류 / 다 운용전략 / 라 시장 / 마 가격변동 / 바 가격·수익률\n답: (    ) → (    ) → (    ) → (    ) → (    ) → (    )"),
        paragraph("3. 7장 1~3단계: 가 위험 측정 / 나 회계처리 / 다 수익률 계산\n답: (    ) → (    ) → (    )"),
        heading("B3. 이 묶음에 들어가지 않는 제목을 고르세요"),
        paragraph("1. 3장 조사분석자료 묶음: ① 작성 원칙 ② 의무공표 ③ 광고심의 ④ 분석사 매매제한\n답: ______  올바른 묶음: ______________________________"),
        paragraph("2. 4장 보험자산배분 묶음: ① 개요 ② OBPI ③ CPPI ④ 액티브 운용\n답: ______  올바른 묶음: ______________________________"),
        heading("B4. 틀린 문장의 목차 관계를 고치세요"),
        paragraph("1. ‘7장은 성과평가 11단계로 구성되고, 각 단계가 TOPIC 하나씩이다.’"),
        answer_lines(),
        paragraph("2. ‘9장에서 샤프의 단일지표모형과 APT는 CAPM의 하위 목차다.’"),
        answer_lines(),
        paragraph("3. ‘2장의 발행시장 공시에는 사업보고서와 주요사항·수시공시가 들어간다.’"),
        answer_lines(),
    ])

    for chapter in chapters:
        number = chapter["number"]
        groups = chapter["groups"]
        parts = [groups[:3], groups[3:]] if number == 2 else [groups]
        for part_index, part in enumerate(parts):
            suffix = f" ({part_index + 1}/2)" if number == 2 else ""
            items = [paragraph("날짜: __________  시도: ____회  /  아래 빈칸은 원문 TOPIC 번호입니다.\n설명 페이지를 덮고 핵심어를 씁니다. 도움을 본 칸에는 H, 독립 정답에는 O, 오류에는 X를 표시하세요.", "small")]
            items.append(heading("1. 묶음 이름을 단서로 세부 목차 복원하기"))
            for group in part:
                name, start, end, _ = group
                slots = [f"{i:02d} __________________________" for i in range(start, end + 1)]
                rows = [[slots[i], slots[i + 1] if i + 1 < len(slots) else ""] for i in range(0, len(slots), 2)]
                items.append(heading(name))
                blank_table = table(rows, [WIDTH / 2, WIDTH / 2], small=True, header=False)
                blank_table.setStyle(TableStyle([
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                items.append(blank_table)
            items.append(heading("2. 관계를 말로 설명하거나 짧게 쓰기"))
            quiz = chapter["questions"]
            selected = list(enumerate(quiz, 1))
            if number == 2:
                selected = selected[:2] if part_index == 0 else selected[2:]
            for question_index, (question, _) in selected:
                items.extend([paragraph(f"C{number}-{question_index}. {question}", "small"), answer_lines(1, height=18)])
            items.append(paragraph("다시 풀 칸: __________________  /  틀린 이유: □ 누락  □ 순서  □ 다른 묶음과 혼동\n재연습: 해당 묶음 확인 → 연결 이유 말하기 → 가리기 → 다른 문제 2~3개 후 재답변", "small"))
            add_page(pages, f"{number}장 목차 복원 문제지{suffix}", "유형: 계층형 빈칸 · 관계 회상 | 정답은 장별 설명과 뒤쪽 정답표", f"worksheet-{number}-{part_index}", items)

    final_mapping = [
        ("이자율 결정이론 · 통화량 증가에 의한 이자율변동", 8),
        ("기본원칙 · 이해상충방지의무", 1),
        ("패시브 · 액티브 · 준액티브 운용", 4),
        ("금융투자분석사의 매매제한 · 투자광고 심의", 3),
        ("CAPM의 CML·SML · APT", 9),
        ("금융투자업 인가·등록 · 공통영업행위 규칙", 2),
        ("선물 스프레드거래 · 풋-콜 패리티", 6),
        ("성과평가 7단계 개요 · 성과발표 방법", 7),
        ("맥컬레이 듀레이션 · 볼록성", 5),
    ]
    add_page(pages, "최종 점검 ① · 전체 목차와 위치", "모든 설명·보기·정답을 덮으세요 | T1 9점 + T2 9점", "final-1", [
        paragraph("날짜: __________  시도: ____회  /  처음 답: 검정색  /  확인 후 수정: 다른 색", "small"),
        heading("T1. 1~9장의 이름을 순서대로 쓰세요 · 각 1점"),
        table([["장", "장 이름"]] + [[f"{i}장", "________________________________________________________"] for i in range(1, 10)], [45, WIDTH - 45]),
        heading("T2. 다음 제목들이 속한 장 번호를 쓰세요 · 각 1점"),
        table([["문항", "목차 단서", "장 번호"]] + [[str(i), text, "______"] for i, (text, _) in enumerate(final_mapping, 1)], [40, WIDTH - 105, 65], small=True),
        paragraph("T1: ____ / 9   T2: ____ / 9   H 표시가 있는 답은 독립 정답으로 세지 않습니다.", "small"),
    ])

    final_branches = [
        (1, "윤리의 대상별 세 항목과, 장의 마지막 두 통제 항목을 쓰세요.", "본인·회사·사회에 대한 윤리 / 내부통제·외부통제"),
        (2, "공시제도를 시장별 두 묶음으로 나누고, 각 묶음의 모든 TOPIC을 쓰세요.", "발행시장: 증권신고서 개요·간주모집·투자설명서·증권분석기관 / 유통시장: 사업보고서·주요사항 및 수시공시"),
        (3, "조사분석자료 묶음의 네 TOPIC을 쓰세요.", "작성 원칙 / 금지·제한대상 / 의무공표 / 분석사의 매매제한"),
        (4, "자산배분의 세 갈래를 쓰고, 보험자산배분 개요 다음 두 방법을 쓰세요.", "전략적·전술적·보험자산배분 / OBPI·CPPI"),
        (5, "가격변동 묶음의 세 TOPIC을 쓰세요.", "맥컬레이 듀레이션 / 듀레이션으로 측정하는 가격변동률 / 볼록성"),
        (6, "선물전략 세 TOPIC과 옵션합성전략 두 TOPIC을 쓰세요.", "투기·헤지 / 차익거래 / 스프레드거래 ; 방향성전략 / 변동성전략"),
        (7, "평가절차의 1~3단계를 순서대로 쓰고, 4단계의 세 TOPIC을 쓰세요.", "회계처리 → 수익률 계산 → 위험 측정 ; 기준지표 설정 / 샤프·트레이너·젠센 / 정보·소티노"),
        (8, "거시정책이론의 두 TOPIC과 이자율 묶음의 세 TOPIC을 쓰세요.", "구축효과·유동성함정 / 이자율 결정이론·기간구조·통화량 증가에 의한 이자율변동"),
        (9, "CAPM 아래의 두 선을 한글명·약어로 쓰고, 장의 마지막 두 TOPIC을 쓰세요.", "자본시장선 CML·증권시장선 SML / 포트폴리오 투자전략·투자성과평가"),
    ]
    for part_index, selection in enumerate([final_branches[:5], final_branches[5:]], 1):
        items = [paragraph("장마다 요구한 하위 항목을 모두 맞히면 1점입니다. 표현을 줄여도 의미와 상하 관계가 맞으면 인정합니다. 번호 자체를 외우는 것보다 위치와 관계를 설명하는 데 집중하세요.", "small")]
        for number, question, _ in selection:
            items.extend([heading(f"T3-{number}. {number}장"), paragraph(question, "small"), answer_lines(3)])
        if part_index == 2:
            items.append(paragraph("T3: ____ / 9   최종 합계: ____ / 27   다음 확인 예정: __________", "small"))
        add_page(pages, f"최종 점검 ② · 장 안의 구조 ({part_index}/2)", "유형: 하위 목차 회상 | 두 페이지 합계 T3 9점", f"final-2-{part_index}", items)

    add_page(pages, "정답 · 연습 A와 B", "먼저 풀고 확인하세요 | 답을 본 뒤의 재답변은 별도 표시", "answer-ab", [
        heading("A1. 연결문장"),
        paragraph("① 윤리 ② 법 ③ 협회 ④ 주식 ⑤ 채권 ⑥ 파생 ⑦ 결과 ⑧ 경제 ⑨ 분산"),
        heading("A2. 역할 짝짓기"),
        paragraph("1 나(투자운용결과분석) / 2 라(직무윤리) / 3 다(거시경제) / 4 마(분산투자기법) / 5 가(협회규정) / 6 바(파생상품)"),
        heading("B1. 전체 목차 순서"),
        paragraph("다 → 사 → 마 → 나 → 바 → 자 → 아 → 가 → 라\n직무윤리 → 자본시장법·금융위규정 → 협회규정 → 주식 → 채권 → 파생상품 → 운용결과분석 → 거시경제 → 분산투자"),
        heading("B2. 묶음 안의 순서"),
        paragraph("1. 나 → 라 → 가 → 다 : 공통 → 매매·중개 → 집합투자 → 자문·일임\n2. 나 → 라 → 바 → 마 → 가 → 다 : 종류 → 시장 → 가격·수익률 → 가격변동 → 금리구조 → 전략\n3. 나 → 다 → 가 : 회계처리 → 수익률 계산 → 위험 측정"),
        heading("B3. 다른 묶음에 속하는 항목"),
        paragraph("1. ③ 광고심의 → 투자광고 묶음. 조사분석자료 4개와 투자광고 2개는 구별합니다.\n2. ④ 액티브 운용 → 주식포트폴리오 운용방식 묶음. 보험자산배분은 개요·OBPI·CPPI입니다."),
        heading("B4. 잘못된 관계 고치기"),
        paragraph("1. 성과평가는 7단계이며, 교재의 TOPIC은 11개입니다. 개요가 별도이고 4단계가 TOPIC 5~7, 5단계가 TOPIC 8~9로 나뉩니다.\n2. CAPM의 두 TOPIC은 CML·SML입니다. 단일지표모형과 APT는 뒤에 이어지는 별도의 TOPIC입니다.\n3. 사업보고서와 주요사항·수시공시는 유통시장 공시에 속합니다. 발행시장 공시는 증권신고서 개요·간주모집·투자설명서·증권분석기관입니다."),
        heading("장별 빈칸의 정답 확인 방법"),
        paragraph("각 장 설명 페이지에 원문 TOPIC 번호와 축약 제목이 모두 있습니다. 같은 번호끼리 대조하면 152개 빈칸을 확인할 수 있습니다. ‘말은 비슷하지만 다른 항목’은 구별하고, 뜻이 같은 축약 표현은 정답으로 인정하세요."),
    ])

    for start, end in [(1, 3), (4, 6), (7, 9)]:
        items = []
        for chapter in chapters[start - 1:end]:
            items.append(heading(f"{chapter['number']}장 관계 회상 정답"))
            for index, (_, answer) in enumerate(chapter["questions"], 1):
                items.append(paragraph(f"C{chapter['number']}-{index}. {answer}"))
        items.append(callout("정답을 읽은 뒤에는 해당 질문을 다시 가리고 답하세요. 독립적으로 맞힌 항목만 O로 바꾸고, 같은 묶음에서 누락된 제목이 없는지 한 번 더 확인합니다."))
        add_page(pages, f"정답 · {start}~{end}장 관계 회상", "장별 문제지 2번의 정답 | 빈칸 전체 정답은 장별 설명과 번호로 대조", f"answer-c-{start}", items)

    items = [heading("T1. 전체 목차")]
    items.append(paragraph(" → ".join(f"{c['number']}장 {c['name']}" for c in chapters), "small"))
    items.extend([heading("T2. 장 찾기"), paragraph(" / ".join(f"{i}번: {answer}장" for i, (_, answer) in enumerate(final_mapping, 1)))])
    items.append(heading("T3. 장 안의 구조"))
    for number, _, answer in final_branches:
        items.append(paragraph(f"{number}번. {answer}", "small"))
    items.extend([heading("채점 기준"), paragraph("T1은 각 장 이름과 순서가 맞으면 1점, T2는 각 장 번호가 맞으면 1점입니다. T3은 요구한 항목과 상하 관계를 모두 맞혀야 문항당 1점입니다. 읽고 쓴 답과 도움을 받은 답은 독립 정답에서 제외합니다. 총 27점입니다.", "small")])
    add_page(pages, "정답 · 최종 점검", "9개 장의 순서 + 목차 위치 + 하위 관계 = 27점", "answer-final", items)

    add_page(pages, "반복 기록 · 목표를 달성할 때까지", "틀린 항목만 보완하고, 다음 확인에서는 도움 없이 답하세요", "tracking", [
        callout("완료: 최종 점검 27/27을 두 번 달성하며, 그중 한 번은 다음 날 이후에 자료를 보지 않고 답한다."),
        paragraph("이 기준은 이번 학습을 끝낼 시점을 정하기 위한 운영 기준입니다. 이후 3일 뒤에도 다시 확인하세요. 틀리면 해당 묶음만 복구하고 재확인 일정을 잡습니다."),
        table([["회차·날짜", "T1 /9", "T2 /9", "T3 /9", "다시 볼 장·문항", "다음 확인"]] + [[f"{i}회 /", "", "", "", "", ""] for i in range(1, 7)], [77, 48, 48, 48, 177, WIDTH - 398], small=True),
        heading("오류에 따라 다음 행동을 고르세요"),
        table([
            ["관찰한 오류", "다음 행동"],
            ["장 이름이 빠짐", "세 장 묶음을 다시 말하고 빠진 장의 앞뒤를 연결합니다."],
            ["순서가 바뀜", "뒤바뀐 두 항목 사이에 연결문장을 하나 만듭니다."],
            ["다른 장·묶음에 넣음", "두 장의 질문을 비교하고, 해당 제목의 부모 묶음을 말합니다."],
            ["보기는 맞지만 빈칸은 못 씀", "첫 단어만 보고 답한 뒤, 그 단서도 가리고 다시 답합니다."],
            ["바로는 맞고 다음 날 잊음", "다음 날 먼저 회상하고, 막힌 묶음만 다시 설명·재연습합니다."],
        ], [135, WIDTH - 135], small=True),
        heading("자유 복원 · 마지막에 남길 한 문장"),
        paragraph("‘3과목은 어떤 흐름이며, 지금 공부하는 장은 그 안에서 무엇을 맡는가?’에 답하세요."),
        answer_lines(3),
        paragraph("확장 목표: 각 장 문제지를 다시 출력해 152개 TOPIC도 모두 독립적으로 복원합니다. 순서는 교재와 대조하되 뜻이 같은 핵심어는 허용합니다.", "small"),
    ])

    sources = [
        ("구조화 독서법", "g1N1_GFniLE", "제목의 상하 관계 구별, 목차를 질문으로 바꾸기, 핵심어를 단서로 내용 복원"),
        ("청킹, 막상 공부에 적용해보려니 어려우셨죠?", "Toa43mkjhl8", "관련 내용을 묶고 묶음에 이름을 붙이는 방법"),
        ("뼈대가 없이 공부하면 살이 붙지를 않아요", "fMCS6166ut4", "목차의 흐름과 관계를 먼저 생각하고 지식을 배치하는 방법"),
        ("쓰는 것은 시간낭비입니다 · 키워드 공부법", "SxL8INrDni8", "문장 전체 대신 핵심어를 남기고 말로 재현해 확인하는 방법"),
        ("책은 3단계로 나눠서 읽습니다", "Ir1ymyNLhaw", "익숙해지기·이해하기·암기하기의 구분"),
    ]
    items = [heading("목차의 기준 자료"), paragraph("src/target/3과목.pdf. 원문 앞부분의 9개 장과 각 장의 TOPIC별 학습체크 목차를 기준으로 구성했습니다. 각 장의 번호와 순서를 유지하고 긴 제목은 의미가 남도록 줄였습니다."), table([["장", "원문 PDF 목차 쪽", "TOPIC 수"]] + [[f"{c['number']}장", str(toc_pages[c['number']]), str(len(c['topics']))] for c in chapters], [90, 230, WIDTH - 320], small=True), heading("공부법의 기준 자료")]
    for title, video_id, use in sources:
        items.append(paragraph(f"{title} [{video_id}]\n적용: {use}", "small"))
    items.extend([paragraph("위 자막은 src/YouTube_자막_2026-10-12에 보관되어 있습니다. 현재 src에 method라는 별도 폴더는 없어, 해당 공부법 자막을 참조했습니다. 자동자막의 문장 오류를 그대로 인용하지 않고 학습 행동으로 정리했습니다.", "small"), heading("이 문제집에서 새로 구성한 부분"), paragraph("장별 암기 묶음·연결문장·질문·정답·25분 일정·반복 간격·27점 완료 기준은 이번 목표를 위해 구성했습니다. 묶음은 교재의 공식 분류명을 대신하지 않으며, 본문 지식이나 공식·법규 수치의 숙달 여부는 평가하지 않습니다.", "small")])
    add_page(pages, "참조 자료와 적용 범위", "원문 목차와 학습용 재구성을 구분합니다", "sources", items)

    page_numbers = {page.key: number for number, page in enumerate(pages, 1)}
    pages[0].items.extend([
        heading("필요한 페이지 바로 찾기"),
        paragraph(
            f"공부법 2~3쪽 · 장별 설명 {page_numbers['chapter-1-0']}~{page_numbers['chapter-9-0']}쪽\n"
            f"반복 문제 {page_numbers['exercise-a']}~{page_numbers['worksheet-9-0']}쪽 · 최종 점검 "
            f"{page_numbers['final-1']}~{page_numbers['final-2-2']}쪽\n"
            f"정답 {page_numbers['answer-ab']}~{page_numbers['answer-final']}쪽 · 반복 기록 "
            f"{page_numbers['tracking']}쪽 · 참조 자료 {page_numbers['sources']}쪽",
            "small",
        ),
    ])
    for page in pages:
        if page.key.startswith("worksheet-"):
            _, chapter_number, part_number = page.key.split("-")
            answer_page = page_numbers[f"chapter-{chapter_number}-{part_number}"]
            page.subtitle = f"유형: 계층형 빈칸 · 관계 회상 | TOPIC 빈칸 정답: {answer_page}쪽"
    return pages


def draw_document(pages: list[WorkbookPage]) -> None:
    """Render pages and reject any overflowing content."""
    OUTPUT.mkdir(exist_ok=True)
    canvas = Canvas(str(PDF_PATH), pagesize=A4, pageCompression=1)
    canvas.setTitle("3과목 목차 암기: 공부법과 반복학습 문제집")
    canvas.setAuthor("학습자료 정리")
    canvas.setSubject("9개 장·152개 TOPIC의 구조 파악과 반복 회상")
    for index, page in enumerate(pages, 1):
        canvas.bookmarkPage(page.key)
        canvas.addOutlineEntry(page.title, page.key, level=0, closed=False)
        canvas.setFillColor(TEAL)
        canvas.rect(42, PAGE_HEIGHT - 45, 32, 4, fill=1, stroke=0)
        title_style = ParagraphStyle("title", fontName="MalgunBold", fontSize=18 if len(page.title) < 34 else 14.8, leading=23, wordWrap="CJK", textColor=NAVY)
        title = Paragraph(escape(page.title), title_style)
        _, title_height = title.wrap(WIDTH, 80)
        title.drawOn(canvas, 42, PAGE_HEIGHT - 60 - title_height)
        canvas.setFont("Malgun", 8.5)
        canvas.setFillColor(GRAY)
        canvas.drawString(42, PAGE_HEIGHT - 69 - title_height, page.subtitle)
        canvas.setStrokeColor(LINE)
        canvas.line(42, 39, PAGE_WIDTH - 42, 39)
        canvas.setFont("Malgun", 8)
        canvas.drawString(42, 25, "3과목 목차 파악 · 읽기 → 회상 → 확인 → 재연습")
        canvas.drawRightString(PAGE_WIDTH - 42, 25, f"{index} / {len(pages)}")
        top = PAGE_HEIGHT - 88 - title_height
        frame = Frame(42, 50, WIDTH, top - 50, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        remaining = list(page.items)
        frame.addFromList(remaining, canvas)
        if remaining:
            raise ValueError(f"Page {index} overflows: {page.title}; remaining={len(remaining)}")
        canvas.showPage()
    canvas.save()


def validate_document(chapters: list[dict], pages: list[WorkbookPage]) -> None:
    """Check topic coverage, Korean extraction, page count, and rendered previews."""
    from pypdf import PdfReader
    import pypdfium2 as pdfium
    from PIL import Image, ImageDraw

    outline = json.loads((ROOT / "preparation/target_analysis/outline.json").read_text(encoding="utf-8-sig"))
    source_chapters = [chapter for chapter in outline["chapters"] if chapter["document"] == "P3"]
    for chapter, original in zip(chapters, source_chapters, strict=True):
        assert chapter["name"] == original["name"]
        assert len(chapter["topics"]) == len(original["topics"])
        coverage = [i for _, start, end, _ in chapter["groups"] for i in range(start, end + 1)]
        assert coverage == list(range(1, len(chapter["topics"]) + 1))
    assert sum(len(chapter["topics"]) for chapter in chapters) == 152
    reader = PdfReader(PDF_PATH)
    assert len(reader.pages) == len(pages)
    extracted = [page.extract_text() for page in reader.pages]
    assert all(len(text) > 90 for text in extracted)
    all_text = "\n".join(extracted)
    for chapter in chapters:
        for topic in chapter["topics"]:
            assert "".join(topic.split()) in "".join(all_text.split()), topic
    assert "\ufffd" not in all_text
    previews = HERE / "previews"
    previews.mkdir(exist_ok=True)
    pdf = pdfium.PdfDocument(str(PDF_PATH))
    thumbnails = []
    for index in range(len(pdf)):
        bitmap = pdf[index].render(scale=0.55)
        preview = bitmap.to_pil().convert("RGB")
        thumbnails.append(preview.copy())
        preview.save(previews / f"page_{index + 1:02d}.png")
    columns = 5
    cell_width, cell_height = 350, 490
    sheet = Image.new("RGB", (columns * cell_width, ((len(thumbnails) + columns - 1) // columns) * cell_height), "#dce3e8")
    draw = ImageDraw.Draw(sheet)
    for index, thumbnail in enumerate(thumbnails):
        x = (index % columns) * cell_width + 10
        y = (index // columns) * cell_height + 22
        sheet.paste(thumbnail, (x, y))
        draw.text((x, y - 17), str(index + 1), fill="black")
    sheet.save(previews / "contact_sheet.png")
    for index in [1, 4, 8, 9, 16, 21, 26]:
        if index < len(pdf):
            pdf[index].render(scale=1.4).to_pil().save(previews / f"detail_{index + 1:02d}.png")
    report = {
        "pdf": str(PDF_PATH),
        "pages": len(pages),
        "chapters": 9,
        "topics": 152,
        "topic_coverage": "All original topic numbers covered once in each chapter grouping",
        "korean_text_extraction": "passed",
        "page_overflow": "none",
        "page_index": [{"page": i, "title": page.title, "key": page.key} for i, page in enumerate(pages, 1)],
    }
    (HERE / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


def main() -> None:
    """Generate the PDF and its verification artifacts."""
    chapters = json.loads((HERE / "content.json").read_text(encoding="utf-8"))["chapters"]
    toc_pages = {1: 3, 2: 59, 3: 161, 4: 203, 5: 251, 6: 309, 7: 369, 8: 401, 9: 433}
    pages = build_pages(chapters, toc_pages)
    draw_document(pages)
    validate_document(chapters, pages)


if __name__ == "__main__":
    main()
