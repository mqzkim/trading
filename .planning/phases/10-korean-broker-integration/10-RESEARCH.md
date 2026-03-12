# Phase 10: Korean Broker Integration - Research

**Researched:** 2026-03-13
**Domain:** KIS (한국투자증권) broker adapter, Korean market order rules, DDD broker abstraction
**Confidence:** HIGH (codebase analysis) / MEDIUM (python-kis library specifics)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- KIS 개발자 등록 아직 미완료 — Mock-first로 개발
- 한국투자증권(KIS) 사용 확정
- Mock 모드로 전체 개발 완료 후 실제 KIS API 연결 (Alpaca mock fallback 패턴 동일)
- 인증 정보는 .env 패턴 동일: KIS_APP_KEY, KIS_APP_SECRET, KIS_ACCOUNT_NO
- 한국 시장은 bracket order 미지원 — 시스템 모니터링 기반 stop loss
- 일간 가격 체크 후 조건 충족 시 시장가 매도 주문 제출 (중기 보유 전략에 적합)
- 기본 주문 유형: 시장가 (중기 보유라 슬리페이지 무시 가능)
- BUY/SELL 모두 지원 (stop loss 자동 매도에 필요)
- 호가 단위 + 가격제한(+-30%) 자동 검증 (잘못된 주문 방지)
- US/KR 포트폴리오 분리 운영 (각각 별도 자본금, 환율 고려 불필요)
- 포지션 사이징 룰 동일 적용: Fractional Kelly(1/4) + ATR 기반 stop loss
- KRW 자본금은 .env에 설정: KR_CAPITAL (예: 10000000)
- 통화만 KRW로 변경, 나머지 리스크 룰 동일
- execution/domain에 IBrokerAdapter ABC 정의 (DDD 원칙 준수)
- AlpacaExecutionAdapter와 KisExecutionAdapter 모두 IBrokerAdapter 구현
- 핸들러는 인터페이스만 의존 — bootstrap에서 시장별 어댑터 주입
- BracketSpec을 범용 OrderSpec으로 확장 (stop_loss/take_profit 선택적 필드)
- Alpaca는 OrderSpec을 bracket order로 변환, KIS는 단건 주문으로 변환
- CLI --market kr/us 플래그로 시장 전환 (Phase 6에서 도입한 패턴 동일)

### Claude's Discretion
- IBrokerAdapter 메서드 시그니처 세부 설계
- Mock 모드 응답 데이터 구조
- 호가 단위 테이블 구현 방식
- Stop loss 모니터링 스케줄링 메커니즘
- KIS API 에러 핸들링 및 재시도 정책

### Deferred Ideas (OUT OF SCOPE)
- KIS 실전 매매 지원 — Phase 10은 모의투자만, 실전은 Paper Trading 검증 후
- 환율 변환 및 US/KR 통합 포트폴리오 뷰 — 현재는 분리 운영
- KIS WebSocket 실시간 호가 — 중기 보유 전략에 불필요
- 한국 시장 특화 리스크 룰 (가격제한폭 활용 등) — 동일 룰 우선 적용
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| KR-01 | python-kis 기반 KIS 브로커 어댑터 (IBrokerRepository 구현) | IBrokerAdapter ABC 설계, KisExecutionAdapter 구현 패턴 |
| KR-02 | KIS 모의투자 지원 (mock trading 환경) | Mock fallback 패턴 (AlpacaExecutionAdapter 동일), KIS paper trading URL |
| KR-03 | KRW 통화 처리 및 포지션 사이징 적용 | OrderSpec 확장, KR_CAPITAL 설정, 호가 단위 검증 |
</phase_requirements>

---

## Summary

Phase 10은 기존 AlpacaExecutionAdapter 패턴을 한국 시장에 복제한다. 핵심 작업은 세 가지다: (1) `IBrokerAdapter` ABC를 `execution/domain/repositories.py`에 추가하여 `TradePlanHandler`가 구체 어댑터 대신 인터페이스에 의존하도록 리팩터링, (2) `KisExecutionAdapter`를 mock-first로 구현, (3) `BracketSpec`을 `OrderSpec`으로 확장하여 stop_loss/take_profit이 선택적 필드가 되도록 변경.

