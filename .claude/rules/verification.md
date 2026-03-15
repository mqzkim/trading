# Verification Rule (MANDATORY)

> **코드 변경 작업 완료 전 반드시 검증을 수행한다. 검증 없이 "완료" 선언 금지.**

## 필수 검증 단계

1. **타입체크** — typecheck 또는 mypy 실행, 에러 0
2. **테스트** — 관련 테스트 실행, 전부 통과
3. **린트** — lint 또는 ruff check 실행, 에러 0
4. **결과 명시** — 실행 결과를 사용자에게 구체적으로 보고 (pass/fail + 숫자)
5. **수동 확인** — UI 변경 시 스크린샷, API 변경 시 curl 테스트

## 보고 형식

```
검증 결과:
- typecheck: PASS (에러 0)
- test: PASS (12/12 통과)
- lint: PASS (경고 2, 에러 0)
```

## 생략 허용 조건

아래 경우에만 검증 생략 가능:
- 문서/주석만 변경 (.md, 코드 내 주석)
- 설정 파일만 변경 (.gitignore, .json 설정)
- 코드 변경 없는 대화/질문/응답

## 프로젝트별 명령

| 프로젝트 | typecheck | test | lint |
|---------|-----------|------|------|
| claude-workspace | `npm run typecheck` | `npm run test` | `npm run lint` |
| trading | `mypy src/` | `pytest tests/` | `ruff check src/` |
