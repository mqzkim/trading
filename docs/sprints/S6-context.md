# S6 — Backtest & QA Sprint: Context Document

- Sprint ID: `S6`
- 작성일: 2026-03-03
- 선행 조건: S5 PASS ✅

## 목표
- `core/backtest/`: 워크포워드 백테스트 엔진 구현
- 캐시 TTL 테스트 안정화 (test_cache_hit_on_second_call)
- 통합 테스트: 전체 파이프라인 E2E 검증

## 구현 범위
```
core/backtest/
├── __init__.py
├── engine.py        # 백테스트 실행 엔진 (단순 규칙 기반)
└── metrics.py       # Sharpe, CAGR, MaxDD, Win Rate

tests/unit/
├── test_backtest_engine.py
└── test_backtest_metrics.py

tests/integration/
└── test_pipeline_integration.py   # 전체 파이프라인 E2E
```

## 성공 기준
- 백테스트 엔진: OHLCV + 시그널 → 성과 지표 산출
- Sharpe Ratio, CAGR, Max Drawdown, Win Rate 계산
- 통합 테스트 PASS
- 누적 단위테스트 모두 PASS (기존 실패 1건 포함 픽스)
