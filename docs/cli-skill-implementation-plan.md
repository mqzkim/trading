# CLI & Claude Skill 구현 플랜

## CLI & Claude Skill Implementation Plan

**작성일**: 2026-03-02
**전략 기반**: `strategy-recommendation.md`의 "하나의 코드, 두 개의 제품" 전략 적용
**핵심**: Scoring Engine 공통 기반 → Personal Layer + Commercial Layer 동시 서빙

---

## 1. 전체 아키텍처

### 1.1 3계층 코드 구조

```
trading-system/
│
├── core/                     ← 공통 기반 (Personal + Commercial 모두 사용)
│   ├── __init__.py
│   ├── config.py             # .env 로딩, 설정 관리
│   ├── scoring/              # QuantScore 엔진
│   ├── regime/               # RegimeRadar 엔진
│   ├── signals/              # SignalFusion 엔진
│   └── data/                 # 데이터 클라이언트
│
├── personal/                 ← 개인 전용 (투자 자문 영역)
│   ├── __init__.py
│   ├── position_sizer.py     # Kelly + ATR 사이징
│   ├── risk_manager.py       # 4단계 리스크 관리
│   ├── bias_checker.py       # 행동 편향 체크
│   ├── self_improver.py      # 자기 개선 루프
│   ├── execution/            # 브로커 연동
│   └── performance/          # 성과 분석
│
├── commercial/               ← 상업 제품 (정보 제공 영역)
│   ├── __init__.py
│   └── api/                  # FastAPI REST API
│
├── cli/                      ← CLI 인터페이스 (양쪽 공유)
│   ├── __init__.py
│   ├── app.py                # Typer 메인 앱
│   └── commands/             # 서브커맨드
│
├── .claude/                  ← Claude Skill 정의
│   ├── CLAUDE.md             # 프로젝트 메모리
│   ├── settings.json
│   └── skills/               # 12개 Claude Skill
│
├── tests/
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

### 1.2 의존성 흐름

```
.claude/skills/ ──────► cli/commands/ ──────► core/
      │                       │                 │
      │                       │          ┌──────┴──────┐
      │                       │          ▼             ▼
      │                       ├──► personal/    commercial/api/
      │                       │
      └── Claude Agent SDK ───┘

규칙:
  - core/ 는 personal/, commercial/ 에 의존하지 않음 (역방향 금지)
  - personal/ 과 commercial/ 은 서로 의존하지 않음
  - cli/ 는 core/ + personal/ + commercial/ 모두 import 가능
  - .claude/skills/ 는 cli/ 명령어를 Bash로 호출
```

---

## 2. Core 모듈 상세 설계

### 2.1 core/config.py — 설정 관리

```python
# 핵심 설계
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Data APIs
    eodhd_api_token: str = ""
    twelve_data_api_key: str = ""
    fmp_api_key: str = ""

    # Brokers
    alpaca_api_key: str = ""
    alpaca_secret_key: str = ""
    alpaca_paper: bool = True
    kis_app_key: str = ""
    kis_app_secret: str = ""

    # System
    trading_mode: str = "paper"  # paper | live
    max_position_size: float = 0.08
    max_daily_loss: float = 0.02
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### 2.2 core/scoring/ — QuantScore 엔진

```
core/scoring/
├── __init__.py          # CompositeScorer 클래스 export
├── f_score.py           # Piotroski F-Score (0-9)
├── z_score.py           # Altman Z-Score
├── m_score.py           # Beneish M-Score
├── g_score.py           # Mohanram G-Score (0-8)
├── technical.py         # 기술적 점수 (추세+모멘텀+거래량)
├── sentiment.py         # 센티먼트 점수
├── composite.py         # 복합 점수 합산 + 정규화
└── normalizer.py        # 백분위 순위, 섹터 중립, z-score 정규화
```

