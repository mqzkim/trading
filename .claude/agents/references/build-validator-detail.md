# Build Validator — Detail

## 실행 순서

### 1. 프로젝트 감지
```bash
git diff --name-only HEAD | head -50
```
- `claude-workspace/` 하위 → Next.js 프로젝트
- `trading/` 하위 → Python 프로젝트

### 2. Next.js 검증
```bash
cd claude-workspace && npm run typecheck && npm run lint && npm run test
```

### 3. Python 검증
```bash
cd trading && mypy src/ && ruff check src/ && pytest tests/
```

### 4. 결과 보고
각 단계의 pass/fail 상태와 에러 메시지를 간결하게 요약한다.
에러가 있으면 수정 제안을 포함한다.

## 제약
- 코드를 수정하지 않는다 (읽기 전용)
- 검증 결과만 보고한다
