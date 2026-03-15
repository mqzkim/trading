# 주문 실행 규칙 상세

## 주문 라우팅 로직

```
1. 리스크 검증 통과 확인 (risk_manager.passed == true)
2. 모드 확인 (paper / live)
3. 주문 유형 결정
4. 브로커 API 호출
5. 체결 확인 + 스탑로스 주문 설정
```

## 주문 유형 선택 기준

| 상황 | 주문 유형 | 이유 |
|------|----------|------|
| 즉시 진입 필요 + 유동성 풍부 | Market | 빠른 체결 |
| 목표 가격 있음 + 비급함 | Limit | 가격 우위 |
| 브레이크아웃 대기 | Stop-Limit | 추세 확인 후 진입 |
| 긴급 청산 | Market | 즉시 체결 우선 |

## Alpaca API 연동

### Paper Trading (Phase 1 기본)
```
Base URL: https://paper-api.alpaca.markets
인증: APCA-API-KEY-ID + APCA-API-SECRET-KEY
시장 시간: EST 09:30-16:00
```

### Live Trading (명시적 전환 필요)
```
Base URL: https://api.alpaca.markets
⚠️ 모든 주문에 사용자 확인 필수
```

## 스탑로스 자동 설정

모든 매수 주문과 함께 스탑로스 주문 자동 설정:
```
stop_price = entry_price - ATR(21) * 3.0
limit_price = stop_price - (ATR(21) * 0.5)  // 슬리피지 마진
order_type = "stop_limit"
```

## 비상 프로토콜

### reduce_50% (Level 2)
```
1. 모든 보유 종목의 현재 수량 조회
2. 각 종목 50% 수량 시장가 매도
3. 스탑로스 타이트닝: ATR 3.0x → 2.5x
4. 실행 보고서 생성
```

### emergency_liquidate (Level 3)
```
1. 모든 보유 종목 전량 시장가 매도
2. 대기 주문 전량 취소
3. 냉각기 타이머 시작 (30일)
4. 긴급 보고서 생성
```