**핵심 인터페이스**:
```python
# core/scoring/composite.py
from dataclasses import dataclass

@dataclass
class ScoreResult:
    symbol: str
    composite_score: float         # 0-100
    risk_adjusted_score: float     # 복합 - 테일리스크 패널티
    safety_passed: bool            # Z-Score > 1.81 AND M-Score < -1.78
    fundamental: FundamentalScore  # 가치+품질+성장+건전성
    technical: TechnicalScore      # 추세+모멘텀+거래량
    sentiment: SentimentScore      # 애널리스트+내부자+공매도
    regime: str                    # 현재 레짐
    timestamp: str

class CompositeScorer:
    def __init__(self, data_client, regime_detector):
        ...

    def score(self, symbol: str, timeframe: str = "position") -> ScoreResult:
        """단일 종목 복합 스코어링"""
        # 1. 안전성 필터
        z = self.z_scorer.calculate(symbol)
        m = self.m_scorer.calculate(symbol)
        if z < 1.81 or m > -1.78:
            return ScoreResult(safety_passed=False, ...)

        # 2. 3축 스코어링
        fundamental = self.fundamental_scorer.calculate(symbol)
        technical = self.technical_scorer.calculate(symbol)
        sentiment = self.sentiment_scorer.calculate(symbol)

        # 3. 레짐 기반 가중치
        weights = self._get_regime_weights(timeframe)
        composite = (
            weights.fundamental * fundamental.score +
            weights.technical * technical.score +
            weights.sentiment * sentiment.score
        )

        # 4. 리스크 조정
        risk_penalty = self._calculate_tail_risk(symbol)
        risk_adjusted = composite - 0.3 * risk_penalty

        return ScoreResult(composite_score=composite, ...)

    def screen(self, market: str, min_score: float = 70,
               top_n: int = 20) -> list[ScoreResult]:
        """시장 전체 스크리닝"""
        ...
```

### 2.3 core/regime/ — RegimeRadar 엔진

```python
# core/regime/detector.py
@dataclass
class RegimeResult:
    regime: str              # "Low-Vol Bull" 등
    confidence: float        # 0-1
    probabilities: dict      # 각 레짐별 확률
    indicators: dict         # VIX, MA, ADX, 수익률곡선
    strategy_affinity: dict  # 전략별 친화도

class RegimeDetector:
    REGIMES = {
        "Low-Vol Bull":  {"vix": "<20", "trend": "up",   "adx": ">25"},
        "High-Vol Bull": {"vix": ">20", "trend": "up",   "adx": ">25"},
        "Low-Vol Range": {"vix": "<20", "trend": "flat", "adx": "<20"},
        "High-Vol Bear": {"vix": ">25", "trend": "down", "adx": ">25"},
    }

    def detect(self) -> RegimeResult:
        """현재 시장 레짐 판별"""
        vix = self.data.get_vix()
        sp500 = self.data.get_sp500_vs_200ma()
        adx = self.data.get_market_adx()
        yield_curve = self.data.get_yield_curve_slope()
        # ... 규칙 기반 판별 + 확률 계산
```

### 2.4 core/signals/ — SignalFusion 엔진

```python
# core/signals/fusion.py
@dataclass
class SignalResult:
    symbol: str
    consensus: str           # "BULLISH" | "NEUTRAL" | "BEARISH"
    agreement: int           # 동의 방법론 수 (0-4)
    methods: dict            # 각 방법론 상세
    regime_context: str

class SignalFusion:
    def __init__(self, regime_detector: RegimeDetector):
        self.strategies = {
            "canslim": CANSLIMStrategy(),
            "magic_formula": MagicFormulaStrategy(),
            "dual_momentum": DualMomentumStrategy(),
            "trend_following": TrendFollowingStrategy(),
        }

    def analyze(self, symbol: str) -> SignalResult:
        """4전략 시그널 생성 + 합의"""
        results = {}
        for name, strategy in self.strategies.items():
            results[name] = strategy.evaluate(symbol)

        # 레짐 기반 가중치
        regime = self.regime_detector.detect()
        weights = self._get_regime_weights(regime.regime)

        # 합의 계산
        bullish_count = sum(1 for r in results.values() if r.signal == "BULLISH")
        consensus = "BULLISH" if bullish_count >= 3 else \
                    "BEARISH" if bullish_count <= 1 else "NEUTRAL"

        return SignalResult(consensus=consensus, agreement=bullish_count, ...)
```

### 2.5 core/data/ — 데이터 클라이언트

```
core/data/
├── __init__.py
├── base.py              # 추상 DataClient 인터페이스
├── eodhd_client.py      # Phase 1: EODHD ($100/mo)
├── twelve_data_client.py # Phase 2: Twelve Data ($229/mo)
├── fmp_client.py        # Phase 3: FMP ($150/mo)
├── yfinance_client.py   # 보조/프로토타이핑 전용
├── cache.py             # 로컬 파일 캐시 (SQLite)
└── resolver.py          # 심볼 해석 (AAPL → US, 005930 → KRX)
```

