# 트레이딩 방법론 → Claude Skill 변환 플랜

## Trading Methodology to Claude Skill Conversion Plan

**목적**: docs/에 정리된 4대 트레이딩 방법론 문서를 Claude Code Skills + Team Agents 기반의
실행 가능한 AI 트레이딩 어시스턴트 시스템으로 변환

**핵심 원칙**:
- 9계층 스킬 체인 → 9개 전문 Claude Skill로 1:1 매핑
- 독립적 분석 작업 → Team Agents 병렬 실행으로 속도 극대화
- 자기 개선 루프 → 자동 피드백 스킬로 구현
- 단타 지양 → 모든 스킬에 중장기 시간축 강제

---

## 1. 아키텍처 개요

### 1.1 전체 시스템 구조

```
.claude/
├── CLAUDE.md                          # 프로젝트 메모리 + 트레이딩 원칙
├── settings.json                      # Team Agent 활성화, 권한 설정
├── skills/
│   │
│   │  ── [ 오케스트레이터 ] ──────────────────────────
│   ├── trading-orchestrator/          # 메인 코디네이터 (전체 파이프라인 관리)
│   │   ├── SKILL.md
│   │   └── workflows/
│   │       ├── full-pipeline.md       # 전체 9계층 파이프라인 실행
│   │       ├── quick-scan.md          # 빠른 종목 스캔
│   │       └── portfolio-review.md    # 포트폴리오 점검
│   │
│   │  ── [ Layer 1: 데이터 ] ────────────────────────
│   ├── data-ingest/                   # 데이터 수집 + 피처 엔지니어링
│   │   ├── SKILL.md
│   │   └── sources.md                 # 데이터 소스 레퍼런스
│   │
│   │  ── [ Layer 2: 레짐 감지 ] ─────────────────────
│   ├── regime-detect/                 # 시장 레짐 판별
│   │   ├── SKILL.md
│   │   └── regime-rules.md
│   │
│   │  ── [ Layer 3: 시그널 생성 ] ────────────────────
│   ├── signal-generate/               # 멀티 전략 시그널 생성
│   │   ├── SKILL.md
│   │   └── strategies/
│   │       ├── canslim.md             # CAN SLIM 인코딩
│   │       ├── magic-formula.md       # Magic Formula 인코딩
│   │       ├── dual-momentum.md       # Dual Momentum 인코딩
│   │       └── trend-following.md     # 트렌드 팔로잉 인코딩
│   │
│   │  ── [ Layer 4: 스코어링 + 전략 선택 ] ──────────
│   ├── scoring-engine/                # 정량적 복합 스코어링
│   │   ├── SKILL.md
│   │   └── scoring-models/
│   │       ├── f-score.md             # Piotroski F-Score
│   │       ├── z-score.md             # Altman Z-Score
│   │       ├── m-score.md             # Beneish M-Score
│   │       ├── g-score.md             # Mohanram G-Score
│   │       └── composite.md           # 복합 점수 계산 규칙
│   │
│   │  ── [ Layer 5: 포지션 사이징 ] ──────────────────
│   ├── position-sizer/                # Kelly + ATR 기반 사이징
│   │   ├── SKILL.md
│   │   └── sizing-rules.md
│   │
│   │  ── [ Layer 6: 리스크 관리 ] ────────────────────
│   ├── risk-manager/                  # 4단계 리스크 관리
│   │   ├── SKILL.md
│   │   └── risk-rules.md
│   │
│   │  ── [ Layer 7: 실행 계획 ] ──────────────────────
│   ├── execution-planner/             # 주문 계획 생성
│   │   ├── SKILL.md
│   │   └── execution-rules.md
│   │
│   │  ── [ Layer 8: 성과 분석 ] ──────────────────────
│   ├── performance-analyst/           # 4단계 어트리뷰션
│   │   ├── SKILL.md
│   │   └── attribution-rules.md
│   │
│   │  ── [ Layer 9: 자기 개선 ] ──────────────────────
│   ├── self-improver/                 # WFO + 파라미터 최적화
│   │   ├── SKILL.md
│   │   └── improvement-rules.md
│   │
│   │  ── [ 유틸리티 스킬 ] ──────────────────────────
│   ├── backtest-validator/            # 백테스트 검증 + 오버피팅 탐지
│   │   ├── SKILL.md
│   │   └── validation-checklist.md
│   │
│   └── bias-checker/                  # 행동재무학 편향 체크
│       ├── SKILL.md
│       └── biases.md
│
├── agents/                            # Team Agent 정의
│   ├── fundamental-analyst.md         # 기본적 분석 전문 에이전트
│   ├── technical-analyst.md           # 기술적 분석 전문 에이전트
│   ├── sentiment-analyst.md           # 센티먼트 분석 전문 에이전트
│   ├── risk-auditor.md                # 리스크 감사 전문 에이전트
│   └── methodology-verifier.md        # 방법론 검증 전문 에이전트
│
└── docs/                              # 기존 리서치 문서 (참조 자료)
    ├── README.md
    ├── trading-methodology-overview.md
    ├── quantitative-scoring-methodologies.md
    ├── skill_chaining_and_self_improvement_research.md
    └── verified-methodologies-and-risk-management.md
```