한국 시장의 핵심 제약은 bracket order 미지원이다. KIS는 단건 주문만 지원하므로, stop loss는 시스템 모니터링(CLI command 또는 cron)을 통해 일간 가격 체크 후 별도 매도 주문으로 처리해야 한다. 호가 단위(tick size)는 주가 구간에 따라 5단계로 다르며, 주문 제출 전 자동 검증이 필요하다.

python-kis 라이브러리는 KIS Open API를 Python으로 래핑한 PyPI 패키지다. 모의투자(paper trading) 환경은 실전과 동일한 API 엔드포인트에 별도 baseURL로 접근하며, 인증 토큰 발급 → 주문 제출 → 잔고 조회 흐름이 Alpaca와 유사하다.

**Primary recommendation:** `IBrokerAdapter` 추상화 → `AlpacaExecutionAdapter` 래핑 → `KisExecutionAdapter` 추가 순서로 구현. 모든 로직은 mock 모드로 먼저 완성하고 실제 KIS 연결은 선택적 확장으로 남긴다.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python-kis | latest | KIS Open API Python 래퍼 | KIS 공식 지원 라이브러리 |
| pydantic-settings | 2.x | KIS_APP_KEY 등 .env 설정 로드 | 기존 프로젝트 패턴 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-dateutil | stdlib | 한국 시장 시간 처리 | 장 운영시간 체크 필요 시 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| python-kis | KIS REST API 직접 호출 | 직접 호출은 토큰 관리, 헤더 구성 등 반복 코드 증가. python-kis가 이를 추상화 |

**Installation:**
```bash
pip install python-kis
```

---

## Architecture Patterns

### Recommended Project Structure

이 Phase에서 변경/추가되는 파일:

```
src/
├── execution/
│   ├── domain/
│   │   ├── repositories.py      # IBrokerAdapter ABC 추가
│   │   └── value_objects.py     # BracketSpec → OrderSpec 확장
│   ├── infrastructure/
│   │   ├── alpaca_adapter.py    # IBrokerAdapter 구현으로 래핑
│   │   └── kis_adapter.py       # 신규: KisExecutionAdapter
│   └── application/
│       └── handlers.py          # AlpacaExecutionAdapter → IBrokerAdapter 타입 전환
├── bootstrap.py                 # --market 플래그 기반 어댑터 주입
└── cli/
    └── main.py                  # execute 명령 --market 확장
```

### Pattern 1: IBrokerAdapter ABC 정의

**What:** `execution/domain/repositories.py`에 `IBrokerAdapter` ABC 추가. 도메인 레이어에 인터페이스, 인프라 레이어에 구현체.

**When to use:** `TradePlanHandler`가 구체 어댑터(Alpaca/KIS)를 알 필요 없을 때.

```python
# src/execution/domain/repositories.py
from abc import ABC, abstractmethod
from .value_objects import OrderSpec, OrderResult

class IBrokerAdapter(ABC):
    """브로커 어댑터 인터페이스. 모든 시장 어댑터가 구현."""

    @abstractmethod
    def submit_order(self, spec: OrderSpec) -> OrderResult: ...

    @abstractmethod
    def get_positions(self) -> list[dict]: ...

    @abstractmethod
    def get_account(self) -> dict: ...
```

### Pattern 2: OrderSpec (BracketSpec 확장)

**What:** `BracketSpec`을 `OrderSpec`으로 확장. `stop_loss_price`와 `take_profit_price`를 `Optional[float]`으로 변경. `BracketSpec`은 backward-compat re-export로 유지.

```python
# src/execution/domain/value_objects.py
@dataclass(frozen=True)
class OrderSpec(ValueObject):
    """범용 주문 스펙. Alpaca는 bracket으로, KIS는 단건으로 변환."""

    symbol: str = ""
    quantity: int = 0
    entry_price: float = 0.0
    direction: str = "BUY"                    # BUY / SELL
    stop_loss_price: Optional[float] = None   # KIS: 시스템 모니터링
    take_profit_price: Optional[float] = None # KIS: 미사용

# Backward compatibility
BracketSpec = OrderSpec
```

