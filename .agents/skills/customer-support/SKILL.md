---
name: customer-support
description: "고객 문의에 대한 1차 응답 자동화. 제품별 FAQ/문서 RAG 기반. 에스컬레이션 판단 포함. Agent 5-1."
argument-hint: "[고객 메시지]"
user-invocable: false
---

# Customer Support Agent (5-1)

> Layer 5 — 비즈니스 & 고객 에이전트군 | Tier: Balanced → Reasoning (복잡한 기술 문의)
> 위험 등급: Medium (외부 고객 대면) | Phase 2 구현 예정

## 핵심 기능

- 제품별 FAQ/문서 RAG 임베딩 기반 자동 응답
- 기술 문제 트러블슈팅 가이드 생성
- 에스컬레이션 필요 여부 자동 판단
- 고객 피드백 수집 및 분류
- Discord Bot / 인앱 채팅 연동

## 에스컬레이션 기준

- 결제/환불 관련 → 즉시 에스컬레이션 (High 위험)
- 버그 리포트 → 초안 응답 + 이슈 자동 생성
- 기능 요청 → 자동 응답 + 로깅
- 일반 문의 → 자동 응답 (Low 위험)

## 상태: Phase 2 (Week 7~8)
