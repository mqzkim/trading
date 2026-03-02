# S0 — 운영체계 부트스트랩: Context Document

- Sprint ID: `S0`
- 기준 문서: `docs/sprint-plan.md` (v2.0, Gate-first)
- 작성일: 2026-03-03
- 상태: 진행 중

---

## 1. 스프린트 목표

Gate 운영과 Skill/Agent 강제 체계를 실제로 작동시키는 운영 Sprint.

S0는 기능 구현 Sprint가 아니다. S1~S9가 Gate 기반으로 올바르게 실행되기 위한 운영 인프라 자체를 확립하는 Sprint다. 이 Sprint가 PASS 판정을 받아야만 S1이 시작될 수 있다.

S0의 목표를 세 줄로 요약하면 다음과 같다.

1. 모든 작업을 Team Agent가 수행 가능하도록 Skill/Agent 체계를 완비한다.
2. 스프린트 운영에 필요한 공백 Skill 4종과 도메인 Agent 10종을 G3에서 생성한다.
3. Gate 실행 템플릿(gate-runbook.md)을 확정하고 드라이런으로 Gate 체계가 실제로 작동함을 검증한다.

---

## 2. 범위 (Scope)

### In Scope

S0에서 다루는 항목은 아래와 같다.

- G0: S0 Context 문서(`S0-context.md`) 작성 및 범위/성공기준/리스크 명시
- G1: 전체 작업 목록에 대한 Skill 매핑 감사(`S0-skill-matrix.md`) 수행
- G2: 전체 작업 목록에 대한 담당 Agent 매핑(`S0-agent-matrix.md`) 수행
- G3: 공백 Skill 4종 생성 및 도메인 Agent 10종 정의, Hub 등록
- G4: Gate 실행 템플릿(`docs/sprints/gate-runbook.md`) 확정
- G5: Gate 드라이런 수행 및 검증 결과 기록(`S0-validation.md`)
- G6: PASS/WARN/FAIL 판정 문서(`S0-release-review.md`) 작성
- G7: 메모리 저장, 회고(`S0-retrospective.md`), git commit, git push로 Full Close-Out 완료

### Out of Scope

S0에서 다루지 않는 항목은 아래와 같다.

- 트레이딩 기능 코드 구현 (data-ingest, scoring-engine, regime-detect 등)
- 백테스트 수행 또는 실제 시장 데이터 처리
- 상업 API 서버 구축
- Paper Trading 실행
- S1~S9의 어떠한 Gate도 선행 진입 금지

---

## 3. 성공 기준 (Exit Criteria)

각 Gate의 Exit Criteria 요약표. 모든 항목이 충족되어야 해당 Gate가 PASS 판정을 받는다.

| Gate | 이름 | Exit Criteria | 판정 기준 |
|------|------|--------------|----------|
| G0 | Context Init | `S0-context.md` 존재, 범위/성공기준/리스크 명시 | 이 문서가 완성 상태일 것 |
| G1 | Skill Coverage | `S0-skill-matrix.md` 존재, 모든 S0 작업에 Skill 매핑 완료, 공백 Skill 목록 명시 | 미매핑 작업 0건 |
| G2 | Agent Coverage | `S0-agent-matrix.md` 존재, 모든 S0 작업에 담당 Agent 매핑 완료 | 담당 Agent 없는 작업 0건 |
| G3 | Bootstrap | 공백 Skill 4종 파일 생성 완료, 도메인 Agent 10종 정의 완료, hub-manager 동기화 완료, skill-auditor 재감사 후 누락 0건 | 공백 0건 |
| G4 | Build | `docs/sprints/gate-runbook.md` 존재, Gate 실행 절차 문서화 완료 | 템플릿 확정 |
| G5 | Verify | `S0-validation.md` 존재, Gate 드라이런 실행 결과 기록, 체계 작동 확인 | 드라이런 PASS |
| G6 | Release Review | `S0-release-review.md` 존재, PASS/WARN/FAIL 판정 명시, 근거 기록 | PASS 또는 WARN |
| G7 | Full Close-Out | 메모리 저장 완료, 회고 문서 존재, git commit 완료(Conventional Commit 형식), git push 완료 | Full Close-Out 4단계 모두 완료 |

