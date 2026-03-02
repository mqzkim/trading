# Gate 실행 런북 (Gate Execution Runbook)

> 버전: 1.0 | 확정일: 2026-03-03
> 모든 스프린트(S1~S9)의 Gate 실행 표준 절차
> 기준 문서: `docs/sprint-plan.md` (v2.0, Gate-first) 섹션 3

---

## 1. Gate 표준 흐름

모든 스프린트는 동일한 8개 Gate(G0~G7)를 순서대로 통과한다. Gate를 건너뛰거나 순서를 변경하는 것은 금지한다.

```
G0: Context Init ─── 컨텍스트 복구, 스프린트 범위/성공기준/리스크 고정
 |
 v
G1: Skill Coverage ── 모든 작업에 Skill 매핑, 공백 Skill 식별
 |
 v
G2: Agent Coverage ── 모든 작업에 담당 Agent 매핑, 부재 Agent 식별
 |
 v
G3: Bootstrap ─────── 누락 Skill/Agent 생성, Hub 등록, 재감사
 |
 v
G4: Build ─────────── 구현/문서/설정 작업 실행 (스프린트 핵심)
 |
 v
G5: Verify ────────── 테스트/검증/품질 감사
 |
 v
G6: Release Review ── PASS/WARN/FAIL 최종 판정
 |
 v
G7: Full Close-Out ── 메모리 저장 -> 회고 -> git commit -> git push
```

**핵심 규칙**: Exit Criteria 미충족 시 다음 Gate 진입 금지. FAIL 판정 시 G4 또는 G3로 롤백.

---

## 2. Gate별 실행 체크리스트

### G0: Context Init

**목적**: 이전 세션의 컨텍스트를 복구하고, 이번 스프린트의 범위/성공기준/리스크를 고정한다.

**Entry Criteria**:
- [ ] 이전 스프린트가 G7 Full Close-Out으로 완료되었거나, 첫 번째 스프린트(S0)이다
- [ ] 스프린트 ID가 확정되었다 (S0~S9)

**실행 체크리스트**:
- [ ] `docs/sprint-plan.md`에서 해당 스프린트 섹션 읽기
- [ ] 이전 스프린트 회고(`docs/sprints/<prev>-retrospective.md`) 읽기
- [ ] 프로젝트 메모리(`.claude/CLAUDE.md`) 읽기로 컨텍스트 복구
- [ ] `docs/sprints/<sprint-id>-context.md` 작성
  - 스프린트 목표 (1문장)
  - In Scope / Out of Scope 명시
  - Gate별 Exit Criteria 요약표
  - 필수 산출물 목록
  - 리스크 및 대응 방안
  - 담당 Agent 배정표

**Exit Criteria**:
- [ ] `docs/sprints/<sprint-id>-context.md` 파일이 존재한다
- [ ] 범위, 성공기준, 리스크가 명시적으로 기록되어 있다
- [ ] 담당 Agent 배정이 완료되어 있다

**필수 Skill**: `sprint`, `lead`, `retrospective`
**담당 Agent**: 해당 스프린트의 주 오케스트레이터 Agent

---

### G1: Skill Coverage

**목적**: 이번 스프린트의 모든 작업에 Skill이 매핑되어 있는지 감사하고, 공백 Skill을 식별한다.

**Entry Criteria**:
- [ ] G0 PASS (Context 문서 완성)

**실행 체크리스트**:
- [ ] G0 Context 문서에서 작업 목록 추출
- [ ] 각 작업에 대해 `.claude/skills/` 에서 매칭 Skill 탐색
- [ ] 매칭 결과를 `docs/sprints/<sprint-id>-skill-matrix.md`에 기록
  - 작업명 | 매핑된 Skill | 상태(Covered/Gap)
- [ ] 공백 Skill 목록 명시 (G3에서 생성 대상)
- [ ] 미매핑 작업이 0건이 될 때까지 반복