```python
# core/data/base.py
from abc import ABC, abstractmethod

class DataClient(ABC):
    @abstractmethod
    def get_price_history(self, symbol: str, days: int = 252) -> pd.DataFrame:
        """일간 OHLCV 히스토리"""

    @abstractmethod
    def get_fundamentals(self, symbol: str) -> dict:
        """재무제표 (손익, 재무상태, 현금흐름)"""

    @abstractmethod
    def get_quote(self, symbol: str) -> dict:
        """현재가 + 변동"""
```

---

## 3. Personal 모듈 상세 설계

### 3.1 personal/position_sizer.py

```python
@dataclass
class SizingResult:
    symbol: str
    target_weight: float     # 포트폴리오 비중 (0-0.08)
    shares: int              # 매수 주수
    dollar_amount: float     # 매수 금액
    stop_loss: float         # 스탑로스 가격
    risk_amount: float       # 리스크 금액
    method: str              # "min(kelly, atr) × conviction"

class PositionSizer:
    def __init__(self, kelly_fraction: float = 0.25, risk_per_trade: float = 0.01):
        self.kelly_fraction = kelly_fraction
        self.risk_per_trade = risk_per_trade

    def calculate(self, symbol: str, score: ScoreResult,
                  portfolio_value: float, regime: RegimeResult) -> SizingResult:
        # Kelly 기반
        kelly_size = self._kelly_sizing(symbol)
        # ATR 기반
        atr_size = self._atr_sizing(symbol, portfolio_value)
        # 확신도 조정
        conviction = 0.5 + (score.composite_score / 100)  # 0.5 ~ 1.5
        # 최종
        target = min(kelly_size, atr_size) * conviction * regime.confidence
        target = max(0.01, min(target, self.max_position))
        return SizingResult(target_weight=target, ...)
```

### 3.2 personal/risk_manager.py

```python
class DrawdownLevel(Enum):
    NORMAL = 0      # < 10%
    WARNING = 1     # 10-15%: 신규 진입 중단
    DEFENSIVE = 2   # 15-20%: 50% 축소
    EMERGENCY = 3   # > 20%: 전량 청산

class RiskManager:
    def check_trade(self, proposed_trade, portfolio) -> RiskReport:
        """제안된 거래의 리스크 검증"""
        violations = []
        # 단일 종목 비중 <= 8%
        if self._check_concentration(proposed_trade, portfolio) > 0.08:
            violations.append("single_stock_limit_exceeded")
        # 섹터 <= 25%
        if self._check_sector(proposed_trade, portfolio) > 0.25:
            violations.append("sector_limit_exceeded")
        # 낙폭 상태
        dd_level = self._check_drawdown(portfolio)
        if dd_level >= DrawdownLevel.WARNING:
            violations.append(f"drawdown_level_{dd_level.value}")
        return RiskReport(passed=len(violations) == 0, ...)

    def check_portfolio(self, portfolio) -> PortfolioRiskReport:
        """포트폴리오 전체 리스크 점검"""
        ...
```

### 3.3 personal/execution/ — 브로커 연동

```
personal/execution/
├── __init__.py
├── base.py               # 추상 Executor 인터페이스
├── alpaca_executor.py     # Phase 1: 미국 매매
├── kis_executor.py        # Phase 2: 한국 매매
└── paper_logger.py        # 모의 매매 로깅
```

```python
# personal/execution/base.py
class TradeExecutor(ABC):
    @abstractmethod
    def submit_order(self, order: Order) -> OrderResult: ...

    @abstractmethod
    def get_positions(self) -> list[Position]: ...

    @abstractmethod
    def get_account(self) -> AccountInfo: ...

# personal/execution/alpaca_executor.py
class AlpacaExecutor(TradeExecutor):
    def __init__(self, api_key, secret_key, paper=True):
        self.client = TradingClient(api_key, secret_key, paper=paper)

    def submit_order(self, order: Order) -> OrderResult:
        if self.config.require_confirmation():
            # live 모드에서는 확인 요청
            confirm = input(f"실전 주문: {order}. 진행? (y/n): ")
            if confirm.lower() != 'y':
                return OrderResult(status="cancelled")
        req = MarketOrderRequest(...)
        return self.client.submit_order(req)
```

