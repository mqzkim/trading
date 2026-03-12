# Phase 1: Data Foundation — Context

> Discuss-phase 완료: 2026-03-12 | 4개 Gray Area 해결

## Phase Goal

Users can ingest, store, and query reliable US equity data (price + fundamentals) with point-in-time correctness.

## Requirements Covered

DATA-01, DATA-02, DATA-03, DATA-04, SCOR-01, SCOR-02, SCOR-03, SCOR-04

## Decisions

### Gray Area 1: 종목 유니버스 범위

| 항목 | 결정 |
|------|------|
| 초기 유니버스 | **S&P 500 + S&P 400 (~900종목)** |
| 업데이트 주기 | **주간** |
| 섹터 분류 | **GICS 11섹터** |
| 섹터 제외 | **금융 + 유틸리티 제외** (Recommended와 다름 — 금융주 재무구조 특수성, 유틸리티 규제 산업 특수성) |

### Gray Area 2: 데이터 소스 전략

| 항목 | 결정 |
|------|------|
| 가격 데이터 | **yfinance 단독** (EODHD 제거) |
| SEC 재무 데이터 | **edgartools 주력 + yfinance 보조** (filing date 추적은 edgartools만 가능) |
| 기존 DataClient | **core/ 래핑** (기존 로직 유지, DDD infrastructure에서 import) |
| 동시성 | **asyncio 병렬** (동시 5-10개 요청) |

### Gray Area 3: 기존 코드 활용 범위

| 항목 | 결정 |
|------|------|
| F/Z/M-Score 계산 | **core/ 로직 재사용** (piotroski_f_score(), altman_z_score() 등 기존 함수 유지, DDD handler에서 호출) |
| data_ingest DDD 구조 | **경량 DDD** (domain/VOs + infrastructure/clients만, handler 없이 직접 호출) — Recommended(완전 DDD)와 다름 |
| 이벤트 버스 | **async 이벤트 버스** (asyncio 기반 비동기) — Recommended(동기 in-process)와 다름 |

### Gray Area 4: Point-in-Time 엄격도

| 항목 | 결정 |
|------|------|
| Filing date 추적 | **완전 엄격** (SEC filing date 필수, 모든 쿼리에 as-of-date 필터) |
| 품질 검증 범위 | **핵심 검증** (결측값, stale 3일+, 이상치 3시그마+) |
| 불완전 종목 처리 | **제외 + 로그** (스크리닝에서 제외, 누락 항목 로깅) |

## Existing Code to Leverage

### 재사용 (as-is 래핑)
- `core/data/client.py` — DataClient (yfinance 가격 수집)
- `core/data/cache.py` — SQLite TTL 캐시
- `core/scoring/fundamental.py` — piotroski_f_score(), altman_z_score(), beneish_m_score()
- `core/scoring/safety.py` — SafetyGate 검증

### 재사용 (DDD 도메인 모델)
- `src/shared/domain/` — Entity, ValueObject, DomainEvent, Result 기반 클래스
- `src/scoring/domain/value_objects.py` — SafetyGateResult, CompositeScore 등

### 새로 구현 필요
- `src/data_ingest/` — 경량 DDD 바운디드 컨텍스트 (domain/VOs + infrastructure/clients)
- DuckDB 분석 DB 통합
- edgartools SEC 재무 데이터 수집 + filing date 추적
- asyncio 기반 이벤트 버스 (`src/shared/infrastructure/event_bus.py`)
- 유니버스 관리 (S&P 500+400, 주간 업데이트, GICS 분류)
- 데이터 품질 검증 파이프라인

## Architecture Notes

```
src/
  data_ingest/              # 경량 DDD (새 바운디드 컨텍스트)
    domain/
      value_objects.py      # Ticker, OHLCV, FinancialStatement, FilingDate VOs
      __init__.py
    infrastructure/
      yfinance_client.py    # core/data/client.py 래핑
      edgartools_client.py  # SEC filing date 추적 (신규)
      duckdb_store.py       # 분석 워크로드 (신규)
      sqlite_store.py       # 운영 상태 (기존 cache 래핑)
      __init__.py
    DOMAIN.md
  scoring/                  # 기존 DDD 컨텍스트 (F/Z/M-Score 추가)
    domain/                 # 기존 유지
    infrastructure/
      core_scoring_adapter.py  # core/scoring/ 래핑 (신규)
  shared/
    domain/                 # 기존 유지
    infrastructure/
      event_bus.py          # async 이벤트 버스 (신규)
```

## Risks & Mitigations

| 리스크 | 완화 방안 |
|--------|-----------|
| yfinance adjusted close 동작 변경 | Phase 1 초기에 실증 검증 |
| edgartools XBRL 소형주 커버리지 | 샘플 테스트 후 yfinance fallback |
| asyncio 이벤트 버스 복잡도 | 단순 pub/sub만 구현, 복잡한 패턴 배제 |
| DuckDB + SQLite 이중 DB 운영 복잡도 | 역할 분리 명확화 (분석 vs 운영) |

## Success Criteria (from ROADMAP.md)

1. 3+ 년 daily OHLCV + 3+ 년 분기 재무제표 수집
2. Filing date 태깅 (period-end가 아닌 filing date 기준)
3. 데이터 품질 검증 (결측, stale, 이상치) 보고서
4. DuckDB 500+ 종목 스크리닝 30초 이내
5. Safety gate (Z > 1.81, M < -1.78) 필터링 + 참조값 일치 검증
