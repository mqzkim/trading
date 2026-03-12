"""Ensemble valuation + margin of safety -- pure math, no external dependencies.

Confidence-weighted ensemble of DCF (40%) + EPV (35%) + Relative (25%).
Low-confidence models get reduced effective weight, redistributed proportionally.
Margin of safety uses GICS sector-adjusted thresholds.

References:
- CONTEXT.md locked decisions: DCF 40%, EPV 35%, Relative 25%
- Sector MoS thresholds: Tech 25%, Staples 15%, default 20%
"""
from __future__ import annotations

import math

# Base weights per locked decision
VALUATION_WEIGHTS: dict[str, float] = {
    "dcf": 0.40,
    "epv": 0.35,
    "relative": 0.25,
}

# GICS sector -> minimum margin of safety threshold
# Higher-volatility sectors require larger margin of safety
SECTOR_MOS_THRESHOLDS: dict[str, float] = {
    "Information Technology": 0.25,
    "Communication Services": 0.25,
    "Consumer Discretionary": 0.22,
    "Health Care": 0.22,
    "Industrials": 0.20,
    "Materials": 0.20,
    "Energy": 0.20,
    "Real Estate": 0.18,
    "Consumer Staples": 0.15,
    "Utilities": 0.15,
}

DEFAULT_MOS_THRESHOLD = 0.20


def compute_ensemble(
    dcf_value: float,
    dcf_confidence: float,
    epv_value: float,
    epv_confidence: float,
    relative_value: float,
    relative_confidence: float,
) -> dict:
    """Compute confidence-weighted ensemble intrinsic value.

    Each model's effective weight = base_weight * confidence, normalized to sum to 1.0.
    Confidence score = 0.6 * model_agreement + 0.4 * data_completeness.

    Args:
        dcf_value: DCF intrinsic value per share.
        dcf_confidence: DCF model confidence [0, 1].
        epv_value: EPV intrinsic value per share.
        epv_confidence: EPV model confidence [0, 1].
        relative_value: Relative valuation estimate per share.
        relative_confidence: Relative model confidence [0, 1].

    Returns:
        Dict with intrinsic_value, confidence, effective_weights,
        model_agreement, data_completeness.
    """
    models = {
        "dcf": (dcf_value, dcf_confidence),
        "epv": (epv_value, epv_confidence),
        "relative": (relative_value, relative_confidence),
    }

    # Step 1: Compute raw weights = base_weight * confidence
    raw_weights = {
        name: VALUATION_WEIGHTS[name] * conf
        for name, (_, conf) in models.items()
    }
    total_raw = sum(raw_weights.values())

    # Edge case: all zero confidence
    if total_raw <= 0:
        return {
            "intrinsic_value": 0.0,
            "confidence": 0.0,
            "effective_weights": {"dcf": 0.0, "epv": 0.0, "relative": 0.0},
            "model_agreement": 0.0,
            "data_completeness": 0.0,
        }

    # Step 2: Normalize to effective weights summing to 1.0
    effective_weights = {
        name: raw / total_raw for name, raw in raw_weights.items()
    }

    # Step 3: Weighted intrinsic value
    intrinsic_value = sum(
        effective_weights[name] * val for name, (val, _) in models.items()
    )

    # Step 4: Model agreement -- 1 - CV of positive model values
    positive_values = [val for val, conf in models.values() if val > 0 and conf > 0]
    if len(positive_values) >= 2:
        mean_v = sum(positive_values) / len(positive_values)
        if mean_v > 0:
            variance = sum((v - mean_v) ** 2 for v in positive_values) / len(positive_values)
            cv = math.sqrt(variance) / mean_v
            model_agreement = max(0.0, 1.0 - cv)
        else:
            model_agreement = 0.0
    elif len(positive_values) == 1:
        # Single model: cannot compute CV, penalize agreement
        model_agreement = 0.0
    else:
        model_agreement = 0.0

    # Step 5: Data completeness = total_raw / sum(base_weights)
    sum_base = sum(VALUATION_WEIGHTS.values())
    data_completeness = total_raw / sum_base if sum_base > 0 else 0.0

    # Step 6: Combined confidence = 0.6 * agreement + 0.4 * completeness
    confidence = 0.6 * model_agreement + 0.4 * data_completeness
    confidence = max(0.0, min(1.0, confidence))

    return {
        "intrinsic_value": intrinsic_value,
        "confidence": confidence,
        "effective_weights": effective_weights,
        "model_agreement": model_agreement,
        "data_completeness": data_completeness,
    }


def compute_margin_of_safety(
    intrinsic_mid: float,
    market_price: float,
    sector: str,
) -> dict:
    """Compute margin of safety with sector-adjusted thresholds.

    MoS = (intrinsic - market) / intrinsic.
    Positive MoS means stock is undervalued.

    Args:
        intrinsic_mid: Ensemble intrinsic value per share.
        market_price: Current market price per share.
        sector: GICS sector name for threshold lookup.

    Returns:
        Dict with margin_of_safety, sector_threshold, has_margin.
    """
    if intrinsic_mid == 0:
        return {
            "margin_of_safety": 0.0,
            "sector_threshold": SECTOR_MOS_THRESHOLDS.get(sector, DEFAULT_MOS_THRESHOLD),
            "has_margin": False,
        }

    mos = (intrinsic_mid - market_price) / intrinsic_mid
    sector_threshold = SECTOR_MOS_THRESHOLDS.get(sector, DEFAULT_MOS_THRESHOLD)
    has_margin = mos >= sector_threshold

    return {
        "margin_of_safety": mos,
        "sector_threshold": sector_threshold,
        "has_margin": has_margin,
    }
