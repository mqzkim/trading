# 트레이딩 시스템 전략 추천서

## Trading System Strategy Recommendation

**작성일**: 2026-03-02
**목적**: 트레이딩 시스템 컴포넌트를 개인 사용(Personal)과 상업 제품(Commercial)으로 분류하고 각각의 구현 전략을 수립
**핵심 원칙**: Scoring Engine을 공통 기반으로 삼아 한 번의 구현으로 양쪽을 모두 충족

---

## 1. 전략 분류의 기준

### 1.1 분류 축

```
┌──────────────────────────────────────────────────────────────┐
│                      분류 기준 2x2 매트릭스                      │
├──────────────────────┬───────────────────────────────────────┤
│                      │  확장 가능성 (Scalability)              │
│                      ├──────────────────┬────────────────────┤
│                      │  낮음 (개인화 필수)  │  높음 (범용 제공 가능) │
├──────────────────────┼──────────────────┼────────────────────┤
│ 법적  │ 라이센스 불필요 │  개인 전용 도구    │  ⭐ 상업 제품       │
│ 제약  │ (정보 제공)     │  (B 영역)         │  (A 영역)          │
│       ├────────────────┼──────────────────┼────────────────────┤
│       │ 라이센스 필요   │  개인 전용        │  기관용 제품         │
│       │ (투자 자문)     │  (D 영역)        │  (C 영역, 장벽 높음) │
└──────────────────────┴──────────────────┴────────────────────┘
```

**핵심 경계선**: "투자 자문" vs "투자 정보 제공"

| 구분 | 정의 | 라이센스 | 예시 |
|------|------|---------|------|
| **투자 정보** | 데이터, 통계, 점수, 팩터 분석 | 불필요 | "AAPL의 F-Score는 8/9입니다" |
| **투자 자문** | 특정 종목 매수/매도 추천, 포지션 크기 제안 | 필요 | "AAPL을 자본의 4.5% 매수하세요" |

→ **상업 제품은 A 영역(정보 제공 + 확장 가능)에 집중**
→ **개인 시스템은 B+D 영역(투자 자문 포함 가능)을 자유롭게 활용**

### 1.2 공유 기반 (Shared Foundation)

```
                ┌─────────────────────────────┐
                │      Scoring Engine          │
                │   (F-Score, Z-Score, 복합점수) │
                │      = 공통 기반 레이어        │
                └──────────────┬──────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                                  ▼
    ┌─────────────────┐               ┌─────────────────┐
    │  Personal Layer  │               │ Commercial Layer │
    │                  │               │                  │
    │ • Position Sizer │               │ • Screener API   │
    │ • Risk Manager   │               │ • Signal Service │
    │ • Execution      │               │ • Regime API     │
    │ • Self-Improver  │               │ • Backtest Valid. │
    │ • Bias Checker   │               │ • Risk Analytics │
    │ • Orchestrator   │               │ • Attribution    │
    └─────────────────┘               └─────────────────┘
```

---

## 2. 개인 사용 (Personal) 상세 전략

### 2.1 개인 시스템의 핵심 가치

```
"내 돈, 내 규칙, 내 포트폴리오에 최적화된 의사결정 시스템"

다른 사람에게는 줄 수 없는 가치:
  - 내 리스크 허용도에 맞춘 Kelly 파라미터
  - 내 보유 종목 기반 낙폭 방어
  - 내 과거 거래로 학습한 자기 개선
  - 내 편향 패턴을 아는 Bias Checker
  - 내 계좌에 직접 연결된 실행 시스템
```

### 2.2 개인 전용 컴포넌트 상세

#### A. Full 9-Layer Orchestrator (개인 핵심)

```
/trading-orchestrator full AAPL

  실행 흐름:
  ① 데이터 수집 → ② 레짐 판별 → ③ 4전략 병렬 시그널
  → ④ 3축 병렬 스코어링 → ⑤ Kelly+ATR 사이징 → ⑥ 리스크 검증
  → ⑦ 실행 계획 → ⑧ Bias Check → ⑨ 최종 보고서

  이 전체 파이프라인은 개인화가 필수:
  - 각 Layer의 파라미터가 내 포트폴리오에 맞게 조정됨
  - 레짐별 전략 가중치가 내 성향에 맞게 설정됨
  - 남에게 제공하면 "일반적 분석"이 되어 가치 하락

왜 판매 부적합:
  - 9계층 전체를 타인에게 설명/커스터마이징하는 비용이 제품 가치를 초과
  - 실행(주문)까지 포함하면 투자자문 라이센스 필요
  - 복잡도가 높아 지원/유지보수 부담 과중
```

