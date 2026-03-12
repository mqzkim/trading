"""Signals Application Layer — Handlers."""
from __future__ import annotations

from src.shared.domain import Ok, Err, Result
from src.signals.domain import (
    SignalDirection,
    MethodologyType,
    MethodologyResult,
    SignalFusionService,
    ISignalRepository,
    SIGNAL_STRATEGY_WEIGHTS,
    DEFAULT_SIGNAL_WEIGHTS,
)
from .commands import GenerateSignalCommand

# MethodologyType enum은 대문자 값 사용 (CAN_SLIM, MAGIC_FORMULA 등)
# 커맨드의 소문자 method_name을 대문자로 변환하여 매핑
_METHOD_NAME_MAP: dict[str, str] = {
    "can_slim": "CAN_SLIM",
    "magic_formula": "MAGIC_FORMULA",
    "dual_momentum": "DUAL_MOMENTUM",
    "trend_following": "TREND_FOLLOWING",
}

# core/signals/ evaluator result "signal" key -> MethodologyType mapping
_SIGNAL_KEY_TO_METHOD: dict[str, str] = {
    "CAN SLIM": "CAN_SLIM",
    "Magic Formula": "MAGIC_FORMULA",
    "Dual Momentum": "DUAL_MOMENTUM",
    "Trend Following": "TREND_FOLLOWING",
}


class SignalError(Exception):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