### 1.2 스킬 체인 → Claude Skill 매핑

```
트레이딩 스킬 체인              Claude Skill              Team Agent 활용
──────────────────         ────────────────         ──────────────────

Layer 1: 데이터 인프라    →  /data-ingest            단독 실행
         │
Layer 2: 레짐 감지       →  /regime-detect          단독 실행
         │
Layer 3: 시그널 생성      →  /signal-generate        ★ 4 Team Agents 병렬
         │                                             (CAN SLIM, Magic Formula,
         │                                              Dual Momentum, Trend)
Layer 4: 스코어링         →  /scoring-engine         ★ 3 Team Agents 병렬
         │                                             (Fundamental, Technical,
         │                                              Sentiment 각각 분석)
Layer 5: 포지션 사이징    →  /position-sizer         단독 실행
         │
Layer 6: 리스크 관리      →  /risk-manager           ★ 2 Team Agents 병렬
         │                                             (Risk Auditor + Bias Checker)
Layer 7: 실행 계획       →  /execution-planner       단독 실행
         │
Layer 8: 성과 분석       →  /performance-analyst     ★ 4 Team Agents 병렬
         │                                             (Trade/Strategy/Factor/Skill
         │                                              각 레벨 어트리뷰션)
Layer 9: 자기 개선       →  /self-improver           단독 실행

전체 오케스트레이션:
  /trading-orchestrator     → 위 9개 스킬을 순차/병렬로 체이닝
```

### 1.3 Team Agent 병렬 실행 설계

**핵심 병렬화 포인트** (가장 큰 성능 이득):

```
포인트 1: 멀티 전략 시그널 생성 (Layer 3)
┌──────────────────────────────────────────┐
│  trading-orchestrator 가 4개 에이전트 동시 스폰  │
│                                          │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐
│  │CAN SLIM │  │Magic    │  │Dual      │  │Trend     │
│  │Agent    │  │Formula  │  │Momentum  │  │Following │
│  │         │  │Agent    │  │Agent     │  │Agent     │
│  └────┬────┘  └────┬────┘  └────┬─────┘  └────┬─────┘
│       │            │            │              │
│       └────────────┴────────────┴──────────────┘
│                        │
│               종합 시그널 병합
└──────────────────────────────────────────┘

포인트 2: 3축 스코어링 (Layer 4)
┌──────────────────────────────────────────┐
│  scoring-engine 이 3개 분석가 동시 스폰         │
│                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  │Fundamental   │  │Technical     │  │Sentiment     │
│  │Analyst Agent │  │Analyst Agent │  │Analyst Agent │
│  │              │  │              │  │              │
│  │• F-Score     │  │• 추세/MA     │  │• 애널리스트   │
│  │• Z-Score     │  │• 모멘텀      │  │• 내부자 거래  │
│  │• EV/EBIT     │  │• 거래량      │  │• 공매도 비율  │
│  │• ROE/ROIC    │  │• RSI/ADX     │  │• 뉴스 센티먼트│
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
│         │                 │                  │
│         └─────────────────┴──────────────────┘
│                           │
│              정규화 → 가중 합산 → 복합 점수
└──────────────────────────────────────────┘

포인트 3: 리스크 다중 검증 (Layer 6)
┌──────────────────────────────────────────┐
│  ┌──────────────┐  ┌──────────────┐      │
│  │Risk Auditor  │  │Bias Checker  │      │
│  │Agent         │  │Agent         │      │
│  │              │  │              │      │
│  │• VaR/CVaR    │  │• 손실 회피   │      │
│  │• 섹터 집중도  │  │• 처분 효과   │      │
│  │• 상관관계     │  │• 과신       │      │
│  │• 낙폭 체크   │  │• 앵커링     │      │
│  └──────┬───────┘  └──────┬───────┘      │
│         └─────────────────┘               │
│              리스크 종합 보고서             │
└──────────────────────────────────────────┘
```

