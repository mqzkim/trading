---
name: strategy-dual-momentum
description: "Dual Momentum 방법론 인코딩 레퍼런스"
---

# Dual Momentum 방법론 인코딩 (Antonacci)

## 핵심 원리

상대 모멘텀과 절대 모멘텀을 동시 적용.
둘 다 통과해야 투자, 하나라도 실패하면 채권으로 회피.

## 상대 모멘텀 (Cross-Sectional)

```
자산 A의 12개월 수익률 vs 자산 B의 12개월 수익률
상대적으로 높은 자산을 선택
```

적용 예:
- 미국 주식 (SPY) vs 글로벌 주식 (EFA)
- 12개월 수익률이 높은 쪽 선택

## 절대 모멘텀 (Time-Series)

```
선택된 자산의 12개월 수익률 > T-Bill 수익률?
  YES → 해당 자산 투자
  NO  → 채권(AGG)으로 회피
```

## 의사결정 흐름

```
SPY 12M return > EFA 12M return?
  YES: SPY 선택
    SPY 12M return > T-Bill?
      YES → SPY 투자 (BUY)
      NO  → AGG 투자 (AVOID 주식)
  NO: EFA 선택
    EFA 12M return > T-Bill?
      YES → EFA 투자 (BUY)
      NO  → AGG 투자 (AVOID 주식)
```

## 시그널 변환

- **BUY**: 상대+절대 모멘텀 모두 통과 (score: 1/1)
- **AVOID**: 절대 모멘텀 미통과 (score: 0/1)

## 보유 기간

- 월간 리밸런싱
- 최소 보유: 1개월
