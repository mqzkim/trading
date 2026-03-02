# 포지션 사이징 규칙 상세

## Kelly Criterion

```
Full Kelly: f* = (p * b - q) / b
  p = 승률
  b = 승리 시 평균 수익/손실 비율
  q = 1 - p (패배 확률)

Fractional Kelly (1/4):
  target_kelly = f* / 4

예시: 승률 55%, 손익비 2:1
  f* = (0.55 * 2 - 0.45) / 2 = 0.325 (32.5%)
  target_kelly = 0.325 / 4 = 0.081 (8.1%) → max 8%로 클램프
```

## ATR 기반 사이징

```
ATR(21) = 21일 Average True Range
stop_distance = ATR(21) * 3.0
risk_per_trade = portfolio_value * 0.01

shares = risk_per_trade / stop_distance
target_weight = (shares * current_price) / portfolio_value

예시: 포트폴리오 $100K, ATR=$5, 주가=$180
  stop_distance = $5 * 3.0 = $15
  shares = $1,000 / $15 = 66주
  dollar_amount = 66 * $180 = $11,880
  target_weight = $11,880 / $100,000 = 11.9% → max 8%로 클램프
```

## 확신도 조정

```
conviction = 0.5 + (composite_score / 100)

점수 40 → conviction = 0.9 (약한 확신)
점수 70 → conviction = 1.2 (강한 확신)
점수 90 → conviction = 1.4 (매우 강한 확신)
```

## 최종 공식

```
target = min(kelly_size, atr_size) * conviction * regime_confidence
target = clamp(target, 0.01, 0.08)
```

## 하드 리밋

- 단일 종목 최대: 8% (절대 초과 금지)
- 단일 종목 최소: 1% (의미 있는 포지션)
- 섹터 최대: 25%
- Full Kelly 사용: **절대 금지**
