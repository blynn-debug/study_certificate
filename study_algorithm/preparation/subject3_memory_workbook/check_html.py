"""Check the ledger document in headless Chrome and render its A4 print output."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'preparation/pdf_tools'))

from playwright.sync_api import sync_playwright
from pypdf import PdfReader
import pypdfium2 as pdfium
from PIL import Image, ImageDraw

HTML_PATH = ROOT / 'output/3과목_목차암기_공부법과_반복학습_문제집.html'
CHECK_DIR = HERE / 'html_preview'
CHECK_DIR.mkdir(exist_ok=True)
ORIGINAL_POPEN = subprocess.Popen


class HiddenPopen(ORIGINAL_POPEN):
    """Keep the automation driver and helpers on a windowless Windows path."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        kwargs['creationflags'] = int(kwargs.get('creationflags', 0)) | subprocess.CREATE_NO_WINDOW
        super().__init__(*args, **kwargs)


def main() -> None:
    """Inspect both screen and print layout and record objective checks."""
    subprocess.Popen = HiddenPopen
    errors = []
    failed_requests = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',
            headless=True,
        )
        page = browser.new_page(viewport={'width': 1200, 'height': 1000}, device_scale_factor=1)
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('requestfailed', lambda request: failed_requests.append({'url': request.url, 'reason': request.failure}))
        page.goto(HTML_PATH.as_uri(), wait_until='networkidle', timeout=45000)
        page.evaluate('document.fonts.ready')
        page.screenshot(path=str(CHECK_DIR / 'desktop.png'))
        page.locator('#chapter-2 .term').first.screenshot(path=str(CHECK_DIR / 'chapter_card.png'))
        page.locator('#answers .answers').first.screenshot(path=str(CHECK_DIR / 'answer_rotation.png'))
        screen = page.evaluate('''() => ({
            bodyFont: getComputedStyle(document.body).fontFamily,
            titleFont: getComputedStyle(document.querySelector('h1')).fontFamily,
            answerRotation: getComputedStyle(document.querySelector('.ans-body')).transform,
            topicBlanks: document.querySelectorAll('[data-topic-blank]').length,
            topicAnswers: document.querySelectorAll('[data-topic-answer]').length,
            missingFigureClass: [...document.querySelectorAll('.term,.note,.scroll,.q,.answers,.meta')].filter(e=>!e.classList.contains('fig')).length,
            conceptCardsWithoutData: [...document.querySelectorAll('.term')].filter(e=>!e.querySelector('.deal')).length,
            loadedFonts: [...document.fonts].filter(f=>f.status==='loaded').map(f=>({family:f.family,weight:f.weight})),
            overflow: document.documentElement.scrollWidth > innerWidth,
            brokenAnchors: [...document.querySelectorAll('a[href^="#"]')].filter(e=>!document.querySelector(e.getAttribute('href'))).map(e=>e.href)
        })''')
        assert screen['topicBlanks'] == screen['topicAnswers'] == 152
        assert not screen['missingFigureClass']
        assert not screen['conceptCardsWithoutData']
        assert not screen['brokenAnchors']
        assert screen['answerRotation'].startswith('matrix(-1,')
        page.set_viewport_size({'width': 390, 'height': 844})
        page.screenshot(path=str(CHECK_DIR / 'mobile.png'))
        mobile = page.evaluate('''() => ({
            overflow: document.documentElement.scrollWidth > innerWidth,
            background: getComputedStyle(document.body).backgroundImage,
            metaColumns: getComputedStyle(document.querySelector('.meta')).gridTemplateColumns
        })''')
        page.emulate_media(media='print', reduced_motion='reduce')
        page.set_viewport_size({'width': 703, 'height': 1024})
        printing = page.evaluate('''() => ({
            answerRotation: getComputedStyle(document.querySelector('.ans-body')).transform,
            worksheetStart: getComputedStyle(document.querySelector('#worksheet')).breakBefore,
            background: getComputedStyle(document.body).backgroundImage,
            printColor: getComputedStyle(document.body).printColorAdjust,
            headerDisplay: getComputedStyle(document.querySelector('thead')).display,
            oversizedFigures: [...document.querySelectorAll('.fig')].filter(e=>e.getBoundingClientRect().height>1024).map(e=>({tag:e.tagName,class:e.className,height:e.getBoundingClientRect().height,text:e.innerText.slice(0,90)})),
            overflowingTables: [...document.querySelectorAll('table')].filter(e=>e.getBoundingClientRect().width>e.parentElement.getBoundingClientRect().width+1).map(e=>({width:e.getBoundingClientRect().width,text:e.innerText.slice(0,70)}))
        })''')
        page.pdf(path=str(CHECK_DIR / 'print_check.pdf'), prefer_css_page_size=True, print_background=True, display_header_footer=False)
        browser.close()
    pdf_path = CHECK_DIR / 'print_check.pdf'
    reader = PdfReader(pdf_path)
    pdf = pdfium.PdfDocument(str(pdf_path))
    page_texts = [p.extract_text() for p in reader.pages]
    contact_width, contact_height, columns = 240, 350, 6
    contact = Image.new('RGB', (columns * contact_width, ((len(pdf) + columns - 1) // columns) * contact_height), '#DCE4E3')
    draw = ImageDraw.Draw(contact)
    for index in range(len(pdf)):
        img = pdf[index].render(scale=0.36).to_pil().convert('RGB')
        x = index % columns * contact_width + 10
        y = index // columns * contact_height + 25
        contact.paste(img, (x, y))
        draw.text((x, y - 18), str(index + 1), fill='#16232E')
    contact.save(CHECK_DIR / 'print_contact.png')
    report = {
        'screen': screen, 'mobile': mobile, 'print': printing,
        'console_errors': errors, 'failed_requests': failed_requests,
        'print_pages': len(reader.pages),
        'sparse_pages': [{'page': i + 1, 'characters': len(t.strip()), 'text': t[:100]} for i, t in enumerate(page_texts) if len(t.strip()) < 70],
    }
    (CHECK_DIR / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