**Exit Criteria**:
- [ ] `docs/sprints/<sprint-id>-skill-matrix.md` 파일이 존재한다
- [ ] 모든 작업에 Skill 매핑이 완료되었다 (미매핑 0건)
- [ ] 공백 Skill 목록이 명시되어 있다 (0건이면 "없음"으로 명시)

**필수 Skill**: `skill-auditor`, `task-router`
**담당 Agent**: `skill-auditor`

---

### G2: Agent Coverage

**목적**: 이번 스프린트의 모든 작업에 담당 Team Agent가 매핑되어 있는지 확인하고, 부재 Agent를 식별한다.

**Entry Criteria**:
- [ ] G1 PASS (Skill 매핑 완료)

**실행 체크리스트**:
- [ ] G1 Skill Matrix에서 작업 목록 확인
- [ ] 각 작업에 담당 Agent 지정
- [ ] 결과를 `docs/sprints/<sprint-id>-agent-matrix.md`에 기록
  - 작업명 | 담당 Agent | 보조 Agent | 상태(Assigned/Missing)
- [ ] 부재 Agent 목록 명시 (G3에서 생성 대상)
- [ ] 담당 Agent 없는 작업이 0건이 될 때까지 반복

**Exit Criteria**:
- [ ] `docs/sprints/<sprint-id>-agent-matrix.md` 파일이 존재한다
- [ ] 모든 작업에 담당 Agent가 지정되었다 (미지정 0건)
- [ ] 부재 Agent 목록이 명시되어 있다

**필수 Skill**: `lead`, `sprint`
**담당 Agent**: `backend-architect` 또는 `trading-orchestrator-lead`

---

### G3: Bootstrap

**목적**: G1/G2에서 식별된 누락 Skill과 부재 Agent를 생성하고, Hub에 등록한다.

**Entry Criteria**:
- [ ] G2 PASS (Agent 매핑 완료)
- [ ] 공백 Skill 목록이 확정되었다
- [ ] 부재 Agent 목록이 확정되었다

**실행 체크리스트**:
- [ ] 공백 Skill 생성 (각 Skill에 대해):
  - [ ] `.claude/skills/<skill-name>/SKILL.md` 또는 `.claude/skills/<skill-name>.md` 작성
  - [ ] 역할, 입력 인자, 출력 포맷, 제약, 참조문서 명시
- [ ] 부재 Agent 생성 (각 Agent에 대해):
  - [ ] `agent-bootstrap` Skill로 Agent 정의 파일 생성
  - [ ] CLAUDE.md 모델 배정 기준 준수 (opus/sonnet/haiku)
- [ ] `hub-manager` 로 Hub 동기화 실행
- [ ] `skill-auditor` 로 재감사 수행 -> 누락 0건 확인

**Exit Criteria**:
- [ ] 모든 공백 Skill 파일이 생성되었다
- [ ] 모든 부재 Agent 정의 파일이 생성되었다
- [ ] Hub 동기화가 완료되었다
- [ ] 재감사 결과 누락 0건이다

**필수 Skill**: `skill-creator`, `hub-manager`, `agent-bootstrap`
**담당 Agent**: `backend-architect`, `technical-writer`

---

### G4: Build

**목적**: 스프린트의 핵심 구현/문서/설정 작업을 실행한다. 각 스프린트의 실질적 산출물이 여기서 생성된다.

**Entry Criteria**:
- [ ] G3 PASS (누락 Skill/Agent 0건)
- [ ] 모든 필요한 Skill과 Agent가 사용 가능하다

**실행 체크리스트**:
- [ ] 스프린트 Context 문서의 핵심 산출물 목록 확인
- [ ] 각 산출물에 대해 매핑된 Skill을 호출하여 작업 수행
- [ ] 코드 작성 시 `workflow.md` 규칙 준수:
  - [ ] 관련 소스 파일을 먼저 읽기
  - [ ] 기존 구현 여부 확인
  - [ ] 최소 변경으로 문제 해결
- [ ] 작업 완료 시 산출물 파일 존재 여부 확인

**Exit Criteria**:
- [ ] 해당 스프린트의 핵심 산출물이 모두 생성되었다
- [ ] 코드가 구문 오류 없이 작성되었다 (해당 시)
- [ ] 문서가 표준 템플릿을 따르고 있다 (해당 시)

