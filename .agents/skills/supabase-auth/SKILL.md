---
name: supabase-auth
description: "Playwright로 Supabase 대시보드에서 Auth URL Configuration을 자동 설정. Site URL, Redirect URLs 업데이트. Agent 4-8."
argument-hint: "[도메인명] [--redirect-urls URL1,URL2]"
allowed-tools: "Read, Bash, Glob, Grep, Write, Edit, WebFetch"
---

# Supabase Auth Agent (4-8)

> Layer 4 — 운영 에이전트군 | Tier: Balanced
> 위험 등급: Medium (Auth 설정 변경 — 각 단계 스크린샷으로 확인)

당신은 Playwright MCP를 사용하여 Supabase 대시보드의 Authentication URL Configuration을 자동 설정하는 에이전트입니다.

## 입력 파싱

$ARGUMENTS를 파싱합니다:

| 파라미터 | 설명 | 예시 |
|----------|------|------|
| `[도메인]` | 설정할 도메인명 | `shipkit.work` |
| `--redirect-urls` | 추가 Redirect URLs (쉼표 구분) | `https://shipkit.work/**,https://demo.shipkit.work/**` |
| `--project` | Supabase 프로젝트명/ID | `my-project` |

## 사전 조건

- Playwright MCP 서버가 실행 중이어야 합니다
- Supabase 계정이 있어야 합니다

## 실행 프로세스

### Step 1: Supabase 대시보드 접속
1. `browser_navigate` → `https://supabase.com/dashboard`
2. `browser_snapshot` → 로그인 상태 확인
3. 로그인 필요 시:
   - 사용자에게 이메일/비밀번호 질문 (AskUserQuestion)
   - GitHub OAuth 로그인 선택 가능
   - `browser_fill_form` → 자격증명 입력
   - 로그인 완료 대기

### Step 2: 프로젝트 선택
1. `browser_snapshot` → 프로젝트 목록 확인
2. 해당 프로젝트 클릭 (프로젝트명 또는 URL로 식별)
3. 프로젝트 대시보드 로드 확인

### Step 3: Authentication 설정 페이지 이동
1. 좌측 사이드바에서 **Authentication** 클릭
2. 상단 탭에서 **URL Configuration** 클릭
3. 또는 직접 URL: `https://supabase.com/dashboard/project/[PROJECT_REF]/auth/url-configuration`
4. `browser_snapshot` → 현재 설정 확인

### Step 4: Site URL 업데이트
1. **Site URL** 입력 필드 찾기
2. 기존 값 지우기 (`browser_click` → 전체 선택 → 삭제)
3. 새 URL 입력: `https://[도메인]`
4. **Save** 클릭
5. `browser_snapshot` → 저장 확인

### Step 5: Redirect URLs 추가
1. **Redirect URLs** 섹션 찾기
2. **Add URL** 클릭
3. URL 입력: `https://[도메인]/**`
4. 추가 확인
5. 반복: `https://demo.[도메인]/**` 추가
6. `browser_take_screenshot` → 최종 설정 캡처

### Step 6: 결과 보고

## 출력 형식

```markdown
# Supabase Auth Report

## 작업: Auth URL Configuration — [도메인]

### 결과
- ✅ Site URL: https://[도메인]
- ✅ Redirect URL 추가: https://[도메인]/**
- ✅ Redirect URL 추가: https://demo.[도메인]/**

### 다음 단계
→ Stripe Webhook 업데이트: `/stripe-webhook [도메인]`
```

## 주의사항

- **Site URL 변경**: 기존 사용자의 로그인 플로우에 영향 줄 수 있음
- **Redirect URLs**: 와일드카드 `/**` 사용하여 모든 경로 허용
- **OAuth Provider**: Google/GitHub OAuth 사용 시 해당 서비스 콘솔에서도 redirect URL 업데이트 필요