### Pattern 3: KisExecutionAdapter (mock-first)

**What:** `AlpacaExecutionAdapter`와 동일한 mock fallback 패턴. credentials 없으면 자동 mock.

```python
# src/execution/infrastructure/kis_adapter.py
class KisExecutionAdapter(IBrokerAdapter):
    def __init__(
        self,
        app_key: Optional[str] = None,
        app_secret: Optional[str] = None,
        account_no: Optional[str] = None,
    ) -> None:
        self._use_mock = not (app_key and app_secret and account_no)
        # python-kis lazy import: _init_client()에서만 import

    def submit_order(self, spec: OrderSpec) -> OrderResult:
        if self._use_mock:
            return self._mock_order(spec)
        return self._real_order(spec)
```

### Pattern 4: 호가 단위(Tick Size) 검증

**What:** 한국 시장 호가 단위 테이블 적용. 주가 구간별 tick size를 계산하여 주문 가격을 반올림.

**Korean tick size table (KRX 기준):**
```python
# src/execution/infrastructure/kis_adapter.py
def _tick_size(price: float) -> int:
    """KRX 호가 단위 (2024년 기준)."""
    if price < 1_000:      return 1
    if price < 5_000:      return 5
    if price < 10_000:     return 10
    if price < 50_000:     return 50
    if price < 100_000:    return 100
    if price < 500_000:    return 500
    return 1_000

def _round_to_tick(price: float) -> int:
    """주가를 호가 단위로 반올림."""
    tick = _tick_size(price)
    return int(round(price / tick) * tick)
```

### Pattern 5: Bootstrap 시장별 어댑터 주입

**What:** `bootstrap.py`가 `market` 파라미터를 받아 US면 AlpacaAdapter, KR이면 KisAdapter를 TradePlanHandler에 주입.

```python
# src/bootstrap.py
def bootstrap(db_factory=None, market: str = "us") -> dict:
    ...
    if market == "kr":
        adapter = KisExecutionAdapter(
            app_key=settings.KIS_APP_KEY,
            app_secret=settings.KIS_APP_SECRET,
            account_no=settings.KIS_ACCOUNT_NO,
        )
        capital = settings.KR_CAPITAL
    else:
        adapter = AlpacaExecutionAdapter(
            api_key=settings.ALPACA_API_KEY,
            secret_key=settings.ALPACA_SECRET_KEY,
        )
        capital = settings.US_CAPITAL

    trade_plan_handler = TradePlanHandler(
        trade_plan_service=TradePlanService(),
        trade_plan_repo=SqliteTradePlanRepository(...),
        execution_adapter=adapter,  # IBrokerAdapter 타입
        capital=capital,
    )
```

### Anti-Patterns to Avoid

- **handlers.py에서 AlpacaExecutionAdapter 직접 import:** 현재 코드에 `from src.execution.infrastructure.alpaca_adapter import AlpacaExecutionAdapter`가 있음. 이를 `IBrokerAdapter`로 교체해야 함.
- **module-level python-kis import:** `import kis` 금지. 반드시 메서드 내부에서 lazy import (기존 alpaca-py 패턴 동일).
- **OrderSpec validation에서 KIS 불가 조건 강제:** `take_profit_price`가 없어도 유효한 KIS 주문이므로 validation을 Optional 기준으로 수정.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| KIS API 토큰 관리 | 직접 OAuth 토큰 갱신 로직 | python-kis 내장 토큰 관리 | 만료 처리, 자동 갱신 포함 |
| 한국 시장 휴장일 | 자체 휴장일 DB | pykrx (이미 도입) | Phase 6에서 이미 구현됨 |
| 포지션 사이징 수학 | 재구현 | TradePlanService.generate_plan() | 이미 존재, 시장 무관 |

**Key insight:** 대부분의 로직이 이미 AlpacaExecutionAdapter와 TradePlanService에 있다. 이 Phase는 새 로직 작성보다 기존 패턴을 KIS에 복제하는 작업이다.

---

## Common Pitfalls