#### B. Position Sizer (개인 전용)

```
왜 개인만 쓸 수 있는가:
  - Kelly 공식의 입력값이 "내 승률, 내 평균 수익, 내 평균 손실"
  - 다른 사람의 트레이딩 통계와 완전히 다름
  - "4.5% 배분하라"는 제안 = 투자 자문 (라이센스 필요)

개인 사용법:
  /position-sizer AAPL --score 85 --portfolio 100000
  → "Kelly: 6.2%, ATR: 4.8% → 최종: 4.5% ($4,500, 15주)"
  → "Stop Loss: $172.50, Risk: $45 (자본의 0.45%)"
```

#### C. Self-Improver (개인 전용)

```
왜 개인만 쓸 수 있는가:
  - 내 과거 6개월 거래 데이터로 Walk-Forward 재최적화
  - "레짐 정확도 52% → HMM 재학습 필요" 같은 진단은 내 데이터 기반
  - 남의 거래 히스토리에 적용하면 의미 없음

개인 사용법:
  /self-improver --period 6months
  → "시그널 IC 0.02 < 임계값 0.03: 모멘텀 피처 드리프트 감지"
  → "권고: Dual Momentum lookback 12→9개월로 단축"
  → "WFE 48% < 50%: 파라미터 수 축소 권고"
```

#### D. Execution Planner + 브로커 연동 (개인 전용)

```
왜 개인만 쓸 수 있는가:
  - 내 Alpaca/KIS 계좌에 직접 주문 제출
  - 타인 계좌 접근 = 법적 이슈 (자산운용 라이센스)
  - Paper Trading도 내 계좌에서만 의미

개인 사용법:
  /execution-planner AAPL --action buy --shares 15
  → Alpaca Paper Trading 주문 제출
  → 체결 확인 → 포트폴리오 업데이트
```

#### E. Bias Checker (개인 부가 기능)

```
개인 사용법:
  /bias-checker --portfolio portfolio.json --proposed-trade "SELL AAPL 15"
  → "⚠️ 처분 효과 의심: AAPL이 +32% 수익 중인데 매도하려는 이유?"
  → "⚠️ 앵커링: 매수가($145)를 기준으로 판단하고 있지 않은지?"
  → "✅ 스코어 기반 결정이라면 진행 가능"
```

### 2.3 개인 시스템 구현 우선순위

```
Phase 1 (Week 1-2): 기반
  ① Scoring Engine (공통 기반)
  ② Data Ingest + Regime Detect

Phase 2 (Week 3-4): 개인 핵심
  ③ Position Sizer
  ④ Risk Manager + Bias Checker
  ⑤ Execution Planner (Alpaca Paper)

Phase 3 (Week 5-6): 자동화
  ⑥ Trading Orchestrator (풀 파이프라인)
  ⑦ Signal Generation (4전략)

Phase 4 (Week 7-8): 자기 개선
  ⑧ Performance Analyst
  ⑨ Self-Improver
```

### 2.4 개인 시스템 예상 비용

| 항목 | Phase 1 | Phase 2 | Phase 3 | 최종 |
|------|---------|---------|---------|------|
| 데이터 API (EODHD) | $100/mo | $100/mo | $100/mo | $100/mo |
| 브로커 (Alpaca) | $0 | $0 | $0 | $0 |
| Claude API (스킬 실행) | ~$5/mo | ~$15/mo | ~$30/mo | ~$50/mo |
| **월 합계** | **$105** | **$115** | **$130** | **$150** |

---

## 3. 상업 제품 (Commercial) 상세 전략

### 3.1 상업 제품의 핵심 원칙

```
절대 규칙:
  1. "정보 제공"만 한다 (점수, 데이터, 통계, 시그널 강도)
  2. "매수/매도하라"고 말하지 않는다 (투자 자문 회피)
  3. 면책조항 필수 ("이 정보는 투자 자문이 아닙니다")
  4. 포지션 크기를 절대 제안하지 않는다

포지셔닝:
  "AI 기반 정량적 주식 분석 플랫폼"
  ≠ "AI 트레이딩 봇" (이건 라이센스 필요)
```

### 3.2 Tier 1: 높은 상업성 (즉시 제품화 가능)

#### 제품 1: QuantScore — 복합 스코어링 API

