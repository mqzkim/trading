---
name: position-sizer
description: "Fractional Kelly와 ATR 기반으로 최적 포지션 크기를 계산합니다. 개인 포트폴리오 규모와 리스크 허용도에 맞춰 조정합니다. Layer 5. 개인 전용."
argument-hint: "[symbol] [--portfolio-value N] [--score N]"
user-invocable: true
allowed-tools: "Read, Bash"
---

# Position Sizer Skill (Layer 5)

> 포지션 사이징 전문가. Kelly Criterion과 ATR 기반으로 최적 포지션 크기를 계산합니다.
> **개인 전용** — 투자 자문 영역으로 상업 제품에서 제외.

## 역할

복합 스코어, 변동성, ATR, 포트폴리오 가치, 레짐 확신도를 입력받아
최적 포지션 크기(비중, 주수, 금액)와 스탑로스를 산출합니다.

## 하드 규칙 (절대 위반 금지)

| 규칙 | 값 | 비고 |
|------|---|------|
| Kelly fraction | **1/4** | Full Kelly 절대 금지 |
| Risk per trade | **자본의 1%** | 단일 거래 최대 손실 |
| ATR stop | **3.0 x ATR(21)** | 기본 스탑 거리 |
| 최대 단일 종목 | **8%** | 포트폴리오 비중 상한 |
| 최소 포지션 | **1%** | 의미 있는 최소 비중 |

## 사이징 공식

```
Kelly 기반:
  kelly_size = kelly_fraction * (win_rate * odds - loss_rate) / odds

ATR 기반:
  stop_distance = ATR(21) * 3.0
  atr_size = (portfolio_value * 0.01) / stop_distance

확신도 조정:
  conviction = 0.5 + (composite_score / 100)  // 0.5 ~ 1.5

최종 사이즈:
  target = min(kelly_size, atr_size) * conviction * regime_confidence
  target = clamp(target, min=0.01, max=0.08)
```

## 출력 포맷

```json
{
  "skill": "position-sizer",
  "status": "success",
  "data": {
    "symbol": "AAPL",
    "target_weight": 0.045,
    "shares": 15,
    "dollar_amount": 4500,
    "stop_loss": 172.50,
    "risk_amount": 100.00,
    "sizing_method": "min(kelly, atr) * conviction",
    "kelly_raw": 0.062,
    "atr_raw": 0.048,
    "conviction_multiplier": 1.29,
    "regime_confidence": 0.78
  }
}
```

## 참조 문서

- `docs/skill_chaining_and_self_improvement_research.md` §9 — Kelly 사이징 상세
- `docs/verified-methodologies-and-risk-management.md` — ATR 스탑 규칙
