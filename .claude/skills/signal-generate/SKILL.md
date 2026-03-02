---
name: signal-generate
description: "4가지 검증된 방법론(CAN SLIM, Magic Formula, Dual Momentum, Trend Following)을 동시 실행하여 합의 시그널을 생성합니다. Team Agent 4개 병렬. Layer 3."
argument-hint: "[symbol(s)]"
user-invocable: true
allowed-tools: "Read, Bash, Agent"
---

# Signal Generate Skill (Layer 3)

> 멀티 전략 시그널 생성 코디네이터. 4가지 검증된 방법론을 병렬 실행합니다.

## 역할

CAN SLIM, Magic Formula, Dual Momentum, Trend Following
4가지 방법론을 Team Agent로 동시 실행하고 합의 시그널을 생성합니다.

## Team Agent 설계

| Agent | 전문 방법론 | 모델 | 시간축 |
|-------|-----------|------|--------|
| CAN SLIM Agent | 7가지 CANSLIM 기준 | sonnet | 수주~수개월 |
| Magic Formula Agent | Earnings Yield + ROC | haiku | 1년 |
| Dual Momentum Agent | 상대+절대 모멘텀 | haiku | 1~12개월 |
| Trend Following Agent | MA/ADX/Breakout | haiku | 수주~수개월 |

## 각 Agent 출력 포맷 (통일)

```json
{
  "methodology": "CAN SLIM",
  "ticker": "AAPL",
  "signal": "BUY",
  "score": 6,
  "score_max": 7,
  "confidence": 0.85,
  "holding_period": "weeks_to_months",
  "key_factors": {},
  "reasoning": "..."
}
```

## CAN SLIM Agent 상세

7가지 기준 평가:
- **C** (Current Quarterly EPS): 분기 EPS 성장률 > 25%
- **A** (Annual EPS): 연간 EPS 3년 CAGR > 25%
- **N** (New High/Product): 52주 신고가 또는 신제품/경영진
- **S** (Supply/Demand): 거래량 증가, 유통주식수 적당
- **L** (Leader): 섹터 내 상대강도 상위 20%
- **I** (Institutional): 기관 보유 증가, 퀄리티 기관 보유
- **M** (Market Direction): 시장 방향 상승세 (레짐 참조)

## Magic Formula Agent 상세

Greenblatt's Magic Formula:
- **Earnings Yield**: EBIT / Enterprise Value (높을수록 좋음)
- **Return on Capital**: EBIT / (Net Working Capital + Net Fixed Assets)
- 두 지표 순위 합산, 상위 종목 선택

## Dual Momentum Agent 상세

Antonacci's Dual Momentum:
- **상대 모멘텀**: 12개월 수익률 기준 자산 간 비교
- **절대 모멘텀**: 12개월 수익률 > 0 (T-Bill 대비)
- 둘 다 통과해야 BUY 시그널

## Trend Following Agent 상세

- **MA Cross**: 50MA > 200MA (골든크로스)
- **ADX**: > 25 (추세 존재)
- **Breakout**: 20일 고가 돌파
- 3가지 중 2개 이상 충족 시 BUY

## 합의 판정

```
3/4 이상 BULLISH → consensus: "BULLISH" (강한 매수)
3/4 이상 BEARISH → consensus: "BEARISH" (강한 매도)
그 외           → consensus: "NEUTRAL" (관망)
```

## 레짐 기반 가중 합산

```
Low-Vol Bull:   canslim=0.30, magic=0.20, momentum=0.25, trend=0.25
High-Vol Bull:  canslim=0.20, magic=0.25, momentum=0.25, trend=0.30
Low-Vol Range:  canslim=0.15, magic=0.40, momentum=0.20, trend=0.25
High-Vol Bear:  canslim=0.10, magic=0.35, momentum=0.30, trend=0.25
Transition:     등가중 (각 0.25)
```

## 출력 포맷

```json
{
  "skill": "signal-generate",
  "status": "success",
  "data": {
    "symbol": "AAPL",
    "consensus": "BULLISH",
    "agreement": 3,
    "regime_context": "Low-Vol Bull",
    "methods": {
      "canslim": { "signal": "BUY", "score": 6, "score_max": 7 },
      "magic_formula": { "signal": "BUY", "score": 82, "score_max": 100 },
      "dual_momentum": { "signal": "BUY", "score": 1, "score_max": 1 },
      "trend_following": { "signal": "HOLD", "score": 1, "score_max": 3 }
    },
    "weighted_score": 0.78
  }
}
```

## 참조 문서

- `docs/verified-methodologies-and-risk-management.md` §2 — 검증된 방법론 상세
- `.claude/skills/signal-generate/strategies/` — 방법론별 인코딩
