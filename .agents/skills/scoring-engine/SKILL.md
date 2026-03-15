---
name: scoring-engine
description: "정량적 복합 스코어링을 실행합니다. F-Score, Z-Score, M-Score, G-Score를 포함한 3축(기본적/기술적/센티먼트) 분석으로 0-100 복합 점수를 산출합니다. Team Agent 3개 병렬 활용. Layer 4."
argument-hint: "[symbol] [--detail] [--screen market]"
user-invocable: true
allowed-tools: "Read, Bash, Agent"
---

# Scoring Engine Skill (Layer 4)

> 정량적 복합 스코어링 코디네이터. 3축 분석을 병렬 수행하여 종합 점수를 산출합니다.

## 역할

기본적/기술적/센티먼트 3축 분석을 Team Agent로 병렬 수행하고,
레짐 기반 가중치로 합산하여 0-100 복합 점수를 산출합니다.

## 실행 규칙

### 단일 종목 분석
1. `trading score {symbol} --detail --output json` 실행
2. 결과를 사용자에게 테이블 형태로 보고
3. 안전성 필터 미통과 시 경고 강조

### 시장 스크리닝 (--screen 사용 시)
1. `trading screen --market {market} --min-score 70 --top 20` 실행
2. 상위 종목 리스트를 테이블로 출력

### Team Agent 병렬 분석 (심화 분석 요청 시)

3개 에이전트를 동시 스폰:

| Agent | 분석 영역 | 모델 | 스윙 가중치 | 포지션 가중치 |
|-------|---------|------|-----------|------------|
| Fundamental Analyst | 가치+품질+성장+건전성 | sonnet | 35% | 50% |
| Technical Analyst | 추세+모멘텀+거래량 | haiku | 40% | 30% |
| Sentiment Analyst | 애널리스트+내부자+공매도 | haiku | 25% | 20% |

## 안전성 필터 (Pass/Fail, 하드 게이트)

**반드시 통과해야 스코어링 진행**:
- Altman Z-Score > 1.81 (파산 위험 없음)
- Beneish M-Score < -1.78 (이익 조작 없음)

미통과 시: `safety_passed: false`, composite_score = 0, 분석 중단.

## Fundamental Analyst 상세

```
입력: 재무제표 데이터
처리:
  1. 안전성 필터: Z-Score > 1.81 AND M-Score < -1.78
  2. 서브 스코어:
     - 가치: Percentile_Rank(EV/EBIT) + Percentile_Rank(P/B)
     - 품질: Piotroski F-Score (0-9) → 정규화
     - 성장: EPS CAGR 3년, 매출 CAGR 3년
     - 건전성: Z-Score 연속값 정규화
  3. 정규화: 백분위 순위 (0-100), 섹터 중립
출력: fundamental_score (0-100)
```

## Technical Analyst 상세

```
입력: OHLCV + 기술적 지표
처리:
  1. 추세 점수: Price vs MA(200), ADX, MACD 방향
  2. 모멘텀 점수: 12-1개월 수익률, 섹터 상대강도
  3. 거래량 점수: OBV 추세, 거래량 비율
  4. 정규화: 백분위 순위 (0-100)
출력: technical_score (0-100)
```

## Sentiment Analyst 상세

```
입력: 애널리스트 추정치, 내부자 거래, 공매도 데이터
처리:
  1. 추정치 변경 방향 (상향/하향)
  2. 내부자 매수/매도 비율
  3. 공매도 비율 변화
  4. 정규화: 백분위 순위 (0-100)
출력: sentiment_score (0-100)
```

## 복합 점수 합산

```
Composite_Score = w_F * fundamental + w_T * technical + w_S * sentiment

리스크 조정:
  Risk_Adjusted = Composite - 0.3 * Tail_Risk_Penalty

정렬 후 상위 N개 선택
```

## 출력 포맷

```json
{
  "skill": "scoring-engine",
  "status": "success",
  "data": {
    "symbol": "AAPL",
    "composite_score": 78.5,
    "risk_adjusted_score": 75.2,
    "safety_passed": true,
    "fundamental": {
      "score": 82,
      "f_score": 8,
      "z_score": 4.21,
      "m_score": -2.89,
      "ev_ebit_pct": 65,
      "roe": 0.45
    },
    "technical": {
      "score": 74,
      "trend": "bullish",
      "momentum_pct": 70,
      "volume": "confirming"
    },
    "sentiment": {
      "score": 71,
      "analyst_revision": "up",
      "insider_net": "buy",
      "short_interest_change": -0.02
    },
    "regime": "Low-Vol Bull",
    "weights": { "fundamental": 0.35, "technical": 0.40, "sentiment": 0.25 }
  }
}
```

## 참조 문서

- `docs/quantitative-scoring-methodologies.md` — 스코어링 모델 상세
- `.Codex/skills/scoring-engine/scoring-models/` — 개별 스코어 계산 규칙
