---
name: health-monitor
description: "7개 제품의 가용성·응답시간·에러율 실시간 모니터링. IDEA 6-C CronPing SaaS의 내부 버전(Dogfooding). Agent 4-2."
argument-hint: "[서비스명 또는 URL]"
user-invocable: false
---

# Health Monitor Agent (4-2)

> Layer 4 — 운영 & 모니터링 에이전트군 | Tier: Fast → Balanced (이상 원인 분석)
> 위험 등급: Low | Phase 3 구현 예정
> Dogfooding: 내부 사용 → IDEA 6-C CronPing SaaS로 외부 판매

## 핵심 기능

- Uptime 모니터링 (HTTP 헬스체크)
- 응답 시간 추적 (P50/P95/P99)
- 에러율 모니터링 (4xx/5xx)
- SSL 인증서 만료 감지
- 이상 감지 시 → Alert Agent에 전달

## 상태: Phase 3 (Week 9~12)
