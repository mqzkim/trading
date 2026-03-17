"""Self-improver domain -- value objects."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WeightProposal:
    """A proposed weight adjustment for a scoring axis in a specific regime.

    Only covers fundamental/technical/sentiment axis weights.
    Never proposes risk parameter changes (ATR multiplier, Kelly fraction, etc).
    """

    id: str  # UUID4 string
    regime: str  # "Bull" | "Bear" | "Sideways" | "Crisis" | "Transition"
    axis: str  # "fundamental" | "technical" | "sentiment"
    current_weight: float
    proposed_weight: float
    walk_forward_sharpe: float
    status: str = "pending"  # "pending" | "approved" | "rejected"