### Pitfall 1: handlers.py의 구체 타입 의존
**What goes wrong:** `TradePlanHandler.__init__`이 `AlpacaExecutionAdapter` 타입을 명시하고 있어 `KisExecutionAdapter` 주입 시 mypy 에러.
**Why it happens:** Phase 6 전에는 어댑터가 하나뿐이었음.
**How to avoid:** `IBrokerAdapter`로 타입 힌트 전환. `from src.execution.domain.repositories import IBrokerAdapter` 사용.
**Warning signs:** mypy `Argument 3 to "TradePlanHandler" has incompatible type "KisExecutionAdapter"` 에러.

### Pitfall 2: BracketSpec validation이 Optional 필드를 거부
**What goes wrong:** 기존 `BracketSpec._validate()`가 `stop_loss_price >= entry_price`를 항상 체크. KIS SELL 주문이나 stop_loss 없는 주문이 ValueError 발생.
**Why it happens:** BracketSpec은 Alpaca bracket 전용으로 설계됨.
**How to avoid:** `OrderSpec`에서 validation 로직을 direction과 필드 존재 여부에 따라 조건부로 적용.

### Pitfall 3: 호가 단위 무시
**What goes wrong:** KIS API가 호가 단위에 맞지 않는 가격으로 주문 시 에러 반환 (실전 모드).
**Why it happens:** ATR 기반 stop loss 가격은 소수점이 있을 수 있음.
**How to avoid:** `KisExecutionAdapter._real_order()`에서 `_round_to_tick()` 적용.

### Pitfall 4: KIS 모의투자 URL 혼용
**What goes wrong:** python-kis에서 실전/모의투자 URL을 잘못 설정하면 실전 주문이 제출됨.
**Why it happens:** 환경 구분 설정 누락.
**How to avoid:** `KisExecutionAdapter`는 항상 `virtual=True` (모의투자) 파라미터 사용. 실전 지원은 DEFERRED.

### Pitfall 5: capital 파라미터 미전달
**What goes wrong:** TradePlanService.generate_plan()에 KRW capital이 전달되지 않아 USD 자본금으로 포지션 사이징됨.
**Why it happens:** bootstrap에서 capital 분기 누락.
**How to avoid:** bootstrap()에 `market` 파라미터 추가 후 `KR_CAPITAL` 또는 `US_CAPITAL` 분기 명시.

---

## Code Examples

### KisExecutionAdapter 기본 골격
```python
# Source: AlpacaExecutionAdapter 패턴 복제
class KisExecutionAdapter(IBrokerAdapter):
    def __init__(self, app_key=None, app_secret=None, account_no=None):
        self._app_key = app_key
        self._app_secret = app_secret
        self._account_no = account_no
        self._use_mock = not (app_key and app_secret and account_no)
        self._client: Any = None
        if not self._use_mock:
            self._init_client()

    def _init_client(self) -> None:
        try:
            import kis  # lazy import
            self._client = kis.Client(
                app_key=self._app_key,
                app_secret=self._app_secret,
                virtual=True,  # 항상 모의투자
            )
        except Exception as e:
            logger.warning("KIS client init failed, falling back to mock: %s", e)
            self._use_mock = True

    def submit_order(self, spec: OrderSpec) -> OrderResult:
        if self._use_mock:
            return self._mock_order(spec)
        return self._real_order(spec)

    def _mock_order(self, spec: OrderSpec) -> OrderResult:
        order_id = f"KIS-MOCK-{spec.symbol}-{uuid4().hex[:8]}"
        return OrderResult(
            order_id=order_id,
            status="filled",
            symbol=spec.symbol,
            quantity=spec.quantity,
            filled_price=spec.entry_price,
        )
```

