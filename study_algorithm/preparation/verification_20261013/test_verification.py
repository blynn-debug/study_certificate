"""Regressions for legal evidence separation, version gates, and actual corrections."""

import hashlib
import json
from pathlib import Path

import pytest

from legal_index import parse_articles, read_article

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_old_addenda_are_not_indexed_as_current_article_one():
    text = "법률 [시행 2026. 7. 1.]\n제1조(목적) 현재 본문\n제2조의3(특례) 현재 특례\n부  칙 <2020>\n제1조(시행일) 옛 시행일"
    result = parse_articles("sample", text)
    assert [x["article"] for x in result["items"]] == ["제1조", "제2조의3"]
    assert "옛 시행일" not in result["items"][0]["text"]
    assert "옛 시행일" in result["supplementary_provisions"]


def test_kofia_hyphenated_articles_are_not_merged():
    result = parse_articles("rule", "제2-29조(대상) 하나\n제2-29조의2(예외) 둘\n제3조(끝) 셋")
    assert [x["article"] for x in result["items"]] == ["제2-29조", "제2-29조의2", "제3조"]


def test_ambiguous_article_numbers_fail_closed(tmp_path, monkeypatch):
    import legal_index
    (tmp_path / "articles").mkdir()
    value = {"items": [{"article": "제1조"}, {"article": "제1조"}]}
    (tmp_path / "articles/law.json").write_text(json.dumps(value), encoding="utf-8")
    monkeypatch.setattr(legal_index, "ROOT", tmp_path)
    with pytest.raises(ValueError):
        read_article("law", "제1조")


def test_future_kofia_versions_are_not_current_sources():
    business = load("sources/kofia_business.json")
    assert "historySeq=1803" in business["retrieved_url"]
    assert "historySeq=1811" not in business["retrieved_url"]
    reviews = {x["id"]: x for x in load("source_version_reviews.json")["items"]}
    assert reviews["V001"]["state"] == "future_version_excluded"
    assert "2026년 12월 1일" in reviews["V001"]["evidence"][0]["quote"]


def test_pdf_annex_has_real_hash_and_is_not_a_guessed_formula():
    ref = read_article("financial_investment_details_annex15", "별표15")
    assert "총외화자산" in ref["text"]
    assert ref["sha256"] == hashlib.sha256(ref["text"].encode("utf-8")).hexdigest()
    meta = load("sources/financial_investment_details_annex15.json")
    raw = (ROOT / "sources/financial_investment_details_annex15.pdf").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == meta["content_sha256"]


def test_period_asset_liability_ratio_is_not_maturity_gap_ratio():
    # A numeric witness for the actual textbook/prior-analysis mistake.
    asset_one_month, liability_one_month, total_fx_asset = 80, 100, 200
    gap = (asset_one_month - liability_one_month) / total_fx_asset
    assert gap == -0.10
    assert asset_one_month / liability_one_month < 0.90


def test_official_exam_uses_inclusive_70_and_40_boundaries():
    data = load("exam_structure.json")["data"]
    master = data["examMst"]
    assert int(master["successStd"]) == 70
    assert int(master["rejectStd"]) == 40
    assert int(master["itemCnt"]) == 100


def test_every_verified_claim_has_retrievable_official_evidence():
    claims = load("verified_claims.json")["items"]
    assert len(claims) == len({x["id"] for x in claims})
    for claim in claims:
        assert claim["whole_item_release"] is False
        assert claim["as_of"] == "2026-10-13"
        assert claim["evidence"]
        for source in claim["evidence"]:
            assert source["url"].startswith("https://")
            assert source["article_sha256"] == hashlib.sha256(source["text"].encode("utf-8")).hexdigest()


def test_no_items_disappear_when_source_errors_are_held():
    registry = load("item_verification_registry.json")["items"]
    summary = load("verification_summary.json")
    assert len(registry) == len({x["id"] for x in registry}) == 2292
    assert sum(summary["item_states"].values()) == 2292
    errors = {x["id"] for x in registry if x["original_source_state"] == "held_source_correction"}
    assert {"S1C1T03-SUP-02", "S3C2T10-SUP-01", "S3C2-ADD-14"} <= errors
    assert summary["complete_current_law_item_verification"] is False
