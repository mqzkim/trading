#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  .agents/scripts/create-worktree.sh <name> [options]

Options:
  --base <ref>           Base ref to create from (default: main)
  --path <dir>           Explicit worktree path
  --branch <name>        Explicit branch name
  --detach               Create a detached worktree instead of a branch
  --env <mode>           link|copy|example|skip (default: link)
  --venv <mode>          link|create|skip (default: link)
  --force                Allow an existing empty target directory
  --dry-run              Print actions without executing
  -h, --help             Show this help

Defaults:
  Worktree root: $CODEX_WORKTREE_ROOT or ~/.codex-worktrees/<repo-name>/
  Branch name : codex/worktree-<slug>
EOF
}

log() {
  printf '[codex-worktree] %s\n' "$*"
}

fail() {
  printf '[codex-worktree] ERROR: %s\n' "$*" >&2
  exit 1
}

slugify() {
  printf '%s' "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//; s/-+/-/g'
}

run() {
  if [ "$DRY_RUN" -eq 1 ]; then
    printf '+'
    for arg in "$@"; do
      printf ' %q' "$arg"
    done
    printf '\n'
    return 0
  fi

  "$@"
}

ensure_parent_dir() {
  local target="$1"
  local parent

  parent="$(dirname "$target")"
  if [ ! -d "$parent" ]; then
    run mkdir -p "$parent"
  fi
}

link_or_copy() {
  local label="$1"
  local source="$2"
  local target="$3"
  local mode="$4"

  if [ -e "$target" ] || [ -L "$target" ]; then
    log "skip $label: already exists at $target"
    return 0
  fi

  case "$mode" in
    link)
      if [ -e "$source" ] || [ -L "$source" ]; then
        ensure_parent_dir "$target"
        run ln -s "$source" "$target"
        log "$label linked -> $source"
      else
        log "skip $label: source not found at $source"
      fi
      ;;
    copy)
      if [ -f "$source" ]; then
        ensure_parent_dir "$target"
        run cp "$source" "$target"
        log "$label copied from $source"
      else
        log "skip $label: source not found at $source"
      fi
      ;;
    skip)
      log "skip $label"
      ;;
    *)
      fail "unsupported mode '$mode' for $label"
      ;;
  esac
}

python_bin() {
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi

  if command -v python >/dev/null 2>&1; then
    command -v python
    return 0
  fi

  return 1
}

NAME=""
BASE_REF="main"
WORKTREE_PATH=""
BRANCH_NAME=""
DETACH=0
ENV_MODE="link"
VENV_MODE="link"
FORCE=0
DRY_RUN=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --base)
      [ "$#" -ge 2 ] || fail "--base requires a value"
      BASE_REF="$2"
      shift 2
      ;;
    --path)
      [ "$#" -ge 2 ] || fail "--path requires a value"
      WORKTREE_PATH="$2"
      shift 2
      ;;
    --branch)
      [ "$#" -ge 2 ] || fail "--branch requires a value"
      BRANCH_NAME="$2"
      shift 2
      ;;
    --detach)
      DETACH=1
      shift
      ;;
    --env)
      [ "$#" -ge 2 ] || fail "--env requires a value"
      ENV_MODE="$2"
      shift 2
      ;;
    --venv)
      [ "$#" -ge 2 ] || fail "--venv requires a value"
      VENV_MODE="$2"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      fail "unknown option: $1"
      ;;
    *)
      if [ -n "$NAME" ]; then
        fail "only one worktree name can be provided"
      fi
      NAME="$1"
      shift
      ;;
  esac
done

[ -n "$NAME" ] || {
  usage
  exit 1
}

case "$ENV_MODE" in
  link|copy|example|skip) ;;
  *)
    fail "--env must be one of: link, copy, example, skip"
    ;;
esac

case "$VENV_MODE" in
  link|create|skip) ;;
  *)
    fail "--venv must be one of: link, create, skip"
    ;;
esac

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || fail "not inside a git repository"
REPO_NAME="$(basename "$REPO_ROOT")"
SLUG="$(slugify "$NAME")"
[ -n "$SLUG" ] || fail "name '$NAME' produced an empty slug"

