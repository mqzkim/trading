---
name: portfolio-manager
description: "7개 제품 포트폴리오 전체를 조감하며 시간/자원 투입 추천. 주간 우선순위 리포트, 집중 제품 Top 3, 포기/집중 판단 지원. Agent 0-1."
argument-hint: ""
user-invocable: false
---

# Portfolio Manager Agent (0-1)

> Layer 0 — 오케스트레이션 에이전트 | Tier: Balanced → Reasoning (전략적 판단)
> 위험 등급: Low | Phase 3 구현 예정

## 핵심 기능

- 각 제품의 Stripe 매출, Vercel Analytics, Supabase 사용량 통합
- 주간 우선순위 리포트 생성
- "이번 주 집중해야 할 제품 Top 3" 추천
- 포기/집중 판단 지원 (데이터 기반)
- 다른 에이전트에 작업 지시 (Task Router 연동)

## Daniel Vassallo 전략 구현

"반응 좋은 것에 집중, 안 되는 것은 빠르게 포기"를
데이터 기반으로 자동 판단 보조.

## 상태: Phase 3 (Week 19~24)
