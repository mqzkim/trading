# Trading System - Gate-Driven Full Sprint Master Plan

> Version: 2.0 (Gate-first)
> Date: 2026-03-02
> Scope: `trading/` repository only
> Single Source of Truth: this file (`docs/sprint-plan.md`)

---

## 0. 문서 목적

이 문서는 트레이딩 시스템의 모든 스프린트를 Gate 단위로 통제하기 위한 실행 기준서다.
핵심 목표는 다음 3가지다.

1. 모든 작업을 Team Agent가 수행 가능하도록 구조화
2. 모든 작업을 Skill 기반으로 강제
3. 매 스프린트 종료 시 메모리 저장, 회고, git commit, git push까지 완료하는 Full Sprint 운영

---

## 1. 기준 문서 (Deep Read 반영)

본 계획은 아래 문서의 핵심 제약을 통합해 작성한다.

- `.claude/CLAUDE.md`
- `docs/strategy-recommendation.md`
- `docs/skill-conversion-plan.md`
- `docs/cli-skill-implementation-plan.md`
- `docs/trading-methodology-overview.md`
- `docs/quantitative-scoring-methodologies.md`
- `docs/verified-methodologies-and-risk-management.md`
- `docs/skill_chaining_and_self_improvement_research.md`
- `docs/api-technical-feasibility.md`

핵심 반영 사항:

- 단타 금지, 스윙/포지션 중심
- 공통 코어(`core`) + 개인(`personal`) + 상업(`commercial`) 분리
- 상업 제품은 정보 제공만, 투자 자문 문구/행위 금지
- 리스크 한도 고정: 단일 8%, 섹터 25%, 거래당 1%, ATR 2.5~3.5x, Fractional Kelly 1/4
- 낙폭 방어 3단계: 10% / 15% / 20%
- 검증 기준: PBO < 10%, WFE > 50%, Signal IC >= 0.03, Regime Accuracy >= 55%

---

## 2. 절대 운영 규칙

### 2.1 Skill-First (강제)

모든 실행 작업은 Skill 호출로 시작한다.

- Skill 매칭 성공: 해당 Skill로 실행
- Skill 매칭 실패: Skill 생성 Gate를 먼저 통과한 뒤 실행

허용되는 비-Skill 활동은 아래로 제한한다.

- 문서/코드 읽기
- 상태 조회 (`git status`, 로그 확인)
- 사용자 질의/응답

### 2.2 Team-Agent-First (강제)

모든 Gate에는 담당 Team Agent가 명시되어야 한다.
담당 Agent 부재 시, Agent 생성 Gate를 먼저 수행한다.

### 2.3 Gate 통과 전 다음 단계 금지

각 Gate는 `Entry Criteria`와 `Exit Criteria`를 가진다.
Exit 미충족 시 다음 Gate 진행 금지.

### 2.4 Full Sprint 종료 강제

모든 스프린트는 마지막 Gate에서 아래 4개를 반드시 완료한다.

1. 작업 메모리 저장
2. 스프린트 회고
3. git commit
4. git push

---

## 3. Gate 표준 모델

모든 스프린트는 동일한 8개 Gate를 사용한다.

| Gate | 이름 | 목적 | 필수 Skill |
|------|------|------|-----------|
| G0 | Context Init | 컨텍스트 복구, 범위 고정 | `sprint`, `lead`, `retrospective` |
| G1 | Skill Coverage | 작업-스킬 매핑, 누락 식별 | `skill-auditor`, `task-router` |
| G2 | Agent Coverage | 작업-에이전트 매핑, 누락 식별 | `lead`, `sprint` |
| G3 | Bootstrap | 누락 Skill/Agent 생성 | `skill-creator`, `hub-manager` |
| G4 | Build | 구현/문서/설정 작업 실행 | 스프린트별 핵심 Skill |
| G5 | Verify | 테스트/검증/품질 감사 | `test-generator`, `quality-gate`, `code-review` |
| G6 | Release Review | Gate 판정(PASS/WARN/FAIL) | `quality-gate`, `skill-auditor` |
| G7 | Full Close-Out | 메모리, 회고, commit, push | `retrospective`, `sprint` |

