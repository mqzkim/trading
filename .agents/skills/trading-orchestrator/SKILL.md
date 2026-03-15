---
name: trading-orchestrator
description: "전체 9계층 트레이딩 파이프라인을 오케스트레이션합니다. 종목 분석, 포트폴리오 점검, 리밸런싱 판단을 체계적으로 수행합니다. 최대 13개 Team Agent를 활용합니다. 개인 전용."
argument-hint: "[full|quick|review] [symbol|portfolio]"
user-invocable: true
allowed-tools: "Read, Bash, Agent"
---

# Trading Orchestrator Skill (메인 코디네이터)

> 전체 9계층 파이프라인의 진입점이자 코디네이터.
> 최대 13개 Team Agent를 활용하여 종합적인 트레이딩 분석을 수행합니다.
> **개인 전용** — 투자 자문 영역으로 상업 제품에서 제외.

## 역할

3가지 워크플로우(full, quick, review)를 제공하며,
각 워크플로우는 9개 전문 스킬을 순차/병렬로 체이닝합니다.

## 워크플로우

### 1. Full Pipeline (전체 분석)
`/trading-orchestrator full AAPL`

**9계층 순차/병렬 실행**:
```
Layer 1: /data-ingest AAPL              → 데이터 수집 (순차)
Layer 2: /regime-detect                 → 레짐 판별 (순차)
Layer 3: /signal-generate AAPL          → 4 Team Agents 병렬 시그널
Layer 4: /scoring-engine AAPL           → 3 Team Agents 병렬 스코어링
Layer 5: /position-sizer AAPL           → 포지션 계산 (순차)
Layer 6: /risk-manager                  → 2 Team Agents 병렬 리스크 검증
Layer 7: /execution-planner AAPL        → 실행 계획 (순차)
Layer 8: /bias-checker                  → 편향 체크 (순차)
Layer 9: 최종 보고서 생성
```

**Team Agent 총 사용**: 최대 13개 (4+3+2+4)

### 2. Quick Scan (빠른 분석)
`/trading-orchestrator quick "AAPL MSFT GOOGL"`

```
1. /data-ingest (각 종목)      → 데이터 수집
2. /scoring-engine (3 agents)  → 3축 스코어링
3. 비교 테이블 출력
```

### 3. Portfolio Review (포트폴리오 점검)
`/trading-orchestrator review`

```
1. 보유 종목 일괄 스코어링
2. /risk-manager (전체 포트폴리오)
3. 리밸런싱 제안
```

## 실패 처리

| 상황 | 처리 |
|------|------|
| Agent 타임아웃 (60초) | 해당 결과 제외, 나머지로 진행 |
| 데이터 누락 | 해당 서브스코어 0, 경고 표시 |
| 전체 실패 | 에러 보고서 생성 |

## 낙폭 트리거 전파

| Level | 조건 | 오케스트레이터 동작 |
|-------|------|-------------------|
| 0 Normal | < 10% | 정상 파이프라인 실행 |
| 1 Warning | 10-15% | `defensive_mode: true` 전파, 신규 매수 차단 |
| 2 Defensive | 15-20% | `/execution-planner`에 `reduce_50%` 명령 |
| 3 Emergency | > 20% | `emergency_liquidate` 발동, 전량 청산 |

## 최종 보고서 형식

```
═══════════════════════════════════════════
  AAPL 종합 분석 보고서
═══════════════════════════════════════════

레짐: Low-Vol Bull (78%)
시그널: BULLISH (3/4 합의)
복합 점수: 78.5 / 100
안전성: PASSED (Z=4.21, M=-2.89)

포지션 제안:
  비중: 4.5% | 15주 | $4,500
  스탑: $172.50 (ATR 3x)
  리스크: $100 (자본의 1%)

리스크 검증: PASSED (Level 0)
편향 체크: CLEAN (0/6 감지)

═══════════════════════════════════════════
```

## 참조 문서

- `docs/skill-conversion-plan.md` §2.1 — 오케스트레이터 상세
- `docs/cli-skill-implementation-plan.md` §6 — 워크플로우 설계
- `.Codex/skills/trading-orchestrator/workflows/` — 워크플로우별 상세
