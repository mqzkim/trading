---
description: 변경된 프로젝트를 감지하여 typecheck/test/lint를 자동 실행합니다
---

# /verify

git diff로 변경된 파일을 감지하고 해당 프로젝트의 검증 파이프라인을 실행한다.

## 사용법
```
/verify              # 현재 변경사항 기준 자동 감지
/verify all          # 모든 프로젝트 검증
/verify <project>    # 특정 프로젝트만 검증
```

## 실행 절차

1. `git diff --name-only` 로 변경 파일 감지
2. 변경 파일이 속한 프로젝트 식별
3. 프로젝트별 검증 명령 순차 실행:

### claude-workspace (Next.js)
```bash
npm run typecheck
npm run lint
npm run test
```

### trading (Python)
```bash
mypy src/
ruff check src/
pytest tests/
```

4. 결과를 pass/fail 요약으로 보고:
```
검증 결과:
- typecheck: PASS (에러 0)
- test: PASS (12/12 통과)
- lint: PASS (경고 2, 에러 0)
```

$ARGUMENTS