### 3.1 Gate 판정 규칙

- PASS: 모든 Exit Criteria 만족
- WARN: 핵심 기능은 충족, 비핵심 이슈 존재 (이슈 등록 필수)
- FAIL: 핵심 기준 미달 (G4 또는 G3로 롤백)

### 3.2 G7 Full Close-Out 체크리스트 (모든 스프린트 공통)

1. Memory 저장
- 대상: `~/.claude/projects/C--workspace-trading/memory/MEMORY.md`
- 기록: 변경 요약, 결정 사항, 실패 패턴, 다음 액션

2. 회고 기록
- `docs/sprints/<sprint-id>-retrospective.md`

3. Git commit
- 스코프 제한 스테이징 (`git add -A` 금지)
- Conventional Commit

4. Git push
- 브랜치 push 후 원격 반영 확인

---

## 4. Team Agent 운영 체계

### 4.1 현재 사용 가능 Agent

- `backend-architect`
- `frontend-developer`
- `fullstack-developer`
- `technical-writer`
- `ui-ux-designer`
- `hub-manager`
- `skill-auditor`
- `llms-maintainer`

### 4.2 본 스프린트 체계에서 요구하는 도메인 Agent

아래 Agent가 없으면 S0의 G3에서 생성한다.

- `trading-orchestrator-lead`
- `data-engineer-agent`
- `fundamental-analyst-agent`
- `technical-analyst-agent`
- `sentiment-analyst-agent`
- `regime-analyst-agent`
- `risk-auditor-agent`
- `execution-ops-agent`
- `backtest-methodology-agent`
- `performance-attribution-agent`

생성 원칙:

- 생성 책임 Agent: `backend-architect` 또는 `technical-writer`
- 생성 방식: Skill 기반 (`skill-creator`로 Agent 생성 Skill 정의 후 생성)
- 등록: `hub-manager`로 허브 재동기화

---

## 5. Skill 카탈로그 및 공백 분석

### 5.1 이미 존재하는 핵심 Skill (트레이딩 도메인)

- `trading-orchestrator`
- `data-ingest`
- `regime-detect`
- `signal-generate`
- `scoring-engine`
- `position-sizer`
- `risk-manager`
- `execution-planner`
- `bias-checker`
- `performance-analyst`
- `self-improver`
- `backtest-validator`

### 5.2 운영용 Skill (이미 존재)

- `quality-gate`
- `task-router`
- `test-generator`
- `code-review`
- `doc-generator`
- `hub-manager`
- `deployment`
- `scaffolding`

### 5.3 스프린트 운영 공백 Skill (S0 G3에서 생성)

- `agent-bootstrap` (Agent 생성/갱신 자동화)
- `sprint-closeout` (메모리+회고+commit+push 강제 워크플로)
- `integration-tester` (E2E 시나리오 통합)
- `paper-trading-ops` (Paper Trading 일일/주간 루틴)

> 정책: G1에서 공백 Skill이 탐지되면 해당 스프린트의 G3에서 즉시 생성하고, G4는 생성 완료 후 진행한다.

---

## 6. 전체 스프린트 로드맵 (Gate 기반)

