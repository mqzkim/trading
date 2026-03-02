"""Regime-based strategy weights and risk adjustments."""

REGIME_WEIGHTS = {
    "Low-Vol Bull":  {"canslim": 0.30, "magic": 0.20, "momentum": 0.25, "trend": 0.25},
    "High-Vol Bull": {"canslim": 0.20, "magic": 0.25, "momentum": 0.25, "trend": 0.30},
    "Low-Vol Range": {"canslim": 0.15, "magic": 0.40, "momentum": 0.20, "trend": 0.25},
    "High-Vol Bear": {"canslim": 0.10, "magic": 0.35, "momentum": 0.30, "trend": 0.25},
    "Transition":    {"canslim": 0.25, "magic": 0.25, "momentum": 0.25, "trend": 0.25},
}

RISK_ADJUSTMENT = {
    "Low-Vol Bull": 1.0,
    "High-Vol Bull": 0.7,
    "Low-Vol Range": 0.8,
    "High-Vol Bear": 0.3,
    "Transition": 0.5,
}

def get_weights(regime: str) -> dict:
    return REGIME_WEIGHTS.get(regime, REGIME_WEIGHTS["Transition"])

def get_risk_adjustment(regime: str) -> float:
    return RISK_ADJUSTMENT.get(regime, 0.5)
