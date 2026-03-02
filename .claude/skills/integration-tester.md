---
name: integration-tester
description: "트레이딩 파이프라인 전체 흐름(데이터→스코어→레짐→시그널→포지션→리스크→실행)을 E2E 통합 테스트로 검증합니다. Paper Trading 모드 전용."
argument-hint: "[run|generate|report] [--scenario full|smoke|regression] [--symbol AAPL]"
user-invocable: true
allowed-tools: "Read, Bash, Grep"
---

# Integration Tester Skill

> E2E 통합 테스트 시나리오 실행 전문가. 트레이딩 파이프라인 전체 흐름을 검증합니다.
> **Paper Trading 모드 전용** — 실거래 API 호출을 절대 하지 않습니다.

## 역할

데이터 수집부터 주문 실행까지 7계층 파이프라인 전체를 E2E로 검증합니다.
각 계층의 입출력 계약(인터페이스)과 데이터 흐름이 올바른지 확인하고
통합 테스트 결과 리포트를 생성합니다.

## 파이프라인 검증 흐름

```
Layer 1: Data Ingest      → EODHD API 연결, 데이터 정합성
    ↓
Layer 2: Regime Detect    → HMM 모델 로드, 레짐 레이블 출력
    ↓
Layer 3: Signal Generate  → 4전략 시그널 생성 (CANSLIM, Magic Formula, Dual Momentum, Trend)
    ↓
Layer 4: Scoring Engine   → F-Score, Z-Score, M-Score, G-Score, Composite
    ↓
Layer 5: Position Sizer   → Kelly Fraction 계산, 포지션 크기 결정
    ↓
Layer 6: Risk Manager     → 리스크 한도 검증, 낙폭 레벨 확인
    ↓
Layer 7: Execution Planner → 주문 계획 생성 (Paper Trading 모드 강제)
```

## 수행 가능 작업

### 1. E2E 테스트 시나리오 생성 (`generate`)

`/integration-tester generate --scenario <full|smoke|regression>`

**시나리오 종류**:

| 시나리오 | 범위 | 실행 시간 | 용도 |
|---------|------|---------|------|
| smoke | 각 계층 1개씩 핵심 경로만 | ~2분 | 빠른 건강 확인 |
| full | 전체 파이프라인 + 경계 케이스 | ~15분 | 스프린트 완료 검증 |
| regression | 이전 버전 대비 출력 비교 | ~10분 | 리팩토링 후 안전 검증 |

생성 위치: `tests/integration/<scenario>-<timestamp>.json`

### 2. 통합 테스트 실행 (`run`)

`/integration-tester run --scenario full --symbol AAPL`

**실행 순서**:

```bash
# 1. Paper Trading 모드 강제 설정 확인
grep -r "PAPER_TRADING=true" .env || echo "ERROR: PAPER_TRADING must be true"

# 2. pytest 통합 테스트 실행
pytest tests/integration/ -v --tb=short -m "not live"

# 3. 각 계층 출력 수집 및 검증
```

**계층별 검증 항목**:

| 계층 | 검증 항목 | 통과 기준 |
|------|---------|---------|
| Data Ingest | 데이터 수신 여부, 필드 완전성 | OHLCV + 펀더멘탈 모두 존재 |
| Regime Detect | 레짐 레이블 유효성 | Bull/Bear/Sideways 중 하나 |
| Signal Generate | 4전략 모두 시그널 반환 | BULLISH/BEARISH/NEUTRAL 중 하나 |
| Scoring Engine | 0-100 범위 점수 | Composite score 0 ≤ x ≤ 100 |
| Position Sizer | Kelly 결과 양수 & 한도 내 | 0 < size ≤ 8% (단일 종목 한도) |
| Risk Manager | 리스크 한도 판정 | passed: true 또는 명확한 위반 이유 |
| Execution Planner | Paper 모드 주문 계획 | mode == "paper", 실거래 URL 없음 |

**경계 케이스 테스트**:

