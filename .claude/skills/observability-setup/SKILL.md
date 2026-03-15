# Observability Setup

Next.js 앱에 PostHog(분석) + Sentry(에러 추적)를 통합하는 스킬.

## 역할

시니어 풀스택 엔지니어. 프로덕션 관찰성(Observability) 스택 구성 전문.
기능 변경 없이 분석/모니터링 레이어 추가. TypeScript strict 모드 유지.

## 수행 가능 작업

### 1. PostHog 프로덕션 통합 (`posthog`)

PostHog JS SDK를 Next.js App Router에 통합.

```typescript
// src/components/providers/posthog-provider.tsx
"use client";
import posthog from "posthog-js";
import { useEffect } from "react";

export function PostHogProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const key = process.env.NEXT_PUBLIC_POSTHOG_KEY;
    if (key && typeof window !== "undefined") {
      posthog.init(key, {
        api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST ?? "https://us.i.posthog.com",
        capture_pageview: false, // PageViewTracker handles this
        capture_pageleave: true,
        loaded: (ph) => {
          if (process.env.NODE_ENV === "development") ph.opt_out_capturing();
        },
      });
    }
  }, []);
  return <>{children}</>;
}
```

대상: `src/components/providers/posthog-provider.tsx`
의존: `posthog-js` 패키지 설치

### 2. Sentry 에러 추적 통합 (`sentry`)

@sentry/nextjs SDK를 Next.js App Router에 통합.

```typescript
// sentry.client.config.ts
import * as Sentry from "@sentry/nextjs";
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 1.0,
  debug: false,
  environment: process.env.NODE_ENV,
});
```

파일:
- `sentry.client.config.ts`
- `sentry.server.config.ts`
- `sentry.edge.config.ts`
- `next.config.ts` → `withSentryConfig()` 래핑

대상: 프로젝트 루트
의존: `@sentry/nextjs` 패키지 설치

### 3. 환경변수 정리 (`env`)

`.env.example`에 관찰성 관련 변수 추가/활성화.

```bash
# Analytics (PostHog)
NEXT_PUBLIC_POSTHOG_KEY=phc_xxx
NEXT_PUBLIC_POSTHOG_HOST=https://us.i.posthog.com

# Error Tracking (Sentry)
SENTRY_DSN=https://xxx@o0.ingest.sentry.io/0
SENTRY_AUTH_TOKEN=sntrys_xxx
```

## 실행 프로세스

1. 대상 파일 Read → 현재 구조 파악
2. 패키지 설치 (`pnpm add`)
3. Provider/Config 파일 생성
4. layout.tsx에 Provider 추가
5. `pnpm typecheck` 통과 확인

## 제약 조건

- TypeScript strict 모드 유지
- 기존 analytics/events.ts의 `track()` 함수 인터페이스 유지
- Sentry DSN 미설정 시 graceful degradation (no-op)
- PostHog key 미설정 시 silently skip (no errors)
- `pnpm typecheck` 통과 필수

## 참고 문서

- `plans/sprints/sprint-19-launch-preparation.md`
- `shipkit/src/lib/analytics/events.ts`
- `shipkit/src/components/analytics/pageview-tracker.tsx`
- `shipkit/src/app/[locale]/layout.tsx`
