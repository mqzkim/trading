# Portfolio Review 워크플로우

## 호출
`/trading-orchestrator review`

## 실행 순서

```
[순차] 보유 종목 목록 조회
         ↓
[병렬] 각 종목 scoring-engine (3 agents)
         ↓
[순차] risk-manager (포트폴리오 전체)
         ↓
[순차] 리밸런싱 제안
```

## 출력 항목

1. **보유 현황**: 종목별 비중, 수익률, 스코어
2. **리스크 상태**: 낙폭 레벨, 집중도, 섹터 분포
3. **리밸런싱 제안**:
   - 스코어 하락 종목: 축소/매도 권고
   - 한도 초과 종목: 비중 조정 권고
   - 신규 후보: 스크리닝 결과 중 상위

## Team Agent: 최대 5개 (3축 + Risk Auditor + Bias Checker)
