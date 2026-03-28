---
name: scoring-composite
description: "복합 점수 계산 규칙 레퍼런스"
---

# 복합 점수 계산 규칙

## 계산 흐름

```
1. 안전성 필터 (하드 게이트)
   Z-Score > 1.81 AND M-Score < -1.78
   → 미통과 시 composite = 0, 분석 중단

2. 3축 개별 스코어링 (각 0-100)
   - fundamental_score (F-Score, Z-Score, 가치, 품질, 성장)
   - technical_score (추세, 모멘텀, 거래량)
   - sentiment_score (애널리스트, 내부자, 공매도)

3. 레짐 기반 가중 합산
   composite = w_F * fundamental + w_T * technical + w_S * sentiment

4. 리스크 조정
   risk_adjusted = composite - 0.3 * tail_risk_penalty
```

## 레짐별 가중치

| 레짐 | Fundamental | Technical | Sentiment |
|------|------------|-----------|-----------|
| Low-Vol Bull (스윙) | 35% | 40% | 25% |
| Low-Vol Bull (포지션) | 50% | 30% | 20% |
| High-Vol Bear | 60% | 25% | 15% |
| Low-Vol Range | 55% | 25% | 20% |
| Transition | 45% | 30% | 25% |

## 정규화 방법

- **백분위 순위**: 전체 유니버스 내 순위 → 0-100
- **섹터 중립**: 섹터 내 순위로 재정규화 (섹터 편향 제거)
- **z-score 정규화**: 평균 0, 표준편차 1 → 0-100 매핑

## Tail Risk Penalty

```
tail_risk_penalty = max(0,
  0.3 * max(0, VaR_99 - historical_VaR_99) +
  0.3 * max(0, beta - 1.5) +
  0.4 * max(0, sector_concentration - 0.25)
)
```

## 최종 순위

risk_adjusted_score 기준 내림차순 정렬 후 상위 N개 선택.
