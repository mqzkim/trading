"""Performance application -- commands."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ApproveProposalCommand:
    proposal_id: str


@dataclass
class RejectProposalCommand:
    proposal_id: str
