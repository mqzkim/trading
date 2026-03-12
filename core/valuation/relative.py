"""Relative Multiples valuation model -- pure math, no external dependencies.

Percentile ranking of PER/PBR/EV-EBITDA within GICS sector peers.
Negative PER excluded. Negative EV/EBITDA excluded. PBR always ranked.

References:
- CONTEXT.md: GICS sector comparison, PER/PBR/EV-EBITDA (VALU-03)
"""
from __future__ import annotations


def _percentile_rank(value: float, peers: list[float]) -> float | None:
    """Compute percentile rank of value within peer list.

    Percentile = (count of peers below value / total peers) * 100.
    Returns None if no peers available.
    """
    if not peers:
        return None
    count_below = sum(1 for p in peers if p < value)
    return (count_below / len(peers)) * 100.0


def compute_relative(
    per: float,
    pbr: float,
    ev_ebitda: float,
    sector_pers: list[float],
    sector_pbrs: list[float],
    sector_ev_ebitdas: list[float],
) -> dict:
    """Compute relative multiples percentile ranking within sector.

    Excludes negative PER from PER ranking (returns None).
    Excludes negative EV/EBITDA from EV/EBITDA ranking (returns None).
    PBR is always ranked (can be negative for distressed companies).
    Composite = average of available percentiles. None if none available.
    """
    # PER: exclude negative
    if per < 0:
        per_percentile = None
    else:
        # Filter sector peers to positive PER only
        positive_pers = [p for p in sector_pers if p >= 0]
        per_percentile = _percentile_rank(per, positive_pers)

    # PBR: always ranked
    pbr_percentile = _percentile_rank(pbr, sector_pbrs)

    # EV/EBITDA: exclude negative
    if ev_ebitda < 0:
        ev_ebitda_percentile = None
    else:
        positive_ev_ebitdas = [e for e in sector_ev_ebitdas if e >= 0]
        ev_ebitda_percentile = _percentile_rank(ev_ebitda, positive_ev_ebitdas)

    # Composite: average of available percentiles
    available = [
        p
        for p in [per_percentile, pbr_percentile, ev_ebitda_percentile]
        if p is not None
    ]
    if available:
        composite_percentile = sum(available) / len(available)
    else:
        composite_percentile = None

    # Peer count: maximum of the three lists
    peer_count = max(len(sector_pers), len(sector_pbrs), len(sector_ev_ebitdas))

    return {
        "per_percentile": per_percentile,
        "pbr_percentile": pbr_percentile,
        "ev_ebitda_percentile": ev_ebitda_percentile,
        "composite_percentile": composite_percentile,
        "peer_count": peer_count,
    }
