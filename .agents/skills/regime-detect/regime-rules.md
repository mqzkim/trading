# 레짐 분류 상세 규칙

## 입력 지표 임계값

### VIX (변동성 지수)
- < 15: 극저변동 (강세 환경)
- 15-20: 저변동 (정상)
- 20-25: 중간변동 (경계)
- 25-30: 고변동 (스트레스)
- > 30: 극고변동 (공포)

### S&P 500 vs 200-day MA
- > +5%: 강한 상승추세
- 0 ~ +5%: 약한 상승추세
- -5% ~ 0: 약한 하락추세
- < -5%: 강한 하락추세

### ADX (Average Directional Index)
- < 20: 추세 없음 (횡보)
- 20-25: 약한 추세
- 25-50: 강한 추세
- > 50: 매우 강한 추세

### 수익률 곡선 기울기 (10Y - 2Y)
- > 0.5%: 정상 (성장 기대)
- 0 ~ 0.5%: 평탄화 (경계)
- < 0: 역전 (침체 경고)

## 레짐 판별 로직

```python
def classify_regime(vix, sp500_vs_200ma, adx, yield_slope):
    is_low_vol = vix < 20
    is_high_vol = vix >= 20
    is_uptrend = sp500_vs_200ma > 0
    is_downtrend = sp500_vs_200ma < -5
    is_trending = adx > 25
    is_ranging = adx < 20

    if is_low_vol and is_uptrend and is_trending:
        return "Low-Vol Bull", min(0.6 + (1 - vix/30) * 0.3, 0.95)
    elif is_high_vol and is_uptrend and is_trending:
        return "High-Vol Bull", min(0.5 + adx/100, 0.85)
    elif is_low_vol and is_ranging:
        return "Low-Vol Range", min(0.5 + (20 - adx)/40, 0.85)
    elif is_high_vol and is_downtrend:
        return "High-Vol Bear", min(0.5 + vix/60, 0.90)
    else:
        return "Transition", max(0.40, 0.60 - abs(sp500_vs_200ma)/20)
```

## 레짐 전환 규칙

- 레짐 변경 시 최소 **5 거래일** 확인 후 전환 확정
- 확률 60% 미만은 Transition으로 분류
- Transition → 다른 레짐 전환 시 점진적 가중치 조정 (1주간)
