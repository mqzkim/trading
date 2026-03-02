# S1 — Data Layer Sprint: Context Document

- Sprint ID: `S1`
- 기준 문서: `docs/sprint-plan.md` (v2.0, Gate-first)
- 작성일: 2026-03-03
- 상태: 진행 중
- 선행 조건: S0 PASS ✅

---

## 1. 스프린트 목표

`data-ingest` Skill을 통해 US/KR 데이터 수집 + SQLite 캐시 + 기술적 지표 계산을 안정화.

트레이딩 파이프라인의 Layer 1을 완성하여 S2(Scoring Engine)가 사용할 정형화된 데이터를 제공한다.

---

## 2. 데이터 소스 및 범위 확정

| 구분 | 소스 | 범위 |
|------|------|------|
| US 가격 | EODHD Phase 1 (yfinance fallback) | 일간 OHLCV 756거래일(3년) |
| KR 가격 | EODHD KR (yfinance fallback) | 일간 OHLCV 756거래일 |
| 재무제표 | EODHD Fundamentals | 최근 4분기 + 연간 3년 |
| 시장지표 | yfinance (^VIX, ^GSPC, ^TNX, ^IRX) | 실시간 |

**API 키 부재 시 폴백**: `yfinance` 기반 동작 (테스트/개발 환경)

---

## 3. 성공 기준 (Exit Criteria)

| Gate | 이름 | Exit Criteria |
|------|------|--------------|
| G0 | Context Init | 이 문서 완성 |
| G1 | Skill Coverage | `data-ingest` Skill이 S1 작업 전체 커버 확인 |
| G2 | Agent Coverage | `data-engineer-agent` 배정 완료 |
| G3 | Bootstrap | 누락 Skill 0건 (market-data-qc 필요 시 생성) |
| G4 | Build | `core/data/` 구현 완료, `tests/unit/test_data_*` 통과 |
| G5 | Verify | 단위테스트 커버리지 80%+, 지표 재현성 PASS |
| G6 | Release Review | PASS 또는 WARN |
| G7 | Full Close-Out | 메모리 저장, 회고, commit, push 완료 |

---

## 4. 필수 산출물

### G0
- `docs/sprints/S1-context.md` (이 문서)

### G1
- `docs/sprints/S1-skill-check.md`

### G2
- `docs/sprints/S1-agent-plan.md`

### G3
- (필요 시) `.claude/skills/market-data-qc/SKILL.md`

### G4
```
core/
└── data/
    ├── __init__.py
    ├── client.py          # DataClient 인터페이스 (EODHD + yfinance 폴백)
    ├── cache.py           # SQLite 캐시 (가격 24h TTL, 재무 7d TTL)
    ├── indicators.py      # ATR(21), ADX(14), MA(50/200), RSI(14), OBV, MACD
    ├── market.py          # VIX, S&P500 vs 200MA, 수익률 곡선
    └── preprocessor.py    # 윈저라이징, 결측값 처리, 수정주가

tests/
└── unit/
    ├── test_data_client.py
    ├── test_data_cache.py
    ├── test_data_indicators.py
    └── test_data_preprocessor.py
```

### G5
- `docs/sprints/S1-verify.md`

### G6
- `docs/sprints/S1-release-review.md`

### G7
- `~/.claude/projects/C--workspace-trading/memory/MEMORY.md` (업데이트)
- `docs/sprints/S1-retrospective.md`
- git commit + push 완료

---

## 5. 기술 스택

- Python 3.11+
- `yfinance` — 폴백 데이터 소스 (API 키 불필요)
- `pandas`, `numpy` — 데이터 처리 + 지표 계산
- `sqlite3` (stdlib) — 로컬 캐시
- `requests` — EODHD API 호출
- `pytest` — 단위 테스트

---

## 6. 리스크

| 리스크 | 대응 |
|--------|------|
| EODHD API 키 없음 | yfinance 폴백으로 전환, .env.example에 키 자리 표시 |
| 지표 재현성 실패 | pandas_ta 대신 수동 계산으로 외부 의존 최소화 |
| SQLite 동시 접근 | WAL 모드 + check_same_thread=False |

---

## 7. 스프린트 시작 선언

- 날짜: 2026-03-03
- 담당 Agent: `data-engineer-agent` (대행: `fullstack-developer`)
- 현재 Gate: G1 (G0 완료)
