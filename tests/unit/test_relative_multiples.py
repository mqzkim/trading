"""Tests for Relative Multiples valuation model pure math.

Covers: compute_relative() percentile ranking, negative metric exclusion,
composite averaging, and edge cases.
"""
from __future__ import annotations

import pytest

from core.valuation.relative import compute_relative


class TestComputeRelative:
    def test_percentile_ranking_within_sector(self) -> None:
        """Stock's PER/PBR/EV-EBITDA ranked as percentiles within sector data."""
        result = compute_relative(
            per=15.0,
            pbr=2.0,
            ev_ebitda=10.0,
            sector_pers=[10.0, 12.0, 15.0, 18.0, 20.0],
            sector_pbrs=[1.0, 1.5, 2.0, 2.5, 3.0],
            sector_ev_ebitdas=[8.0, 9.0, 10.0, 12.0, 15.0],
        )
        assert result["per_percentile"] is not None
        assert result["pbr_percentile"] is not None
        assert result["ev_ebitda_percentile"] is not None
        assert result["peer_count"] == 5

    def test_negative_per_excluded(self) -> None:
        """Negative PER -> per_percentile=None (excluded from ranking)."""
        result = compute_relative(
            per=-5.0,
            pbr=2.0,
            ev_ebitda=10.0,
            sector_pers=[10.0, 15.0, 20.0],
            sector_pbrs=[1.0, 2.0, 3.0],
            sector_ev_ebitdas=[8.0, 10.0, 12.0],
        )
        assert result["per_percentile"] is None

    def test_negative_ebitda_excluded(self) -> None:
        """Negative EV/EBITDA -> ev_ebitda_percentile=None."""
        result = compute_relative(
            per=15.0,
            pbr=2.0,
            ev_ebitda=-3.0,
            sector_pers=[10.0, 15.0, 20.0],
            sector_pbrs=[1.0, 2.0, 3.0],
            sector_ev_ebitdas=[8.0, 10.0, 12.0],
        )
        assert result["ev_ebitda_percentile"] is None

    def test_composite_averages_available_multiples(self) -> None:
        """Composite percentile = average of non-None percentiles."""
        result = compute_relative(
            per=-5.0,  # excluded -> None
            pbr=2.0,
            ev_ebitda=10.0,
            sector_pers=[10.0, 15.0, 20.0],
            sector_pbrs=[1.0, 2.0, 3.0],
            sector_ev_ebitdas=[8.0, 10.0, 12.0],
        )
        # Only PBR and EV/EBITDA contribute
        assert result["per_percentile"] is None
        available = [
            p
            for p in [result["pbr_percentile"], result["ev_ebitda_percentile"]]
            if p is not None
        ]
        expected_composite = sum(available) / len(available)
        assert result["composite_percentile"] == pytest.approx(
            expected_composite, rel=1e-6
        )

    def test_median_stock_gets_approx_50th_percentile(self) -> None:
        """Stock at sector median gets ~50th percentile."""
        sector_pers = [10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 26.0, 28.0]
        # Median is between 18 and 20 -> a stock at 19 should be ~50th percentile
        result = compute_relative(
            per=19.0,
            pbr=2.0,
            ev_ebitda=10.0,
            sector_pers=sector_pers,
            sector_pbrs=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5],
            sector_ev_ebitdas=[6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
        )
        # ~50% of peers below 19 in sector_pers
        assert 40.0 <= result["per_percentile"] <= 60.0

    def test_all_multiples_unavailable_returns_none_composite(self) -> None:
        """All multiples unavailable -> composite_percentile=None."""
        result = compute_relative(
            per=-5.0,
            pbr=2.0,
            ev_ebitda=-3.0,
            sector_pers=[10.0, 15.0],
            sector_pbrs=[],  # no peers
            sector_ev_ebitdas=[8.0, 10.0],
        )
        # PER excluded (negative), PBR no peers, EV/EBITDA excluded (negative)
        assert result["composite_percentile"] is None
