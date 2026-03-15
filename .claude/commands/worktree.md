---
description: Claude용 격리 worktree 작업환경을 생성합니다
---

# /worktree

Claude가 메인 작업트리를 건드리지 않고 별도 브랜치/경로에서 작업할 수 있게
표준 worktree 환경을 생성합니다.

## 사용법

```bash
/worktree <name>
/worktree <name> --base main
/worktree <name> --detach
/worktree <name> --env example --venv create
```

## 기본 동작

- 경로: `~/.claude-worktrees/<repo-name>/<slug>`
- 브랜치: `codex/claude-<slug>`
- `.env`: 루트 `.env`를 링크, 없으면 `.env.example` 복사
- `.claude/settings.local.json`: 링크
- `.venv`: 루트 `.venv`를 링크

## 옵션

- `--base <ref>`: 기준 브랜치/커밋 지정
- `--path <dir>`: 생성 경로 직접 지정
- `--branch <name>`: 브랜치명 직접 지정
- `--detach`: detached HEAD worktree 생성
- `--env link|copy|example|skip`: 환경파일 처리 방식
- `--venv link|create|skip`: 가상환경 처리 방식
- `--force`: 기존 빈 디렉터리 사용 허용
- `--dry-run`: 실제 생성 없이 명령만 출력

## 실행 절차

1. `bash .claude/scripts/create-worktree.sh $ARGUMENTS`
2. 생성된 경로와 브랜치 정보를 보고
3. `cd <path>` 후 Claude 실행 안내

$ARGUMENTS