---

## 2. 각 스킬 상세 설계

### 2.1 `/trading-orchestrator` — 메인 코디네이터

```yaml
---
name: trading-orchestrator
description: 체계적 트레이딩 파이프라인을 오케스트레이션합니다. 종목 분석,
  포트폴리오 점검, 리밸런싱 판단을 체계적으로 수행합니다.
argument-hint: "[workflow] [ticker/portfolio]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash, Agent
model: opus
---
```

**역할**: 전체 9계층 파이프라인의 진입점이자 코디네이터
**워크플로우 3가지**:

| 워크플로우 | 호출 예시 | 설명 | Team Agent 수 |
|-----------|---------|------|-------------|
| `full-pipeline` | `/trading-orchestrator full AAPL` | 전체 9계층 분석 | 최대 13개 |
| `quick-scan` | `/trading-orchestrator scan "AAPL MSFT GOOGL"` | 빠른 스코어링 | 3개 (3축) |
| `portfolio-review` | `/trading-orchestrator review portfolio.json` | 포트폴리오 점검 | 6개 |

**오케스트레이션 흐름 (full-pipeline)**:
```
1. /data-ingest $TICKER           → 데이터 수집 (순차)
2. /regime-detect                 → 레짐 판별 (순차)
3. /signal-generate $TICKER       → 4 Team Agents 병렬 시그널 생성
4. /scoring-engine $TICKER        → 3 Team Agents 병렬 스코어링
5. /position-sizer                → 포지션 계산 (순차, Layer 3-4 결과 사용)
6. /risk-manager                  → 2 Team Agents 병렬 리스크 검증
7. /execution-planner             → 실행 계획 (순차)
8. /bias-checker                  → 편향 체크 (순차)
9. 최종 보고서 생성
```

### 2.2 `/data-ingest` — 데이터 수집

```yaml
---
name: data-ingest
description: 트레이딩 분석에 필요한 시장 데이터를 수집하고 전처리합니다.
argument-hint: "[ticker(s)]"
user-invocable: true
allowed-tools: Bash, Read, Write
model: haiku
---
```

**역할**: yfinance/pykrx/FMP에서 데이터 수집, 전처리, 피처 계산
**출력**: 구조화된 데이터 (가격, 재무제표, 기술적 지표)

**구현 핵심**:
```
수집 대상:
  - 가격: 일간 OHLCV (최소 3년), 주간/월간 변환
  - 펀더멘탈: 최근 4분기 + 연간 3년 재무제표
  - 기술적: MA(50,200), RSI(14), ATR(21), ADX(14), OBV, MACD
  - 시장: VIX, S&P 500 200-day MA, 수익률 곡선

전처리:
  - 이상치 윈저라이징 (1st/99th 백분위)
  - 결측값 처리
  - 수정주가 사용 (배당/분할 조정)

출력 포맷: JSON 또는 구조화된 마크다운 테이블
```

### 2.3 `/regime-detect` — 레짐 감지

```yaml
---
name: regime-detect
description: 현재 시장 레짐을 판별합니다. HMM 로직 기반 정성적 분석 또는
  Python hmmlearn 실행을 통한 정량적 분석을 수행합니다.
user-invocable: true
allowed-tools: Bash, Read
model: sonnet
---
```

**역할**: 시장을 2-4개 상태로 분류, 현재 레짐 확률 산출
**레짐 분류 규칙** (docs 기반 인코딩):

```
입력 지표:
  - VIX 수준 (< 15: 저변동, 15-25: 보통, > 25: 고변동)
  - S&P 500 vs 200-day MA (위: 상승추세, 아래: 하락추세)
  - ADX (> 25: 추세 존재, < 20: 횡보)
  - 수익률 곡선 기울기 (양: 성장, 역전: 침체 경고)

레짐 매핑:
  저변동 + 상승추세 = "Low-Vol Bull"    → 트렌드 팔로잉, 모멘텀 유리
  고변동 + 상승추세 = "High-Vol Bull"   → 넓은 스탑의 트렌드 팔로잉
  저변동 + 횡보     = "Low-Vol Range"   → 평균회귀, 가치 전략 유리
  고변동 + 하락추세 = "High-Vol Bear"   → 방어적, 현금 비중 확대
  불확실 (확률 < 60%) = "Transition"    → 포지션 축소, 헤지

출력:
  {
    "regime": "Low-Vol Bull",
    "confidence": 0.78,
    "vix": 14.2,
    "trend": "bullish",
    "recommended_strategies": ["trend_following", "momentum"],
    "risk_adjustment": 1.0  // 1.0=정상, 0.5=방어적, 0=전량 현금
  }
```

