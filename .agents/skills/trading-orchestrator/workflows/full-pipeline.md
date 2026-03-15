# Full Pipeline 워크플로우

## 호출
`/trading-orchestrator full {SYMBOL}`

## 9계층 실행 순서

```
[순차] Layer 1: data-ingest
         ↓
[순차] Layer 2: regime-detect
         ↓
[병렬] Layer 3: signal-generate (4 agents)
         ↓
[병렬] Layer 4: scoring-engine (3 agents)
         ↓
[순차] Layer 5: position-sizer
         ↓
[병렬] Layer 6: risk-manager (2 agents)
         ↓
[순차] Layer 7: execution-planner
         ↓
[순차] Layer 8: bias-checker
         ↓
[순차] Layer 9: 최종 보고서
```

## 각 레이어 입출력

| Layer | 입력 | 출력 | 선행 조건 |
|-------|------|------|----------|
| 1 | 종목 심볼 | 가격+재무+지표 데이터 | 없음 |
| 2 | 시장 데이터 | 레짐 + 전략 가중치 | Layer 1 |
| 3 | 종목 데이터 + 레짐 | 4전략 합의 시그널 | Layer 1, 2 |
| 4 | 종목 데이터 + 레짐 | 복합 스코어 0-100 | Layer 1, 2 |
| 5 | 스코어 + 레짐 + ATR | 포지션 크기 | Layer 2, 4 |
| 6 | 포지션 + 포트폴리오 | 리스크 보고서 | Layer 5 |
| 7 | 사이징 + 리스크 통과 | 주문 계획 | Layer 5, 6 |
| 8 | 전체 컨텍스트 | 편향 보고서 | Layer 7 |
| 9 | 전체 결과 | 종합 보고서 | 전체 |

## Team Agent 활용 (최대 13개)

- Layer 3: 4개 (CAN SLIM, Magic Formula, Dual Momentum, Trend)
- Layer 4: 3개 (Fundamental, Technical, Sentiment)
- Layer 6: 2개 (Risk Auditor, Bias Checker)
- Layer 8: 별도 4개 (성과 분석 시에만, full-pipeline에서는 미사용)

## 실패 처리

Layer 1-2 실패: 전체 파이프라인 중단, 에러 보고
Layer 3-4 실패: 부분 결과로 진행, 경고 표시
Layer 5-8 실패: 해당 레이어 스킵, 수동 검토 권고