---

## 4. Commercial 모듈 상세 설계

### 4.1 FastAPI 서버

```python
# commercial/api/app.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Trading Analytics API",
    description="AI 기반 정량적 주식 분석 API",
    version="1.0.0",
)

# 면책조항 미들웨어
@app.middleware("http")
async def add_disclaimer(request, call_next):
    response = await call_next(request)
    response.headers["X-Disclaimer"] = (
        "This API provides information only, not investment advice. "
        "Past performance does not guarantee future results."
    )
    return response
```

### 4.2 API Routes

```python
# commercial/api/routes/score.py
@router.get("/api/v1/score/{symbol}")
async def get_score(symbol: str, detail: bool = False):
    """종목 복합 스코어 조회"""
    result = scorer.score(symbol)
    if not detail:
        return {"symbol": symbol, "composite_score": result.composite_score,
                "safety_passed": result.safety_passed}
    return result.to_dict()

@router.get("/api/v1/screen")
async def screen_stocks(market: str = "US", min_score: float = 70,
                        top_n: int = 20, sector: str = None):
    """시장 스크리닝"""
    results = scorer.screen(market, min_score, top_n, sector)
    return {"count": len(results), "stocks": [r.to_summary() for r in results]}

# commercial/api/routes/regime.py
@router.get("/api/v1/regime/current")
async def get_current_regime():
    """현재 시장 레짐 조회"""
    result = regime_detector.detect()
    return result.to_dict()

# commercial/api/routes/signal.py
@router.get("/api/v1/signal/{symbol}")
async def get_signal(symbol: str):
    """종목 멀티 전략 시그널 조회"""
    result = signal_fusion.analyze(symbol)
    return result.to_dict()
```

### 4.3 인증 & Rate Limiting

```python
# commercial/api/auth.py
class APITier(Enum):
    FREE = "free"           # 5 req/day
    STARTER = "starter"     # 100 req/day
    PRO = "pro"             # unlimited

# 티어별 Rate Limit
RATE_LIMITS = {
    APITier.FREE: {"per_day": 5, "markets": ["US"]},
    APITier.STARTER: {"per_day": 100, "markets": ["US", "KRX"]},
    APITier.PRO: {"per_day": None, "markets": ["ALL"]},
}
```

---

## 5. CLI 도구 상세 설계

### 5.1 명령어 체계

```bash
# =========================================
#  Core 명령어 (개인 + 상업 공통)
# =========================================

# 스코어링
trading score AAPL                      # 복합 점수 요약
trading score AAPL --detail             # 3축 상세 점수
trading score AAPL --fscore             # F-Score만
trading score AAPL --zscore             # Z-Score만
trading screen --market US --min-score 70 --top 20   # 스크리닝
trading screen --market KRX --sector tech --min-fscore 7

# 시그널
trading signal AAPL                     # 4전략 합의 시그널
trading signal AAPL --detail            # 각 전략별 상세
trading signal top --market US --min-agreement 3     # 고합의 종목

# 레짐
trading regime                          # 현재 시장 레짐
trading regime --history 90             # 90일 레짐 히스토리

# 데이터
trading data price AAPL                 # 현재가
trading data history AAPL --days 252    # 1년 일봉
trading data fundamentals AAPL          # 재무제표

# =========================================
#  Personal 명령어 (개인 전용)
# =========================================

# 매매
trading buy AAPL --qty 10 --type market
trading buy AAPL --amount 5000
trading sell AAPL --qty 5 --type limit --price 200
trading order status <ORDER_ID>
trading order cancel <ORDER_ID>

# 포트폴리오
trading portfolio show                  # 보유 현황
trading portfolio pnl                   # 수익률
trading portfolio risk                  # 리스크 분석
trading portfolio rebalance --strategy dual-momentum

# 분석 (풀 파이프라인)
trading analyze AAPL                    # 풀 9계층 분석
trading analyze AAPL --quick            # 빠른 스코어링만

# =========================================
#  Commercial 명령어 (API 서버)
# =========================================

trading serve                           # API 서버 시작 (기본 8000)
trading serve --port 8080 --workers 4
```

### 5.2 Typer 구현

