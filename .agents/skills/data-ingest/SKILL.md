---
name: data-ingest
description: "트레이딩 분석에 필요한 시장 데이터를 수집하고 전처리합니다. OHLCV, 재무제표, 기술적 지표 계산. Layer 1."
argument-hint: "[ticker(s)] [--days N] [--fundamentals]"
user-invocable: true
allowed-tools: "Bash, Read"
---

# Data Ingest Skill (Layer 1)

> 시장 데이터 수집 + 전처리 전문가. 모든 분석의 기반 데이터를 준비합니다.

## 역할

데이터 수집, 정제, 피처 엔지니어링을 담당합니다.
가격 데이터, 재무제표, 기술적 지표, 시장 지표를 수집하고 구조화된 형태로 출력합니다.

## 실행 규칙

### 단일 종목 데이터 수집
```bash
trading data price {symbol}                 # 현재가
trading data history {symbol} --days 756    # 3년 일봉
trading data fundamentals {symbol}          # 재무제표
```

### 수집 대상

**가격 데이터**:
- 일간 OHLCV (최소 3년, 756 거래일)
- 주간/월간 변환

**재무제표**:
- 최근 4분기 + 연간 3년 재무제표 (손익, 재무상태, 현금흐름)

**기술적 지표**:
- MA(50, 200), RSI(14), ATR(21), ADX(14), OBV, MACD

**시장 지표**:
- VIX, S&P 500 200-day MA, 수익률 곡선 기울기

### 전처리

- 이상치 윈저라이징 (1st/99th 백분위)
- 결측값 처리 (forward fill → drop)
- 수정주가 사용 (배당/분할 조정)

## 데이터 소스

| 우선순위 | 소스 | 용도 |
|---------|------|------|
| Phase 1 | EODHD | 미국/글로벌 EOD 가격 + 펀더멘탈 |
| Phase 2 | Twelve Data | 실시간 + 글로벌 확장 |
| Phase 3 | FMP | 심화 펀더멘탈 |
| 보조 | yfinance | 프로토타이핑/폴백 |

## 출력 포맷

```json
{
  "skill": "data-ingest",
  "status": "success",
  "data": {
    "symbol": "AAPL",
    "price": { "open": 0, "high": 0, "low": 0, "close": 0, "volume": 0 },
    "history": { "days": 756, "records": [] },
    "fundamentals": { "income": {}, "balance": {}, "cashflow": {} },
    "indicators": {
      "ma50": 0, "ma200": 0, "rsi14": 0, "atr21": 0,
      "adx14": 0, "obv": 0, "macd": {}
    },
    "market": { "vix": 0, "sp500_vs_200ma": 0, "yield_curve_slope": 0 }
  }
}
```

## 참조 문서

- `docs/quantitative-scoring-methodologies.md` — 필요 데이터 필드 정의
- `docs/cli-skill-implementation-plan.md` §2.5 — DataClient 인터페이스
