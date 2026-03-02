"""Signals Application Layer — Handlers."""
from __future__ import annotations

from src.shared.domain import Ok, Err, Result
from src.signals.domain import (
    SignalDirection,
    MethodologyType,
    MethodologyResult,
    SignalFusionService,
    ISignalRepository,
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


class SignalError(Exception):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


class GenerateSignalHandler:
    """단일 종목 시그널 생성 유스케이스.

    1. 각 방법론별 점수 수집 (Infrastructure 위임 또는 core/ fallback)
    2. MethodologyResult 리스트 생성
    3. composite_score 산출 (cmd에 제공되면 사용, 없으면 방법론 scores 평균)
    4. SignalFusionService.fuse() 호출 → (SignalDirection, SignalStrength)
    5. ISignalRepository.save() 저장
    6. Ok(result dict) 반환
    """

    def __init__(
        self,
        signal_repo: ISignalRepository,
        # 방법론별 클라이언트 (Infrastructure에서 주입)
        can_slim_client=None,
        magic_formula_client=None,
        dual_momentum_client=None,
        trend_following_client=None,
    ):
        self._signal_repo = signal_repo
        self._fusion = SignalFusionService()
        self._clients = {
            "can_slim": can_slim_client,
            "magic_formula": magic_formula_client,
            "dual_momentum": dual_momentum_client,
            "trend_following": trend_following_client,
        }

    def handle(self, cmd: GenerateSignalCommand) -> Result:
        symbol = cmd.symbol.upper()

        # 1. 각 방법론별 점수 수집 → MethodologyResult 리스트 구성
        try:
            results: list[MethodologyResult] = []
            for method_name in cmd.methodologies:
                data = self._get_methodology_score(symbol, method_name)

                enum_key = _METHOD_NAME_MAP.get(method_name)
                if enum_key is None:
                    continue
                try:
                    method_type = MethodologyType(enum_key)
                except ValueError:
                    continue

                raw_direction = data.get("direction", "HOLD")
                try:
                    direction = SignalDirection(raw_direction.upper())
                except ValueError:
                    direction = SignalDirection.HOLD

                score = float(data.get("score", 50.0))
                # score 범위 클램핑 (도메인 validation 대비)
                score = max(0.0, min(100.0, score))

                results.append(
                    MethodologyResult(
                        methodology=method_type,
                        score=score,
                        direction=direction,
                        reason=str(data.get("reason", "")),
                    )
                )
        except Exception as e:
            return Err(SignalError(f"Methodology scoring failed: {e}", "SCORING_ERROR"))

        if not results:
            return Err(SignalError("No methodology results available", "NO_RESULTS"))

        # 2. composite_score 결정
        if cmd.composite_score is not None:
            composite_score = cmd.composite_score
        else:
            composite_score = sum(r.score for r in results) / len(results)

        # 3. 합의 시그널 생성 — fuse()는 tuple[SignalDirection, SignalStrength] 반환
        direction, strength = self._fusion.fuse(
            results=results,
            composite_score=composite_score,
            safety_passed=cmd.safety_passed,
        )

        # 4. 저장
        metadata = {
            "methodologies": [r.methodology.value for r in results],
            "scores": {r.methodology.value: r.score for r in results},
            "composite_score": composite_score,
            "consensus_count": strength.consensus_count,
            "safety_passed": cmd.safety_passed,
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
            "methodology_scores": {r.methodology.value: r.score for r in results},
        })

    # ── Infrastructure 위임 ──────────────────────────────────────────

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
        # 기본값 반환
        return {"score": 50.0, "direction": "HOLD", "reason": "fallback default"}
