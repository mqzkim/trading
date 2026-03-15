---
name: performance-optimizer
description: "Next.js 앱 성능 최적화 전문가. N+1 쿼리 제거, Recharts 동적 임포트, 크론 병렬화, 미들웨어 최적화, React.cache() 적용. Agent 1-13."
argument-hint: "[최적화 대상 파일 또는 영역]"
user-invocable: true
---

# Performance Optimizer (Next.js)

Next.js 15 + Supabase 앱의 성능 병목을 제거하는 전문 스킬.

## 역할
시니어 풀스택 엔지니어 — Next.js 성능 최적화, DB 쿼리 튜닝, 번들 최적화 전문

## 수행 가능 작업

### 1. Recharts 동적 임포트
차트 컴포넌트를 `next/dynamic`으로 래핑하여 초기 번들 크기 절감.
- 대상: `src/components/costs/*.tsx`, `src/components/evals/*.tsx`
- `ssr: false`, `loading: () => <Skeleton />` 패턴 적용
- 예상 절감: ~150KB (gzipped ~45KB)

### 2. N+1 쿼리 제거 (코드 레벨)
JS/TS 레이어에서 N+1 쿼리를 JOIN 또는 배치 로딩으로 변환.
- Supabase `.select("*, related_table!inner(field)")` 패턴
- `Promise.all(items.map(item => fetch(item.id)))` 배치 패턴

### 3. 크론 병렬화
순차 실행 크론을 배치 병렬 실행으로 변환.
- `BATCH_SIZE = 5`로 `Promise.all(batch.map(...))` 패턴
- Vercel 60초 타임아웃 대비

### 4. React.cache() 적용
동일 렌더 사이클 내 중복 DB 쿼리 제거.
- `import { cache } from "react"` → `export const getFoo = cache(getOriginalFoo)`
- 대시보드 Server Component에서 중복 호출 방지

### 5. 미들웨어 최적화
`middleware.ts`의 불필요한 인증 호출 제거.
- `matcher` 설정으로 public API 라우트(`/api/v1`, `/api/webhooks`, `/api/cron`) 제외

### 6. 비용 대시보드 중복 쿼리 제거
JS 레이어에서 이미 조회한 데이터를 재활용.
- 월별 필터를 DB 재쿼리 대신 `Array.filter().reduce()` 패턴으로 처리

## 참고 문서
- `plans/sprints/sprint-18-performance.md` — Sprint 18 상세 스펙
- `shipkit/src/lib/costs/queries.ts` — 비용 쿼리
- `shipkit/src/lib/agents/queries.ts` — 에이전트 세션 쿼리
- `shipkit/src/app/api/cron/alerts/route.ts` — 알림 크론
- `shipkit/src/middleware.ts` — 미들웨어

## 제약 조건
- TypeScript strict 모드 유지
- 기존 기능 동작 변경 금지 (순수 성능 최적화만)
- 변경 후 빌드 + 타입체크 통과 필수
- Vercel Hobby 플랜 크론: 하루 1회 제한 준수
