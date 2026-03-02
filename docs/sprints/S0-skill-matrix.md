# S0 Skill Coverage Matrix

> Gate: G1 | Sprint: S0 | 날짜: 2026-03-03
> 기준 문서: `docs/sprint-plan.md` v2.0, `docs/sprints/S0-context.md`
> 담당 Agent: `skill-auditor` (보조: `task-router`)

---

## 1. Gate별 Skill 매핑

아래 표는 S0의 Gate 8종(G0~G7)에서 요구하는 Skill과 현재 Hub 등록 상태, 파일 존재 여부를 교차 검증한 결과다.

판정 기준:
- **READY**: Hub 등록 + 파일 존재 → 즉시 사용 가능
- **MISSING**: Hub 미등록 또는 파일 없음 → G3 생성 필수

| Gate | 이름 | 필수 Skill | Hub 등록 | 파일 존재 | 판정 |
|------|------|-----------|---------|---------|------|
| G0 | Context Init | `sprint` | 없음 | 없음 | MISSING |
| G0 | Context Init | `lead` | 없음 | 없음 | MISSING |
| G1 | Skill Coverage | `skill-auditor` | 있음 | 있음 (agent) | READY |
| G1 | Skill Coverage | `task-router` | 있음 | 있음 | READY |
| G2 | Agent Coverage | `sprint` | 없음 | 없음 | MISSING |
| G3 | Bootstrap | `skill-creator` | 없음 | 없음 | MISSING |
| G3 | Bootstrap | `hub-manager` | 있음 | 있음 | READY |
| G4 | Build | `scaffolding` | 있음 | 있음 | READY |
| G4 | Build | `doc-generator` | 있음 | 있음 | READY |
| G5 | Verify | `quality-gate` | 있음 | 있음 | READY |
| G5 | Verify | `code-review` | 있음 | 있음 | READY |
| G6 | Release Review | `quality-gate` | 있음 | 있음 | READY |
| G7 | Full Close-Out | `sprint-closeout` | 없음 | 없음 | MISSING |
| G7 | Full Close-Out | `retrospective` | 있음 | 있음 (agent) | READY |

> 비고: `skill-auditor`와 `retrospective`는 `.claude/agents/` 경로에 Agent 정의 파일로 존재한다. Skill 파일(`SKILL.md`)과 별개이나 G1/G7 목적에 충분히 부합하므로 READY로 판정한다.

---

## 2. 공백 Skill — G3 생성 대상

`sprint-plan.md` 5.3절에서 S0 G3 생성 대상으로 명시한 공백 Skill 4종과, Gate 매핑 감사에서 추가로 식별된 공백 Skill을 통합해 아래에 정리한다.

### 2.1 sprint-plan.md 5.3절 지정 공백 Skill (4종)

| Skill | 용도 | 필요 Gate | 우선순위 |
|-------|------|----------|---------|
| `agent-bootstrap` | Agent 정의 파일 생성 및 갱신 자동화. G3에서 도메인 Agent 10종 생성 시 사용 | G3 | 높음 |
| `sprint-closeout` | 메모리 저장, 회고 작성, git commit, git push를 순서대로 강제하는 워크플로. 모든 스프린트 G7의 핵심 | G7 | 높음 |
| `integration-tester` | E2E 시나리오 정의, 실행, 결과 기록. S9 Gate 4에서 Paper Trading E2E 검증에 사용 | G5 (S9) | 중간 |
| `paper-trading-ops` | Paper Trading 일일/주간 루틴 실행 및 로그 수집. S9 Gate 4에서 사용 | G4 (S9) | 중간 |

### 2.2 Gate 매핑 감사에서 식별된 추가 공백 Skill

| Skill | 용도 | 필요 Gate | 비고 |
|-------|------|----------|------|
| `sprint` | Sprint 컨텍스트 초기화, Gate 상태 추적, 스프린트 범위 고정. G0/G2 양쪽에서 필요 | G0, G2 | 모든 스프린트 공통 |
| `lead` | 스프린트 리드 판단: 우선순위 결정, Gate 진행 여부 판정, 대행 Agent 지정 | G0 | `trading-orchestrator-lead` Agent와 연계 |
| `skill-creator` | 공백 Skill 명세 작성 및 파일 생성 표준화. G3에서 공백 Skill 생성 시 사용 | G3 | G3 핵심 Skill |