class GenerateSignalHandler:
    """단일 종목 시그널 생성 유스케이스.

    1. 각 방법론별 점수 수집 (CoreSignalAdapter 또는 개별 클라이언트 또는 fallback)
    2. MethodologyResult 리스트 생성
    3. composite_score 산출 (cmd에 제공되면 사용, 없으면 방법론 scores 평균)
    4. SignalFusionService.fuse() 호출 -> (SignalDirection, SignalStrength)
    5. 추론 트레이스 생성
    6. ISignalRepository.save() 저장
    7. Ok(result dict) 반환
    """

    def __init__(
        self,
        signal_repo: ISignalRepository,
        # CoreSignalAdapter (Infrastructure에서 주입) -- 우선 사용
        signal_adapter=None,
        # 방법론별 클라이언트 (레거시 호환)
        can_slim_client=None,
        magic_formula_client=None,
        dual_momentum_client=None,
        trend_following_client=None,
    ):
        self._signal_repo = signal_repo
        self._fusion = SignalFusionService()
        self._adapter = signal_adapter
        self._clients = {
            "can_slim": can_slim_client,
            "magic_formula": magic_formula_client,
            "dual_momentum": dual_momentum_client,
            "trend_following": trend_following_client,
        }

    def handle(self, cmd: GenerateSignalCommand) -> Result:
        symbol = cmd.symbol.upper()

        # 0. Derive market_uptrend from regime for CAN SLIM (SIGNAL-01)
        if self._adapter is not None and cmd.symbol_data is not None and cmd.regime_type is not None:
            market_uptrend = cmd.regime_type in ("Bull", "Sideways")
            cmd_symbol_data = {**cmd.symbol_data, "market_uptrend": market_uptrend}
        else:
            cmd_symbol_data = cmd.symbol_data

        # 1. 방법론별 점수 수집 -> MethodologyResult 리스트 구성
        try:
            if self._adapter is not None and cmd_symbol_data is not None:
                results = self._evaluate_via_adapter(cmd_symbol_data)
            else:
                results = self._evaluate_via_clients(symbol, cmd.methodologies)
        except Exception as e:
            return Err(SignalError(f"Methodology scoring failed: {e}", "SCORING_ERROR"))

        if not results:
            return Err(SignalError("No methodology results available", "NO_RESULTS"))

        # 2. composite_score 결정
        if cmd.composite_score is not None:
            composite_score = cmd.composite_score
        else:
            composite_score = sum(r.score for r in results) / len(results)

        # 3. 합의 시그널 생성 (regime-weighted)
        direction, strength = self._fusion.fuse(
            results=results,
            composite_score=composite_score,
            safety_passed=cmd.safety_passed,
            regime_type=cmd.regime_type,
        )

        # 4. 추론 트레이스 생성 (with regime context and strategy weights)
        weights = SIGNAL_STRATEGY_WEIGHTS.get(cmd.regime_type, DEFAULT_SIGNAL_WEIGHTS) if cmd.regime_type else DEFAULT_SIGNAL_WEIGHTS
        reasoning_trace = self._build_reasoning_trace(
            symbol=symbol,
            direction=direction.value,
            composite_score=composite_score,
            margin_of_safety=cmd.margin_of_safety,
            methodology_results=results,
            safety_passed=cmd.safety_passed,
            regime_type=cmd.regime_type,
            strategy_weights=weights,
        )

        # 5. Structured methodology directions for CLI consumption
        methodology_directions = {
            r.methodology.value: r.direction.value for r in results
        }

        # 6. 저장
        metadata = {
            "methodologies": [r.methodology.value for r in results],
            "scores": {r.methodology.value: r.score for r in results},
            "composite_score": composite_score,
            "consensus_count": strength.consensus_count,
            "safety_passed": cmd.safety_passed,
            "margin_of_safety": cmd.margin_of_safety,
            "reasoning_trace": reasoning_trace,
        }
        self._signal_repo.save(
            symbol=symbol,
            direction=direction.value,
            strength=strength.value,
            metadata=metadata,
        )

        return Ok({
            "symbol": symbol,
            "direction": direction.value,
            "strength": strength.value,
            "consensus_count": strength.consensus_count,
            "methodology_count": len(results),
            "composite_score": composite_score,
            "margin_of_safety": cmd.margin_of_safety,
            "methodology_scores": {r.methodology.value: r.score for r in results},
            "reasoning_trace": reasoning_trace,
            "regime_type": cmd.regime_type,
            "strategy_weights": weights,
            "methodology_directions": methodology_directions,
        })

    # -- Adapter path -----------------------------------------------------------

    def _evaluate_via_adapter(self, symbol_data: dict) -> list[MethodologyResult]:
        """Use CoreSignalAdapter to run all 4 evaluators."""
        raw_results = self._adapter.evaluate_all(symbol_data)
        return self._raw_to_methodology_results(raw_results)

    # -- Legacy client path -----------------------------------------------------

    def _evaluate_via_clients(
        self, symbol: str, methodologies: tuple[str, ...]
    ) -> list[MethodologyResult]:
        """Use individual clients or fallback for each methodology."""
        results: list[MethodologyResult] = []
        for method_name in methodologies:
            data = self._get_methodology_score(symbol, method_name)

            enum_key = _METHOD_NAME_MAP.get(method_name)
            if enum_key is None:
                continue
            try:
                method_type = MethodologyType(enum_key)
            except ValueError:
                continue

            raw_direction = data.get("direction", data.get("signal", "HOLD"))
            try:
                direction = SignalDirection(raw_direction.upper())
            except ValueError:
                direction = SignalDirection.HOLD

            score = float(data.get("score", 50.0))
            score = max(0.0, min(100.0, score))

            results.append(
                MethodologyResult(
                    methodology=method_type,
                    score=score,
                    direction=direction,
                    reason=str(data.get("reason", "")),
                )
            )
        return results

    def _raw_to_methodology_results(self, raw_results: list[dict]) -> list[MethodologyResult]:
        """Convert raw evaluator dicts to MethodologyResult VOs."""
        results: list[MethodologyResult] = []
        for data in raw_results:
            methodology_name = data.get("methodology", "")
            enum_key = _SIGNAL_KEY_TO_METHOD.get(methodology_name)
            if enum_key is None:
                continue
            try:
                method_type = MethodologyType(enum_key)
            except ValueError:
                continue

            raw_signal = data.get("signal", "HOLD")
            try:
                direction = SignalDirection(raw_signal.upper())
            except ValueError:
                direction = SignalDirection.HOLD

            score = float(data.get("score", 50.0))
            score_max = float(data.get("score_max", 100))
            # Normalize to 0-100 scale
            if score_max > 0 and score_max != 100:
                normalized = (score / score_max) * 100
            else:
                normalized = score
            normalized = max(0.0, min(100.0, normalized))

            results.append(
                MethodologyResult(
                    methodology=method_type,
                    score=normalized,
                    direction=direction,
                    reason=str(data.get("reason", "")),
                )
            )
        return results

    # -- Reasoning trace --------------------------------------------------------

    def _build_reasoning_trace(
        self,
        symbol: str,
        direction: str,
        composite_score: float,
        margin_of_safety: float,
        methodology_results: list[MethodologyResult],
        safety_passed: bool,
        regime_type: str | None = None,
        strategy_weights: dict[str, float] | None = None,
    ) -> str:
        """Build human-readable reasoning trace citing specific data points."""
        lines = [f"{symbol}: {direction}"]
        lines.append(f"  Composite Score: {composite_score:.1f}/100")
        lines.append(f"  Margin of Safety: {margin_of_safety:.1%}")
        lines.append(f"  Safety Gate: {'PASS' if safety_passed else 'FAIL'}")
        if regime_type:
            lines.append(f"  Regime: {regime_type}")
        if strategy_weights:
            weight_strs = [f"{k.replace('_', ' ').title()} {v:.0%}" for k, v in strategy_weights.items()]
            lines.append(f"  Strategy Weights: {', '.join(weight_strs)}")
        for r in methodology_results:
            # Use display names for readability
            display_name = r.methodology.value.replace("_", " ").title()
            if display_name == "Can Slim":
                display_name = "CAN SLIM"
            elif display_name == "Magic Formula":
                display_name = "Magic Formula"
            elif display_name == "Dual Momentum":
                display_name = "Dual Momentum"
            elif display_name == "Trend Following":
                display_name = "Trend Following"
            weight_str = f", weight {strategy_weights.get(r.methodology.value, 0.25):.0%}" if strategy_weights else ""
            lines.append(f"  {display_name}: {r.direction.value} (score {r.score:.1f}/100{weight_str})")
        return "\n".join(lines)

    # -- Infrastructure delegation (legacy) -------------------------------------

    def _get_methodology_score(self, symbol: str, method: str) -> dict:
        client = self._clients.get(method)
        if client:
            return client.get(symbol)
        # Fallback: 기존 core/ 로직 (점진적 이전)
        try:
            if method == "can_slim":
                from core.scoring.signal_can_slim import compute_can_slim  # type: ignore
                return compute_can_slim(symbol)
            elif method == "magic_formula":
                from core.scoring.signal_magic_formula import compute_magic_formula  # type: ignore
                return compute_magic_formula(symbol)
            elif method == "dual_momentum":
                from core.scoring.signal_dual_momentum import compute_dual_momentum  # type: ignore
                return compute_dual_momentum(symbol)
            elif method == "trend_following":
                from core.scoring.signal_trend_following import compute_trend_following  # type: ignore
                return compute_trend_following(symbol)
        except ImportError:
            pass
        return {"score": 50.0, "signal": "HOLD", "reason": "fallback default"}