```
제품명: QuantScore
태그라인: "모든 주식을 하나의 숫자로"

핵심 가치:
  - F-Score + Z-Score + M-Score + G-Score + 기술적 + 센티먼트 → 복합 0-100점
  - 개인이 직접 계산하면 2-3시간 → API 한 번으로 2초
  - 섹터 중립 백분위 → 애플 vs 삼성 직접 비교 가능

API 설계:
  GET /api/v1/score/{symbol}
  GET /api/v1/score/{symbol}/detail
  GET /api/v1/screen?min_fscore=7&min_zscore=2.0&market=US
  GET /api/v1/ranking?market=US&sector=tech&top=20

응답 예시:
  {
    "symbol": "AAPL",
    "composite_score": 78.5,
    "safety_filter": { "z_score": 4.21, "m_score": -2.89, "passed": true },
    "fundamental": { "score": 82, "f_score": 8, "value_rank": 65, "quality_rank": 91 },
    "technical": { "score": 74, "trend": "bullish", "momentum_rank": 70 },
    "sentiment": { "score": 71, "analyst_revision": "up", "insider_buy_ratio": 0.65 },
    "risk_adjusted_score": 75.2,
    "updated_at": "2026-03-02T00:00:00Z"
  }

가격 티어:
  Free:    5 req/day, 미국 시장만, 복합 점수만
  Starter: $29/mo, 100 req/day, 미국+한국, 상세 점수
  Pro:     $99/mo, 무제한, 글로벌 5대 시장, 스크리닝, 히스토리컬 점수

경쟁 우위:
  - Finviz: 단일 스코어만 제공, 커스텀 불가
  - Stock Rover: UI 기반, API 없음
  - 우리: 복합 멀티스코어 + API + CLI + Claude Skill
```

#### 제품 2: SignalFusion — 멀티 전략 시그널 서비스

```
제품명: SignalFusion
태그라인: "4가지 검증된 방법론, 하나의 합의"

핵심 가치:
  - CAN SLIM + Magic Formula + Dual Momentum + Trend Following
  - 4가지 독립 방법론 동시 실행 → 합의(Consensus) 시그널
  - "3/4 방법론이 동의 → 고확신" → 의사결정 부담 경감

API 설계:
  GET /api/v1/signal/{symbol}
  GET /api/v1/signal/{symbol}/consensus
  GET /api/v1/signal/top-consensus?market=US&min_agreement=3

응답 예시:
  {
    "symbol": "AAPL",
    "consensus": { "signal": "BULLISH", "agreement": 3, "out_of": 4 },
    "methods": {
      "canslim": { "score": 6, "max": 7, "signal": "BULLISH", "factors": {...} },
      "magic_formula": { "rank": 45, "signal": "NEUTRAL", "earnings_yield": 0.06 },
      "dual_momentum": { "signal": "BULLISH", "relative_momentum": 0.12 },
      "trend_following": { "signal": "BULLISH", "above_200ma": true, "adx": 32 }
    },
    "regime_context": "Low-Vol Bull"
  }

  ※ "BULLISH/NEUTRAL/BEARISH" = 시그널 강도 정보
  ※ "매수/매도 추천" 아님 = 투자 자문이 아님

가격 티어:
  Starter: $49/mo, 일간 상위 20 리스트, 미국
  Pro:     $99/mo, 실시간 시그널, 글로벌, 히스토리컬
  API:     $199/mo, 풀 API 접근, 웹훅 알림
```

#### 제품 3: RegimeRadar — 시장 레짐 감지 API

```
제품명: RegimeRadar
태그라인: "시장의 기분을 읽다"

핵심 가치:
  - 현재 시장 레짐 실시간 판별 + 확률
  - 경쟁 제품 거의 없음 (독보적 차별점)
  - 다른 트레이딩 시스템에 "플러그인"으로 연동 가능

API 설계:
  GET /api/v1/regime/current
  GET /api/v1/regime/history?days=90
  WS  /api/v1/regime/stream

응답 예시:
  {
    "regime": "Low-Vol Bull",
    "confidence": 0.78,
    "probabilities": {
      "low_vol_bull": 0.78,
      "high_vol_bull": 0.12,
      "low_vol_range": 0.07,
      "high_vol_bear": 0.03
    },
    "indicators": {
      "vix": 14.2, "sp500_vs_200ma": 1.08,
      "adx": 28.5, "yield_curve": 0.45
    },
    "strategy_affinity": {
      "trend_following": 0.9,
      "momentum": 0.85,
      "value": 0.5,
      "mean_reversion": 0.3
    },
    "updated_at": "2026-03-02T14:30:00Z"
  }

가격 티어:
  Free:    일간 1회 업데이트, S&P 500만
  Pro:     $19/mo, 30분 업데이트, 글로벌 시장
  Dev:     $49/mo, 실시간 WebSocket, API 접근

왜 팔리는가:
  - "지금 어떤 전략이 잘 먹힐까?" → 가장 기본적인 투자자 질문
  - 퀀트 시스템에 레짐 필터로 바로 연동
  - 뉴스레터/블로그에 "현재 레짐" 위젯으로 임베드
```