```python
# cli/app.py
import typer

app = typer.Typer(
    name="trading",
    help="체계적 트레이딩 분석 시스템",
    no_args_is_help=True,
)

# 서브커맨드 그룹 등록
app.add_typer(score_app, name="score")
app.add_typer(signal_app, name="signal")
app.add_typer(regime_app, name="regime")
app.add_typer(data_app, name="data")
app.add_typer(trade_app, name="buy")   # personal
app.add_typer(portfolio_app, name="portfolio")  # personal
app.add_typer(serve_app, name="serve")  # commercial

# cli/commands/score.py
score_app = typer.Typer(help="정량적 스코어링")

@score_app.command()
def score(
    symbol: str = typer.Argument(help="종목 심볼 (예: AAPL, 005930.KRX)"),
    detail: bool = typer.Option(False, "--detail", "-d", help="상세 출력"),
    fscore: bool = typer.Option(False, "--fscore", help="F-Score만"),
    output: str = typer.Option("table", "--output", "-o", help="table|json"),
):
    """종목의 복합 정량 점수를 계산합니다."""
    scorer = CompositeScorer(get_data_client())
    result = scorer.score(symbol)
    if output == "json":
        print_json(result)
    else:
        print_score_table(result, detail=detail)
```

### 5.3 출력 포맷

```
$ trading score AAPL

  ┌──────────────────────────────────────────┐
  │  AAPL - Apple Inc.                       │
  │  Composite Score: 78.5 / 100             │
  ├──────────────────────────────────────────┤
  │  Safety Filter: ✅ PASSED                 │
  │    Z-Score: 4.21 (> 1.81)               │
  │    M-Score: -2.89 (< -1.78)             │
  ├──────────────────────────────────────────┤
  │  Fundamental:  82 / 100  (weight: 45%)   │
  │    F-Score: 8/9, Value: P65, Quality: P91│
  │  Technical:    74 / 100  (weight: 35%)   │
  │    Trend: Bullish, Momentum: P70         │
  │  Sentiment:    71 / 100  (weight: 20%)   │
  │    Analyst: ↑, Insider: Net Buy          │
  ├──────────────────────────────────────────┤
  │  Regime: Low-Vol Bull (78%)              │
  │  Risk Adjusted: 75.2                     │
  └──────────────────────────────────────────┘

$ trading regime

  ┌──────────────────────────────────────────┐
  │  Market Regime: Low-Vol Bull             │
  │  Confidence: 78%                         │
  ├──────────────────────────────────────────┤
  │  VIX: 14.2    S&P vs 200MA: +8%         │
  │  ADX: 28.5    Yield Curve: +0.45%       │
  ├──────────────────────────────────────────┤
  │  Strategy Affinity:                      │
  │    Trend Following: ████████░░ 90%       │
  │    Momentum:        ████████░░ 85%       │
  │    Value:           █████░░░░░ 50%       │
  │    Mean Reversion:  ███░░░░░░░ 30%       │
  └──────────────────────────────────────────┘
```

---

## 6. Claude Skill 상세 설계

### 6.1 스킬 목록 (전략 적용)

```
.claude/skills/
│
│  ── [ 공통 스킬 (Personal + Commercial) ] ──────────────
├── scoring-engine/SKILL.md          # QuantScore (1순위)
├── regime-detect/SKILL.md           # RegimeRadar (2순위)
├── signal-generate/SKILL.md         # SignalFusion (3순위)
├── data-ingest/SKILL.md             # 데이터 수집
├── backtest-validator/SKILL.md      # 백테스트 검증
│
│  ── [ 개인 전용 스킬 ] ────────────────────────────────
├── trading-orchestrator/SKILL.md    # 풀 파이프라인 오케스트레이터
├── position-sizer/SKILL.md          # Kelly+ATR 사이징
├── risk-manager/SKILL.md            # 4단계 리스크 관리
├── execution-planner/SKILL.md       # 주문 실행 계획
├── bias-checker/SKILL.md            # 행동 편향 체크
├── performance-analyst/SKILL.md     # 4레벨 성과 분석
└── self-improver/SKILL.md           # 자기 개선
```

### 6.2 공통 스킬 상세

#### `/scoring-engine` (1순위 구현)