### 2.4 `/signal-generate` — 시그널 생성 (Team Agents 핵심)

```yaml
---
name: signal-generate
description: 4가지 검증된 방법론으로 동시에 트레이딩 시그널을 생성합니다.
  Team Agents를 활용하여 CAN SLIM, Magic Formula, Dual Momentum,
  트렌드 팔로잉을 병렬 분석합니다.
argument-hint: "[ticker(s)]"
user-invocable: true
allowed-tools: Read, Bash, Agent
model: opus
---
```

**역할**: 4가지 검증된 방법론을 Team Agent로 동시 실행

**Team Agent 설계**:

| Agent | 전문 방법론 | 도구 | 모델 | 시간축 |
|-------|-----------|------|------|--------|
| `canslim-agent` | CAN SLIM 7가지 기준 | Read, Bash | sonnet | 수주~수개월 |
| `magic-formula-agent` | Earnings Yield + ROC | Read, Bash | haiku | 1년 |
| `dual-momentum-agent` | 상대+절대 모멘텀 | Read, Bash | haiku | 1~12개월 |
| `trend-agent` | MA/ADX/Breakout | Read, Bash | haiku | 수주~수개월 |

**각 에이전트 출력 포맷** (통일):
```json
{
  "methodology": "CAN SLIM",
  "ticker": "AAPL",
  "signal": "BUY",           // BUY, HOLD, SELL, AVOID
  "score": 6,                // 방법론별 점수 (정규화 전)
  "score_max": 7,
  "confidence": 0.85,
  "holding_period": "weeks_to_months",
  "key_factors": {
    "C_quarterly_eps": true,
    "A_annual_eps": true,
    "N_new_high": true,
    "S_volume": false,
    "L_leader": true,
    "I_institutional": true,
    "M_market": true
  },
  "reasoning": "..."
}
```

**병합 로직** (오케스트레이터에서):
```
최종_시그널 = 가중_평균(
  canslim_score_정규화 * regime_weight_canslim,
  magic_score_정규화   * regime_weight_magic,
  momentum_score_정규화 * regime_weight_momentum,
  trend_score_정규화   * regime_weight_trend
)

레짐별 가중치:
  Low-Vol Bull:   canslim=0.30, magic=0.20, momentum=0.25, trend=0.25
  High-Vol Bear:  canslim=0.10, magic=0.35, momentum=0.30, trend=0.25
  Low-Vol Range:  canslim=0.15, magic=0.40, momentum=0.20, trend=0.25
  Transition:     등가중 (각 0.25)
```

### 2.5 `/scoring-engine` — 복합 스코어링 (Team Agents 핵심)

```yaml
---
name: scoring-engine
description: 3축 정량적 복합 스코어를 계산합니다. 기본적/기술적/센티먼트
  분석을 Team Agents로 병렬 수행하여 종합 점수를 산출합니다.
argument-hint: "[ticker(s)]"
user-invocable: true
allowed-tools: Read, Bash, Agent
model: opus
---
```

**Team Agent 설계**:

| Agent | 분석 영역 | 가중치 (스윙) | 가중치 (포지션) |
|-------|---------|------------|-------------|
| `fundamental-analyst` | 가치+품질+성장+재무건전성 | 35% | 50% |
| `technical-analyst` | 추세+모멘텀+거래량 | 40% | 30% |
| `sentiment-analyst` | 애널리스트+내부자+공매도 | 25% | 20% |

**Fundamental Analyst Agent 상세**:
```
입력: 재무제표 데이터
처리:
  1. 안전성 필터 (Pass/Fail):
     - Altman Z-Score > 1.81
     - Beneish M-Score < -1.78
  2. 서브 스코어 계산:
     - 가치: Percentile_Rank(EV/EBIT) + Percentile_Rank(P/B)
     - 품질: Piotroski F-Score (0-9) → 정규화
     - 성장: EPS CAGR 3년, 매출 CAGR 3년
     - 건전성: Z-Score 연속값 정규화
  3. 정규화: 백분위 순위 (0-100), 섹터 중립
출력: fundamental_score (0-100), 세부 항목별 점수, 필터 결과
```

**Technical Analyst Agent 상세**:
```
입력: OHLCV + 기술적 지표
처리:
  1. 추세 점수: Price vs MA(200), ADX, MACD 방향
  2. 모멘텀 점수: 12-1개월 수익률, 섹터 상대강도
  3. 거래량 점수: OBV 추세, 거래량 비율
  4. 정규화: 백분위 순위 (0-100)
출력: technical_score (0-100), 세부 항목별 점수
```

