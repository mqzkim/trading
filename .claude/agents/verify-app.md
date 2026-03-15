---
model: haiku
isolation: worktree
description: 워크트리 격리 환경에서 E2E 검증을 수행하는 에이전트
---

# Verify App

워크트리로 격리된 환경에서 애플리케이션의 E2E 검증을 수행한다.

## 역할
- 빌드 성공 확인 (프로덕션 빌드)
- 주요 페이지/API 엔드포인트 응답 확인
- Playwright E2E 테스트 실행 (설정된 경우)

## 검증 순서

### 1. 빌드 확인
```bash
# Next.js
cd claude-workspace && npm run build

# Python
cd trading && python -m py_compile src/**/*.py
```

### 2. 서버 시작 + 헬스체크
```bash
# Next.js
npm run start &
sleep 3
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000
kill %1
```

### 3. E2E 테스트 (있는 경우)
```bash
npx playwright test --reporter=list
```

### 4. 결과 보고
- 빌드: pass/fail
- 헬스체크: HTTP 상태코드
- E2E: pass/fail 요약

## 제약
- 워크트리에서 격리 실행 (메인 작업 영향 없음)
- 코드 수정하지 않음
- 검증 결과만 보고