### GenerateTradePlanCommand에 currency 추가
```python
# src/execution/application/commands.py
@dataclass
class GenerateTradePlanCommand:
    ...
    currency: str = "USD"   # "USD" or "KRW"
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| AlpacaExecutionAdapter 직접 주입 | IBrokerAdapter 인터페이스 주입 | Phase 10 | 시장 전환 가능 |
| BracketSpec (필드 전부 필수) | OrderSpec (stop/target 선택적) | Phase 10 | KIS 단건 주문 지원 |

---

## Open Questions

1. **python-kis API 안정성**
   - What we know: PyPI에 `python-kis` 패키지 존재, KIS 공식 연동 라이브러리
   - What's unclear: 정확한 Client 클래스명과 메서드 시그니처 (KIS 개발자 등록 없이 검증 불가)
   - Recommendation: Mock 모드로 전체 구현 완료. 실제 API 연결은 KIS 계정 등록 후 `_real_order()` 내부만 교체.

2. **Stop loss 모니터링 스케줄링**
   - What we know: 일간 체크로 충분 (중기 보유 전략)
   - What's unclear: CLI monitoring command vs cron 중 어느 쪽이 적합한가
   - Recommendation: CLI `trading monitor-kr --check-stops` 커맨드로 구현. cron 등록은 사용자 재량.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | pytest.ini (or pyproject.toml) |
| Quick run command | `pytest tests/execution/ -x -q` |
| Full suite command | `pytest tests/ -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| KR-01 | KisExecutionAdapter implements IBrokerAdapter | unit | `pytest tests/execution/test_kis_adapter.py -x` | Wave 0 |
| KR-01 | IBrokerAdapter ABC enforced (cannot instantiate) | unit | `pytest tests/execution/test_broker_interface.py -x` | Wave 0 |
| KR-02 | Mock mode returns filled OrderResult without credentials | unit | `pytest tests/execution/test_kis_adapter.py::test_mock_submit_order -x` | Wave 0 |
| KR-02 | TradePlanHandler works with KisExecutionAdapter | unit | `pytest tests/execution/test_trade_plan_handler.py -x` | existing |
| KR-03 | OrderSpec accepts None stop_loss/take_profit | unit | `pytest tests/execution/test_order_spec.py -x` | Wave 0 |
| KR-03 | Tick size rounding for KRW prices | unit | `pytest tests/execution/test_kis_adapter.py::test_tick_size -x` | Wave 0 |
| KR-03 | KR capital used when market=kr in bootstrap | integration | `pytest tests/test_bootstrap.py::test_bootstrap_kr -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/execution/ -x -q`
- **Per wave merge:** `pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/execution/test_kis_adapter.py` — covers KR-01, KR-02, KR-03 (mock mode)
- [ ] `tests/execution/test_broker_interface.py` — covers KR-01 (IBrokerAdapter ABC)
- [ ] `tests/execution/test_order_spec.py` — covers KR-03 (OrderSpec Optional fields)
- [ ] `tests/test_bootstrap.py::test_bootstrap_kr` — covers KR-03 (KR capital injection)

---

## Sources

### Primary (HIGH confidence)
- Codebase: `src/execution/infrastructure/alpaca_adapter.py` — mock fallback 패턴, submit_bracket_order API
- Codebase: `src/execution/domain/repositories.py` — ITradePlanRepository ABC 패턴
- Codebase: `src/execution/domain/value_objects.py` — BracketSpec, OrderResult 구조
- Codebase: `src/execution/application/handlers.py` — TradePlanHandler 의존성 주입 지점
- Codebase: `src/bootstrap.py` — 어댑터 주입 패턴
- KRX 공식: 호가 단위 테이블 (1/5/10/50/100/500/1000 — 주가 구간별)

### Secondary (MEDIUM confidence)
- python-kis PyPI 패키지 — KIS Open API Python 래퍼 (KIS 계정 없이 API 검증 불가)
- KIS Open API 문서 — 모의투자(virtual) 엔드포인트 존재 확인

### Tertiary (LOW confidence)
- python-kis 정확한 Client 클래스/메서드 시그니처 — KIS 개발자 등록 후 확인 필요

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — 기존 AlpacaAdapter 패턴이 명확, KIS 어댑터는 동일 구조 복제
- Architecture: HIGH — IBrokerAdapter 추상화와 주입 지점이 코드베이스에서 명확히 파악됨
- Pitfalls: HIGH — handlers.py 구체 타입 의존, BracketSpec validation 문제는 코드 분석으로 확인
- python-kis API: LOW — KIS 개발자 등록 없이 실제 메서드 검증 불가

**Research date:** 2026-03-13
**Valid until:** 2026-06-13 (python-kis API 안정적, 호가 단위 변경 드물음)