```yaml
---
name: scoring-engine
description: |
  정량적 복합 스코어링을 실행합니다. F-Score, Z-Score, M-Score, G-Score를
  포함한 3축(기본적/기술적/센티먼트) 분석으로 0-100 복합 점수를 산출합니다.
  Team Agent를 활용하여 3축 분석을 병렬 수행합니다.
argument-hint: "[symbol] [--detail] [--screen market]"
user-invocable: true
allowed-tools: Read, Bash, Agent
model: sonnet
---

## 실행 규칙

### 단일 종목 분석
1. `trading score {symbol} --detail --output json` 실행
2. 결과를 사용자에게 테이블 형태로 보고
3. 안전성 필터 미통과 시 경고 강조

### 시장 스크리닝 (--screen 사용 시)
1. `trading screen --market {market} --min-score 70 --top 20` 실행
2. 상위 종목 리스트를 테이블로 출력

### Team Agent 병렬 분석 (심화 분석 요청 시)
3개 에이전트를 동시 스폰:
- **Fundamental Agent** (sonnet): F-Score, Z-Score, 가치/품질/성장 계산
- **Technical Agent** (haiku): 추세, 모멘텀, 거래량 분석
- **Sentiment Agent** (haiku): 애널리스트 추정치, 내부자 거래 분석

결과를 레짐 기반 가중치로 합산하여 최종 복합 점수 산출.

### 출력 포맷
```json
{
  "symbol": "AAPL",
  "composite_score": 78.5,
  "safety_passed": true,
  "fundamental": {"score": 82, "f_score": 8, "z_score": 4.21},
  "technical": {"score": 74, "trend": "bullish"},
  "sentiment": {"score": 71, "analyst_revision": "up"},
  "regime": "Low-Vol Bull",
  "risk_adjusted_score": 75.2
}
```
```

#### `/regime-detect` (2순위 구현)

```yaml
---
name: regime-detect
description: |
  현재 시장 레짐을 판별합니다. VIX, S&P 500 200MA, ADX, 수익률곡선을
  종합하여 4가지 레짐(Low-Vol Bull, High-Vol Bull, Low-Vol Range,
  High-Vol Bear) 중 현재 상태와 확률을 산출합니다.
user-invocable: true
allowed-tools: Read, Bash
model: haiku
---

## 실행 규칙
1. `trading regime --output json` 실행
2. 현재 레짐과 전략 친화도를 보고
3. 레짐이 "High-Vol Bear" 또는 "Transition"이면 경고 강조
```

#### `/signal-generate` (3순위 구현)

```yaml
---
name: signal-generate
description: |
  4가지 검증된 방법론(CAN SLIM, Magic Formula, Dual Momentum,
  Trend Following)을 동시 실행하여 합의 시그널을 생성합니다.
  Team Agent 4개를 병렬 스폰합니다.
argument-hint: "[symbol]"
user-invocable: true
allowed-tools: Read, Bash, Agent
model: sonnet
---

## Team Agent 병렬 실행
4개 에이전트 동시 스폰:
- **CAN SLIM Agent** (sonnet): 7가지 기준 평가
- **Magic Formula Agent** (haiku): Earnings Yield + ROC 순위
- **Dual Momentum Agent** (haiku): 상대+절대 모멘텀
- **Trend Following Agent** (haiku): MA/ADX/Breakout

## 합의 판정
- 3/4 이상 BULLISH → "강한 매수 시그널"
- 3/4 이상 BEARISH → "강한 매도 시그널"
- 그 외 → "중립, 관망 권고"
```

### 6.3 개인 전용 스킬 상세

#### `/trading-orchestrator` (개인 핵심)

```yaml
---
name: trading-orchestrator
description: |
  전체 9계층 트레이딩 파이프라인을 오케스트레이션합니다.
  종목 분석, 포트폴리오 점검, 리밸런싱 판단을 체계적으로 수행합니다.
  최대 13개 Team Agent를 활용합니다.
argument-hint: "[full|quick|review] [symbol|portfolio]"
user-invocable: true
allowed-tools: Read, Bash, Agent, Write
model: opus
---

## 워크플로우

### full (전체 분석)
`/trading-orchestrator full AAPL`
1. /data-ingest → 2. /regime-detect → 3. /signal-generate (4 agents)
→ 4. /scoring-engine (3 agents) → 5. /position-sizer → 6. /risk-manager (2 agents)
→ 7. /execution-planner → 8. /bias-checker → 9. 최종 보고서

### quick (빠른 분석)
`/trading-orchestrator quick "AAPL MSFT GOOGL"`
1. /data-ingest → 2. /scoring-engine (3 agents) → 3. 비교 테이블

### review (포트폴리오 점검)
`/trading-orchestrator review`
1. 보유종목 일괄 스코어링 → 2. 리스크 점검 → 3. 리밸런싱 제안
```

