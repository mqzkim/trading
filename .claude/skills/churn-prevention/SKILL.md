---
name: churn-prevention
description: "이탈 가능성 높은 유료 고객을 사전 감지하고 리텐션 전략 실행. 사용량 감소, 결제 실패 추적, 이탈 위험 점수 산출. Agent 5-4."
argument-hint: "[제품명]"
user-invocable: false
---

# Churn Prevention Agent (5-4)

> Layer 5 — 비즈니스 & 고객 에이전트군 | Tier: Balanced
> 위험 등급: Medium (리텐션 이메일 발송) | Phase 3 구현 예정

## 핵심 기능

- 사용량 감소 감지 (API 호출 수, 로그인 빈도, 기능 사용률)
- 결제 실패 추적 (Stripe Webhook)
- 이탈 위험 점수 = 사용량 변화율 × 결제 상태 × 계정 나이
- 위험 고객에게 개인화된 리텐션 이메일 자동 발송
- 이탈 위험 고객 리스트 + 권장 액션 리포트

## 상태: Phase 3 (Week 13~18)