---

## 4. 필수 산출물

Gate별 산출물 목록. Sprint 종료 시 아래 모든 파일이 존재해야 한다.

### G0 산출물
- `docs/sprints/S0-context.md` (이 문서)

### G1 산출물
- `docs/sprints/S0-skill-matrix.md`
  - 전체 S0 작업 목록
  - 각 작업에 매핑된 Skill 이름
  - 공백 Skill 식별 목록

### G2 산출물
- `docs/sprints/S0-agent-matrix.md`
  - 전체 S0 작업 목록
  - 각 작업에 매핑된 담당 Agent
  - 부재 Agent 식별 목록 (G3 생성 대상)

### G3 산출물
- `.claude/skills/agent-bootstrap/SKILL.md` (공백 Skill 1)
- `.claude/skills/sprint-closeout/SKILL.md` (공백 Skill 2)
- `.claude/skills/integration-tester/SKILL.md` (공백 Skill 3)
- `.claude/skills/paper-trading-ops/SKILL.md` (공백 Skill 4)
- 도메인 Agent 정의 파일 10종:
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
- Hub 동기화 완료 로그

### G4 산출물
- `docs/sprints/gate-runbook.md`
  - 표준 Gate 8종(G0~G7) 실행 절차
  - Entry/Exit Criteria 체크 방법
  - PASS/WARN/FAIL 판정 기준
  - 롤백 절차

### G5 산출물
- `docs/sprints/S0-validation.md`
  - 드라이런 실행 시나리오
  - Gate 체계 작동 여부 결과
  - 발견된 이슈 및 대응

### G6 산출물
- `docs/sprints/S0-release-review.md`
  - 전 Gate 판정 결과 요약
  - 최종 PASS/WARN/FAIL 판정
  - WARN 항목 이슈 등록 내역

### G7 산출물
- `~/.claude/projects/C--workspace-trading/memory/MEMORY.md` (업데이트)
- `docs/sprints/S0-retrospective.md`
- git commit 완료 확인 (커밋 해시)
- git push 완료 확인 (원격 반영)

---

## 5. 리스크 및 대응

S0 수행 중 발생 가능한 리스크와 대응 방안을 사전 식별한다.

| 리스크 | 발생 가능성 | 영향도 | 대응 방안 |
|--------|-----------|-------|---------|
| `trading-orchestrator-lead` Agent 부재로 G0 담당자 없음 | 높음 | 중간 | G0는 `fullstack-developer`가 대행, G3에서 즉시 생성 후 이후 Gate부터 정식 담당 |
| G3에서 공백 Skill 4종 생성 시 내용 불완전 | 중간 | 높음 | `backend-architect` + `technical-writer` 2 Agent 협업으로 생성, `skill-auditor`로 재검토 필수 |
| G5 드라이런에서 Gate 체계 오류 발견 | 중간 | 높음 | G4로 롤백 후 `gate-runbook.md` 수정, 재드라이런 수행 |
| hub-manager 동기화 실패로 Skill 미등록 | 낮음 | 높음 | 동기화 로그 확인 후 재실행, 수동 등록 절차 병행 |
| G7 git push 실패 | 낮음 | 중간 | 원인 분석 후 재시도, 강제 push 금지, 원격 브랜치 상태 확인 후 처리 |
| Agent 정의 파일 10종 생성 시간 초과로 1주 기간 초과 | 중간 | 낮음 | `backend-architect`와 `technical-writer`를 병렬로 투입, 파일 생성 우선 후 내용 보강 |

---

## 6. 담당 Agent 배정

Gate별 주담당 Agent 및 보조 Agent 요약.

