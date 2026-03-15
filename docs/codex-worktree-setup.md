# Codex Worktree Setup

이 저장소에서 Codex 작업을 메인 작업트리와 분리하려면
`.agents/scripts/create-worktree.sh`를 사용한다.

## 무엇이 준비되나

- Git worktree 생성
- 기본 브랜치명 `codex/worktree-<slug>` 적용
- 루트 `.env` 링크, 없으면 `.env.example` 복사
- 루트 `.venv` 링크 또는 독립 가상환경 생성
- `AGENTS.md`, `.agents/`는 Git tracked 자산이라 worktree에 자동 포함

## 기본 생성

```bash
bash .agents/scripts/create-worktree.sh scoring-refactor
```

기본값:

- worktree 경로: `~/.codex-worktrees/trading/scoring-refactor`
- 브랜치: `codex/worktree-scoring-refactor`
- `.env`: 루트 `.env` 링크, 없으면 `.env.example` 복사
- `.venv`: 루트 `.venv` 링크

## 자주 쓰는 예시

새 브랜치로 바로 작업:

```bash
bash .agents/scripts/create-worktree.sh api-hardening
```

기준 브랜치를 바꿔서 생성:

```bash
bash .agents/scripts/create-worktree.sh regime-update --base origin/main
```

실제 브랜치 없이 검증 전용 worktree 생성:

```bash
bash .agents/scripts/create-worktree.sh verify-run --detach --env example --venv skip
```

독립 가상환경 생성:

```bash
bash .agents/scripts/create-worktree.sh research-sandbox --venv create
```

## Codex 앱 기본 worktree와의 차이

Codex 앱은 내부적으로 `C:/Users/USER/.codex/worktrees/...` 아래 임시 worktree를 만들 수 있다.
이 스크립트는 그 내부 경로와 충돌하지 않도록 `~/.codex-worktrees/...` 아래에
지속적으로 재사용할 수 있는 수동 worktree를 만든다.

## 정리

```bash
git -C "$(git rev-parse --show-toplevel)" worktree remove --force ~/.codex-worktrees/trading/scoring-refactor
git -C "$(git rev-parse --show-toplevel)" branch -D codex/worktree-scoring-refactor
```

`.env`, `.venv` 같은 비추적 링크가 생기므로 `worktree remove --force`를 사용한다.
