# Plan-First Rule (MANDATORY)

> **3개 이상의 파일을 변경하는 작업은 반드시 Plan mode에서 시작한다.**

## 적용 기준

- 변경 예상 파일 수 >= 3 → Plan mode 필수
- 새 기능 추가 → Plan mode 필수
- 리팩토링 → Plan mode 필수
- 버그 수정 (단일 파일) → Plan mode 불필요

## Plan mode 프로세스

1. **EnterPlanMode** 진입
2. 영향 받는 파일 목록 작성
3. 각 파일별 변경 내용 명시
4. 리스크 및 롤백 방안 기술
5. 사용자 승인 대기
6. 승인 후 **ExitPlanMode** → 실행

## Plan 필수 항목

- 목표 (Goal)
- 범위 (Scope): 포함/제외 파일
- 변경 계획 (Changes): 파일별 구체적 변경
- 검증 방법 (Validation): 어떤 검증을 실행할지
- 리스크 (Risks): 실패 시 롤백 방안

## 예외

- 긴급 핫픽스 (사용자가 명시적으로 "바로 수정해" 요청)
- 1-2개 파일 수정 (단순 버그 수정, 오타 교정)
