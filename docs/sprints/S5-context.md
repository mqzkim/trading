# S5 — Orchestrator + CLI Sprint: Context Document

- Sprint ID: `S5`
- 작성일: 2026-03-03
- 선행 조건: S4 PASS ✅

## 목표
- `core/orchestrator.py`: 9계층 전체 파이프라인 통합 (data→regime→signal→scoring→sizer→risk→execution)
- `cli/main.py` 확장: `trading score/regime/signal/analyze` 명령어 구현

## 구현 범위
```
core/
└── orchestrator.py   # 9계층 파이프라인 통합 오케스트레이터

cli/
└── main.py           # score/regime/signal/analyze 명령어 추가

tests/unit/
├── test_orchestrator.py       # 오케스트레이터 파이프라인 테스트
└── test_cli_commands.py       # CLI 명령어 Typer 테스트
```

## 성공 기준
- `trading score AAPL` → composite_score 출력
- `trading regime` → 현재 레짐 + 전략 가중치 출력
- `trading signal AAPL` → 4전략 합의 시그널 출력
- `trading analyze AAPL` → 전체 파이프라인 보고서 출력
- 단위테스트 전체 PASS