**Sentiment Analyst Agent 상세**:
```
입력: 애널리스트 추정치, 내부자 거래, 공매도 데이터
처리:
  1. 추정치 변경 방향 (상향/하향)
  2. 내부자 매수/매도 비율
  3. 공매도 비율 변화
  4. 정규화: 백분위 순위 (0-100)
출력: sentiment_score (0-100), 세부 항목별 점수
```

**복합 점수 합산** (오케스트레이터에서):
```
Composite_Score = w_F * fundamental_score + w_T * technical_score + w_S * sentiment_score

리스크 조정:
  Risk_Adjusted_Score = Composite_Score - λ * Tail_Risk_Penalty

최종 순위: 정렬 후 상위 N개 선택
```

### 2.6 `/position-sizer` — 포지션 사이징

```yaml
---
name: position-sizer
description: Fractional Kelly와 ATR 기반으로 최적 포지션 크기를 계산합니다.
argument-hint: "[ticker] [score] [portfolio-value]"
user-invocable: true
allowed-tools: Read, Bash
model: sonnet
---
```

**구현 규칙** (docs 인코딩):
```
입력: composite_score, volatility, atr, portfolio_value, regime_confidence

Kelly 기반:
  kelly_fraction = 0.25  (기본값, 1/4 Kelly)
  kelly_size = kelly_fraction * (win_rate * odds - loss_rate) / odds

ATR 기반:
  risk_per_trade = 0.01  (자본의 1%)
  stop_distance = ATR(21) * 3.0
  atr_size = (portfolio_value * risk_per_trade) / stop_distance

확신도 조정:
  score_multiplier = 0.5 + (composite_score / 100)  // 0.5 ~ 1.5

최종 사이즈:
  target_size = min(kelly_size, atr_size) * score_multiplier * regime_confidence
  target_size = clamp(target_size, min=0.01, max=0.08)  // 1%~8%

출력:
  {
    "ticker": "AAPL",
    "target_weight": 0.045,        // 포트폴리오의 4.5%
    "shares": 15,
    "dollar_amount": 4500,
    "stop_loss": 172.50,
    "risk_amount": 45.00,          // 자본의 ~1%
    "sizing_method": "min(kelly, atr) * conviction",
    "kelly_raw": 0.062,
    "atr_raw": 0.048
  }
```

### 2.7 `/risk-manager` — 리스크 관리 (Team Agents)

```yaml
---
name: risk-manager
description: 다중 레벨 리스크 검증을 수행합니다. Risk Auditor와
  Bias Checker 에이전트가 병렬로 리스크를 점검합니다.
user-invocable: true
allowed-tools: Read, Bash, Agent
model: opus
---
```

**Team Agent 2개 병렬 실행**:

**Risk Auditor Agent**:
```
점검 항목:
  거래 레벨:
    [ ] ATR 스탑로스 설정 완료? (2.5-3.5x ATR)
    [ ] 리스크/거래 <= 1%?

  포트폴리오 레벨:
    [ ] 단일 종목 비중 <= 8%?
    [ ] 섹터 집중도 <= 25%?
    [ ] 상관 클러스터 <= 20%?
    [ ] 현재 낙폭 상태?
      - < 10%: 정상 (Level 0)
      - 10-15%: 경고 → 신규 진입 중단 권고 (Level 1)
      - 15-20%: 방어 → 50% 축소 권고 (Level 2)
      - > 20%: 비상 → 전량 청산 권고 (Level 3)

  출력: risk_report { level, violations[], recommendations[] }
```

**Bias Checker Agent**:
```
점검 항목:
  [ ] 손실 회피: 손실 종목을 이유 없이 보유하고 있지 않은지?
  [ ] 처분 효과: 이익 종목을 너무 일찍 매도하려 하지 않는지?
  [ ] 과신: 포지션 크기가 Kelly 한도를 초과하지 않는지?
  [ ] 확증 편향: 스코어에서 특정 팩터만 강조하지 않는지?
  [ ] 앵커링: 매수가에 대한 언급이 결정에 영향을 주지 않는지?
  [ ] 최근 편향: 최근 성과에 과도하게 반응하지 않는지?

  출력: bias_report { detected_biases[], mitigations[] }
```

### 2.8 `/performance-analyst` — 성과 분석 (Team Agents)