DEFAULT_ROOT="${CODEX_WORKTREE_ROOT:-$HOME/.codex-worktrees/$REPO_NAME}"
WORKTREE_PATH="${WORKTREE_PATH:-$DEFAULT_ROOT/$SLUG}"

if [ "$DETACH" -eq 0 ]; then
  BRANCH_NAME="${BRANCH_NAME:-codex/worktree-$SLUG}"
fi

if [ -e "$WORKTREE_PATH" ]; then
  if [ "$FORCE" -ne 1 ]; then
    fail "target path already exists: $WORKTREE_PATH"
  fi

  if [ -n "$(find "$WORKTREE_PATH" -mindepth 1 -maxdepth 1 2>/dev/null | head -n 1)" ]; then
    fail "--force only supports an existing empty directory: $WORKTREE_PATH"
  fi
fi

run mkdir -p "$(dirname "$WORKTREE_PATH")"

if [ "$DETACH" -eq 1 ]; then
  run git -C "$REPO_ROOT" worktree add --detach "$WORKTREE_PATH" "$BASE_REF"
else
  if git -C "$REPO_ROOT" show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
    fail "branch already exists: $BRANCH_NAME"
  fi
  run git -C "$REPO_ROOT" worktree add -b "$BRANCH_NAME" "$WORKTREE_PATH" "$BASE_REF"
fi

SOURCE_ENV="$REPO_ROOT/.env"
SOURCE_ENV_EXAMPLE="$REPO_ROOT/.env.example"
TARGET_ENV="$WORKTREE_PATH/.env"

case "$ENV_MODE" in
  example)
    link_or_copy ".env" "$SOURCE_ENV_EXAMPLE" "$TARGET_ENV" "copy"
    ;;
  link|copy|skip)
    if [ "$ENV_MODE" != "skip" ] && [ ! -f "$SOURCE_ENV" ] && [ -f "$SOURCE_ENV_EXAMPLE" ]; then
      log ".env not found in repo root, falling back to .env.example"
      link_or_copy ".env" "$SOURCE_ENV_EXAMPLE" "$TARGET_ENV" "copy"
    else
      link_or_copy ".env" "$SOURCE_ENV" "$TARGET_ENV" "$ENV_MODE"
    fi
    ;;
esac

case "$VENV_MODE" in
  link)
    link_or_copy ".venv" "$REPO_ROOT/.venv" "$WORKTREE_PATH/.venv" "link"
    ;;
  create)
    if [ -e "$WORKTREE_PATH/.venv" ] || [ -L "$WORKTREE_PATH/.venv" ]; then
      log "skip .venv: already exists at $WORKTREE_PATH/.venv"
    else
      PYTHON="$(python_bin)" || fail "python3/python not found for --venv create"
      run "$PYTHON" -m venv "$WORKTREE_PATH/.venv"
      if [ "$DRY_RUN" -eq 0 ]; then
        run "$WORKTREE_PATH/.venv/bin/pip" install --upgrade pip
        if [ -f "$WORKTREE_PATH/requirements.txt" ]; then
          run "$WORKTREE_PATH/.venv/bin/pip" install -r "$WORKTREE_PATH/requirements.txt"
        fi
        if [ -f "$WORKTREE_PATH/requirements-dev.txt" ]; then
          run "$WORKTREE_PATH/.venv/bin/pip" install -r "$WORKTREE_PATH/requirements-dev.txt"
        fi
      fi
      log ".venv created in worktree"
    fi
    ;;
  skip)
    log "skip .venv"
    ;;
esac

printf '\n'
log "ready"
printf '  repo   : %s\n' "$REPO_ROOT"
printf '  path   : %s\n' "$WORKTREE_PATH"
if [ "$DETACH" -eq 1 ]; then
  printf '  branch : detached (%s)\n' "$BASE_REF"
else
  printf '  branch : %s\n' "$BRANCH_NAME"
fi
printf '\n'
printf 'Next steps:\n'
printf '  cd %q\n' "$WORKTREE_PATH"
printf '  codex\n'
printf '\n'
printf 'Cleanup:\n'
printf '  git -C %q worktree remove --force %q\n' "$REPO_ROOT" "$WORKTREE_PATH"
if [ "$DETACH" -eq 0 ]; then
  printf '  git -C %q branch -D %q\n' "$REPO_ROOT" "$BRANCH_NAME"
fi