> 정책: G3 생성 대상 목록은 5.3절 4종 + 감사 식별 3종으로 총 7종이다. 단, G3 수행 Skill(`skill-creator`) 자체가 공백이므로 `backend-architect` Agent가 표준 Skill 생성 템플릿에 따라 직접 파일을 생성한 뒤, `skill-creator` Skill을 등록하고 이후 나머지 Skill 생성에 사용한다.

---

## 3. 커버 현황 요약

| 항목 | 수치 |
|------|------|
| S0 Gate별 총 요구 Skill | 14건 (중복 포함) |
| 고유 Skill 종류 | 11종 |
| Hub 등록 + 파일 존재 (READY) | 8종 |
| 공백 (MISSING) | 5종 (`sprint`, `lead`, `skill-creator`, `sprint-closeout`, 그리고 G3 부트스트랩 전용 `agent-bootstrap`) |
| G3 생성 필수 (sprint-plan 5.3 + 감사 식별 통합) | 7종 |

---

## 4. G3 생성 우선순위 및 실행 순서

G3에서 Skill을 생성하는 순서는 의존 관계를 고려해 아래와 같이 정한다.

| 순서 | Skill | 근거 |
|------|-------|------|
| 1 | `skill-creator` | 나머지 모든 Skill 생성의 전제 조건. `backend-architect`가 템플릿 기반으로 직접 작성 |
| 2 | `sprint` | G0/G2 소급 적용 및 S1 이후 모든 스프린트에 즉시 필요 |
| 3 | `lead` | G0 소급 적용. `trading-orchestrator-lead` Agent 연계 정의 필요 |
| 4 | `agent-bootstrap` | G3 도메인 Agent 10종 생성에 사용. `hub-manager`와 연계 |
| 5 | `sprint-closeout` | G7 Full Close-Out 강제 워크플로. S0 G7 진입 전 완료 필수 |
| 6 | `integration-tester` | S9까지 유예 가능하나 S0 G3에서 파일 생성만 완료 권장 |
| 7 | `paper-trading-ops` | S9까지 유예 가능하나 S0 G3에서 파일 생성만 완료 권장 |

---

## 5. 작업-Skill 전체 매핑

S0의 작업 항목별 담당 Skill 매핑이다. 이 표에서 미매핑 작업이 0건이어야 G1 Exit Criteria를 충족한다.

| 작업 항목 | 담당 Skill | 상태 |
|----------|-----------|------|
| S0 컨텍스트 문서 생성 및 범위 선언 | `sprint`, `lead` | MISSING (G3 생성 후 소급 적용) |
| 전체 작업 Skill 매핑 감사 수행 | `skill-auditor` | READY |
| 작업-Skill 라우팅 테이블 작성 | `task-router` | READY |
| 공백 Skill 식별 및 목록화 | `skill-auditor` | READY |
| 담당 Agent 매핑 (G2) | `sprint` | MISSING (G3 생성 후 소급 적용) |
| 공백 Skill 4종 + 3종 Skill 파일 생성 | `skill-creator` | MISSING (G3 최우선 생성 대상) |
| Hub 동기화 수행 | `hub-manager` | READY |
| Skill 재감사 (누락 0건 확인) | `skill-auditor` | READY |
| Gate Runbook 문서 작성 | `scaffolding`, `doc-generator` | READY |
| Gate 드라이런 실행 및 결과 기록 | `quality-gate`, `code-review` | READY |
| 릴리즈 판정 (PASS/WARN/FAIL) | `quality-gate` | READY |
| 메모리 저장, 회고, commit, push | `sprint-closeout`, `retrospective` | `sprint-closeout` MISSING / `retrospective` READY |

미매핑 작업: **0건**. 모든 작업에 Skill이 지정되어 있으나 5종은 G3에서 생성 후 사용 가능하다.

---

## 6. G1 Exit Criteria 판정

| Exit Criteria | 결과 |
|--------------|------|
| `S0-skill-matrix.md` 문서 존재 | PASS |
| 모든 S0 작업에 Skill 매핑 완료 | PASS (미매핑 0건) |
| 공백 Skill 목록 명시 완료 | PASS (7종 식별) |
| G3 생성 대상 우선순위 정의 | PASS |

**G1 판정: PASS**

다음 Gate: G2 (Agent Coverage) 진행 가능.
G2 완료 후 G3에서 공백 Skill 7종 생성을 즉시 시작한다.
