"""Regime Application Layer — Handlers."""
from __future__ import annotations

import uuid
from src.shared.domain import Ok, Err, Result
from src.regime.domain import (
    RegimeDetectionService,
    IRegimeRepository,
    MarketRegime,
    VIXLevel,
    TrendStrength,
    YieldCurve,
    SP500Position,
)
from .commands import DetectRegimeCommand


class RegimeError(Exception):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


class DetectRegimeHandler:
    """레짐 감지 유스케이스.

    1. 입력 데이터로 Value Objects 생성
    2. RegimeDetectionService.detect() 호출 → (RegimeType, confidence)
    3. MarketRegime 엔티티 조립 후 저장
    4. Ok(result) 반환
    """

    def __init__(self, regime_repo: IRegimeRepository):
        self._regime_repo = regime_repo
        self._detector = RegimeDetectionService()

    def handle(self, cmd: DetectRegimeCommand) -> Result:
        # Value Objects 생성 (domain 레이어)
        try:
            vix = VIXLevel(value=cmd.vix)
            sp500 = SP500Position(current_price=cmd.sp500_price, ma_200=cmd.sp500_ma200)
            trend = TrendStrength(adx=cmd.adx)
            yield_curve = YieldCurve(spread=cmd.yield_spread)
        except ValueError as e:
            return Err(RegimeError(f"Invalid input: {e}", "INVALID_INPUT"))

        # 레짐 감지 (Domain Service) — 반환: tuple[RegimeType, float]
        regime_type, confidence = self._detector.detect(
            vix=vix,
            sp500=sp500,
            trend=trend,
            yield_curve=yield_curve,
        )

        # MarketRegime 엔티티 조립
        regime = MarketRegime(
            _id=str(uuid.uuid4()),
            regime_type=regime_type,
            confidence=confidence,
            vix=vix,
            trend=trend,
            yield_curve=yield_curve,
            sp500=sp500,
        )

        # 저장 (IRegimeRepository.save)
        self._regime_repo.save(regime)

        return Ok({
            "regime_type": regime_type.value,
            "confidence": confidence,
            "vix": cmd.vix,
            "adx": cmd.adx,
            "yield_spread": cmd.yield_spread,
            "sp500_above_ma200": sp500.is_above_ma200,
            "sp500_deviation_pct": round(sp500.deviation_pct, 2),
            "detected_at": regime.detected_at.isoformat(),
        })
