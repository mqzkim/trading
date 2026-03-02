#!/usr/bin/env bash
# kanban-sprint-sync.sh — PostToolUse(Bash) hook
# git commit 패턴을 파싱하여 Kanban 상태를 자동 업데이트
#
# 지원 패턴:
#   feat(sprint-S0/G4): ...  → G4 Done, G5 In Progress
#   chore(sprint-S0/G7): ... → G7 Done (스프린트 완료)
#   wip(sprint-S0/G4): ...   → G4 In Progress

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAP_FILE="$SCRIPT_DIR/../sprint-kanban-map.json"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# stdin에서 tool_input 읽기
INPUT=$(cat 2>/dev/null)
if [ -z "$INPUT" ]; then exit 0; fi

# bash 명령어 추출
COMMAND=$(echo "$INPUT" | node -e "
  let data='';
  process.stdin.on('data',c=>data+=c);
  process.stdin.on('end',()=>{
    try {
      const input = JSON.parse(data);
      console.log(input.tool_input?.command || '');
    } catch { console.log(''); }
  });
" 2>/dev/null)

# git commit 명령인지 확인
if ! echo "$COMMAND" | grep -qE "git commit"; then
  exit 0
fi

# 최신 커밋 메시지 읽기
COMMIT_MSG=$(git -C "$REPO_ROOT" log -1 --pretty=%s 2>/dev/null)
if [ -z "$COMMIT_MSG" ]; then exit 0; fi

# 패턴 매칭: feat|fix|chore|wip(sprint-SN/GN): 또는 feat(sprint-SN):
SPRINT_ID=$(echo "$COMMIT_MSG" | grep -oP '(?<=sprint-)[A-Z][0-9]+(?=[/)])' 2>/dev/null)
GATE_ID=$(echo "$COMMIT_MSG" | grep -oP '(?<=/)[A-Z][0-9]+(?=\))' 2>/dev/null)

if [ -z "$SPRINT_ID" ]; then exit 0; fi

# 매핑 파일에서 item_id 조회
PROJECT_ID=$(node -e "const m=require('$MAP_FILE'); console.log(m._meta.project_id);" 2>/dev/null)
STATUS_FIELD=$(node -e "const m=require('$MAP_FILE'); console.log(m._meta.status_field_id);" 2>/dev/null)
DONE_OPT=$(node -e "const m=require('$MAP_FILE'); console.log(m._meta.status_options.Done);" 2>/dev/null)
IN_PROGRESS_OPT=$(node -e "const m=require('$MAP_FILE'); console.log(m._meta.status_options['In Progress']);" 2>/dev/null)
TODO_OPT=$(node -e "const m=require('$MAP_FILE'); console.log(m._meta.status_options.Todo);" 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then exit 0; fi

# Gate 지정 커밋: SN/GN 패턴
if [ -n "$GATE_ID" ]; then
  ITEM_ID=$(node -e "
    const m=require('$MAP_FILE');
    const sprint=m.sprints['$SPRINT_ID'];
    if(sprint && sprint.gates['$GATE_ID']) {
      console.log(sprint.gates['$GATE_ID'].item_id);
    }
  " 2>/dev/null)

  if [ -n "$ITEM_ID" ]; then
    # wip 커밋: In Progress
    if echo "$COMMIT_MSG" | grep -qiE "^wip\("; then
      gh project item-edit \
        --project-id "$PROJECT_ID" \
        --id "$ITEM_ID" \
        --field-id "$STATUS_FIELD" \
        --single-select-option-id "$IN_PROGRESS_OPT" 2>/dev/null
      echo "[kanban-sync] $SPRINT_ID/$GATE_ID → In Progress"
    else
      # 일반 커밋: Done으로 이동
      gh project item-edit \
        --project-id "$PROJECT_ID" \
        --id "$ITEM_ID" \
        --field-id "$STATUS_FIELD" \
        --single-select-option-id "$DONE_OPT" 2>/dev/null
      echo "[kanban-sync] $SPRINT_ID/$GATE_ID → Done"

      # 다음 Gate를 Todo로 이동
      NEXT_GATE=$(node -e "
        const m=require('$MAP_FILE');
        const sprint=m.sprints['$SPRINT_ID'];
        if(!sprint) process.exit(0);
        const gates=Object.keys(sprint.gates);
        const idx=gates.indexOf('$GATE_ID');
        if(idx>=0 && idx+1<gates.length) {
          console.log(JSON.stringify({gate:gates[idx+1], item_id:sprint.gates[gates[idx+1]].item_id}));
        }
      " 2>/dev/null)

      if [ -n "$NEXT_GATE" ]; then
        NEXT_ITEM_ID=$(echo "$NEXT_GATE" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>console.log(JSON.parse(d).item_id));" 2>/dev/null)
        NEXT_GATE_NAME=$(echo "$NEXT_GATE" | node -e "let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>console.log(JSON.parse(d).gate));" 2>/dev/null)
        if [ -n "$NEXT_ITEM_ID" ]; then
          gh project item-edit \
            --project-id "$PROJECT_ID" \
            --id "$NEXT_ITEM_ID" \
            --field-id "$STATUS_FIELD" \
            --single-select-option-id "$TODO_OPT" 2>/dev/null
          echo "[kanban-sync] $SPRINT_ID/$NEXT_GATE_NAME → Todo (next gate)"
        fi
      fi
    fi
  fi
fi

exit 0