| 케이스 | 설명 | 기대 결과 |
|--------|------|---------|
| 데이터 누락 | 펀더멘탈 일부 필드 없음 | 해당 서브스코어 0, 경고 출력 |
| 낙폭 15% | Defensive 모드 진입 | 신규 매수 차단, 포지션 50% 축소 계획 |
| 낙폭 20% | Emergency 모드 진입 | 전량 청산 명령 생성 |
| Kelly 0 이하 | 매수 신호 없음 | 주문 계획 미생성, 이유 명시 |
| 섹터 한도 초과 | 기술주 25% 도달 | Risk Manager FAIL, 거래 차단 |

### 3. 결과 리포트 생성 (`report`)

`/integration-tester report --run-id <id>`

생성 위치: `docs/test-reports/integration-<run-id>.md`

**리포트 표준 포맷**:
```markdown
# Integration Test Report

**Run ID**: <id>
**날짜**: <YYYY-MM-DD HH:MM>
**시나리오**: full
**대상 종목**: AAPL
**모드**: PAPER

## 요약

| 계층 | 상태 | 소요 시간 | 비고 |
|------|------|---------|------|
| Data Ingest | PASS | 1.2s | |
| Regime Detect | PASS | 0.3s | |
| Signal Generate | PASS | 2.1s | |
| Scoring Engine | PASS | 0.8s | |
| Position Sizer | PASS | 0.1s | |
| Risk Manager | PASS | 0.2s | |
| Execution Planner | PASS | 0.1s | |

**전체 결과**: PASS (7/7)

## 실패 상세 (있을 경우)
<실패 계층, 오류 메시지, 스택 트레이스>

## 경계 케이스 결과
<각 경계 케이스 통과/실패 여부>
```

## 실패 처리

| 상황 | 처리 |
|------|------|
| PAPER_TRADING 환경변수 미설정 | 즉시 중단, 설정 방법 안내 |
| 실거래 API 호출 감지 | 즉시 중단, 해당 코드 위치 출력 |
| 계층 타임아웃 (30초) | 해당 계층 TIMEOUT 처리, 나머지 계층 계속 |
| pytest 미설치 | 즉시 중단, `pip install pytest` 안내 |

## 출력 포맷

```json
{
  "skill": "integration-tester",
  "status": "success",
  "data": {
    "run_id": "int-20260303-001",
    "scenario": "full",
    "symbol": "AAPL",
    "mode": "paper",
    "layers": {
      "data_ingest": { "status": "PASS", "duration_ms": 1200 },
      "regime_detect": { "status": "PASS", "duration_ms": 300, "output": "Bull" },
      "signal_generate": { "status": "PASS", "duration_ms": 2100, "consensus": "BULLISH" },
      "scoring_engine": { "status": "PASS", "duration_ms": 800, "composite": 74.5 },
      "position_sizer": { "status": "PASS", "duration_ms": 100, "size_pct": 4.5 },
      "risk_manager": { "status": "PASS", "duration_ms": 200, "risk_level": 0 },
      "execution_planner": { "status": "PASS", "duration_ms": 100, "order_type": "limit" }
    },
    "total": { "passed": 7, "failed": 0, "total": 7 },
    "report_path": "docs/test-reports/integration-int-20260303-001.md"
  }
}
```

## 제약 조건

- Paper Trading 모드에서만 실행한다 — 실거래 API 호출은 어떤 경우에도 금지
- 실행 전 반드시 `PAPER_TRADING=true` 환경변수를 확인한다
- pytest 실행 시 `-m "not live"` 마커를 반드시 포함한다
- 실거래 API 엔드포인트(api.alpaca.markets) 호출이 감지되면 즉시 중단한다
- 테스트 결과 리포트는 `docs/test-reports/` 경로에 저장한다

## 참조 문서

- `docs/cli-skill-implementation-plan.md` — 파이프라인 계층 설계
- `docs/verified-methodologies-and-risk-management.md` §4-§5 — 리스크 한도 기준
- `docs/api-technical-feasibility.md` — Alpaca Paper Trading API 상세
- `.claude/skills/trading-orchestrator/SKILL.md` — 파이프라인 전체 흐름 참조