### 3.3 Tier 2: 중간 상업성 (니치 시장)

#### 제품 4: BacktestGuard — 백테스트 검증 서비스

```
제품명: BacktestGuard
태그라인: "당신의 백테스트는 진짜입니까?"
타겟: 퀀트 개발자, 알고 트레이딩 팀

핵심:
  - PBO (Probability of Backtest Overfitting) 계산
  - WFE (Walk-Forward Efficiency) 검증
  - Deflated Sharpe Ratio
  - 파라미터 안정성 테스트
  - "이 전략은 오버피팅 확률 62%입니다" → 매우 가치 있는 정보

가격: $29/mo (개인), $199/mo (팀)
시장 크기: 작지만 WTP(Willingness To Pay) 높음
```

#### 제품 5: RiskLens — 포트폴리오 리스크 분석

```
제품명: RiskLens
타겟: 개인 투자자, RIA(Registered Investment Advisor)

핵심:
  - 3단계 낙폭 방어 알림 (10%/15%/20%)
  - 섹터/상관관계 클러스터 분석
  - VaR/CVaR 리포트
  - 행동 편향 경고

가격: $39/mo
경쟁: 많지만, "행동 편향 경고" 기능으로 차별화
```

#### 제품 6: AlphaAttribution — 성과 분석

```
제품명: AlphaAttribution
타겟: 자산운용사, 헤지펀드, 패밀리 오피스

핵심:
  - 4레벨 어트리뷰션 (포트폴리오/전략/거래/팩터)
  - Fama-French 팩터 분해
  - "수익의 62%는 모멘텀 팩터, 23%는 품질 팩터에서 발생"

가격: $99/mo (기관용)
시장: 기관 투자자 (높은 WTP, 긴 세일즈 사이클)
```

### 3.4 상업 제품 통합 아키텍처

```
┌────────────────────────────────────────────────────────┐
│                  Trading Analytics Platform              │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Public API Gateway                   │    │
│  │   /api/v1/score  /api/v1/signal  /api/v1/regime   │    │
│  └──────────┬──────────┬──────────────┬─────────────┘    │
│             │          │              │                    │
│  ┌──────────┴──┐ ┌─────┴──────┐ ┌────┴──────────┐       │
│  │ QuantScore  │ │SignalFusion│ │ RegimeRadar   │       │
│  │ (스코어링)   │ │ (시그널)    │ │ (레짐 감지)   │       │
│  └──────┬──────┘ └─────┬──────┘ └───────┬───────┘       │
│         │              │                │                 │
│  ┌──────┴──────────────┴────────────────┴──────────┐    │
│  │              Shared Scoring Engine                │    │
│  │   F-Score  Z-Score  M-Score  Composite  Regime    │    │
│  └──────────────────────┬───────────────────────────┘    │
│                         │                                 │
│  ┌──────────────────────┴───────────────────────────┐    │
│  │              Data Layer (Cached)                   │    │
│  │   EODHD / Twelve Data / FMP                       │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │              Tier 2 Products (니치)                │    │
│  │   BacktestGuard  │  RiskLens  │  AlphaAttribution │    │
│  └──────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────┘
```

---

## 4. 종합 비교 매트릭스

### 4.1 컴포넌트별 분류

