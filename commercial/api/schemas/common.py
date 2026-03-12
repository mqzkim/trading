"""Common schemas -- disclaimer constant and shared models."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


DISCLAIMER = (
    "이 정보는 투자 참고용 데이터이며 투자 권고나 자문이 아닙니다. "
    "투자 결정의 책임은 투자자에게 있습니다. "
    "This information is provided for reference only and does not constitute "
    "investment advice or recommendation. "
    "Investment decisions are the sole responsibility of the investor."
)


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: Optional[str] = None