**필수 Skill**: 스프린트별 핵심 Skill (아래 섹션 6 참조)
**담당 Agent**: 스프린트별 지정 Agent

---

### G5: Verify

**목적**: G4에서 생성된 산출물의 품질을 테스트하고 검증한다.

**Entry Criteria**:
- [ ] G4 PASS (핵심 산출물 생성 완료)

**실행 체크리스트**:
- [ ] 단위 테스트 작성 및 실행 (코드 산출물이 있는 경우)
  ```bash
  pytest tests/unit/test_<module>.py -v --tb=short
  ```
- [ ] 타입 체크 / 린트 실행 (해당 시)
  ```bash
  mypy <module_path> --strict
  ruff check <module_path>
  ```
- [ ] 산출물 완전성 검사:
  - [ ] 모든 필수 산출물 파일이 존재하는가
  - [ ] 각 파일의 내용이 Exit Criteria를 충족하는가
- [ ] 검증 결과를 `docs/sprints/<sprint-id>-verify.md`에 기록
- [ ] 검증 기준 미달 항목이 있으면 G4로 롤백

**Exit Criteria**:
- [ ] `docs/sprints/<sprint-id>-verify.md` 파일이 존재한다
- [ ] 모든 테스트가 통과했다 (또는 WARN 항목으로 등록)
- [ ] 핵심 품질 기준을 충족했다

**필수 Skill**: `test-generator`, `quality-gate`, `code-review`
**담당 Agent**: `skill-auditor` 또는 스프린트별 검증 담당 Agent

---

### G6: Release Review

**목적**: 전체 Gate 진행 상황을 종합 검토하고 PASS/WARN/FAIL 최종 판정을 내린다.

**Entry Criteria**:
- [ ] G5 PASS (검증 완료)

**실행 체크리스트**:
- [ ] G0~G5 각 Gate의 Exit Criteria 충족 여부 재확인
- [ ] 핵심 품질 기준 최종 점검 (스프린트별 기준 -- sprint-plan.md 참조)
- [ ] PASS/WARN/FAIL 판정 결정
- [ ] `docs/sprints/<sprint-id>-release-review.md` 작성:
  - [ ] 전 Gate 판정 결과 요약표
  - [ ] 최종 판정 (PASS / WARN / FAIL)
  - [ ] WARN 항목 이슈 등록 내역 (해당 시)
  - [ ] FAIL 시 롤백 대상 Gate 명시
  - [ ] 후속 액션 목록

**Exit Criteria**:
- [ ] `docs/sprints/<sprint-id>-release-review.md` 파일이 존재한다
- [ ] PASS 또는 WARN 판정이 기록되어 있다 (FAIL 시 롤백 후 재심)

**필수 Skill**: `quality-gate`, `skill-auditor`
**담당 Agent**: `trading-orchestrator-lead` 또는 `skill-auditor`

---

### G7: Full Close-Out

**목적**: 스프린트를 공식적으로 종료한다. 메모리 저장, 회고, git commit, git push 4단계를 반드시 순서대로 완료한다.

**Entry Criteria**:
- [ ] G6 PASS 또는 WARN (Release Review 완료)

**실행 체크리스트**: 아래 섹션 5 상세 절차 참조.

- [ ] Step 1: Memory 저장 완료
- [ ] Step 2: 회고 문서 작성 완료
- [ ] Step 3: git commit 완료
- [ ] Step 4: git push 완료

**Exit Criteria**:
- [ ] `.claude/CLAUDE.md` 프로젝트 메모리가 업데이트되었다
- [ ] `docs/sprints/<sprint-id>-retrospective.md` 파일이 존재한다
- [ ] git commit이 Conventional Commit 형식으로 완료되었다
- [ ] git push가 성공하여 원격에 반영되었다

**필수 Skill**: `sprint-closeout`, `retrospective`
**담당 Agent**: `technical-writer`, `fullstack-developer`

---