| Sprint | 목표 | 기간 | 선행 조건 |
|--------|------|------|----------|
| S0 | 운영체계 부트스트랩 (Skill/Agent/Gate 체계 확립) | 1주 | 없음 |
| S1 | 데이터 레이어 완성 (`data-ingest`) | 1.5주 | S0 PASS |
| S2 | 스코어링 엔진 완성 (`scoring-engine`) | 2주 | S1 PASS |
| S3 | 레짐+시그널 완성 (`regime-detect` + `signal-generate`) | 2주 | S2 PASS |
| S4 | 포지션/리스크/실행 완성 (`position-sizer`, `risk-manager`, `execution-planner`) | 2주 | S3 PASS |
| S5 | 오케스트레이터+CLI 통합 (`trading-orchestrator`) | 1.5주 | S4 PASS |
| S6 | 백테스트 검증 체계 (`backtest-validator`) | 2주 | S5 PASS |
| S7 | 상업 API v1 (QuantScore/RegimeRadar/SignalFusion) | 2주 | S6 PASS |
| S8 | 성과분석+자기개선 루프 (`performance-analyst`, `self-improver`) | 2주 | S7 PASS |
| S9 | 통합 E2E + Paper Trading 1개월 + 배포 준비 | 4주 | S8 PASS |

---

## 7. Sprint 상세 게이트 설계

## S0. 운영체계 부트스트랩

### 목표

Gate 운영과 Skill/Agent 강제 체계를 실제로 작동시키는 운영 Sprint.

### Gate 계획

| Gate | 담당 Agent | 필수 Skill | 주요 산출물 | Exit Criteria |
|------|-----------|-----------|-----------|--------------|
| G0 | `trading-orchestrator-lead`(없으면 `fullstack-developer`) | `sprint`, `lead` | `docs/sprints/S0-context.md` | 범위/성공기준/리스크 명시 |
| G1 | `skill-auditor` | `skill-auditor`, `task-router` | `docs/sprints/S0-skill-matrix.md` | 모든 작업에 스킬 매핑 완료 |
| G2 | `backend-architect` | `sprint` | `docs/sprints/S0-agent-matrix.md` | 모든 작업에 담당 Agent 매핑 완료 |
| G3 | `backend-architect`, `technical-writer` | `skill-creator`, `hub-manager` | 공백 Skill 4종 + 도메인 Agent 10종 정의 | 공백 0건 |
| G4 | `fullstack-developer` | `scaffolding`, `doc-generator` | `docs/sprints/gate-runbook.md` | Gate 실행 템플릿 확정 |
| G5 | `skill-auditor` | `quality-gate`, `code-review` | `docs/sprints/S0-validation.md` | Gate 드라이런 PASS |
| G6 | `trading-orchestrator-lead` | `quality-gate` | `docs/sprints/S0-release-review.md` | PASS/WARN/FAIL 판정 |
| G7 | `technical-writer` + `fullstack-developer` | `sprint-closeout`, `retrospective` | 메모리/회고/commit/push 완료 로그 | Full Close-Out 4단계 완료 |

## S1. Data Layer Sprint

### 목표

`data-ingest`를 통해 US/KR 데이터 수집 + 캐시 + 지표 계산을 안정화.

### 핵심 품질 기준

- API 장애 시 재시도/폴백
- 캐시 TTL 정책
- 지표 재현성 (ATR/ADX/MA/RSI)

### Gate 계획

| Gate | 담당 Agent | 필수 Skill | 산출물 | Exit Criteria |
|------|-----------|-----------|-------|--------------|
| G0 | `data-engineer-agent` | `sprint` | `S1-context.md` | 데이터 범위/소스 확정 |
| G1 | `skill-auditor` | `skill-auditor` | `S1-skill-check.md` | `data-ingest` 커버 확인 |
| G2 | `trading-orchestrator-lead` | `task-router` | `S1-agent-plan.md` | 작업별 Agent 지정 |
| G3 | `backend-architect` | `skill-creator` | (필요 시) `market-data-qc` Skill | 누락 Skill 0건 |
| G4 | `data-engineer-agent` | `data-ingest` | `core/data/*`, `tests/unit/test_data_*` | 데이터 파이프라인 구현 |
| G5 | `risk-auditor-agent` | `test-generator`, `quality-gate` | 검증 리포트 | 단위테스트 커버리지 기준 충족 |
| G6 | `skill-auditor` | `quality-gate` | 릴리즈 판정 | PASS 또는 WARN |
| G7 | `technical-writer` | `sprint-closeout`, `retrospective` | 메모리/회고/commit/push | Full Close-Out 완료 |