| Gate | 주담당 Agent | 보조 Agent | 비고 |
|------|-----------|-----------|------|
| G0 | `trading-orchestrator-lead` | `fullstack-developer` | 부재 시 `fullstack-developer` 대행 |
| G1 | `skill-auditor` | `task-router` | Skill 매핑 감사 전담 |
| G2 | `backend-architect` | `trading-orchestrator-lead` | Agent 매핑 및 부재 Agent 식별 |
| G3 | `backend-architect`, `technical-writer` | `hub-manager`, `skill-auditor` | 공백 Skill + Agent 생성 후 hub 동기화 |
| G4 | `fullstack-developer` | `technical-writer` | Gate Runbook 문서화 |
| G5 | `skill-auditor` | `quality-gate` | 드라이런 실행 및 검증 |
| G6 | `trading-orchestrator-lead` | `quality-gate`, `skill-auditor` | 최종 판정 |
| G7 | `technical-writer`, `fullstack-developer` | `retrospective` | Full Close-Out 4단계 강제 완료 |

Agent 부재 원칙: 담당 Agent가 존재하지 않을 경우 해당 Gate 진행 전에 G3로 진입해 Agent를 먼저 생성한다. 단, G0와 G3는 현재 존재하는 `fullstack-developer` 또는 `backend-architect`가 대행을 허용한다.

---

## 7. 제약 조건

S0 전체 수행 과정에서 반드시 준수해야 하는 제약 조건이다. 이를 위반하면 해당 Gate는 자동 FAIL 처리된다.

### Skill-First 강제

- 모든 실행 작업은 Skill 호출로 시작한다.
- Skill 매칭 성공: 해당 Skill로 즉시 실행한다.
- Skill 매칭 실패: G3로 이동해 Skill을 먼저 생성한 뒤 실행한다.
- 허용되는 비-Skill 활동은 문서/코드 읽기, 상태 조회(`git status`, 로그 확인), 사용자 질의/응답으로 제한한다.

### Team-Agent-First 강제

- 모든 Gate에는 담당 Team Agent가 명시되어야 한다.
- 담당 Agent 없이 Gate를 수행하는 것은 금지한다.
- 담당 Agent 부재 시 Agent 생성 Gate(G3)를 먼저 완료한다.

### Gate 순서 강제

- 각 Gate는 Entry Criteria를 충족한 뒤에만 진입한다.
- Exit Criteria 미충족 시 다음 Gate 진행을 금지한다.
- FAIL 판정 시 G4 또는 G3로 롤백한다.
- S0 PASS 판정 없이 S1 진입을 금지한다.

### Full Sprint 종료 강제 (G7)

G7에서 아래 4단계를 모두 완료해야만 S0가 종료된 것으로 인정한다.

1. 작업 메모리 저장 (`~/.claude/projects/C--workspace-trading/memory/MEMORY.md`)
2. 스프린트 회고 (`docs/sprints/S0-retrospective.md`)
3. git commit (스코프 제한 스테이징, `git add -A` 금지, Conventional Commit 형식)
4. git push (원격 반영 확인)

### Git 운영 제약

- 스테이징은 변경 파일 지정 방식만 허용 (`git add -A` 금지)
- `.env`, 자격증명, 토큰 커밋 금지
- 커밋 메시지 형식: `feat|fix|chore(sprint-S0): <내용>`
- push 실패 시 원인 분석 후 재시도, 강제 push 금지

---

## 8. 스프린트 시작 선언

- 날짜: 2026-03-03
- 상태: 진행 중
- 현재 Gate: G0 (Context Init)
- 다음 Gate: G1 (이 문서 완성 후 진행 가능)

### 운영 시작 체크리스트

- [x] 스프린트 ID 확정: S0
- [x] G0 문서 생성: `docs/sprints/S0-context.md`
- [ ] G1 Skill 매핑 완료
- [ ] G2 Agent 매핑 완료
- [ ] G3 공백 Skill 4종 생성 완료
- [ ] G3 도메인 Agent 10종 생성 완료
- [ ] G4 Gate Runbook 확정
- [ ] G5 드라이런 PASS
- [ ] G6 릴리즈 판정 완료
- [ ] G7 Full Close-Out 완료
