"""Regime Application Layer -- Handlers."""
from __future__ import annotations

import uuid
from src.shared.domain import Ok, Err, Result
from src.shared.infrastructure.sync_event_bus import SyncEventBus
from src.regime.domain import (
    RegimeDetectionService,
    IRegimeRepository,
    MarketRegime,
    RegimeChangedEvent,
    RegimeType,
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
    """Regime detection use case.

    1. Fetch data if command has sentinel zeros (fallback pattern)
    2. Create Value Objects from input data
    3. RegimeDetectionService.detect() -> (RegimeType, confidence)
    4. Track 3-day confirmation via find_latest()
    5. Publish RegimeChangedEvent only on confirmed regime transition
    6. Save MarketRegime entity and return Ok(result)
    """

    def __init__(
        self,
        regime_repo: IRegimeRepository,
        bus: SyncEventBus | None = None,
        data_client: object | None = None,
    ):
        self._regime_repo = regime_repo
        self._bus = bus
        self._data_client = data_client
        self._detector = RegimeDetectionService()
        self._last_confirmed_type: RegimeType | None = None

    def _fetch_regime_data(self) -> dict:
        """Fetch regime indicator values from data client or fallback import."""
        if self._data_client is not None:
            return self._data_client.fetch_regime_snapshot()  # type: ignore[union-attr]
        # Fallback: direct import (same pattern as ScoreSymbolHandler)
        from src.data_ingest.infrastructure.regime_data_client import (
            RegimeDataClient,
        )

        client = RegimeDataClient()
        return client.fetch_regime_snapshot()

    def handle(self, cmd: DetectRegimeCommand) -> Result:
        # Sentinel detection: all zeros means "fetch data automatically"
        if cmd.vix == 0.0 and cmd.sp500_price == 0.0 and cmd.adx == 0.0:
            snapshot = self._fetch_regime_data()
            cmd = DetectRegimeCommand(
                vix=snapshot["vix"],
                sp500_price=snapshot["sp500_close"],
                sp500_ma200=snapshot["sp500_ma200"],
                adx=snapshot["adx"],
                yield_spread=snapshot["yield_spread"],
            )

        # Value Objects (domain layer)
        try:
            vix = VIXLevel(value=cmd.vix)
            sp500 = SP500Position(
                current_price=cmd.sp500_price, ma_200=cmd.sp500_ma200
            )
            trend = TrendStrength(adx=cmd.adx)
            yield_curve = YieldCurve(spread=cmd.yield_spread)
        except ValueError as e:
            return Err(RegimeError(f"Invalid input: {e}", "INVALID_INPUT"))

        # Regime detection (Domain Service)
        regime_type, confidence = self._detector.detect(
            vix=vix,
            sp500=sp500,
            trend=trend,
            yield_curve=yield_curve,
        )

        # 3-day confirmation state machine
        previous = self._regime_repo.find_latest()

        if previous and previous.regime_type == regime_type:
            confirmed_days = previous.confirmed_days + 1
        else:
            confirmed_days = 1

        # Construct MarketRegime with confirmation tracking
        regime = MarketRegime(
            _id=str(uuid.uuid4()),
            regime_type=regime_type,
            confidence=confidence,
            vix=vix,
            trend=trend,
            yield_curve=yield_curve,
            sp500=sp500,
            confirmed_days=confirmed_days,
        )

        # Initialize last confirmed type from repo on first call
        if self._last_confirmed_type is None and previous and previous.is_confirmed:
            self._last_confirmed_type = previous.regime_type

        # Publish event only when:
        # 1. Regime is confirmed (>=3 consecutive days)
        # 2. Regime differs from last confirmed regime (or no prior confirmation)
        should_publish = regime.is_confirmed and (
            self._last_confirmed_type is None
            or self._last_confirmed_type != regime_type
        )

        if should_publish and self._bus is not None:
            event = RegimeChangedEvent(
                previous_regime=(
                    self._last_confirmed_type
                    if self._last_confirmed_type is not None
                    else regime_type
                ),
                new_regime=regime_type,
                confidence=confidence,
                vix_value=cmd.vix,
                adx_value=cmd.adx,
            )
            self._bus.publish(event)

        # Update last confirmed type when regime becomes confirmed
        if regime.is_confirmed:
            self._last_confirmed_type = regime_type

        # Save to repo
        self._regime_repo.save(regime)

        return Ok(
            {
                "regime_type": regime_type.value,
                "confidence": confidence,
                "vix": cmd.vix,
                "adx": cmd.adx,
                "yield_spread": cmd.yield_spread,
                "sp500_above_ma200": sp500.is_above_ma200,
                "sp500_deviation_pct": round(sp500.deviation_pct, 2),
                "detected_at": regime.detected_at.isoformat(),
                "confirmed_days": confirmed_days,
                "is_confirmed": regime.is_confirmed,
            }
        )
