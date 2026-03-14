# Phase 21: Foundation - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Next.js 16 프로젝트 셋업, FastAPI JSON API 엔드포인트 추가, BFF 프록시 아키텍처 구성. 개발자가 `npm run dev`로 Next.js를 실행하고 모든 데이터가 BFF 프록시를 통해 FastAPI에서 흘러오는 것을 검증할 수 있는 상태. UI 디자인이나 컴포넌트 구현은 Phase 22 범위.

</domain>

<decisions>
## Implementation Decisions

### JSON API 응답 구조
- 기존 QueryHandler(`OverviewQueryHandler`, `SignalsQueryHandler`, `RiskQueryHandler`, `PipelineQueryHandler`)가 반환하는 Python dict를 그대로 JSON으로 반환
- 별도 Pydantic DTO 변환 없음 -- 프론트엔드에서 필요한 형태로 가공
- 엔드포인트 URL: `/api/v1/dashboard/overview`, `/api/v1/dashboard/signals`, `/api/v1/dashboard/risk`, `/api/v1/dashboard/pipeline`

### JSON API 라우터
- 새 `APIRouter(prefix="/api/v1/dashboard")` 추가 -- 기존 `/dashboard/` HTML 라우트와 공존
- 기존 HTMX 라우트는 그대로 유지 (Phase 25 Cleanup에서 제거)
- 조회(GET) API + 변경(POST) API 모두 Phase 21에서 구현 (pipeline run, approval CRUD, review approve/reject)

### 개발 워크플로우
- 터미널 2개 별도 실행: 터미널 1에서 FastAPI(8000), 터미널 2에서 Next.js(3000)
- 통합 스크립트(concurrently) 없음 -- 별도 실행으로 독립적 재시작 가능

### 프로젝트 구조
- Next.js 프로젝트 위치: `trading/dashboard/` (기존 Python `src/dashboard/`와 별도)
- 패키지 매니저: npm (시스템에 설치된 npm 10.9.4 사용)
- App Router 4개 페이지 플랫 구조:
  - `app/(dashboard)/page.tsx` (Overview)
  - `app/(dashboard)/signals/page.tsx`
  - `app/(dashboard)/risk/page.tsx`
  - `app/(dashboard)/pipeline/page.tsx`

### 프록시 설정
- `next.config.ts` rewrites로 `/api/*` 요청을 `http://localhost:8000`으로 프록시
- SSE 프록시도 Phase 21에서 설정 (`/api/v1/dashboard/events` 경로 포함)
- FastAPI 미실행 시: "백엔드 연결 불가 - FastAPI를 먼저 실행하세요" 에러 메시지 표시

### Claude's Discretion
- Next.js 프로젝트 초기화 세부 설정 (tsconfig, biome 설정 등)
- JSON API 라우터 내부 구현 방식 (동일 QueryHandler 재사용 vs 래퍼)
- 에러 메시지 UI 컴포넌트 디자인
- TypeScript 타입 정의 방식

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/dashboard/application/queries.py`: 4개 QueryHandler -- dict 반환 로직 그대로 JSON API에서 재사용
- `src/dashboard/presentation/app.py`: FastAPI 앱 팩토리 -- 새 JSON 라우터를 `app.include_router()`로 추가
- `src/dashboard/infrastructure/sse_bridge.py`: SSE 브릿지 -- JSON API SSE 엔드포인트에서 재사용
- `src/bootstrap.py`: 컨텍스트 dict 생성 -- QueryHandler에 주입되는 모든 repo/handler 포함

### Established Patterns
- DDD 레이어 구조: `domain/` → `application/` → `infrastructure/` → `presentation/`
- FastAPI APIRouter with prefix: 기존 `/dashboard` prefix 패턴
- QueryHandler 패턴: `__init__(ctx)` + `handle()` → dict 반환
- SSE bridge: 도메인 이벤트 → SSE 스트리밍 패턴 확립

### Integration Points
- `create_dashboard_app()`: 새 JSON 라우터를 기존 앱에 추가하는 진입점
- `app.state.ctx`: 모든 repo/handler가 담긴 컨텍스트 dict
- `app.state.sse_bridge`: SSE 이벤트 스트리밍 브릿지
- `next.config.ts` rewrites: Next.js → FastAPI 프록시 설정

</code_context>

<specifics>
## Specific Ideas

No specific requirements -- open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope

</deferred>

---

*Phase: 21-foundation*
*Context gathered: 2026-03-14*
