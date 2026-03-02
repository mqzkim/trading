# S2 — Sprint Retrospective

- 완료: 2026-03-03 | 판정: PASS

## 잘된 것
- 27/27 테스트 첫 실행 통과
- 안전성 하드게이트(Z/M-Score) 경계값 테스트 완성
- yfinance proxy로 실제 API 없이 전체 파이프라인 동작

## 개선점
- F-Score는 분기 재무데이터 필요 — yfinance proxy 정확도 제한
- 센티먼트: 공매도/내부자 거래 데이터 yfinance 미제공 → S7 API 서버 시 개선

## S3 준비사항
- `core/regime/`: VIX + S&P500 + ADX + 수익률곡선으로 4가지 레짐 분류
- `core/signals/`: CAN SLIM, Magic Formula, Dual Momentum, Trend Following 4전략 합의
- `core/data.market.get_all()` 활용
