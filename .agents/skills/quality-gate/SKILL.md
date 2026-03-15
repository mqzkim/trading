---
name: quality-gate
description: "에이전트가 생성한 결과물(코드, 콘텐츠, 배포)의 품질을 최종 검증. lint/typecheck/test 통과, 팩트체크, 톤 일관성, 스모크 테스트. Agent 0-3."
argument-hint: "[에이전트 출력 결과]"
user-invocable: false
---

# Quality Gate Agent (0-3)

> Layer 0 — 오케스트레이션 에이전트 | Tier: Balanced → Reasoning (보안 이슈 발견 시)
> 위험 등급: Low | Phase 3 구현 예정

## 핵심 기능

- 코드 결과물: lint/typecheck/test 통과 여부 검증
- 콘텐츠 결과물: 팩트체크, 톤 일관성, 가이드라인 준수
- 배포 결과물: 스모크 테스트, 성능 기준 충족 확인
- Pass/Fail 판정 + 사유 + 수정 제안
- Fail 시 인간에게 에스컬레이션

## 품질 기준 참조

- 코드: `.Codex/skills/code-review/spec.md` 기준 적용
- 디자인: `.Codex/skills/design-review/spec.md` 기준 적용
- 콘텐츠: content-writer 글쓰기 원칙 준수 확인

## 상태: Phase 3 (Week 19~24)
