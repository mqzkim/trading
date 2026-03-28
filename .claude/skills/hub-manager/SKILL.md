---
name: hub-manager
description: "Claude Hub 중앙 스킬/설정 관리. 레지스트리 조회, 에셋 동기화, 새 레포 부트스트랩, 상태 확인을 수행합니다."
argument-hint: "[list|status|sync|init|scan] [options]"
allowed-tools: "Read, Bash, Glob, Grep"
user-invocable: true
---

# Claude Hub Manager

워크스페이스의 모든 스킬, 에이전트, 커맨드, 룰, 출력 스타일을 중앙에서 관리합니다.

## Hub 위치
- 허브 루트: `/c/workspace/.claude/hub/`
- 레지스트리: `/c/workspace/.claude/hub/registry.json`
- 공유 에셋: `/c/workspace/.claude/hub/shared/`

## 명령어

$ARGUMENTS를 파싱하여 실행:

### `list [--type TYPE]`
레지스트리에서 에셋 목록 조회. `registry.json`을 읽어 TYPE별 필터링.

### `status`
전체 에셋 현황과 동기화 상태 표시. 각 레포의 `.claude/` 디렉토리를 스캔하여 레지스트리와 비교.

### `sync [--push|--pull|--both]`
공유 에셋 동기화. 허브 `shared/`와 각 레포의 `.claude/` 간 파일 복사.

### `init <repo-path> [alias]`
새 레포를 허브에 등록하고 공유 에셋 부트스트랩. `registry.json`에 항목 추가 후 `shared/` 에셋 복사.

### `scan`
모든 레포 스캔 → 레지스트리 갱신. 등록된 레포 경로를 순회하며 에셋 목록 업데이트.

## 주의사항
- 동기화 전 `status`로 현황 확인 권장
- 충돌 시 원본(origin) 우선 자동 덮어쓰기
- `init` 실행 시 모든 공유 에셋이 새 레포에 복사됨
