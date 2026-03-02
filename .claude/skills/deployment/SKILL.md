---
name: deployment
description: "코드 변경을 안전하게 프로덕션에 배포. Vercel Preview/Production 배포, 롤백, 스모크 테스트 자동 실행. Agent 4-1."
argument-hint: "[브랜치명 또는 PR 번호]"
user-invocable: false
---

# Deployment Agent (4-1)

> Layer 4 — 운영 & 모니터링 에이전트군 | Tier: Fast
> 위험 등급: High (프로덕션 배포) | Phase 2 구현 예정

## 핵심 기능

- Vercel Git Integration 기반 Preview/Production 배포
- GitHub Actions 연동 (typecheck, test, lint 체크)
- 배포 후 스모크 테스트 자동 실행
- 롤백 자동화 (실패 감지 시)
- 환경 변수 관리

## HITL 정책

- Preview 배포: 자동 (Low 위험)
- Production 배포: 명시적 승인 필요 (High 위험)
- 롤백: 자동 + 즉시 알림 (High 위험)

## 상태: Phase 2 (Week 8)
