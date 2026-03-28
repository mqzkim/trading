---
name: scoring-z-score
description: "Altman Z-Score 파산 위험 평가 규칙 레퍼런스"
---

# Altman Z-Score (파산 위험 평가)

## 공식

```
Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5

X1 = 운전자본 / 총자산
X2 = 이익잉여금 / 총자산
X3 = EBIT / 총자산
X4 = 자기자본 시가총액 / 총부채
X5 = 매출 / 총자산
```

## 해석

| Z-Score | 영역 | 해석 |
|---------|------|------|
| > 2.99 | Safe Zone | 파산 위험 낮음 |
| 1.81 ~ 2.99 | Grey Zone | 주의 필요 |
| < 1.81 | Distress Zone | 파산 위험 높음 |

## 안전성 필터 역할

**Z-Score > 1.81이 하드 게이트**:
- 통과 시: 스코어링 진행
- 미통과 시: 분석 중단, `safety_passed: false`

## 정규화
연속값 → 0-100 백분위 순위 (섹터 내)