```yaml
---
name: performance-analyst
description: 4단계 성과 어트리뷰션을 수행합니다.
  포트폴리오/전략/거래/스킬 레벨의 성과를 분석합니다.
user-invocable: true
allowed-tools: Read, Bash, Agent
model: opus
---
```

**4레벨 어트리뷰션을 4개 Team Agent로 병렬**:

| Agent | 레벨 | 핵심 지표 |
|-------|------|---------|
| `portfolio-attribution-agent` | 포트폴리오 | Sharpe, Sortino, Calmar, MDD, 팩터 어트리뷰션 |
| `strategy-attribution-agent` | 전략 | 전략별 Sharpe, 승률, 상관관계, 낙폭 |
| `trade-attribution-agent` | 거래 | 거래별 P&L, 슬리피지, 보유기간, 진입/청산 타이밍 |
| `skill-attribution-agent` | 스킬 | 레짐 정확도, IC, Kelly 효율, 리스크 관리 효과 |

### 2.9 `/self-improver` — 자기 개선

```yaml
---
name: self-improver
description: 성과 분석 결과를 기반으로 시스템 파라미터 개선을 제안합니다.
  Walk-Forward 결과와 스킬별 진단을 분석하여 구체적 조정안을 도출합니다.
user-invocable: true
allowed-tools: Read, Bash, Write
model: opus
---
```

**자기 개선 루프 인코딩**:
```
입력: performance-analyst 출력 (4레벨 어트리뷰션)

진단 → 처방 매핑:
  레짐 정확도 < 55%     → HMM 재학습 권고, 피처 추가 제안
  시그널 IC < 0.03      → Walk-Forward 재최적화, 피처 중요도 드리프트 체크
  Kelly 효율 < 70%      → 켈리 파라미터 재보정, 변동성 추정 검토
  전략 상관관계 > 0.7   → 전략 교체/추가 필요
  MDD > 15%            → 스탑 파라미터 타이트닝, 레짐 필터 강화
  WFE < 50%            → 오버피팅 의심, 파라미터 수 축소

출력:
  {
    "diagnostics": { ... },
    "flags": ["signal_quality_low", "regime_detection_degraded"],
    "recommended_actions": [
      "walk_forward_reoptimize_signals",
      "retrain_hmm_model",
      "reduce_parameter_count"
    ],
    "priority": "high",
    "next_review_date": "2026-04-01"
  }
```

### 2.10 `/backtest-validator` — 백테스트 검증

```yaml
---
name: backtest-validator
description: 백테스트 결과의 유효성을 검증합니다. 오버피팅, 생존자 편향,
  미래정보 편향 등을 체크합니다.
user-invocable: true
allowed-tools: Read, Bash
model: sonnet
---
```

**검증 체크리스트** (docs 인코딩):
```
데이터 무결성:
  [ ] Point-in-Time 펀더멘탈? (재수정 데이터 사용 안 함?)
  [ ] 생존자 편향 없는 유니버스? (상장폐지 종목 포함?)
  [ ] 기업행위 조정? (분할, 배당)
  [ ] 10년+ 히스토리, 다중 시장 사이클?

방법론:
  [ ] Walk-Forward 또는 CPCV? (단일 IS/OOS 분할 아님?)
  [ ] 현실적 리밸런싱 주기?
  [ ] 거래비용 포함? (수수료 + 스프레드 + 시장 충격)
  [ ] 용량 제약 고려?

통계 검증:
  [ ] PBO < 10%?
  [ ] WFE > 50%?
  [ ] 파라미터 ±10% 변경 시 성과 유지?
  [ ] 샤프비율 t-stat > 2?
```

---

## 3. CLAUDE.md 설계

프로젝트 루트의 `.claude/CLAUDE.md`에 트레이딩 시스템의 핵심 원칙을 기록:

```markdown
# Trading System Project Memory

## 핵심 원칙
- 단타(데이 트레이딩, 스캘핑) 절대 금지
- 모든 판단은 정량적 스코어 기반 (주관적 판단 배제)
- 검증된 방법론만 사용 (학술 논문 또는 10년+ 백테스트)
- Fractional Kelly (1/4) 기본, 절대 Full Kelly 사용 금지
- 최대 낙폭 20% 초과 시 전량 청산 후 냉각기

## 시간축
- 최소 보유 기간: 2주 (스윙), 3개월 (포지션)
- 리밸런싱: 월간 (스윙), 분기 (포지션)
- 데이터 분석: 주간/월간 차트 기반

## 리스크 한도
- 단일 종목: 최대 8%
- 섹터: 최대 25%
- 거래당 리스크: 자본의 1%
- ATR 스탑: 2.5-3.5x ATR(21)

## 방법론 문서 위치
- docs/trading-methodology-overview.md (통합 개요)
- docs/quantitative-scoring-methodologies.md (스코어링)
- docs/skill_chaining_and_self_improvement_research.md (스킬 체인)
- docs/verified-methodologies-and-risk-management.md (검증된 방법론)

## 기술 스택
- 데이터: yfinance, pykrx, FinanceDataReader
- 기술 분석: pandas-ta
- 백테스팅: VectorBT (리서치), Backtrader (실행)
- ML: scikit-learn, XGBoost, hmmlearn
- 최적화: Optuna, PyPortfolioOpt
```

