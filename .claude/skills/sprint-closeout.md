---
name: sprint-closeout
description: "Full Sprint Close-Out 강제 워크플로를 실행합니다. 메모리 저장 → 회고 작성 → git commit → git push 4단계를 순서대로 강제 수행합니다."
argument-hint: "[sprint-id] [--message 'commit message']"
user-invocable: true
allowed-tools: "Read, Write, Bash, Grep"
---

# Sprint Close-Out Skill

> Full Sprint Close-Out 강제 워크플로 코디네이터. 4단계를 순서대로 빠짐없이 실행합니다.

## 역할

스프린트 완료 시점에 반드시 수행해야 하는 4단계 마감 워크플로를 강제합니다.
어느 한 단계라도 실패하면 즉시 중단하고 오류를 보고합니다.
단계 건너뛰기나 순서 변경은 허용하지 않습니다.

## 4단계 강제 워크플로

```
Step 1: MEMORY.md 업데이트
    ↓ 성공 시에만
Step 2: 회고 문서 생성
    ↓ 성공 시에만
Step 3: git commit (Conventional Commit)
    ↓ 성공 시에만
Step 4: git push
```

### Step 1. MEMORY.md 업데이트

파일: `.claude/CLAUDE.md` (Trading System Project Memory)

업데이트 항목:
- 완료된 기능/태스크 목록
- 미해결 이슈 또는 다음 스프린트 이월 항목
- 새로운 아키텍처 결정 사항 (있을 경우)
- 리스크 한도 또는 전략 변경 사항 (있을 경우)

실패 기준: 파일이 존재하지 않거나 Write 작업 실패 시 중단.

### Step 2. 회고 문서 생성

파일 경로: `docs/sprints/<sprint-id>-retrospective.md`

예: `docs/sprints/S0-G3-retrospective.md`

**회고 문서 표준 포맷**:
```markdown
# Sprint <sprint-id> Retrospective

**날짜**: <YYYY-MM-DD>
**스프린트 목표**: <한 줄 목표>
**상태**: CLOSED

## 완료된 작업

| 태스크 | 설명 | 결과 |
|--------|------|------|
| ... | ... | DONE |

## 미완료 / 이월

| 태스크 | 이유 | 다음 스프린트 |
|--------|------|-------------|
| ... | ... | ... |

## 잘한 점
- ...

## 개선점
- ...

## 다음 스프린트 액션 아이템
1. ...

## ADR (아키텍처 결정 기록)

### ADR-<N>: <제목>
- **결정**: ...
- **이유**: ...
- **트레이드오프**: ...
```

실패 기준: `docs/sprints/` 디렉토리 생성 불가 또는 Write 실패 시 중단.

### Step 3. git commit

**규칙**:
- Conventional Commit 형식 필수: `type(scope): message`
- 허용 type: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`
- 파일 지정 스테이징 필수 (`git add -A` 절대 금지)
- `.env` 파일 스테이징 금지

**스테이징 대상 (명시적 지정)**:
```bash
git add .claude/CLAUDE.md
git add docs/sprints/<sprint-id>-retrospective.md
git add <sprint에서 변경된 코드 파일들>
```

**커밋 메시지 예시**:
```
docs(sprint): close out S0-G3 bootstrap sprint

- Add agent-bootstrap, sprint-closeout, integration-tester, paper-trading-ops skills
- Update project memory with S0-G3 completion
- Add S0-G3 retrospective document
```

실패 기준: `git add` 또는 `git commit` 실패 시 중단.

### Step 4. git push

```bash
git push origin main
```

실패 기준: push 실패 시 원인 보고 (네트워크, 권한, 충돌 등 구분).
force-push는 명시적 사용자 승인 없이 절대 금지.

## 실패 처리 프로토콜

| 실패 단계 | 처리 |
|---------|------|
| Step 1 실패 | 즉시 중단, MEMORY.md 경로와 오류 메시지 출력 |
| Step 2 실패 | 즉시 중단, Step 1 변경 사항은 보존 (롤백 안 함) |
| Step 3 실패 | 즉시 중단, git status 출력하여 원인 진단 |
| Step 4 실패 | 즉시 중단, `git push --verbose` 출력 포함 오류 보고 |

**어느 단계에서 실패해도 이미 완료된 단계는 롤백하지 않습니다.**
중단 지점과 재시작 방법을 명시합니다.

## 출력 포맷

```json
{
  "skill": "sprint-closeout",
  "status": "success",
  "data": {
    "sprint_id": "S0-G3",
    "steps": {
      "step1_memory_update": { "status": "done", "file": ".claude/CLAUDE.md" },
      "step2_retrospective": { "status": "done", "file": "docs/sprints/S0-G3-retrospective.md" },
      "step3_git_commit": { "status": "done", "commit_hash": "abc1234", "message": "docs(sprint): close out S0-G3" },
      "step4_git_push": { "status": "done", "branch": "main", "remote": "origin" }
    },
    "completed_at": "2026-03-03T12:00:00Z"
  }
}
```

## 제약 조건

- 4단계 중 하나라도 실패 시 즉시 중단하고 오류를 보고한다
- `git add -A` 사용을 절대 금지한다 — 파일을 명시적으로 지정해야 한다
- `.env`, 자격증명, API 키가 포함된 파일을 스테이징하지 않는다
- force-push는 사용자의 명시적 승인 없이 금지한다
- published commit을 amend하지 않는다
- 회고 문서는 `docs/sprints/<sprint-id>-retrospective.md` 경로를 반드시 준수한다

## 참조 문서

- `.claude/CLAUDE.md` — 프로젝트 메모리 (업데이트 대상)
- `.claude/rules/workflow.md` — Git Discipline 규칙
- `.claude/rules/retrospective.md` — 회고 작성 원칙
- `docs/sprints/` — 이전 스프린트 회고 참조