#### `/position-sizer` (개인 전용)

```yaml
---
name: position-sizer
description: |
  Fractional Kelly와 ATR 기반으로 최적 포지션 크기를 계산합니다.
  개인 포트폴리오 규모와 리스크 허용도에 맞춰 조정합니다.
argument-hint: "[symbol] [--portfolio-value N] [--score N]"
user-invocable: true
allowed-tools: Read, Bash
model: haiku
---

## 규칙
- Kelly fraction: 1/4 (절대 Full Kelly 금지)
- Risk per trade: 자본의 1%
- ATR stop: 3.0 × ATR(21)
- 최대 단일 종목: 8%
- 최소 포지션: 1%
```

---

## 7. 구현 로드맵 (전략 적용)

### Phase 1: 공통 기반 + MVP (Week 1-3)

```
Week 1: 프로젝트 셋업 + 데이터 레이어
  ☐ pyproject.toml, .env.example, .gitignore
  ☐ core/config.py (pydantic-settings)
  ☐ core/data/eodhd_client.py (Phase 1 데이터)
  ☐ core/data/yfinance_client.py (보조)
  ☐ core/data/cache.py (SQLite 로컬 캐시)
  ☐ core/data/resolver.py (심볼 해석)

Week 2: Scoring Engine (1순위 - 양쪽 핵심)
  ☐ core/scoring/f_score.py
  ☐ core/scoring/z_score.py
  ☐ core/scoring/m_score.py
  ☐ core/scoring/technical.py
  ☐ core/scoring/composite.py
  ☐ core/scoring/normalizer.py
  ☐ cli/commands/score.py
  ☐ tests/test_scoring.py

Week 3: Regime + Signal 기본
  ☐ core/regime/detector.py (규칙 기반)
  ☐ core/signals/canslim.py
  ☐ core/signals/magic_formula.py
  ☐ core/signals/dual_momentum.py
  ☐ core/signals/trend_following.py
  ☐ core/signals/fusion.py
  ☐ cli/commands/regime.py
  ☐ cli/commands/signal.py

검증:
  $ trading score AAPL --detail     ← 동작 확인
  $ trading regime                  ← 동작 확인
  $ trading signal AAPL             ← 동작 확인
```

### Phase 2: 개인 핵심 (Week 4-5)

```
Week 4: Position Sizer + Risk Manager
  ☐ personal/position_sizer.py
  ☐ personal/risk_manager.py
  ☐ personal/bias_checker.py
  ☐ cli/commands/analyze.py (풀 파이프라인)
  ☐ tests/test_position_sizer.py
  ☐ tests/test_risk_manager.py

Week 5: Execution + Orchestrator
  ☐ personal/execution/alpaca_executor.py (Paper Trading)
  ☐ cli/commands/trade.py (buy, sell, order)
  ☐ cli/commands/portfolio.py
  ☐ .claude/skills/ (12개 스킬 YAML 작성)
  ☐ .claude/CLAUDE.md

검증:
  $ trading analyze AAPL            ← 풀 9계층 분석
  $ trading buy AAPL --qty 10       ← Paper Trading 주문
  $ trading portfolio show          ← 보유 현황
  /scoring-engine AAPL              ← Claude Skill 동작
  /trading-orchestrator full AAPL   ← 오케스트레이터 동작
```

### Phase 3: 상업 제품 v1 (Week 6-7)

```
Week 6: FastAPI 서버
  ☐ commercial/api/app.py
  ☐ commercial/api/routes/score.py   (QuantScore API)
  ☐ commercial/api/routes/regime.py  (RegimeRadar API)
  ☐ commercial/api/routes/signal.py  (SignalFusion API)
  ☐ commercial/api/auth.py (API Key 인증)
  ☐ commercial/api/rate_limiter.py
  ☐ cli/commands/serve.py

Week 7: 배포 + 문서
  ☐ Dockerfile
  ☐ docker-compose.yml (API + Redis 캐시)
  ☐ API 문서 (자동 생성: /docs)
  ☐ 랜딩 페이지 초안

검증:
  $ trading serve --port 8000
  $ curl localhost:8000/api/v1/score/AAPL
  $ curl localhost:8000/api/v1/regime/current
```