---

## 4. settings.json 설계

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Glob",
      "Grep",
      "Bash(python3 *)",
      "Bash(pip install *)",
      "Bash(git *)"
    ]
  },
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

---

## 5. 구현 순서 (Phase별 로드맵)

### Phase 1: 기반 인프라 (1주)

```
목표: 프로젝트 구조 + 핵심 2개 스킬 완성

작업:
  1. .claude/ 디렉토리 구조 생성
  2. CLAUDE.md 작성 (프로젝트 메모리)
  3. settings.json 설정
  4. /data-ingest 스킬 구현
     - yfinance/pykrx 데이터 수집 스크립트 작성
     - 기술적 지표 계산 (pandas-ta)
     - 출력 포맷 정의
  5. /regime-detect 스킬 구현
     - VIX/MA/ADX 기반 규칙 인코딩
     - 레짐 분류 로직

검증: /data-ingest AAPL → /regime-detect 순차 실행 성공
```

### Phase 2: 스코어링 엔진 (1-2주)

```
목표: 3축 스코어링 + Team Agent 병렬화

작업:
  1. /scoring-engine 스킬 구현
  2. fundamental-analyst Agent 정의
     - F-Score, Z-Score, M-Score 계산 로직
     - 가치/품질/성장 서브스코어
  3. technical-analyst Agent 정의
     - 추세/모멘텀/거래량 서브스코어
  4. sentiment-analyst Agent 정의
     - 애널리스트 추정치, 내부자 거래
  5. 복합 점수 합산 로직
  6. 정규화 (백분위 순위, 섹터 중립)

검증: /scoring-engine "AAPL MSFT GOOGL" → 3 Agent 병렬 → 복합 점수 출력
```

### Phase 3: 시그널 생성 + 검증된 방법론 (1-2주)

```
목표: 4가지 검증된 방법론의 Claude Skill 인코딩

작업:
  1. /signal-generate 스킬 구현
  2. CAN SLIM Agent (strategies/canslim.md)
  3. Magic Formula Agent (strategies/magic-formula.md)
  4. Dual Momentum Agent (strategies/dual-momentum.md)
  5. Trend Following Agent (strategies/trend-following.md)
  6. 시그널 병합 로직 (레짐 기반 가중치)

검증: /signal-generate AAPL → 4 Agent 병렬 → 통합 시그널
```

### Phase 4: 포지션 사이징 + 리스크 (1주)

```
목표: 포지션 사이징 + 다중 리스크 검증

작업:
  1. /position-sizer 스킬 구현 (Kelly + ATR)
  2. /risk-manager 스킬 구현
  3. Risk Auditor Agent 정의
  4. Bias Checker Agent 정의
  5. 낙폭 3단계 방어 로직 인코딩

검증: 포지션 제안 → 리스크 검증 통과 → 실행 계획 출력
```

### Phase 5: 오케스트레이터 + 통합 (1주)

```
목표: 전체 파이프라인 통합

작업:
  1. /trading-orchestrator 스킬 구현
  2. 3가지 워크플로우 (full-pipeline, quick-scan, portfolio-review)
  3. /execution-planner 스킬 구현
  4. /backtest-validator 스킬 구현
  5. 전체 파이프라인 End-to-End 테스트

검증: /trading-orchestrator full AAPL → 전체 9계층 → 최종 보고서
```

### Phase 6: 성과 분석 + 자기 개선 (1-2주)

```
목표: 피드백 루프 완성

작업:
  1. /performance-analyst 스킬 구현
  2. 4레벨 어트리뷰션 Agent (4개)
  3. /self-improver 스킬 구현
  4. 진단 → 처방 매핑 인코딩
  5. 개선 주기 스케줄러 (월간/분기)

검증: 모의 거래 데이터 → 성과 분석 → 개선 제안 → 파라미터 조정
```

