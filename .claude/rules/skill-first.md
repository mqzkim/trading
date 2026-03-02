# Skill-First Workflow Rule (MANDATORY)

> **모든 작업은 반드시 Skill을 통해 실행한다. 예외 없음.**

## 핵심 원칙

**사용자의 모든 작업 요청은 — 아무리 사소하더라도 — 반드시 Skill을 경유해야 한다.**

이 규칙은 다른 모든 워크플로우 규칙보다 우선한다.

## 실행 프로토콜

### Step 1: Skill 매칭
사용자 요청을 받으면 **가장 먼저** 기존 Skill 목록에서 매칭되는 Skill을 찾는다.

- 매칭 기준: 요청의 도메인, 작업 유형, 키워드
- 부분 매칭도 허용 (70% 이상 관련성이면 해당 Skill 사용)

### Step 2: Skill이 있는 경우
→ 즉시 `Skill` 도구로 해당 Skill을 호출하여 작업 수행

### Step 3: Skill이 없는 경우 (필수 생성)
적절한 Skill이 없으면 **작업 수행 전에** 반드시 새 Skill을 생성한다:

1. **Skill 설계**: 요청 도메인에 맞는 Skill 정의
   - 파일 위치: `.claude/skills/<skill-name>.md`
   - 역할, 수행 가능 작업, 참고 문서 명시
2. **Team Agent 활용**: 적절한 전문 에이전트를 통해 Skill 파일 생성
   - `backend-architect` → 백엔드/API 관련 Skill
   - `frontend-developer` → UI/프론트엔드 관련 Skill
   - `fullstack-developer` → 풀스택 관련 Skill
   - `technical-writer` → 문서/콘텐츠 관련 Skill
   - `ui-ux-designer` → 디자인 관련 Skill
   - 범용 작업 → `general-purpose` 에이전트
3. **Hub 등록**: 생성된 Skill을 Hub에 등록 (`/hub-manager sync`)
4. **Skill 호출**: 생성된 Skill을 사용하여 원래 작업 수행

## Skill 생성 템플릿

```markdown
# <Skill Name>

<한 줄 설명>

## 역할
<전문가 역할 정의>

## 수행 가능 작업

### 1. <작업 카테고리>
<상세 설명>

### 2. <작업 카테고리>
<상세 설명>

## 참고 문서
- <관련 문서 경로>

## 제약 조건
- <준수해야 할 규칙>
```

## 금지 사항

- **직접 코드 작성/수정 금지** — Skill을 거치지 않은 직접 실행 금지
- **"이건 너무 간단해서 Skill 필요 없다" 판단 금지** — 모든 작업은 Skill 경유
- **Skill 없이 Agent만 호출하는 것도 금지** — Skill 생성 후 Skill을 통해 작업

## 예외 (이것만 허용)

- 사용자와의 **대화/질문/응답** (정보 제공, 설명)
- **파일 읽기/탐색** (코드 리뷰를 위한 사전 조사)
- **메모리 업데이트** (세션 회고, 학습 기록)
- **Git 상태 확인** (git status, git log 등 조회성 명령)

## 적용 범위

이 규칙은 다음 모든 상황에 적용된다:
- 코드 작성, 수정, 삭제
- 파일 생성, 구조 변경
- 빌드, 테스트, 배포
- 리팩토링, 최적화
- 문서 작성, 업데이트
- 환경 설정, 의존성 관리
- 디버깅, 트러블슈팅
