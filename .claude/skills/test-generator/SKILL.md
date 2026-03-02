---
name: test-generator
description: "코드 변경에 대한 유닛/E2E 테스트를 자동 생성. Vitest + Playwright 기반. 엣지 케이스 탐지 및 커버리지 분석 포함. Agent 1-4."
argument-hint: "[파일 경로 또는 diff]"
allowed-tools: "Read, Grep, Glob, Bash, Write, Edit"
---

# Test Generator Agent (1-4)

> Layer 1 — 개발 에이전트군 | Tier: Balanced
> 위험 등급: Low | Phase 2 구현 예정

## 핵심 기능

- 소스 코드 분석 → 유닛 테스트 자동 생성 (Vitest)
- 엣지 케이스 자동 탐지 (경계값, null, 빈 배열, 동시성)
- 기존 테스트와의 중복 방지
- 커버리지 분석 및 미커버 영역 식별
- E2E 시나리오 제안 (Playwright)

## 테스트 생성 원칙

1. 각 함수의 정상 경로(happy path) + 최소 2개 엣지 케이스
2. Arrange-Act-Assert 패턴 준수
3. 테스트 간 의존성 없음 (독립 실행 가능)
4. 모킹은 외부 의존성만 (Supabase, Stripe, 외부 API)
5. 테스트 설명은 행위 중심 ("should return X when Y")

## 상태: Phase 2 (Week 7~8)