## S2. Scoring Engine Sprint

### 목표

F/Z/M/G 및 3축 점수 통합으로 0-100 복합 점수 엔진 고도화.

### 핵심 품질 기준

- 안전성 필터 하드게이트: Z > 1.81, M < -1.78
- 스코어 정규화 일관성
- 시장/섹터 중립 랭킹 재현성

### Gate 계획

| Gate | 담당 Agent | 필수 Skill | 산출물 | Exit Criteria |
|------|-----------|-----------|-------|--------------|
| G0 | `fundamental-analyst-agent` | `sprint` | `S2-context.md` | 지표 정의/경계 확정 |
| G1 | `skill-auditor` | `skill-auditor` | `S2-skill-check.md` | `scoring-engine` 적용 범위 확정 |
| G2 | `trading-orchestrator-lead` | `task-router` | `S2-agent-plan.md` | 3축 Agent 배정 완료 |
| G3 | `backend-architect` | `skill-creator` | (필요 시) `factor-normalizer` Skill | 누락 Skill 0건 |
| G4 | `fundamental/technical/sentiment` 3Agent 병렬 | `scoring-engine` | `core/scoring/*` | 3축 점수 산출 성공 |
| G5 | `backtest-methodology-agent` | `test-generator`, `quality-gate` | `S2-verify.md` | 기준값 테스트 통과 |
| G6 | `skill-auditor` | `quality-gate`, `code-review` | `S2-release-review.md` | PASS/WARN |
| G7 | `technical-writer` | `sprint-closeout`, `retrospective` | Close-Out 기록 | Full Close-Out 완료 |

## S3. Regime + Signal Sprint

### 목표

레짐 감지와 4전략 시그널 합의를 연결해 Layer 2-3 완성.

### 핵심 품질 기준

- 레짐 정확도 목표: 55%+
- 전략 합의 로직 일관성
- 레짐별 가중치 적용 검증

### Gate 계획

| Gate | 담당 Agent | 필수 Skill | 산출물 | Exit Criteria |
|------|-----------|-----------|-------|--------------|
| G0 | `regime-analyst-agent` | `sprint` | `S3-context.md` | 레짐 라벨/평가기준 확정 |
| G1 | `skill-auditor` | `skill-auditor` | `S3-skill-check.md` | `regime-detect`, `signal-generate` 커버 |
| G2 | `trading-orchestrator-lead` | `task-router` | `S3-agent-plan.md` | 4전략 Agent 병렬 설계 완료 |
| G3 | `backend-architect` | `skill-creator` | (필요 시) `signal-consensus-qc` Skill | 누락 Skill 0건 |
| G4 | 5Agent 병렬(레짐1+전략4) | `regime-detect`, `signal-generate` | `core/regime/*`, `core/signals/*` | 전략 합의 출력 성공 |
| G5 | `backtest-methodology-agent` | `quality-gate`, `test-generator` | `S3-verify.md` | IC/레짐 예비검증 통과 |
| G6 | `skill-auditor` | `quality-gate` | `S3-release-review.md` | PASS/WARN |
| G7 | `technical-writer` | `sprint-closeout`, `retrospective` | Close-Out 기록 | Full Close-Out 완료 |

## S4. Position / Risk / Execution Sprint

### 목표

포지션 사이징, 리스크 방어, 실행 계획까지 개인 운용 핵심 완성.

### 핵심 품질 기준

- Kelly 1/4 강제
- 1% 리스크/거래 강제
- 단일 8%, 섹터 25% 강제
- 낙폭 10/15/20% 정책 반영

### Gate 계획