### Phase 4: 확장 (Week 8-10)

```
Week 8: 글로벌 확장
  ☐ core/data/twelve_data_client.py (글로벌 실시간)
  ☐ personal/execution/kis_executor.py (한국 매매)
  ☐ core/data/fmp_client.py (심화 펀더멘탈)

Week 9: 성과 분석 + 자기 개선
  ☐ personal/performance/attribution.py
  ☐ personal/self_improver.py
  ☐ .claude/skills/performance-analyst/
  ☐ .claude/skills/self-improver/

Week 10: 최적화 + 안정화
  ☐ 캐싱 최적화 (Redis + SQLite 2계층)
  ☐ Rate Limit 처리 (지수 백오프)
  ☐ 에러 핸들링 + 폴백
  ☐ 통합 테스트 (E2E)
  ☐ 모니터링 (Prometheus 메트릭)
```

---

## 8. 기술 스택

### 8.1 핵심 의존성

```toml
# pyproject.toml
[project]
name = "trading-system"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    # Core
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "python-dotenv>=1.0",

    # Data
    "pandas>=2.0",
    "numpy>=1.24",
    "eodhd>=1.0",
    "yfinance>=0.2",
    "requests>=2.31",

    # CLI
    "typer>=0.12",
    "rich>=13.0",         # 테이블/컬러 출력

    # Technical Analysis
    "pandas-ta>=0.3",

    # API Server (commercial)
    "fastapi>=0.110",
    "uvicorn>=0.27",
]

[project.optional-dependencies]
broker = [
    "alpaca-py>=0.20",       # US 매매
]
global = [
    "twelvedata>=1.2",       # 글로벌 데이터
]
ml = [
    "scikit-learn>=1.4",     # ML 스코어링
    "xgboost>=2.0",          # 메타러닝
    "hmmlearn>=0.3",         # 레짐 감지
    "optuna>=3.5",           # 하이퍼파라미터
]
```

### 8.2 프레임워크 선택 이유

| 선택 | 이유 |
|------|------|
| **Typer** (CLI) | Click 기반이지만 타입 힌트, 자동완성, 더 적은 코드. Rich와 통합 우수 |
| **FastAPI** (API) | Typer와 같은 팀(tiangolo) 제작, 비동기, 자동 OpenAPI 문서, Pydantic 통합 |
| **Pydantic** (검증) | 타입 안전, 설정 관리, API 스키마 자동 생성. 전 계층 관통 |
| **Rich** (출력) | 터미널 테이블, 프로그레스바, 컬러 출력. CLI UX 핵심 |
| **SQLite** (캐시) | 설치 불필요, 파일 기반, API 응답 캐싱에 적합 |

---

## 9. 테스트 전략

```
tests/
├── core/
│   ├── test_f_score.py           # F-Score 계산 검증 (알려진 종목으로)
│   ├── test_z_score.py           # Z-Score 계산 검증
│   ├── test_composite.py         # 복합 점수 가중치/정규화
│   ├── test_regime.py            # 레짐 판별 규칙
│   ├── test_signals.py           # 시그널 합의 로직
│   └── test_data_clients.py      # 데이터 클라이언트 (mock)
├── personal/
│   ├── test_position_sizer.py    # Kelly/ATR 계산 정확도
│   ├── test_risk_manager.py      # 리스크 한도 검증
│   └── test_bias_checker.py      # 편향 감지 로직
├── commercial/
│   └── test_api.py               # FastAPI 엔드포인트 (TestClient)
└── integration/
    └── test_full_pipeline.py     # E2E: score → signal → size → risk
```

**테스트 원칙**:
- 스코어링 함수는 알려진 값으로 검증 (AAPL 2024 F-Score = ? 으로 교차 검증)
- 데이터 클라이언트는 mock으로 테스트 (API 호출 없이)
- 리스크 매니저는 경계값 테스트 (8% 초과, 25% 초과 등)
- CI에서 `pytest tests/core tests/personal` 자동 실행