## 3. Gate 판정 기준

모든 Gate는 G6 Release Review에서 아래 세 가지 중 하나로 판정된다.

| 판정 | 조건 | 액션 |
|------|------|------|
| **PASS** | 모든 Exit Criteria 100% 충족. 핵심 품질 기준 통과. 테스트 전량 통과. | 다음 Gate로 진행한다. |
| **WARN** | 핵심 기능은 충족하나 비핵심 이슈가 존재한다. (예: 문서 보완 필요, 테스트 커버리지 미달이나 핵심 경로는 통과) | 이슈를 등록하고 다음 Gate로 진행한다. WARN 항목은 다음 스프린트 G0에서 이월 이슈로 추적한다. |
| **FAIL** | 핵심 기준 미달. Exit Criteria의 필수 항목 미충족. 테스트 핵심 경로 실패. | G4(구현 미비 시) 또는 G3(Skill/Agent 부족 시)로 롤백한다. 롤백 후 해당 Gate부터 재실행한다. |

### 판정 결정 흐름

```
모든 Exit Criteria 충족?
  |
  +-- Yes --> 핵심 품질 기준 통과?
  |             |
  |             +-- Yes --> PASS
  |             |
  |             +-- No  --> 비핵심 이슈만? --> Yes --> WARN
  |                                       --> No  --> FAIL
  |
  +-- No  --> 핵심 항목 미충족? --> Yes --> FAIL
                               --> No  --> WARN (비핵심만 미충족)
```

### 스프린트별 핵심 품질 기준 (판정에 활용)

| Sprint | 핵심 기준 |
|--------|---------|
| S0 | Gate 체계 드라이런 PASS, 공백 Skill/Agent 0건 |
| S1 | API 장애 시 재시도/폴백, 캐시 TTL 정책, 지표 재현성 |
| S2 | 안전성 필터 하드게이트(Z>1.81, M<-1.78), 스코어 정규화 일관성 |
| S3 | 레짐 정확도 55%+, 전략 합의 로직 일관성 |
| S4 | Kelly 1/4 강제, 1% 리스크/거래, 단일 8%/섹터 25%, 낙폭 3단계 반영 |
| S5 | full/quick/review 3모드 동작, 부분 실패 허용 + 경고 보고 |
| S6 | PBO<10%, WFE>50%, Sharpe t-stat>2, Look-ahead/survivorship 체크 |
| S7 | 투자 자문 문구 금지, 면책조항 삽입, 인증/레이트리밋 적용 |
| S8 | Signal IC>=0.03, Kelly 효율>=70%, 진단 자동/반영 승인 기반 |
| S9 | 20거래일 Paper 로그, Sharpe>1.0, MDD<10%, 배포 아티팩트 빌드 가능 |

---

## 4. Kanban 연동 규칙

### 커밋 메시지 패턴과 Kanban 상태 변화

커밋 메시지의 scope에 스프린트/Gate 정보를 포함하여 Kanban 상태를 추적한다.

| 커밋 메시지 패턴 | Kanban 상태 변화 | 설명 |
|----------------|----------------|------|
| `feat(sprint-SN/GN): ...` | GN -> Done, G(N+1) -> Todo | Gate 완료, 다음 Gate 대기 |
| `wip(sprint-SN/GN): ...` | GN -> In Progress | Gate 작업 진행 중 |
| `fix(sprint-SN/GN): ...` | GN -> In Progress (재작업) | Gate 내 결함 수정 |
| `chore(sprint-SN/GN): ...` | 상태 변화 없음 | 보조 작업 (설정, 린트 등) |
| `docs(sprint-SN/GN): ...` | GN -> In Progress 또는 Done | 문서화 작업 |

### 커밋 메시지 형식

```
<type>(sprint-<SN>/<GN>): <변경 요약 (한 줄)>

<선택: 본문 상세 설명>
```

**허용 type**: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`

**예시**:

```bash
# G0 완료
git commit -m "feat(sprint-S1/G0): initialize data layer sprint context"

# G4 작업 진행 중
git commit -m "wip(sprint-S2/G4): implement F-Score calculation module"

