---
name: execution-planner
description: "주문 실행 계획을 생성합니다. 리스크 검증 통과 후 구체적인 주문 타입, 가격, 수량, 타이밍을 결정합니다. Layer 7. 개인 전용."
argument-hint: "[symbol] [--action buy|sell] [--sizing-result JSON]"
user-invocable: true
allowed-tools: "Read, Bash"
---

# Execution Planner Skill (Layer 7)

> 주문 실행 계획 전문가. 리스크 검증 통과 후 구체적인 주문을 설계합니다.
> **개인 전용** — 투자 자문 영역으로 상업 제품에서 제외.

## 역할

포지션 사이징과 리스크 검증 결과를 기반으로
구체적인 주문 타입, 가격, 수량, 타이밍, 스탑로스 주문을 설계합니다.

## 실행 규칙

### 매수 계획
```bash
trading buy {symbol} --qty {N} --type {market|limit|stop-limit}
```

### 매도 계획
```bash
trading sell {symbol} --qty {N} --type {limit} --price {P}
```

## 주문 타입

| 타입 | 용도 | 조건 |
|------|------|------|
| Market | 즉시 체결 필요 | 유동성 충분, 스프레드 좁음 |
| Limit | 특정 가격 이하 매수 | 비급한 진입, 가격 우위 확보 |
| Stop-Limit | 브레이크아웃 진입 | 추세 확인 후 진입 |

## 브로커 연동

| Phase | 브로커 | 시장 | 비고 |
|-------|--------|------|------|
| Phase 1 | Alpaca | 미국 | Paper Trading 기본 |
| Phase 2 | KIS | 한국 | 추후 추가 |

## Paper vs Live 모드

- **Paper** (기본): 모의 매매, 확인 없이 즉시 실행
- **Live**: 실전 매매, **반드시 사용자 확인 후 실행**

```
⚠️ LIVE 모드 주문:
  종목: AAPL
  수량: 15주
  주문유형: Limit @ $185.00
  스탑로스: $172.50
  예상 금액: $2,775.00

  진행하시겠습니까? (y/n)
```

## 비상 프로토콜

| 상황 | 명령 | 동작 |
|------|------|------|
| 낙폭 15% (Level 2) | `reduce_50%` | 모든 포지션 50% 축소 |
| 낙폭 20% (Level 3) | `emergency_liquidate` | 전량 시장가 청산 |

## 출력 포맷

```json
{
  "skill": "execution-planner",
  "status": "success",
  "data": {
    "symbol": "AAPL",
    "action": "buy",
    "order_type": "limit",
    "limit_price": 185.00,
    "quantity": 15,
    "stop_loss_order": {
      "type": "stop-limit",
      "stop_price": 172.50,
      "limit_price": 171.00
    },
    "estimated_cost": 2775.00,
    "broker": "alpaca",
    "mode": "paper",
    "timing": "market_open"
  }
}
```

## 참조 문서

- `docs/cli-skill-implementation-plan.md` §3.3 — Executor 인터페이스
- `docs/api-technical-feasibility.md` — Alpaca/KIS API 상세
