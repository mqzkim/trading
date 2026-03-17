# Performance

## 책임
거래 이력 추적, Brinson-Fachler 4단계 성과 기여도 분석, IC/Kelly 시그널 검증.

## 핵심 엔티티
- ClosedTrade: 완료된 거래 기록 (진입/청산 가격, 스코어 스냅샷 포함)

## 외부 의존성
- portfolio 컨텍스트 (PositionClosedEvent 구독을 통한 이벤트 통신)
- core/backtest/metrics.py (Sharpe, MaxDrawdown, WinRate 재사용)

## 주요 유스케이스
1. 포지션 청산 시 거래 이력을 DuckDB에 자동 저장
2. 대시보드에서 Brinson-Fachler 성과 기여도 분석 요청
3. 스코어링 축별 IC (Information Coefficient) 계산
4. Kelly 효율성 모니터링

## 변경 불가 규칙
- 50건 미만의 거래에서는 기여도 분석을 수행하지 않음 (빈 결과 반환)
- IC 계산에 최소 20건의 거래 필요
- 도메인 레이어에 DuckDB 직접 import 금지