# G4 완료
git commit -m "feat(sprint-S2/G4): complete 3-axis scoring engine"

# G5 테스트 수정
git commit -m "fix(sprint-S2/G5): correct Z-Score boundary validation"

# G7 Close-Out
git commit -m "docs(sprint-S2/G7): close out scoring engine sprint"
```

### Kanban 보드 상태값

```
Todo  ->  In Progress  ->  Done
 |              |            |
 |              +--- FAIL ---+-- 롤백 시 다시 In Progress로
 |                           |
 +--- WARN 등록 이슈 --------+-- 다음 Sprint G0에서 추적
```

### 상태 전환 규칙

1. G0 Context Init이 완료되면 -> G0 Done, G1 Todo
2. 각 Gate의 Exit Criteria를 모두 충족하면 -> 해당 Gate Done, 다음 Gate Todo
3. FAIL 판정 시 -> 롤백 대상 Gate를 In Progress로 되돌린다
4. G7 Full Close-Out이 완료되면 -> Sprint 전체 Done, 다음 Sprint S(N+1) Todo

---

## 5. G7 Full Close-Out 절차 (모든 스프린트 공통)

G7은 스프린트를 공식적으로 종료하는 최종 Gate다. 아래 4단계를 **반드시 순서대로** 완료해야 한다. 어느 한 단계라도 실패하면 즉시 중단하고 오류를 보고한다. 단계 건너뛰기나 순서 변경은 금지한다.

```
Step 1: Memory 저장
    | (성공 시에만)
    v
Step 2: 회고 문서 작성
    | (성공 시에만)
    v
Step 3: git commit
    | (성공 시에만)
    v
Step 4: git push
```

### Step 1: Memory 저장

**대상 파일**: `.claude/CLAUDE.md` (Trading System Project Memory)

**업데이트 항목**:
- 완료된 기능/태스크 목록 (이번 스프린트에서 추가/변경된 것)
- 새로운 아키텍처 결정 사항 (있을 경우)
- 미해결 이슈 또는 다음 스프린트 이월 항목
- 리스크 한도 또는 전략 변경 사항 (있을 경우)

**실패 기준**: 파일이 존재하지 않거나 Write 작업 실패 시 즉시 중단.

### Step 2: 회고 문서 작성

**대상 파일**: `docs/sprints/<sprint-id>-retrospective.md`

**필수 섹션**:

```markdown
# Sprint <sprint-id> Retrospective

**날짜**: <YYYY-MM-DD>
**스프린트 목표**: <한 줄 목표>
**상태**: CLOSED

## 완료 요약
- 기간: <시작일> ~ <종료일>
- 완료 Gate: G0 ~ G7
- 주요 산출물: <파일 목록>

## 잘한 점
1. ...
2. ...
3. ...

## 개선할 점
1. ...
2. ...
3. ...

## 실패/리스크 기록
- 이슈: <발생한 문제>
- 원인: <근본 원인>
- 재발 방지: <대책>

## 다음 스프린트 액션
1. ...
2. ...
3. ...
```

**실패 기준**: `docs/sprints/` 디렉토리 접근 불가 또는 Write 실패 시 중단. Step 1 결과는 롤백하지 않는다.

### Step 3: git commit

**규칙**:
- 파일 지정 스테이징만 허용 (`git add -A` 절대 금지)
- `.env`, 자격증명, API 키 파일 스테이징 금지
- Conventional Commit 형식 필수

**실행 절차**:

```bash
# 1. 변경 파일 확인
git status

# 2. 스코프 제한 스테이징 (변경된 파일만 개별 지정)
git add .claude/CLAUDE.md
git add docs/sprints/<sprint-id>-context.md
git add docs/sprints/<sprint-id>-skill-matrix.md
git add docs/sprints/<sprint-id>-agent-matrix.md
git add docs/sprints/<sprint-id>-verify.md
git add docs/sprints/<sprint-id>-release-review.md
git add docs/sprints/<sprint-id>-retrospective.md
git add <해당 스프린트에서 변경된 코드/설정 파일들>

