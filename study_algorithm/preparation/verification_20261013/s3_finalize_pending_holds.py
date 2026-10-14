"""Persist individual unresolved findings after reading the complete TARGET item."""

import json
from pathlib import Path

BASE = Path(__file__).parent
path = BASE / "subject3_holds.json"
data = json.loads(path.read_text(encoding="utf-8"))
rows = [
    {"id": "NOTE-S3C2-Q006", "reason": "원문X정답의해설은유통성없음=손실가능성없음이라고잘못설명한다.사적금전채권도채무불이행손실이있고법4조3·9항상발행및권리성격검토가필요해사적·비유통성만으로배제할수없다.원문의일반적인사적채권이정확히무엇을뜻하는지원서교정확인필요.", "evidence_checked": ["TARGET NOTE:41 제06문항전체발문·출판해설", "capital:제4조 제3항·제9항"]},
    {"id": "NOTE-S3C2-Q037", "reason": "교재X는적기시정조치를권고·요구·명령세유형으로한정하지만발문포함된다는표현은이행절차까지포괄할수있다.현행규정3-30~3-33에계획제출·평가·이행절차가같이규정되어원문범위유지시단일정답확정불가.세조치유형의명칭인가로바꾸면원문질문범위가축소되므로보류.", "evidence_checked": ["TARGET NOTE:45 제37문항·출판해설", "financial_investment_rule:제3-26조~제3-33조"]},
    {"id": "S3C2T13-SUP-02", "reason": "원문4보기확인.③의인수대상회사증권전부는법72조의그인수증권매수신용으로최소교정필요.④의1년징역·3천만원벌금부정을확정하려면현행전체벌칙및위임신용공여규정별제재대조가추가필요하여출판정답④만으로승인하지않음.", "evidence_checked": ["TARGET P3:93 전체보기·정답④·행정제재해설", "capital:제72조", "financial_investment_rule:제4-21조"]},
    {"id": "S3C2T28-SUP-02", "reason": "원문4공시유형과정답②확인.①주요경영사항일률다음날·②자율공시다음날까지해야한다는의무표현은현행KRX시장별규정직접대조가필요.기존법161조주요사항보고서는거래소수시공시와다르므로대체근거로승인하지않음.", "evidence_checked": ["TARGET P3:126 제02문항전보기·정답②·해설", "capital:제161조", "현재articles목록에KRX공시규정전체본문없음"]},
]
existing = {row["id"] for row in data["items"]}
data["items"].extend(row for row in rows if row["id"] not in existing)
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(len(data["items"]))
