"""Pipeline Infrastructure -- Notification Services.

Notifier protocol + SlackNotifier (webhook) + LogNotifier (fallback).
SlackNotifier never raises on failure -- logs warning and continues.
"""
from __future__ import annotations

import logging
from typing import Protocol

import httpx

logger = logging.getLogger(__name__)


class Notifier(Protocol):
    """Notification protocol -- send pipeline status messages."""

    def notify(self, title: str, message: str, level: str = "info") -> None: ...


_EMOJI_MAP = {
    "info": ":information_source:",
    "warning": ":warning:",
    "error": ":rotating_light:",
    "success": ":white_check_mark:",
}


class SlackNotifier:
    """Send notifications via Slack webhook.

    Gracefully logs warning on failure -- never raises.
    If webhook_url is None, silently skips.
    """

    def __init__(self, webhook_url: str | None) -> None:
        self._webhook_url = webhook_url

    def notify(self, title: str, message: str, level: str = "info") -> None:
        """Send a Slack notification. No-op if webhook URL is not configured."""
        if not self._webhook_url:
            logger.debug("Slack notification skipped: no webhook URL configured")
            return

        emoji = _EMOJI_MAP.get(level, ":speech_balloon:")
        payload = {"text": f"{emoji} *{title}*\n{message}"}

        try:
            resp = httpx.post(self._webhook_url, json=payload, timeout=10.0)
            resp.raise_for_status()
        except Exception as e:
            logger.warning("Slack notification failed: %s", e)


class LogNotifier:
    """Fallback notifier that logs messages via Python logging."""

    def notify(self, title: str, message: str, level: str = "info") -> None:
        """Log the notification at appropriate level."""
        log_level = logging.WARNING if level == "error" else logging.INFO
        logger.log(log_level, "[%s] %s: %s", level.upper(), title, message)
