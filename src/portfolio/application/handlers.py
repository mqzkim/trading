"""Portfolio Application Layer — Handlers."""
from __future__ import annotations

from datetime import date

from src.shared.domain import Err, Ok, Result
from src.portfolio.domain import (
    ATRStop,
    DrawdownLevel,
    IPortfolioRepository,
    IPositionRepository,
    Portfolio,
    Position,
    PortfolioRiskService,
)

from .commands import ClosePositionCommand, OpenPositionCommand


class PortfolioError(Exception):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


class PortfolioManagerHandler:
    """포트폴리오 관리 유스케이스.

    open_position:  Kelly 사이징 → 낙폭 방어 체크 → ATR Stop → Position 저장
    close_position: 청산 손익 계산 → 저장소에서 제거
    """

    def __init__(
        self,
        portfolio_repo: IPortfolioRepository,
        position_repo: IPositionRepository,
        initial_portfolio_value: float = 100_000.0,
    ):
        self._portfolio_repo = portfolio_repo
        self._position_repo = position_repo
        self._risk_svc = PortfolioRiskService()
        self._initial_value = initial_portfolio_value

    def open_position(self, cmd: OpenPositionCommand) -> Result:
        """포지션 진입 유스케이스.

        Returns:
            Ok({'symbol', 'shares', 'weight', 'entry_price', 'total_value',
                'kelly', 'stop_price'})
            Err(PortfolioError)
        """
        # 1. 포트폴리오 조회 또는 생성
        portfolio = self._portfolio_repo.find_by_id(cmd.portfolio_id)
        if portfolio is None:
            portfolio = Portfolio(
                portfolio_id=cmd.portfolio_id,
                initial_value=self._initial_value,
            )

        # 포지션이 없을 때 total_value=0 이므로 initial_value로 fallback
        portfolio_value = portfolio.total_value or self._initial_value

        # 2. Kelly 사이징
        sizing = self._risk_svc.compute_kelly_size(
            win_rate=cmd.win_rate,
            win_loss_ratio=cmd.win_loss_ratio,
            portfolio_value=portfolio_value,
            price=cmd.entry_price,
        )

        if sizing["shares"] == 0:
            return Err(PortfolioError("Kelly sizing 결과 0주 — 진입 불가", "KELLY_ZERO"))

        # 3. 낙폭 방어 체크 (CAUTION 이상 또는 단일 종목 8% 초과 차단)
        if not portfolio.can_open_position(cmd.symbol, sizing["weight"]):
            dd = portfolio.drawdown_level.value
            return Err(PortfolioError(f"낙폭 방어 발동 ({dd}) — 신규 진입 불가", "DRAWDOWN_BLOCK"))

        # 4. ATR Stop 생성
        atr_stop: ATRStop | None = None
        if cmd.atr is not None:
            atr_stop = self._risk_svc.compute_atr_stop(
                cmd.entry_price, cmd.atr, cmd.atr_multiplier
            )

        # 5. Position 생성 및 저장
        position = Position(
            symbol=cmd.symbol.upper(),
            entry_price=cmd.entry_price,
            quantity=sizing["shares"],
            entry_date=date.today(),
            strategy=cmd.strategy,
            atr_stop=atr_stop,
            sector=cmd.sector,
        )
        portfolio.add_position(position)
        self._position_repo.save(position)
        self._portfolio_repo.save(portfolio)

        return Ok({
            "symbol": cmd.symbol.upper(),
            "shares": sizing["shares"],
            "weight": sizing["weight"],
            "entry_price": cmd.entry_price,
            "total_value": position.market_value,
            "kelly": sizing["kelly"],
            "stop_price": atr_stop.stop_price if atr_stop else None,
        })

    def close_position(self, cmd: ClosePositionCommand) -> Result:
        """포지션 청산 유스케이스.

        Returns:
            Ok({'symbol', 'pnl', 'pnl_pct'})
            Err(PortfolioError)
        """
        position = self._position_repo.find_by_symbol(cmd.symbol.upper())
        if position is None:
            return Err(PortfolioError(f"포지션 없음: {cmd.symbol}", "POSITION_NOT_FOUND"))

        pnl_info = position.close(cmd.exit_price)
        self._position_repo.delete(cmd.symbol.upper())

        portfolio = self._portfolio_repo.find_by_id(cmd.portfolio_id)
        if portfolio and cmd.symbol.upper() in portfolio.positions:
            del portfolio.positions[cmd.symbol.upper()]
            self._portfolio_repo.save(portfolio)

        return Ok(pnl_info)
