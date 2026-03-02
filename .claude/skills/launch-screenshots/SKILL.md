---
name: launch-screenshots
description: "배포된 ShipKit 데모 사이트의 스크린샷을 Playwright로 자동 촬영. 랜딩 페이지, 대시보드, AI 챗 화면 등. Agent 3-5."
argument-hint: "[base-url] [--output-dir ./screenshots] [--login email:password]"
allowed-tools: "Read, Bash, Glob"
---

# Launch Screenshots Agent (3-5)

> Layer 3 — 콘텐츠 & 마케팅 에이전트군 | Tier: Balanced
> 위험 등급: Low (읽기 전용, 스크린샷 파일 생성만)

당신은 제품 스크린샷을 자동으로 촬영하는 에이전트입니다.
Playwright MCP 도구를 사용하여 배포된 사이트의 주요 화면을 캡처합니다.

## 입력 파싱

$ARGUMENTS를 파싱합니다:
- 첫 번째 인자: base URL (기본값: `https://demo.shipkit.work`)
- `--output-dir`: 스크린샷 저장 경로 (기본값: `./screenshots`)
- `--login`: 로그인 정보 (기본값: `demo@shipkit.work:demo1234!`)
- `--skip-login`: 로그인 없이 퍼블릭 페이지만 촬영

## 실행 프로세스

### 0. 준비

1. 출력 디렉토리 생성: `mkdir -p [output-dir]`
2. Playwright MCP 도구 사용 가능 여부 확인
3. 브라우저 뷰포트를 1920x1080으로 리사이즈

### 1. 랜딩 페이지 스크린샷

1. `mcp__playwright__browser_navigate` → `[base-url]`
2. 페이지 로드 완료 대기 (`mcp__playwright__browser_wait_for`)
3. `mcp__playwright__browser_take_screenshot` → `01-landing.png`
4. 결과 확인 및 저장

### 2. 로그인

1. `mcp__playwright__browser_navigate` → `[base-url]/sign-in`
2. 이메일 필드에 입력: `mcp__playwright__browser_fill_form`
3. 비밀번호 필드에 입력
4. 로그인 버튼 클릭: `mcp__playwright__browser_click`
5. 대시보드 리다이렉트 대기

### 3. 대시보드 스크린샷

1. `mcp__playwright__browser_navigate` → `[base-url]/dashboard`
2. 사이드바 펼침 상태 확인
3. `mcp__playwright__browser_take_screenshot` → `02-dashboard.png`

### 4. AI Chat 스크린샷

1. `mcp__playwright__browser_navigate` → `[base-url]/dashboard/ai-chat` 또는 `[base-url]/dashboard/ai`
2. 페이지 로드 대기
3. `mcp__playwright__browser_take_screenshot` → `03-ai-chat.png`

### 5. 에디터 스크린샷 (수동 안내)

> 에디터 화면(VS Code)은 브라우저로 접근할 수 없습니다.
> 아래 2장은 수동으로 촬영해주세요:

- **04-project-tree.png**: VS Code에서 `src/` 폴더를 펼친 프로젝트 트리
- **05-claude-md.png**: VS Code에서 `CLAUDE.md` 파일을 열어둔 화면

**Windows 스크린샷**: `Win + Shift + S` → 영역 선택 → `[output-dir]`에 저장

## 출력 형식

```markdown
# 📸 Screenshot Report

## 자동 촬영 완료
- ✅ 01-landing.png — 랜딩 페이지 (1920x1080)
- ✅ 02-dashboard.png — 대시보드 (로그인 상태)
- ✅ 03-ai-chat.png — AI 챗 화면

## 수동 촬영 필요
- ⏳ 04-project-tree.png — VS Code 프로젝트 트리
  → VS Code에서 `src/` 폴더 펼친 상태로 `Win+Shift+S`
- ⏳ 05-claude-md.png — CLAUDE.md 화면
  → VS Code에서 `CLAUDE.md` 열고 `Win+Shift+S`

## 저장 위치
[output-dir]/

## 다음 단계
→ 수동 스크린샷 촬영 후 `/launch-package` 실행
```

## 참고

- 권장 해상도: 1920x1080 이상
- 다크 모드에서도 촬영하려면 `--dark` 플래그 추가 (추후 지원)
- Gumroad, ProductHunt 이미지 규격에 맞춰 크롭 필요 시 별도 안내

## 관련 에이전트 연동

- `/launch-preflight` 통과 후 이 에이전트 실행
- 이 에이전트 출력 → `/launch-package`에서 스크린샷 경로 참조
