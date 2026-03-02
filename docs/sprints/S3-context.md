# S3 — Regime + Signal Sprint: Context Document

- Sprint ID: `S3`
- 작성일: 2026-03-03
- 선행 조건: S2 PASS ✅

## 목표
- `core/regime/`: VIX/S&P500/ADX/수익률곡선 기반 4가지 레짐 분류
- `core/signals/`: CAN SLIM / Magic Formula / Dual Momentum / Trend Following 4전략 합의 시그널

## 구현 범위
```
core/regime/
├── __init__.py
├── classifier.py   # 레짐 분류 로직 (규칙 기반)
└── weights.py      # 레짐별 전략 가중치 + 리스크 조정

core/signals/
├── __init__.py
├── canslim.py      # 7기준 CAN SLIM
├── magic_formula.py  # Earnings Yield + ROC
├── dual_momentum.py  # 상대+절대 모멘텀
├── trend_following.py  # MA/ADX/Breakout
└── consensus.py    # 4전략 합의 + 레짐 가중

tests/unit/
├── test_regime_classifier.py
├── test_signal_canslim.py
├── test_signal_consensus.py
```

## 성공 기준
- 레짐 정확도 목표: 55%+ (규칙 기반, 단위테스트에서 경계 케이스 검증)
- 4전략 합의: 3/4 이상 BULLISH/BEARISH → 합의, 그 외 NEUTRAL
- 단위테스트 전체 PASS
