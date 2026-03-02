# /kanban — 프로젝트 칸반 보드 관리

GitHub Projects 칸반 보드를 조회·관리합니다.

## 사용법

- `/kanban` — 전체 현황 대시보드
- `/kanban list [project]` — 프로젝트별 이슈 목록
- `/kanban add <title> --project <name> --priority <level>` — 이슈 생성
- `/kanban start <issue-number>` — 이슈 작업 시작 (브랜치 생성 + 보드 In Progress 이동)
- `/kanban done <issue-number>` — 이슈 완료 처리 (PR 생성 + 보드 In Review 이동)
- `/kanban web` — 웹 보드 열기

## 환경 정보

- **Owner:** mqzkim
- **Repo:** mqzkim/local-workspace
- **Project Number:** 1
- **Project ID:** PVT_kwHOAJ7Yb84BQfi9

### Status 필드 (ID: PVTSSF_lAHOAJ7Yb84BQfi9zg-mHx4)
| 컬럼 | Option ID |
|------|-----------|
| Backlog | bc3cbeb4 |
| Todo | 3e5ed4c7 |
| In Progress | c6a8fecd |
| In Review | 572d115c |
| Done | 1cad29c3 |

### 커스텀 필드 ID
| 필드 | ID |
|------|-----|
| Project | PVTSSF_lAHOAJ7Yb84BQfi9zg-mHzs |
| Priority | PVTSSF_lAHOAJ7Yb84BQfi9zg-mH1E |
| Type | PVTSSF_lAHOAJ7Yb84BQfi9zg-mH2c |
| Effort | PVTF_lAHOAJ7Yb84BQfi9zg-mH3w |

## 실행

$ARGUMENTS 를 파싱하여 아래 분기를 따릅니다:

### 인자 없음 (대시보드)
1. `bash scripts/kanban-status.sh` 실행
2. 결과를 사용자에게 보여줌

### `list [project]`
1. project 인자가 있으면: `gh issue list --repo mqzkim/local-workspace --label "project:<project>" --state open --json number,title,labels`
2. 없으면: `gh issue list --repo mqzkim/local-workspace --state open --json number,title,labels`
3. 우선순위별 정렬하여 출력

### `add <title> --project <name> --priority <level>`
1. `gh issue create --repo mqzkim/local-workspace --title "<title>" --label "project:<name>,priority:<level>"`
2. 생성된 이슈를 프로젝트 보드에 추가:
   `gh project item-add 1 --owner mqzkim --url <이슈URL>`
3. 생성된 이슈 번호 + URL 출력

### `start <issue-number>`
1. `gh issue view <number> --repo mqzkim/local-workspace --json title,labels` 로 이슈 정보 확인
2. 이슈 제목에서 slug 생성하여 브랜치명 결정: `feat/#<number>-<slug>`
3. `git checkout -b <branch-name>` 실행
4. 보드에서 Status를 **In Progress**로 이동:
   ```bash
   ITEM_ID=$(gh project item-list 1 --owner mqzkim --format json --limit 500 | node -e "
     const d=JSON.parse(require('fs').readFileSync(0,'utf8'));
     const item=d.items.find(i=>i.content&&i.content.number===<number>);
     if(item) console.log(item.id);
   ")
   gh project item-edit --project-id PVT_kwHOAJ7Yb84BQfi9 --id $ITEM_ID --field-id PVTSSF_lAHOAJ7Yb84BQfi9zg-mHx4 --single-select-option-id c6a8fecd
   ```
5. 이슈에 코멘트: `gh issue comment <number> --repo mqzkim/local-workspace --body "🔨 작업 시작 — 브랜치: <branch-name>"`

### `done <issue-number>`
1. `gh issue view <number> --repo mqzkim/local-workspace --json title` 로 제목 확인
2. 현재 브랜치의 변경사항 확인 (`git status`)
3. 현재 브랜치를 push: `git push -u origin <current-branch>`
4. `gh pr create --repo mqzkim/local-workspace --title "<이슈 제목>" --body "Closes #<number>"`
5. 보드에서 Status를 **In Review**로 이동:
   ```bash
   ITEM_ID=$(gh project item-list 1 --owner mqzkim --format json --limit 500 | node -e "
     const d=JSON.parse(require('fs').readFileSync(0,'utf8'));
     const item=d.items.find(i=>i.content&&i.content.number===<number>);
     if(item) console.log(item.id);
   ")
   gh project item-edit --project-id PVT_kwHOAJ7Yb84BQfi9 --id $ITEM_ID --field-id PVTSSF_lAHOAJ7Yb84BQfi9zg-mHx4 --single-select-option-id 572d115c
   ```
6. PR URL 출력

### `web`
1. `gh project view 1 --owner mqzkim --web` 실행하여 브라우저에서 보드 열기