| Gate | 담당 Agent | 필수 Skill | 산출물 | Exit Criteria |
|------|-----------|-----------|-------|--------------|
| G0 | `risk-auditor-agent` | `sprint` | `S4-context.md` | 리스크 한도 고정 선언 |
| G1 | `skill-auditor` | `skill-auditor` | `S4-skill-check.md` | `position-sizer`, `risk-manager`, `execution-planner` 확인 |
| G2 | `trading-orchestrator-lead` | `task-router` | `S4-agent-plan.md` | 실행/리스크 책임 분리 |
| G3 | `backend-architect` | `skill-creator` | (필요 시) `drawdown-guard` Skill | 누락 Skill 0건 |
| G4 | `execution-ops-agent` + `risk-auditor-agent` | `position-sizer`, `risk-manager`, `execution-planner`, `bias-checker` | `personal/*` | 사이징-리스크-실행 체인 동작 |
| G5 | `backtest-methodology-agent` | `test-generator`, `quality-gate` | `S4-verify.md` | 경계값 테스트 통과 |
| G6 | `skill-auditor` | `quality-gate`, `code-review` | `S4-release-review.md` | PASS/WARN |
| G7 | `technical-writer` | `sprint-closeout`, `retrospective` | Close-Out 기록 | Full Close-Out 완료 |

## S5. Orchestrator + CLI Integration Sprint

### 목표

`trading-orchestrator` 기준으로 전체 파이프라인 CLI 실행까지 통합.

### 핵심 품질 기준

- `full`, `quick`, `review` 세 워크플로 동작
- 오류 시 부분 실패 허용 + 경고 보고
- 사용자 출력 일관성

### Gate 계획

| Gate | 담당 Agent | 필수 Skill | 산출물 | Exit Criteria |
|------|-----------|-----------|-------|--------------|
| G0 | `trading-orchestrator-lead` | `sprint` | `S5-context.md` | 오케스트레이션 범위 고정 |
| G1 | `skill-auditor` | `skill-auditor` | `S5-skill-check.md` | 핵심 스킬 9계층 매핑 완료 |
| G2 | `task-router` 담당 Agent | `task-router` | `S5-agent-plan.md` | 병렬/순차 실행 분해 |
| G3 | `backend-architect` | `skill-creator` | (필요 시) `cli-builder` Skill | 누락 Skill 0건 |
| G4 | `fullstack-developer` | `trading-orchestrator`, `scaffolding` | `cli/*`, 오케스트레이터 워크플로 | 3모드 실행 성공 |
| G5 | `risk-auditor-agent` | `quality-gate`, `test-generator` | `S5-verify.md` | E2E 스모크 테스트 통과 |
| G6 | `skill-auditor` | `quality-gate` | `S5-release-review.md` | PASS/WARN |
| G7 | `technical-writer` | `sprint-closeout`, `retrospective` | Close-Out 기록 | Full Close-Out 완료 |

## S6. Backtest & QA Sprint

### 목표

백테스트 신뢰성 검증 체계를 정식 Gate로 구축.

### 핵심 품질 기준

- PBO < 10%
- WFE > 50%
- Sharpe t-stat > 2
- Look-ahead / survivorship / overfitting 방지 체크리스트 통과

### Gate 계획

| Gate | 담당 Agent | 필수 Skill | 산출물 | Exit Criteria |
|------|-----------|-----------|-------|--------------|
| G0 | `backtest-methodology-agent` | `sprint` | `S6-context.md` | 검증 기준 확정 |
| G1 | `skill-auditor` | `skill-auditor` | `S6-skill-check.md` | `backtest-validator` 범위 확인 |
| G2 | `task-router` 담당 Agent | `task-router` | `S6-agent-plan.md` | 통계검증 담당 분리 |
| G3 | `backend-architect` | `skill-creator` | (필요 시) `validation-pipeline` Skill | 누락 Skill 0건 |
| G4 | `backtest-methodology-agent` | `backtest-validator` | 검증 코드/리포트 | 12항목 체크 동작 |
| G5 | `quality-gate` 담당 Agent | `quality-gate`, `code-review` | `S6-verify.md` | 지표 기준 충족 |
| G6 | `skill-auditor` | `quality-gate` | `S6-release-review.md` | PASS/WARN |
| G7 | `technical-writer` | `sprint-closeout`, `retrospective` | Close-Out 기록 | Full Close-Out 완료 |

