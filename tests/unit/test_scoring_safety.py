"""Unit tests for core/scoring/safety.py"""
import math
import pytest
from core.scoring.safety import altman_z_score, beneish_m_score, check_safety, ALTMAN_THRESHOLD, BENEISH_THRESHOLD


def test_altman_healthy_company():
    # Healthy company: high working capital, revenue, market cap
    z = altman_z_score(
        working_capital=5e8,
        total_assets=2e9,
        retained_earnings=8e8,
        ebit=3e8,
        market_cap=4e9,
        total_liabilities=8e8,
        revenue=3e9,
    )
    assert z > ALTMAN_THRESHOLD, f"Expected Z > {ALTMAN_THRESHOLD}, got {z}"


def test_altman_distressed_company():
    # Distressed: negative working capital, low revenue
    z = altman_z_score(
        working_capital=-1e8,
        total_assets=1e9,
        retained_earnings=-5e8,
        ebit=-2e8,
        market_cap=1e8,
        total_liabilities=9e8,
        revenue=5e7,
    )
    assert z < ALTMAN_THRESHOLD


def test_altman_zero_assets():
    z = altman_z_score(0, 0, 0, 0, 0, 0, 0)
    assert math.isnan(z)


def test_beneish_clean_company():
    # Clean accounting: neutral values -> M < -1.78
    m = beneish_m_score(1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, -0.05)
    assert m < BENEISH_THRESHOLD


def test_beneish_manipulator():
    # Aggressive values -> M > -1.78
    m = beneish_m_score(1.5, 1.2, 1.3, 1.4, 0.7, 1.5, 1.3, 0.08)
    assert m > BENEISH_THRESHOLD


def test_check_safety_both_pass():
    result = check_safety(z_score=3.0, m_score=-2.5)
    assert result["safety_passed"] is True
    assert result["z_pass"] is True
    assert result["m_pass"] is True


def test_check_safety_z_fail():
    result = check_safety(z_score=1.0, m_score=-2.5)
    assert result["safety_passed"] is False
    assert result["z_pass"] is False


def test_check_safety_m_fail():
    result = check_safety(z_score=3.0, m_score=-1.0)
    assert result["safety_passed"] is False
    assert result["m_pass"] is False


def test_boundary_values():
    # Exactly at threshold -- should fail (not strictly greater)
    r1 = check_safety(z_score=ALTMAN_THRESHOLD, m_score=-2.5)
    assert r1["z_pass"] is False  # must be > threshold

    r2 = check_safety(z_score=3.0, m_score=BENEISH_THRESHOLD)
    assert r2["m_pass"] is False  # must be < threshold
