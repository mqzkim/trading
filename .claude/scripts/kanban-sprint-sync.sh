#!/usr/bin/env bash
# kanban-sprint-sync.sh — PostToolUse(Bash) hook
# git commit 패턴 감지 → Kanban 업데이트 + 브랜치 생성 + PR 자동 생성
#
# 커밋 패턴:
#   wip(sprint-SN/GN): ...   → 브랜치 claude/sprint-SN/GN 생성 + GN In Progress
#   feat(sprint-SN/GN): ...  → GN Done + 다음 Gate Todo + PR 자동 생성
#   chore(sprint-SN/GN): ... → 위와 동일 (G7 close-out용)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAP_FILE="$SCRIPT_DIR/../sprint-kanban-map.json"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
LOG_FILE="$SCRIPT_DIR/kanban-sync.log"

log() { echo "[$(date '+%H:%M:%S')] $*" >> "$LOG_FILE"; }

# stdin에서 tool_input 읽기
INPUT=$(cat 2>/dev/null || true)
if [ -z "$INPUT" ]; then exit 0; fi

# bash 명령어 추출
COMMAND=$(echo "$INPUT" | node -e "
  let d='';
  process.stdin.on('data',c=>d+=c);
  process.stdin.on('end',()=>{
    try { const i=JSON.parse(d); console.log(i.tool_input?.command||''); }
    catch { console.log(''); }
  });
" 2>/dev/null || true)

# git commit/push 명령만 처리
if ! echo "$COMMAND" | grep -qE "git (commit|push)"; then
  exit 0
fi

log "Detected git command: $(echo "$COMMAND" | head -c 80)"

# 최신 커밋 메시지 읽기
COMMIT_MSG=$(git -C "$REPO_ROOT" log -1 --pretty=%s 2>/dev/null || true)
if [ -z "$COMMIT_MSG" ]; then exit 0; fi

log "Commit msg: $COMMIT_MSG"

# 패턴 매칭
SPRINT_ID=$(echo "$COMMIT_MSG" | grep -oP '(?<=sprint-)[A-Z][0-9]+(?=[/)])' 2>/dev/null || true)
GATE_ID=$(echo "$COMMIT_MSG"   | grep -oP '(?<=/)[A-Z][0-9]+(?=\))'         2>/dev/null || true)

if [ -z "$SPRINT_ID" ] || [ -z "$GATE_ID" ]; then
  exit 0
fi

log "Parsed: $SPRINT_ID/$GATE_ID"

# 매핑 파일 확인
if [ ! -f "$MAP_FILE" ]; then
  log "ERROR: MAP_FILE not found: $MAP_FILE"
  exit 0
fi

# 메타 정보 로드
PROJECT_ID=$(node -e "const m=require('$MAP_FILE'); console.log(m._meta.project_id);" 2>/dev/null || true)
STATUS_FIELD=$(node -e "const m=require('$MAP_FILE'); console.log(m._meta.status_field_id);" 2>/dev/null || true)
DONE_OPT=$(node -e "const m=require('$MAP_FILE'); console.log(m._meta.status_options.Done);" 2>/dev/null || true)
IN_PROGRESS_OPT=$(node -e "const m=require('$MAP_FILE'); console.log(m._meta.status_options['In Progress']);" 2>/dev/null || true)
TODO_OPT=$(node -e "const m=require('$MAP_FILE'); console.log(m._meta.status_options.Todo);" 2>/dev/null || true)
REPO=$(node -e "const m=require('$MAP_FILE'); console.log(m._meta.repo);" 2>/dev/null || true)

if [ -z "$PROJECT_ID" ]; then
  log "ERROR: Failed to load project metadata"
  exit 0
fi

# Gate 정보 조회
GATE_INFO=$(node -e "
  const m=require('$MAP_FILE');
  const sprint=m.sprints['$SPRINT_ID'];
  if(sprint && sprint.gates['$GATE_ID']) {
    console.log(JSON.stringify(sprint.gates['$GATE_ID']));
  }
" 2>/dev/null || true)

if [ -z "$GATE_INFO" ]; then
  log "WARN: No mapping for $SPRINT_ID/$GATE_ID"
  exit 0
fi

ITEM_ID=$(echo "$GATE_INFO" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>console.log(JSON.parse(d).item_id||''));" 2>/dev/null || true)
ISSUE_NUM=$(echo "$GATE_INFO" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>console.log(JSON.parse(d).issue||''));" 2>/dev/null || true)
BRANCH_NAME="claude/sprint-${SPRINT_ID}/${GATE_ID}"
CURRENT_BRANCH=$(git -C "$REPO_ROOT" branch --show-current 2>/dev/null || true)

# ──────────────────────────────────────────
# wip 커밋: 브랜치 생성 + In Progress
# ──────────────────────────────────────────
if echo "$COMMIT_MSG" | grep -qiE "^wip\("; then
  # 브랜치가 없으면 생성
  if [ "$CURRENT_BRANCH" != "$BRANCH_NAME" ]; then
    git -C "$REPO_ROOT" checkout -b "$BRANCH_NAME" 2>/dev/null || \
    git -C "$REPO_ROOT" checkout "$BRANCH_NAME" 2>/dev/null || true
    log "Branch created/checked-out: $BRANCH_NAME"
  fi

  gh project item-edit \
    --project-id "$PROJECT_ID" \
    --id "$ITEM_ID" \
    --field-id "$STATUS_FIELD" \
    --single-select-option-id "$IN_PROGRESS_OPT" 2>/dev/null || true

  log "$SPRINT_ID/$GATE_ID → In Progress"
  echo "[kanban-sync] $SPRINT_ID/$GATE_ID → In Progress (branch: $BRANCH_NAME)"
  exit 0
fi

# ──────────────────────────────────────────
# feat/chore/fix 커밋: Done + 다음 Gate Todo + PR 생성
# ──────────────────────────────────────────

# 1) Kanban: 현재 Gate → Done
gh project item-edit \
  --project-id "$PROJECT_ID" \
  --id "$ITEM_ID" \
  --field-id "$STATUS_FIELD" \
  --single-select-option-id "$DONE_OPT" 2>/dev/null || true
log "$SPRINT_ID/$GATE_ID → Done"

# 2) 다음 Gate → Todo
NEXT_INFO=$(node -e "
  const m=require('$MAP_FILE');
  const sprint=m.sprints['$SPRINT_ID'];
  if(!sprint) process.exit(0);
  const gates=Object.keys(sprint.gates);
  const idx=gates.indexOf('$GATE_ID');
  if(idx>=0 && idx+1<gates.length){
    const next=gates[idx+1];
    console.log(JSON.stringify({gate:next, ...sprint.gates[next]}));
  }
" 2>/dev/null || true)

if [ -n "$NEXT_INFO" ]; then
  NEXT_ITEM_ID=$(echo "$NEXT_INFO" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>console.log(JSON.parse(d).item_id||''));" 2>/dev/null || true)
  NEXT_GATE=$(echo "$NEXT_INFO"    | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>console.log(JSON.parse(d).gate||''));" 2>/dev/null || true)
  if [ -n "$NEXT_ITEM_ID" ]; then
    gh project item-edit \
      --project-id "$PROJECT_ID" \
      --id "$NEXT_ITEM_ID" \
      --field-id "$STATUS_FIELD" \
      --single-select-option-id "$TODO_OPT" 2>/dev/null || true
    log "$SPRINT_ID/$NEXT_GATE → Todo"
  fi
fi

# 3) feature 브랜치인 경우 → PR 자동 생성
if echo "$CURRENT_BRANCH" | grep -qE "^claude/sprint-"; then
  # 브랜치 push (PR 생성 전 필요)
  git -C "$REPO_ROOT" push -u origin "$CURRENT_BRANCH" 2>/dev/null || true

  # PR 제목 = 커밋 메시지 첫 줄
  PR_TITLE="$COMMIT_MSG"
  PR_BODY="## Sprint $SPRINT_ID — Gate $GATE_ID

$(git -C "$REPO_ROOT" log -1 --pretty=%b 2>/dev/null || true)

---
Closes #$ISSUE_NUM

🤖 Auto-generated by kanban-sprint-sync"

  PR_URL=$(gh pr create \
    --repo "$REPO" \
    --title "$PR_TITLE" \
    --body "$PR_BODY" \
    --base main \
    --head "$CURRENT_BRANCH" \
    --label "sprint" 2>/dev/null || true)

  if [ -n "$PR_URL" ]; then
    log "PR created: $PR_URL"
    echo "[kanban-sync] PR created: $PR_URL"
  fi
else
  # main 직접 커밋 (S0처럼 브랜치 없는 경우) → push만
  git -C "$REPO_ROOT" push origin main 2>/dev/null || true
  log "Direct push to main (no branch)"
fi

echo "[kanban-sync] $SPRINT_ID/$GATE_ID → Done${NEXT_GATE:+ | $SPRINT_ID/$NEXT_GATE → Todo}"
exit 0
