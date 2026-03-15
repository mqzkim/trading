---
name: backtest-validator
description: "백테스트 결과의 유효성을 검증합니다. 오버피팅, 생존자 편향, 미래정보 편향 등을 체크합니다. 공통 스킬."
argument-hint: "[backtest-results path]"
user-invocable: true
allowed-tools: "Read, Bash"
---

# Backtest Validator Skill

> 백테스트 검증 전문가. 결과의 통계적 유효성과 방법론적 건전성을 평가합니다.

## 역할

백테스트 결과를 3가지 카테고리(데이터 무결성, 방법론, 통계 검증)로
종합 검증하여 오버피팅 및 각종 편향을 탐지합니다.

## 검증 체크리스트

### 1. 데이터 무결성

| # | 항목 | 기준 |
|---|------|------|
| 1 | Point-in-Time 펀더멘탈 | 재수정 데이터 사용 안 함 |
| 2 | 생존자 편향 없는 유니버스 | 상장폐지 종목 포함 |
| 3 | 기업행위 조정 | 분할, 배당 반영 |
| 4 | 충분한 히스토리 | 10년+ 다중 시장 사이클 |

### 2. 방법론

| # | 항목 | 기준 |
|---|------|------|
| 5 | Walk-Forward 또는 CPCV | 단일 IS/OOS 분할 아님 |
| 6 | 현실적 리밸런싱 주기 | 일간 리밸런싱 아님 |
| 7 | 거래비용 포함 | 수수료 + 스프레드 + 시장 충격 |
| 8 | 용량 제약 고려 | 거래량 대비 포지션 크기 체크 |

### 3. 통계 검증

| # | 항목 | 기준 | 임계값 |
|---|------|------|--------|
| 9 | PBO | Probability of Backtest Overfitting | < 10% |
| 10 | WFE | Walk-Forward Efficiency | > 50% |
| 11 | 파라미터 민감도 | +/-10% 변경 시 성과 유지 | 변동 < 20% |
| 12 | 샤프비율 t-stat | 통계적 유의성 | > 2.0 |

## 출력 포맷

```json
{
  "skill": "backtest-validator",
  "status": "success",
  "data": {
    "overall_verdict": "PASS",
    "checklist": {
      "data_integrity": { "passed": 4, "total": 4, "items": [] },
      "methodology": { "passed": 3, "total": 4, "items": [] },
      "statistics": { "passed": 4, "total": 4, "items": [] }
    },
    "risk_flags": [],
    "total_passed": 11,
    "total_checks": 12,
    "recommendations": ["거래비용을 보수적으로 재추정 권장"]
  }
}
```

## 참조 문서

- `docs/quantitative-scoring-methodologies.md` §8 — 백테스트 검증 방법론
