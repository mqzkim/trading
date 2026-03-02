---
name: alert
description: "모든 에이전트의 이상 이벤트를 통합하여 Slack/이메일/SMS로 알림. 심각도 분류, 중복 억제, 에스컬레이션 관리. Agent 4-3."
argument-hint: "[이벤트 메시지]"
user-invocable: false
---

# Alert Agent (4-3)

> Layer 4 — 운영 & 모니터링 에이전트군 | Tier: Fast
> 위험 등급: Low | Phase 3 구현 예정

## 핵심 기능

- 알림 통합 (Slack Webhook + Resend 이메일 + Twilio SMS 긴급)
- 심각도 × 빈도 × 시간대 기반 알림 여부 판단
- 중복 알림 억제 (동일 이슈 반복 방지)
- 에스컬레이션 체인 관리
- "하루 알림 5건 이내" 원칙 (알림 피로 방지)

## 상태: Phase 3 (Week 9~12)