## S7. Commercial API v1 Sprint

### 목표

QuantScore/RegimeRadar/SignalFusion API를 정보 제공 원칙으로 출시 가능 상태로 구축.

### 핵심 품질 기준

- 투자 자문 문구 금지
- 면책조항 헤더/본문 삽입
- 인증/레이트리밋 적용

### Gate 계획

| Gate | 담당 Agent | 필수 Skill | 산출물 | Exit Criteria |
|------|-----------|-----------|-------|--------------|
| G0 | `backend-architect` | `sprint` | `S7-context.md` | API 범위/법적 경계 고정 |
| G1 | `skill-auditor` | `skill-auditor` | `S7-skill-check.md` | API 관련 Skill 매핑 완료 |
| G2 | `trading-orchestrator-lead` | `task-router` | `S7-agent-plan.md` | API/보안/문서 담당 배정 |
| G3 | `backend-architect` | `skill-creator`, `hub-manager` | (필요 시) `api-server-builder` Skill | 누락 Skill 0건 |
| G4 | `backend-architect` + `technical-writer` | `api-designer`, `deployment`, `doc-generator` | `commercial/api/*` | 3개 API 엔드포인트 동작 |
| G5 | `risk-auditor-agent` | `quality-gate`, `code-review` | `S7-verify.md` | 법적/보안 체크 PASS |
| G6 | `skill-auditor` | `quality-gate` | `S7-release-review.md` | PASS/WARN |
| G7 | `technical-writer` | `sprint-closeout`, `retrospective` | Close-Out 기록 | Full Close-Out 완료 |

## S8. Performance + Self-Improvement Sprint

### 목표

성과 분석 4레벨과 자동 개선 루프를 연결해 월간 개선 체계 완성.

### 핵심 품질 기준

- Signal IC >= 0.03
- Kelly 효율 >= 70%
- 진단은 자동, 파라미터 반영은 승인 기반

### Gate 계획

| Gate | 담당 Agent | 필수 Skill | 산출물 | Exit Criteria |
|------|-----------|-----------|-------|--------------|
| G0 | `performance-attribution-agent` | `sprint` | `S8-context.md` | KPI/진단 임계값 고정 |
| G1 | `skill-auditor` | `skill-auditor` | `S8-skill-check.md` | `performance-analyst`, `self-improver` 확인 |
| G2 | `trading-orchestrator-lead` | `task-router` | `S8-agent-plan.md` | 4레벨 분석 담당 배정 |
| G3 | `backend-architect` | `skill-creator` | (필요 시) `improvement-governor` Skill | 누락 Skill 0건 |
| G4 | `performance-attribution-agent` | `performance-analyst`, `self-improver` | `personal/performance/*`, `personal/self_improver.py` | 진단->제안 체계 구현 |
| G5 | `risk-auditor-agent` | `quality-gate`, `test-generator` | `S8-verify.md` | 승인 없는 자동반영 금지 검증 |
| G6 | `skill-auditor` | `quality-gate` | `S8-release-review.md` | PASS/WARN |
| G7 | `technical-writer` | `sprint-closeout`, `retrospective` | Close-Out 기록 | Full Close-Out 완료 |

## S9. E2E + Paper Trading + Deployment Readiness Sprint

### 목표

실거래 전 단계(모의)에서 1개월 검증 + 배포 준비 완료.

### 핵심 품질 기준

- 최소 20 거래일 Paper 로그
- Sharpe > 1.0, MDD < 10% (Paper 기간)
- 배포 아티팩트 빌드/실행 가능

### Gate 계획