---

## 6. Team Agent 활용 요약

### 총 에이전트 수: 13개 전문 에이전트

| # | 에이전트 | 스폰 위치 | 모델 | 실행 방식 |
|---|---------|---------|------|---------|
| 1 | CAN SLIM Analyst | signal-generate | sonnet | 병렬 (4개 중 1) |
| 2 | Magic Formula Analyst | signal-generate | haiku | 병렬 (4개 중 1) |
| 3 | Dual Momentum Analyst | signal-generate | haiku | 병렬 (4개 중 1) |
| 4 | Trend Following Analyst | signal-generate | haiku | 병렬 (4개 중 1) |
| 5 | Fundamental Analyst | scoring-engine | sonnet | 병렬 (3개 중 1) |
| 6 | Technical Analyst | scoring-engine | haiku | 병렬 (3개 중 1) |
| 7 | Sentiment Analyst | scoring-engine | haiku | 병렬 (3개 중 1) |
| 8 | Risk Auditor | risk-manager | sonnet | 병렬 (2개 중 1) |
| 9 | Bias Checker | risk-manager | haiku | 병렬 (2개 중 1) |
| 10 | Portfolio Attribution | performance-analyst | haiku | 병렬 (4개 중 1) |
| 11 | Strategy Attribution | performance-analyst | haiku | 병렬 (4개 중 1) |
| 12 | Trade Attribution | performance-analyst | haiku | 병렬 (4개 중 1) |
| 13 | Skill Attribution | performance-analyst | sonnet | 병렬 (4개 중 1) |

### 비용 최적화 전략

```
원칙: "분석의 깊이에 따라 모델 선택"

opus   → 오케스트레이터, 복합 판단이 필요한 스킬 (2개)
sonnet → 중간 복잡도 분석 (4개)
haiku  → 정형화된 계산, 단순 규칙 적용 (7개)

예상 비용 절감: haiku 사용으로 단순 작업 비용 ~90% 절감
```

---

## 7. 핵심 설계 원칙

### 7.1 스킬 간 인터페이스 계약

모든 스킬은 구조화된 JSON으로 소통:
```
{
  "skill": "스킬명",
  "version": "1.0",
  "timestamp": "2026-03-02T00:00:00Z",
  "status": "success|warning|error",
  "data": { ... },              // 핵심 출력
  "metadata": {
    "model_used": "sonnet",
    "execution_time_ms": 1234,
    "confidence": 0.85
  }
}
```

### 7.2 실패 처리

```
에이전트 실패 시:
  - 타임아웃 (60초): 해당 에이전트 결과 제외, 나머지로 진행
  - 데이터 없음: 해당 서브스코어 0으로 처리, 경고 표시
  - 전체 실패: 오케스트레이터가 에러 보고서 생성

낙폭 트리거 시:
  - Level 1 (10%): 모든 스킬에 "defensive_mode: true" 전파
  - Level 2 (15%): /execution-planner에 "reduce_50%" 명령
  - Level 3 (20%): 오케스트레이터가 "emergency_liquidate" 발동
```

### 7.3 문서 참조 체계

각 스킬은 docs/의 해당 섹션을 참조:
```
/scoring-engine       → docs/quantitative-scoring-methodologies.md §1-§3
/signal-generate      → docs/verified-methodologies-and-risk-management.md §2
/regime-detect        → docs/skill_chaining_and_self_improvement_research.md §3
/position-sizer       → docs/skill_chaining_and_self_improvement_research.md §9
/risk-manager         → docs/verified-methodologies-and-risk-management.md §4-§5
/self-improver        → docs/skill_chaining_and_self_improvement_research.md §4-§5
/backtest-validator   → docs/quantitative-scoring-methodologies.md §8
/performance-analyst  → docs/skill_chaining_and_self_improvement_research.md §8
```

---

## 8. 기대 효과

| 측면 | 현재 (문서만) | 전환 후 (Skills + Agents) |
|------|-------------|------------------------|
| 분석 시간 | 수작업 수시간 | `/trading-orchestrator` 수분 |
| 일관성 | 분석자 의존 | 100% 규칙 기반 |
| 병렬성 | 불가 | 최대 13개 Agent 동시 |
| 편향 방어 | 인식만 | Bias Checker 자동 검증 |
| 재현성 | 낮음 | 동일 입력 → 동일 결과 |
| 자기 개선 | 수동 | 월간 자동 진단 + 처방 |
| 비용 효율 | N/A | haiku 7개로 단순작업 최적화 |