# 3. 민감정보 스테이징 여부 재검증
git diff --cached --name-only | grep -E '\.env|credentials|secret|token'
# 위 명령의 출력이 있으면 해당 파일을 git reset HEAD <file>로 제거

# 4. 커밋
git commit -m "docs(sprint-<SN>): close out <sprint description>"
```

**실패 기준**: `git add` 또는 `git commit` 실패 시 중단. `git status` 출력으로 원인 진단.

### Step 4: git push

```bash
git push origin <branch>
```

**실패 기준**: push 실패 시 원인 보고 (네트워크, 권한, 충돌 등 구분). force-push는 사용자의 명시적 승인 없이 절대 금지.

### 실패 처리 프로토콜

| 실패 단계 | 처리 |
|---------|------|
| Step 1 실패 | 즉시 중단. `.claude/CLAUDE.md` 경로와 오류 메시지 출력. |
| Step 2 실패 | 즉시 중단. Step 1 변경 사항은 보존 (롤백 안 함). |
| Step 3 실패 | 즉시 중단. `git status` 출력하여 원인 진단. |
| Step 4 실패 | 즉시 중단. `git push --verbose` 출력 포함 오류 보고. |

**어느 단계에서 실패해도 이미 완료된 단계는 롤백하지 않는다.** 중단 지점과 재시작 방법을 명시한다.

---

## 6. 스킬 매핑 빠른 참조

### Gate 공통 Skill 매핑

| Gate | 필수 Skill | 담당 Agent | 비고 |
|------|-----------|-----------|------|
| G0 | `sprint`, `lead`, `retrospective` | 스프린트 주 오케스트레이터 | 이전 회고 참조 필수 |
| G1 | `skill-auditor`, `task-router` | `skill-auditor` | `.claude/skills/` 전수 스캔 |
| G2 | `lead`, `sprint` | `backend-architect` | Agent 부재 식별 |
| G3 | `skill-creator`, `hub-manager`, `agent-bootstrap` | `backend-architect`, `technical-writer` | 누락 생성 + Hub 동기화 |
| G4 | 스프린트별 핵심 Skill (아래 참조) | 스프린트별 지정 Agent | 핵심 구현 Gate |
| G5 | `test-generator`, `quality-gate`, `code-review` | `skill-auditor` 또는 검증 담당 | 테스트 + 품질 감사 |
| G6 | `quality-gate`, `skill-auditor` | `trading-orchestrator-lead` | 최종 판정 |
| G7 | `sprint-closeout`, `retrospective` | `technical-writer`, `fullstack-developer` | 4단계 강제 종료 |

### 스프린트별 G4 핵심 Skill

| Sprint | G4 핵심 Skill | G4 담당 Agent |
|--------|-------------|--------------|
| S0 | `scaffolding`, `doc-generator` | `fullstack-developer` |
| S1 | `data-ingest` | `data-engineer-agent` |
| S2 | `scoring-engine` | `fundamental/technical/sentiment` 3Agent 병렬 |
| S3 | `regime-detect`, `signal-generate` | 5Agent 병렬 (레짐1 + 전략4) |
| S4 | `position-sizer`, `risk-manager`, `execution-planner`, `bias-checker` | `execution-ops-agent`, `risk-auditor-agent` |
| S5 | `trading-orchestrator`, `scaffolding` | `fullstack-developer` |
| S6 | `backtest-validator` | `backtest-methodology-agent` |
| S7 | `api-designer`, `deployment`, `doc-generator` | `backend-architect`, `technical-writer` |
| S8 | `performance-analyst`, `self-improver` | `performance-attribution-agent` |
| S9 | `integration-tester`, `paper-trading-ops`, `deployment` | `execution-ops-agent` |

---

## 7. 자주 발생하는 블로커 & 해결책

### 블로커 1: 담당 Agent가 존재하지 않는다

**증상**: G0 또는 G2에서 담당 Agent가 `.claude/agents/`에 정의되어 있지 않다.

**해결책**:
1. G0/G3에서만 대행이 허용된다: `fullstack-developer` 또는 `backend-architect`가 대행.
2. G3에서 `agent-bootstrap` Skill로 해당 Agent를 즉시 생성한다.
3. 생성 후 `hub-manager`로 동기화하고, 이후 Gate부터 정식 담당으로 전환한다.

---

### 블로커 2: Skill이 매칭되지 않는 작업이 발견된다

**증상**: G1에서 특정 작업에 매핑할 Skill이 `.claude/skills/`에 없다.

**해결책**:
1. G1에서 공백 Skill 목록에 해당 Skill을 등록한다.
2. G3에서 `skill-creator`를 사용하여 Skill 파일을 생성한다.
3. 생성 순서: Skill 명세 작성 -> Team Agent 지정 -> `hub-manager` 동기화 -> `skill-auditor` 재감사.
4. 재감사에서 누락 0건을 확인한 뒤 G4로 진행한다.

---

### 블로커 3: G5 검증에서 핵심 테스트가 실패한다

**증상**: `pytest` 실행 결과 핵심 경로 테스트가 FAIL이다.

**해결책**:
1. 테스트 실패 로그를 분석하여 근본 원인을 파악한다 (맹목적 재시도 금지).
2. G4로 롤백하여 해당 모듈을 수정한다.
3. 수정 후 G5를 처음부터 재실행한다.
4. 비핵심 테스트 실패는 WARN으로 분류하고 이슈 등록 후 진행 가능하다.

---

### 블로커 4: G7 git push가 실패한다

**증상**: `git push origin <branch>`에서 rejected 오류가 발생한다.

**해결책**:
1. `git pull --rebase origin <branch>`로 원격 변경 사항을 반영한다.
2. 충돌이 있으면 수동으로 해결하고 `git rebase --continue`로 완료한다.
3. 다시 `git push`를 시도한다.
4. **force-push는 사용자의 명시적 승인 없이 절대 금지**한다.
5. 해결 불가 시 오류 메시지 전문과 `git log --oneline -5` 출력을 보고한다.

---

### 블로커 5: 스프린트 중간에 요구사항이 변경된다

**증상**: G4 Build 진행 중에 스프린트 범위를 벗어나는 요청이 들어온다.

**해결책**:
1. 현재 Gate 작업을 먼저 완료한다 (중간 중단 금지).
2. 변경 요청을 다음 스프린트 G0의 이슈로 등록한다.
3. 현재 스프린트의 Context 문서(`<sprint-id>-context.md`)에 "Out of Scope 사유"로 기록한다.
4. 현재 스프린트는 원래 범위대로 완료한다.
5. 긴급 수정이 불가피한 경우에만 G6 Release Review에서 WARN으로 처리하고 이슈 등록한다.

---

## 부록 A: 스프린트 산출물 체크리스트 (G7 전 최종 점검용)

매 스프린트 종료 시 아래 파일이 모두 존재해야 한다.

```
docs/sprints/<sprint-id>-context.md          # G0 산출물
docs/sprints/<sprint-id>-skill-matrix.md     # G1 산출물 (또는 -skill-check.md)
docs/sprints/<sprint-id>-agent-matrix.md     # G2 산출물 (또는 -agent-plan.md)
docs/sprints/<sprint-id>-verify.md           # G5 산출물
docs/sprints/<sprint-id>-release-review.md   # G6 산출물
docs/sprints/<sprint-id>-retrospective.md    # G7 산출물
```

추가로 메모리 업데이트가 완료되어야 한다:

```
.claude/CLAUDE.md                            # 프로젝트 메모리 (업데이트)
```

## 부록 B: Gate 문서 템플릿 참조

각 Gate의 상세 실행 로그를 기록할 때는 `docs/sprints/TEMPLATE-gate.md` 를 사용한다.
스프린트 회고 작성 시에는 `docs/sprints/TEMPLATE-retrospective.md` 를 사용한다.
G7 Close-Out 체크 시에는 `docs/sprints/TEMPLATE-closeout.md` 를 사용한다.
