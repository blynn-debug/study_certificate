"""Collect the identified Korean legal source universe; collection is not verification."""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fetch_official import fetch

ROOT = Path(__file__).resolve().parent
LAWS = {
    "tax_framework": "국세기본법",
    "tax_framework_decree": "국세기본법시행령",
    "income": "소득세법",
    "income_decree": "소득세법시행령",
    "tax_special": "조세특례제한법",
    "tax_special_decree": "조세특례제한법시행령",
    "securities_tax": "증권거래세법",
    "securities_tax_decree": "증권거래세법시행령",
    "local_tax": "지방세법",
    "deposit_protection": "예금자보호법",
    "deposit_protection_decree": "예금자보호법시행령",
    "capital": "자본시장과금융투자업에관한법률",
    "capital_decree": "자본시장과금융투자업에관한법률시행령",
    "consumer": "금융소비자보호에관한법률",
    "consumer_decree": "금융소비자보호에관한법률시행령",
    "governance": "금융회사의지배구조에관한법률",
    "governance_decree": "금융회사의지배구조에관한법률시행령",
    "fsc_establishment": "금융위원회의설치등에관한법률",
    "civil": "민법",
    "commercial": "상법",
    "real_estate_registration": "부동산등기법",
    "national_land": "국토의계획및이용에관한법률",
    "national_land_decree": "국토의계획및이용에관한법률시행령",
    "building": "건축법",
    "building_decree": "건축법시행령",
    "reits": "부동산투자회사법",
    "reits_decree": "부동산투자회사법시행령",
    "securitization": "자산유동화에관한법률",
    "retirement": "근로자퇴직급여보장법",
    "retirement_decree": "근로자퇴직급여보장법시행령",
    "insurance": "보험업법",
    "real_estate_appraisal": "감정평가에관한규칙",
    "local_tax_framework": "지방세기본법",
    "inheritance_gift": "상속세및증여세법",
    "inheritance_gift_decree": "상속세및증여세법시행령",
    "corporate_tax": "법인세법",
    "rural_special_tax": "농어촌특별세법",
    "rural_special_tax_decree": "농어촌특별세법시행령",
    "real_name": "금융실명거래및비밀보장에관한법률",
    "real_name_decree": "금융실명거래및비밀보장에관한법률시행령",
    "trust": "신탁법",
    "foreign_exchange": "외국환거래법",
    "motor_liability": "자동차손해배상보장법",
    "housing_lease": "주택임대차보호법",
    "commercial_lease": "상가건물임대차보호법",
    "housing_city_fund": "주택도시기금법",
    "housing_city_fund_decree": "주택도시기금법시행령",
    "treasury_bond": "국채법",
    "treasury_bond_decree": "국채법시행령",
}
RULES = {
    "financial_investment_rule": "금융투자업규정",
    "financial_investment_details": "금융투자업규정시행세칙",
    "consumer_supervision": "금융소비자보호에관한감독규정",
    "inspection_sanctions": "금융기관검사및제재에관한규정",
    "capital_investigation": "자본시장조사업무규정",
    "securities_disclosure_rule": "증권의발행및공시등에관한규정",
    "securities_disclosure_details": "증권의발행및공시등에관한규정시행세칙",
    "governance_supervision": "금융회사지배구조감독규정",
    "foreign_exchange_rule": "외국환거래규정",
    "treasury_issuance_rule": "국고채권의발행및국고채전문딜러운영에관한규정",
}


def collect(pair):
    """Retrieve one known act or regulation; keep failures explicit."""
    source_id, (name, kind) = pair
    path = ROOT / "sources" / f"{source_id}.json"
    if path.exists():
        cached = json.loads(path.read_text(encoding="utf-8"))
        if cached["http_complete"] and cached["characters"] > 2000:
            return {**cached, "source_name": name, "source_kind": kind, "cache": True}
    try:
        result = fetch(source_id, f"https://www.law.go.kr/{kind}/{name}")
        result.update(source_name=name, source_kind=kind)
        return result
    except Exception as exc:
        return {"id": source_id, "source_name": name, "source_kind": kind,
                "status": "retrieval_failed", "error": f"{type(exc).__name__}: {exc}"}


def main():
    """Collect public sources in a modest number of concurrent reads."""
    jobs = {key: (name, "법령") for key, name in LAWS.items()}
    jobs.update({key: (name, "행정규칙") for key, name in RULES.items()})
    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        for row in executor.map(collect, jobs.items()):
            results.append(row)
            print(row["id"], row["status"], row.get("characters", 0), row.get("effective_date_candidates", []), flush=True)
    (ROOT / "source_registry.json").write_text(
        json.dumps({"as_of": "2026-10-13", "unit": "retrieved source, not verified claim",
                    "count": len(results), "items": results}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
