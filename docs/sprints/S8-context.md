# S8 — Performance + Self-Improvement Sprint: Context Document

- Sprint ID: `S8`
- 작성일: 2026-03-03
- 선행 조건: S7 PASS ✅

## 목표
- `personal/self_improver/`: 성과 기반 자동 파라미터 개선 (Walk-Forward 결과 → 가중치 조정 제안)
- `core/backtest/engine.py` 개선: 수수료/슬리피지 모델 추가
- Walk-Forward 백테스트 분할 (`core/backtest/walk_forward.py`)

## 구현 범위
```
personal/self_improver/
├── __init__.py
└── advisor.py        # 성과 분석 → 파라미터 조정 제안

core/backtest/
└── walk_forward.py   # Walk-Forward 분할 + 앙상블

tests/unit/
├── test_self_improver.py
└── test_walk_forward.py
```

## 성공 기준
- Walk-Forward: n_splits 기반 OOS 테스트 수행
- Self-Improver: 샤프 < 1.0 → 가중치 제안 출력
- 단위테스트 전체 PASS
