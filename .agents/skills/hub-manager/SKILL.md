---
name: hub-manager
description: "Codex Hub 중앙 스킬/설정 관리. 레지스트리 조회, 에셋 동기화, 새 레포 부트스트랩, 상태 확인을 수행합니다."
argument-hint: "[list|status|sync|init|scan] [options]"
allowed-tools: "Read, Bash, Glob, Grep"
user-invocable: true
---

# Codex Hub Manager

워크스페이스의 모든 스킬, 에이전트, 커맨드, 룰, 출력 스타일을 중앙에서 관리합니다.

## Hub 위치
- 허브 루트: `/c/workspace/.Codex/hub/`
- 레지스트리: `/c/workspace/.Codex/hub/registry.json`
- 공유 에셋: `/c/workspace/.Codex/hub/shared/`
- 스크립트: `/c/workspace/.Codex/hub/scripts/`

## 명령어

$ARGUMENTS를 파싱하여 실행:

### `list [--type TYPE]`
레지스트리에서 에셋 목록 조회.
```bash
node /c/workspace/.Codex/hub/scripts/status.js "" TYPE
```

### `status`
전체 에셋 현황과 동기화 상태 표시.
```bash
bash /c/workspace/.Codex/hub/scripts/Codex-hub-status.sh
```

### `sync [--push|--pull|--both]`
공유 에셋 동기화.
```bash
bash /c/workspace/.Codex/hub/scripts/Codex-hub-sync.sh --both
```

### `init <repo-path> [alias]`
새 레포를 허브에 등록하고 공유 에셋 부트스트랩.
```bash
bash /c/workspace/.Codex/hub/scripts/Codex-hub-init.sh <repo-path> [alias]
```

### `scan`
모든 레포 스캔 → 레지스트리 갱신.
```bash
bash /c/workspace/.Codex/hub/scripts/Codex-hub-scan.sh
```

## 주의사항
- 동기화 전 `status`로 현황 확인 권장
- 충돌 시 원본(origin) 우선 자동 덮어쓰기
- `init` 실행 시 모든 공유 에셋이 새 레포에 복사됨