```
                    개인 가치    상업 가치    구현 난이도    법적 리스크   먼저 만들 것
                    ─────────   ─────────   ──────────   ─────────   ──────────
Scoring Engine        ★★★★★      ★★★★★      ★★☆☆☆       없음        ← 1순위 (양쪽 핵심)
Signal Generation     ★★★★★      ★★★★☆      ★★★☆☆       낮음        ← 2순위
Regime Detection      ★★★★☆      ★★★★★      ★★☆☆☆       없음        ← 3순위 (경쟁 없음)
Risk Manager          ★★★★★      ★★★☆☆      ★★★☆☆       낮음        ← 개인 먼저
Position Sizer        ★★★★★      ★☆☆☆☆      ★★☆☆☆       높음        ← 개인 전용
Self-Improver         ★★★★★      ★☆☆☆☆      ★★★★☆       없음        ← 개인 전용
Bias Checker          ★★★★☆      ★★☆☆☆      ★☆☆☆☆       없음        ← 부가 기능
Backtest Validator    ★★★☆☆      ★★★☆☆      ★★★☆☆       없음        ← 퀀트 니치
Execution Planner     ★★★★★      ☆☆☆☆☆      ★★★★☆       매우 높음   ← 개인 전용 (법적)
Orchestrator          ★★★★★      ★☆☆☆☆      ★★★★★       높음        ← 개인 전용 (복잡)
Attribution           ★★★☆☆      ★★★☆☆      ★★★☆☆       없음        ← 기관 니치
Data Ingest           ★★★★★      ★★☆☆☆      ★☆☆☆☆       없음        ← 기반 인프라
```

### 4.2 구현 순서 결정 로직

```
우선순위 공식:
  Priority = (개인가치 + 상업가치) × (1 / 구현난이도) × (1 / 법적리스크)

결과:
  1위: Scoring Engine    → (5+5) × (1/2) × (1/0) = 최고 (양쪽 핵심, 쉬움, 안전)
  2위: Regime Detection  → (4+5) × (1/2) × (1/0) = 높음 (경쟁 없음, 쉬움, 안전)
  3위: Signal Generation → (5+4) × (1/3) × (1/1) = 높음 (양쪽 가치)
  4위: Data Ingest       → (5+2) × (1/1) × (1/0) = 높음 (기반 인프라)
  5위: Risk Manager      → (5+3) × (1/3) × (1/1) = 중간
  6위: Position Sizer    → (5+1) × (1/2) × (1/3) = 중간 (개인 전용)
```

---

## 5. 통합 구현 전략: "하나의 코드, 두 개의 제품"

### 5.1 핵심 전략

```
원칙: Scoring Engine을 공통 기반으로 삼아 코드 한 벌로 양쪽 모두 서빙

trading-system/
├── core/                          # 공통 기반 (Personal + Commercial)
│   ├── scoring/                   # QuantScore 엔진
│   │   ├── f_score.py
│   │   ├── z_score.py
│   │   ├── m_score.py
│   │   ├── g_score.py
│   │   ├── technical.py
│   │   ├── sentiment.py
│   │   └── composite.py
│   ├── regime/                    # RegimeRadar 엔진
│   │   ├── detector.py
│   │   └── rules.py
│   ├── signals/                   # SignalFusion 엔진
│   │   ├── canslim.py
│   │   ├── magic_formula.py
│   │   ├── dual_momentum.py
│   │   └── trend_following.py
│   └── data/                      # 데이터 레이어
│       ├── twelve_data.py
│       ├── eodhd.py
│       └── fmp.py
│
├── personal/                      # 개인 전용 레이어
│   ├── position_sizer.py          # Kelly + ATR
│   ├── risk_manager.py            # 4단계 리스크
│   ├── bias_checker.py            # 행동 편향 체크
│   ├── execution/                 # 브로커 연동
│   │   ├── alpaca_executor.py
│   │   ├── kis_executor.py
│   │   └── futu_executor.py
│   ├── performance/               # 성과 분석
│   │   └── attribution.py
│   └── self_improver.py           # 자기 개선
│
├── commercial/                    # 상업 제품 레이어
│   ├── api/                       # REST API 서버
│   │   ├── app.py                 # FastAPI 서버
│   │   ├── routes/
│   │   │   ├── score.py           # /api/v1/score
│   │   │   ├── signal.py          # /api/v1/signal
│   │   │   └── regime.py          # /api/v1/regime
│   │   ├── auth.py                # API Key 인증
│   │   └── rate_limiter.py        # 티어별 Rate Limit
│   └── cache/                     # 결과 캐싱
│       └── redis_cache.py
│
├── cli/                           # CLI 인터페이스 (양쪽 공유)
│   ├── cli.py                     # Typer 메인
│   ├── commands/
│   │   ├── score.py               # 스코어링 명령
│   │   ├── signal.py              # 시그널 명령
│   │   ├── regime.py              # 레짐 명령
│   │   ├── trade.py               # 매매 명령 (개인 전용)
│   │   ├── portfolio.py           # 포트폴리오 (개인 전용)
│   │   └── serve.py               # API 서버 시작 (상업)
│   └── output/
│       ├── table.py               # 테이블 출력
│       └── json_out.py            # JSON 출력
│
└── .claude/
    ├── CLAUDE.md
    └── skills/                    # Claude Skill (양쪽 공유)
        ├── scoring-engine/
        ├── signal-generate/
        ├── regime-detect/
        ├── trading-orchestrator/  # 개인 전용
        ├── position-sizer/        # 개인 전용
        ├── risk-manager/          # 개인 전용
        └── ...
```

