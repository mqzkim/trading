# S5 — Sprint Retrospective

- 완료: 2026-03-03 | 판정: PASS

## 잘된 것
- 9계층 파이프라인 통합 성공 (data→regime→signal→scoring→sizer→risk→execution)
- CLI 4개 명령어 (regime/score/signal/analyze) 구현
- 18/18 신규 테스트 PASS
- 실제 모듈 API 시그니처에 맞게 orchestrator 적응 (generate_signals, plan_entry 파라미터)

## 개선점
- test_cache_hit_on_second_call: SQLite 캐시 TTL 테스트 불안정 — S6 QA에서 픽스 예정
- orchestrator의 score_symbol 호출 시 fundamental/technical/sentiment 추정값 사용 — S7에서 실제 데이터 연결

## S6 준비사항
- `tests/integration/`: E2E 파이프라인 통합 테스트
- 백테스트 엔진 구현 (`core/backtest/`)
- 캐시 TTL 테스트 안정화
