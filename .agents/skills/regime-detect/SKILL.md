---
name: regime-detect
description: "현재 시장 레짐을 판별합니다. VIX, S&P 500 200MA, ADX, 수익률곡선을 종합하여 4가지 레짐 중 현재 상태와 확률을 산출합니다. Layer 2."
argument-hint: "[--history N]"
user-invocable: true
allowed-tools: "Bash, Read"
---

# Regime Detect Skill (Layer 2)

> 시장 레짐 분류 전문가. 현재 시장 상태를 진단하고 전략 친화도를 산출합니다.

## 역할

VIX, S&P 500 vs 200MA, ADX, 수익률 곡선을 종합하여 현재 시장을 4가지 레짐 중 하나로 분류합니다.
레짐에 따라 전략 가중치와 리스크 조정 팩터를 결정합니다.

## 실행 규칙

1. `trading regime --output json` 실행
2. 현재 레짐과 전략 친화도를 보고
3. "High-Vol Bear" 또는 "Transition"이면 경고 강조

## 레짐 분류 규칙

| 레짐 | VIX | S&P vs 200MA | ADX | 전략 친화도 |
|------|-----|-------------|-----|-----------|
| Low-Vol Bull | < 20 | 위 (상승추세) | > 25 | 트렌드, 모멘텀 유리 |
| High-Vol Bull | > 20 | 위 (상승추세) | > 25 | 넓은 스탑 트렌드 |
| Low-Vol Range | < 20 | 횡보 | < 20 | 평균회귀, 가치 전략 |
| High-Vol Bear | > 25 | 아래 (하락추세) | > 25 | 방어적, 현금 비중 확대 |
| Transition | 불확실 (확률 < 60%) | - | - | 포지션 축소, 헤지 |

## 리스크 조정 팩터

| 레짐 | risk_adjustment |
|------|----------------|
| Low-Vol Bull | 1.0 (정상) |
| High-Vol Bull | 0.7 |
| Low-Vol Range | 0.8 |
| High-Vol Bear | 0.3 (방어적) |
| Transition | 0.5 |

## 레짐별 전략 가중치

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
  "skill": "regime-detect",
  "status": "success",
  "data": {
    "regime": "Low-Vol Bull",
    "confidence": 0.78,
    "probabilities": {
      "Low-Vol Bull": 0.78,
      "High-Vol Bull": 0.10,
      "Low-Vol Range": 0.08,
      "High-Vol Bear": 0.04
    },
    "indicators": {
      "vix": 14.2,
      "sp500_vs_200ma": "+8%",
      "adx": 28.5,
      "yield_curve_slope": 0.45
    },
    "strategy_affinity": {
      "trend_following": 0.90,
      "momentum": 0.85,
      "value": 0.50,
      "mean_reversion": 0.30
    },
    "risk_adjustment": 1.0
  }
}
```

## 경고 조건

- **High-Vol Bear**: 신규 진입 중단 권고, 방어적 전환
- **Transition**: 포지션 축소, 높은 불확실성 경고
- VIX > 30: 극단적 공포 경고

## 참조 문서

- `docs/skill_chaining_and_self_improvement_research.md` §3 — HMM 기반 레짐 감지
- `docs/verified-methodologies-and-risk-management.md` — 레짐별 리스크 관리
