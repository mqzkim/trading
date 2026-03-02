---
name: cost-tracker
description: "인프라·API 비용을 실시간 추적하고 예산 초과 방지. Vercel/Supabase/Claude API/Stripe 비용 통합. IDEA 6-E APIPrice SaaS의 내부 버전(Dogfooding). Agent 4-4."
argument-hint: "[기간: 7d|30d|90d]"
user-invocable: false
---

# Cost Tracker Agent (4-4)

> Layer 4 — 운영 & 모니터링 에이전트군 | Tier: Fast → Balanced (최적화 제안)
> 위험 등급: Low | Phase 3 구현 예정
> Dogfooding: 내부 사용 → IDEA 6-E APIPrice SaaS로 외부 판매

## 핵심 기능

- Vercel/Supabase/Claude API/Stripe 빌링 API 데이터 통합
- 예산 대비 사용량 경고 (80%, 90%, 100% 임계값)
- 비용 최적화 제안 (사용 패턴 분석)
- 월간 비용 리포트 자동 생성
- 에이전트별 API 비용 분배 추적

## 목표 예산

- 전체 인프라: 월 $175 이내
- 에이전트 API 추가: 월 $40~$75 이내
- 총합: 월 $215~$250 이내

## 상태: Phase 3 (Week 9~12)
