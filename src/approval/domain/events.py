"""Approval Domain -- Domain Events.

Events for cross-context communication via SyncEventBus.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.shared.domain import DomainEvent


@dataclass(frozen=True)
class ApprovalCreatedEvent(DomainEvent):
    """Emitted when a new strategy approval is created."""

    approval_id: str = ""


@dataclass(frozen=True)
class ApprovalSuspendedEvent(DomainEvent):
    """Emitted when an approval is suspended."""

    approval_id: str = ""
    reason: str = ""
