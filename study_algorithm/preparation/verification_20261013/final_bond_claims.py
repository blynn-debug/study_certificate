"""Final bond claims checked against preserved primary sources."""

CLAIMS = []


def claim(key, topics, statement, sources, *, caveat=""):
    """Record the legal proposition without approving other topic questions."""
    CLAIMS.append({
        "id": key, "topic_ids": topics.split(), "verified_statement": statement,
        "article_refs": sources.split(), "issue_ids": [],
        "scope_limit": caveat, "effect": "confirmed", "as_of": "2026-10-13",
        "status": "claim_verified_against_official_text",
        "method": "reviewer_read_current_article_and_scoped_the_claim",
        "reviewer": "codex_assistant", "independent_human_review": False,
        "whole_item_release": False,
    })


claim("FB001", "S3C5T03", "국내 회사채 장기등급은 BBB- 이상이 투자등급이고 BB+ 이하는 투기등급이다. AA부터 B에만 +/- 세분기호가 붙는다.", "fb_kcie_ratings:투자등급", caveat="모든등급에세분기호가붙는다는원해설은오류. 법률상모든투자허용범위가이경계와같다는뜻아님.")
claim("FB002", "S3C5T06", "국고채 통합발행은 만기일과 표면금리를 동일하게 하여 종목당발행규모와유동성을높이는제도로2000년5월도입되었다.", "fb_ktb_fungible:통합발행 fb_ktb_history:2000년")
claim("FB003", "S3C5T07", "2026-02-23 시행국고채발행규정2·29·30·34조는 국채투자매매업인가자중재정경제부장관의PD지정,PPD선행,매월만기별공고물량8%인수,분기딜링용국고채평균잔액1조원이상보유를규정한다.", "treasury_issuance_rule:제2조 treasury_issuance_rule:제29조 treasury_issuance_rule:제30조 treasury_issuance_rule:제34조", caveat="30조2항인수실적산정과3항비율조정권한,34조ETF최대1000억원인정포함. 종전교재10%와기관명수정.")
claim("FB004", "S3C5T07", "KRX국채전문유통시장매매수량은10억원정수배이며장내일반채권은개별경쟁매매,장외시장은상대매매로상장/비상장채권을거래한다.", "fb_krx_bond_market:채권시장 fb_ktb_otc:장외시장 fb_ktb_distribution:시장비교", caveat="현재시장거래량비중의실증주장이나모든거래소협의매매의부재까지증명하지않음.")
claim("FB005", "S3C5T03", "미국재무부FRN은지표금리와고정스프레드의합으로이율을계산하며해당지표를매주재설정한다.", "fb_treasury_frn:변동이율", caveat="특정FRN예시이며모든FRN재설정주기가같다는주장아님. 역변동식과가격민감도는명시된수학모형으로별도검증.")

claim("FB006", "S3C5T14", "SEC회사채투자자교육은원리금부도,금리변동,인플레이션구매력하락,유동성,발행자콜위험을각각설명한다. 만기보유는발행자의부도위험을제거하지않는다.", "fb_sec_bond_risks:투자위험", caveat="미국법상권리내용전체를한국채권법으로전용하지않고공통경제위험정의에한정. 콜옵션은계약에존재할때만적용.")

claim("FB007", "S3C5T06", "재정경제부국채시장낙찰예시에서Dutch는최고낙찰금리일률적용,Conventional은각자응찰금리적용,차등가격은금리구간별최고금리적용으로구분한다.", "fb_ktb_auction:낙찰방식 treasury_issuance_rule:제8조", caveat="낮은응찰금리부터배정하는순서는가격결정방식세종류모두와구별된다. 국고채규정8조8항은공고에따른단일/구간최고금리및FRN특례를정함.")

claim("FB008", "S3C5T14 S3C5T17", "연준2016FEDS연구는미국1973~2016표본에서신용스프레드확대가향후경기침체확률상승과관련됨을보고한다.", "fb_fed_creditcycle:경기와스프레드", caveat="표본내통계관계이지한국현재전시장불변법칙이나개별호황/불황의결과보장이아님. 연구자의견과정책공식전망도구별.")
