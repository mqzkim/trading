---
name: task-router
description: "들어오는 작업/이벤트를 적절한 에이전트에 라우팅. 이벤트 분류, 디스패칭, 실행 큐 관리, 재시도 처리. Agent 0-2."
argument-hint: "[이벤트 JSON]"
user-invocable: false
---

# Task Router Agent (0-2)

> Layer 0 — 오케스트레이션 에이전트 | Tier: Fast
> 위험 등급: Low | Phase 3 구현 예정

## 핵심 기능

- 웹훅/크론/수동 이벤트 분류
- 적절한 에이전트로 작업 디스패칭
- Redis + BullMQ 기반 실행 큐 관리
- 에이전트별 우선순위 큐
- 실패 시 DLQ(Dead Letter Queue) + 재시도 정책
- 실행 결과 로깅

## 구현 기술

- Next.js API Route — 이벤트 수신
- Redis + BullMQ — 작업 큐
- Supabase — 실행 로그 저장

## 상태: Phase 3 (Week 19~24)