### 5.2 단계별 확장 경로

```
Phase 1 (Week 1-3): 공통 기반 = 개인 시작 + 상업 시작
  ├── core/scoring (F-Score, Z-Score, 복합)     → 개인 사용 즉시 가능
  ├── core/regime (레짐 감지)                    → 개인 사용 + API 골격
  ├── core/data (EODHD 연동)                    → 데이터 파이프라인
  └── cli/commands/score, regime                 → CLI 도구

Phase 2 (Week 4-5): 개인 핵심 완성
  ├── personal/position_sizer                    → 포지션 계산
  ├── personal/risk_manager                      → 리스크 검증
  ├── personal/execution/alpaca_executor          → Paper Trading
  └── .claude/skills/ (개인 스킬 7개)             → Claude Skill 연동

Phase 3 (Week 6-7): 상업 제품 v1
  ├── core/signals (4전략)                       → SignalFusion
  ├── commercial/api (FastAPI 서버)               → REST API
  ├── commercial/api/routes/score                 → QuantScore API
  ├── commercial/api/routes/regime                → RegimeRadar API
  └── 배포 (Docker + Railway/Fly.io)

Phase 4 (Week 8-10): 확장
  ├── commercial/api/routes/signal                → SignalFusion API
  ├── personal/performance/attribution            → 성과 분석
  ├── personal/self_improver                      → 자기 개선
  └── Twelve Data / KIS 연동                     → 글로벌 확장
```

---

## 6. 수익 모델 예측

### 6.1 상업 제품 매출 시나리오

#### 보수적 시나리오 (12개월 후)

| 제품 | 사용자 수 | 평균 단가 | MRR |
|------|---------|---------|-----|
| QuantScore | 50명 | $45/mo | $2,250 |
| RegimeRadar | 30명 | $25/mo | $750 |
| SignalFusion | 20명 | $75/mo | $1,500 |
| **합계** | **100명** | | **$4,500/mo** |

#### 비용

| 항목 | 월 비용 |
|------|--------|
| 데이터 API (Twelve Data + EODHD + FMP) | $479 |
| 서버 (Railway/Fly.io) | $50 |
| Claude API (캐시 활용, 배치 처리) | $100 |
| **합계** | **$629/mo** |

#### 손익

```
MRR $4,500 - 비용 $629 = 순이익 $3,871/mo (마진 86%)
```

### 6.2 개인 시스템의 가치

```
정량화 불가하지만:
  - 감정적 매매 방지 → 연간 낙폭 방어 가치 (수백~수천만원)
  - 체계적 스코어링 → 분석 시간 90% 절감 (주 10시간 → 1시간)
  - 자기 개선 루프 → 장기 수익률 개선
  - "내 투자 시스템이 있다"는 심리적 안정감
```

---

## 7. 결정 사항 요약

### 확정 전략

| 항목 | 결정 |
|------|------|
| **공통 기반** | Scoring Engine (F-Score, Z-Score, 복합점수) |
| **개인 전용** | Position Sizer, Risk Manager, Execution, Self-Improver, Orchestrator |
| **상업 Tier 1** | QuantScore (스코어링 API), SignalFusion (시그널), RegimeRadar (레짐) |
| **상업 Tier 2** | BacktestGuard, RiskLens, AlphaAttribution |
| **법적 원칙** | "정보 제공"만 (투자 자문 아님), 면책조항 필수 |
| **구현 순서** | Scoring → Regime → Signal → Position → Risk → Execution → Self-Improve |
| **코드 구조** | core/ (공유) + personal/ + commercial/ 3계층 |
| **Phase 1 데이터** | EODHD ($100/mo) + yfinance (보조) |
| **Phase 2 데이터** | + Twelve Data ($229/mo) |
| **Phase 3 데이터** | + FMP ($150/mo) |
| **CLI 프레임워크** | Typer (모던, Click 기반, 타입 힌트) |
| **API 프레임워크** | FastAPI (비동기, 자동 문서화, Typer와 호환) |
| **브로커 Phase 1** | Alpaca (미국, 무료 Paper Trading) |
| **브로커 Phase 2** | + KIS (한국) |
