# Claude Worktree Setup

이 저장소에서 Claude 작업을 메인 작업트리와 분리하려면
`.claude/scripts/create-worktree.sh`를 사용한다.

## 왜 필요한가

- 메인 작업 디렉터리를 오염시키지 않음
- 브랜치별 실험과 검증을 분리할 수 있음
- `.env`, `.venv`, Claude 로컬 설정을 빠르게 재사용할 수 있음
- `.claude/settings.json` 훅이 worktree 경로를 자동 인식하므로 메인 경로 하드코딩 문제가 없음

## 기본 생성

```bash
bash .claude/scripts/create-worktree.sh scoring-refactor
```

기본값:

- worktree 경로: `~/.claude-worktrees/trading/scoring-refactor`
- 브랜치: `codex/claude-scoring-refactor`
- `.env`: 루트 `.env` 링크, 없으면 `.env.example` 복사
- `.claude/settings.local.json`: 루트 파일 링크
- `.venv`: 루트 `.venv` 링크

## 자주 쓰는 예시

새 브랜치로 바로 작업:

```bash
bash .claude/scripts/create-worktree.sh api-hardening
```

기준 브랜치를 바꿔서 생성:

```bash
bash .claude/scripts/create-worktree.sh regime-update --base origin/main
```

실제 브랜치 없이 검증 전용 worktree 생성:

```bash
bash .claude/scripts/create-worktree.sh verify-run --detach --env example --venv skip
```

독립 가상환경 생성:

```bash
bash .claude/scripts/create-worktree.sh research-sandbox --venv create
```

## 정리

생성된 worktree 제거:

```bash
git -C "$(git rev-parse --show-toplevel)" worktree remove --force ~/.claude-worktrees/trading/scoring-refactor
git -C "$(git rev-parse --show-toplevel)" branch -D codex/claude-scoring-refactor
```

스크립트는 실행 후 정확한 정리 명령도 함께 출력한다.
