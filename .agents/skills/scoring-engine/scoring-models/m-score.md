# Beneish M-Score (이익 조작 탐지)

## 공식

```
M = -4.84 + 0.920*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI
    + 0.115*DEPI - 0.172*SGAI + 4.679*TATA - 0.327*LVGI

DSRI = Days Sales in Receivables Index
GMI  = Gross Margin Index
AQI  = Asset Quality Index
SGI  = Sales Growth Index
DEPI = Depreciation Index
SGAI = SGA Expense Index
TATA = Total Accruals to Total Assets
LVGI = Leverage Index
```

## 해석

| M-Score | 해석 |
|---------|------|
| < -1.78 | 조작 가능성 낮음 (정상) |
| >= -1.78 | 조작 가능성 높음 (경고) |

## 안전성 필터 역할

**M-Score < -1.78이 하드 게이트**:
- 통과 시: 스코어링 진행
- 미통과 시: 분석 중단, 이익 조작 의심 경고

## 주요 변수 해석

- **DSRI 높음**: 매출채권 증가 (매출 인식 과대)
- **GMI 높음**: 매출총이익률 하락 (수익성 악화 은폐)
- **AQI 높음**: 자산 품질 하락 (비용 자본화 의심)
- **TATA 높음**: 발생액 비율 높음 (현금흐름과 이익 괴리)
