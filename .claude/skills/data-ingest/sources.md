# 데이터 소스 레퍼런스

## EODHD (Phase 1 — 메인)

| 엔드포인트 | 용도 | Rate Limit |
|-----------|------|-----------|
| `/eod/{symbol}` | 일간 OHLCV | 100K req/day |
| `/fundamentals/{symbol}` | 재무제표 | 100K req/day |
| `/real-time/{symbol}` | 실시간 시세 | 100K req/day |
| `/technical/{symbol}` | 기술적 지표 | 100K req/day |

**API Key**: `.env`의 `EODHD_API_TOKEN`
**가격**: $79.99/mo (All-World Extended)

## Twelve Data (Phase 2 — 글로벌 확장)

| 엔드포인트 | 용도 | Rate Limit |
|-----------|------|-----------|
| `/time_series` | OHLCV 히스토리 | 800 req/min |
| `/quote` | 현재가 | 800 req/min |
| `/income_statement` | 손익계산서 | 800 req/min |

**API Key**: `.env`의 `TWELVE_DATA_API_KEY`

## FMP (Phase 3 — 심화 펀더멘탈)

| 엔드포인트 | 용도 | Rate Limit |
|-----------|------|-----------|
| `/income-statement/{symbol}` | 손익 | 250 req/min |
| `/balance-sheet-statement/{symbol}` | 재무상태 | 250 req/min |
| `/cash-flow-statement/{symbol}` | 현금흐름 | 250 req/min |
| `/key-metrics/{symbol}` | 핵심 지표 | 250 req/min |

**API Key**: `.env`의 `FMP_API_KEY`

## yfinance (보조/폴백)

무료, API Key 불필요. 프로토타이핑 및 EODHD 장애 시 폴백.
Rate Limit 비공식: ~2K req/hour 권장.

## 폴백 전략

```
1차: EODHD (메인)
  ↓ 실패 시
2차: yfinance (보조)
  ↓ 실패 시
3차: 캐시된 데이터 (SQLite, 최대 1일 이전)
  ↓ 없으면
에러 반환
```