| Gate | 담당 Agent | 필수 Skill | 산출물 | Exit Criteria |
|------|-----------|-----------|-------|--------------|
| G0 | `trading-orchestrator-lead` | `sprint` | `S9-context.md` | Paper 운영 범위 확정 |
| G1 | `skill-auditor` | `skill-auditor` | `S9-skill-check.md` | 통합/운영 스킬 확인 |
| G2 | `task-router` 담당 Agent | `task-router` | `S9-agent-plan.md` | E2E, 운영, 배포 역할 분리 |
| G3 | `backend-architect` | `skill-creator`, `hub-manager` | `integration-tester`, `paper-trading-ops`(없으면 생성) | 누락 Skill 0건 |
| G4 | `execution-ops-agent` | `integration-tester`, `paper-trading-ops`, `deployment` | Paper 로그, E2E 리포트, Docker 아티팩트 | 20거래일 운영 데이터 확보 |
| G5 | `risk-auditor-agent` + `backtest-methodology-agent` | `quality-gate`, `performance-analyst` | `S9-verify.md` | KPI 기준 판정 |
| G6 | `skill-auditor` | `quality-gate`, `code-review` | `S9-release-review.md` | PASS/WARN |
| G7 | `technical-writer` | `sprint-closeout`, `retrospective` | 메모리/회고/commit/push | Full Close-Out 완료 |

---

## 8. Skill 미존재 시 생성 프로세스 (표준)

모든 스프린트의 G3에서 아래 순서를 따른다.

1. 누락 Skill 명세 작성
- 파일: `.claude/skills/<skill-name>/SKILL.md`
- 내용: 역할, 입력 인자, 출력 포맷, 제약, 참조문서

2. Team Agent 지정
- 시스템/백엔드: `backend-architect`
- 문서/규칙형: `technical-writer`
- 통합 작업: `fullstack-developer`

3. 허브 동기화
- `hub-manager`를 통해 스캔/동기화 수행

4. 재감사
- `skill-auditor`로 누락 0건 확인

---

## 9. Sprint 종료 산출물 규격 (강제)

매 스프린트 종료 시 최소 아래 파일이 존재해야 한다.

- `docs/sprints/<sprint-id>-context.md`
- `docs/sprints/<sprint-id>-skill-check.md`
- `docs/sprints/<sprint-id>-agent-plan.md`
- `docs/sprints/<sprint-id>-verify.md`
- `docs/sprints/<sprint-id>-release-review.md`
- `docs/sprints/<sprint-id>-retrospective.md`

그리고 메모리 업데이트 기록이 있어야 한다.

- `~/.claude/projects/C--workspace-trading/memory/MEMORY.md`

---

## 10. Git 운영 규칙 (G7에서 강제)

- 스테이징은 변경 파일 지정 방식 사용
- `.env`, 자격증명, 토큰 커밋 금지
- 커밋 메시지: `feat|fix|chore(sprint-SN): ...`
- push 실패 시 원인 분석 후 재시도, 우회 강제 금지

권장 템플릿:

```bash
git add <changed files>
git commit -m "feat(sprint-SN): <gate summary>"
git push origin <branch>
```

---

## 11. 운영 시작 체크 (실행용)

스프린트 시작 전에 아래를 확인한다.

- [ ] 이번 스프린트 ID 확정 (S0~S9)
- [ ] G0 문서 생성
- [ ] G1 Skill 매핑 완료
- [ ] G2 Agent 매핑 완료
- [ ] 공백 Skill/Agent 존재 시 G3 생성 계획 반영
- [ ] G7 Close-Out 담당자 지정

---

## 12. 이 문서의 사용 방식

- 모든 작업 요청은 먼저 현재 스프린트의 Gate 상태로 변환한다.
- Gate 단위로만 진행 상태를 업데이트한다.
- Gate 미통과 상태에서 다음 Gate를 열지 않는다.
- 스프린트 종료 판단은 G7 완료 여부로만 결정한다.

이 문서를 기준으로 작업하면,

1. Skill 없는 실행이 사라지고,
2. Team Agent 책임이 명확해지며,
3. 매 스프린트가 메모리/회고/커밋/푸시까지 닫히는 Full Sprint로 운영된다.
