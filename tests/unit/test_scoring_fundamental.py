"""Unit tests for core/scoring/fundamental.py"""
import pytest
from core.scoring.fundamental import compute_fundamental_score, piotroski_f_score


HEALTHY_HIGHLIGHTS = {
    "market_cap": 2_500_000_000_000,
    "pe_ratio": 28.5,
    "eps": 6.11,
    "revenue": 400_000_000_000,
    "net_income": 97_000_000_000,
    "debt_to_equity": 0.5,
    "current_ratio": 1.5,
    "roa": 0.18,
    "roe": 0.45,
    "fcf": 90_000_000_000,
}

HEALTHY_VALUATION = {"pb": 3.5, "ev_ebitda": 22.0}


def test_healthy_company_passes_safety():
    result = compute_fundamental_score(HEALTHY_HIGHLIGHTS, HEALTHY_VALUATION)
    assert result["safety_passed"] is True


def test_healthy_company_score_range():
    result = compute_fundamental_score(HEALTHY_HIGHLIGHTS, HEALTHY_VALUATION)
    assert 0 <= result["fundamental_score"] <= 100


def test_distressed_company_fails_safety():
    bad = {
        "market_cap": 10_000_000,
        "revenue": 1_000_000,
        "net_income": -5_000_000,
        "debt_to_equity": 10.0,
        "current_ratio": 0.3,
        "roa": -0.15,
        "roe": -0.5,
        "fcf": -2_000_000,
    }
    result = compute_fundamental_score(bad, {})
    assert result["safety_passed"] is False
    assert result["fundamental_score"] == 0


def test_piotroski_max_score():
    h = {
        "roa": 0.15,
        "fcf": 1e9,
        "debt_to_equity": 0.3,
        "current_ratio": 2.0,
        "roe": 0.3,
        "revenue": 1e10,
        "market_cap": 5e10,
    }
    score = piotroski_f_score(h)
    assert 0 <= score <= 9


def test_piotroski_poor_fundamentals():
    h = {
        "roa": -0.05,
        "fcf": -1e8,
        "debt_to_equity": 3.0,
        "current_ratio": 0.5,
        "roe": -0.1,
        "revenue": 1e8,
        "market_cap": 5e8,
    }
    score = piotroski_f_score(h)
    assert score < 5


def test_none_values_handled():
    result = compute_fundamental_score({}, {})
    # Should not raise, should handle gracefully
    assert "fundamental_score" in result


def test_reproducibility():
    r1 = compute_fundamental_score(HEALTHY_HIGHLIGHTS, HEALTHY_VALUATION)
    r2 = compute_fundamental_score(HEALTHY_HIGHLIGHTS, HEALTHY_VALUATION)
    assert r1["fundamental_score"] == r2["fundamental_score"]
