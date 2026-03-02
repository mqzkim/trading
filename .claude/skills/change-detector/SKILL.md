---
name: change-detector
description: "웹사이트·API·데이터 소스의 변경을 감지하고 알림. IDEA 3 디렉토리 자동 업데이트와 IDEA 6-E 가격 변동 추적의 핵심. Agent 2-3."
argument-hint: "[URL 또는 모니터링 설정 파일]"
user-invocable: false
---

# Change Detector Agent (2-3)

> Layer 2 — 데이터 & 수집 에이전트군 | Tier: Fast
> 위험 등급: Low | Phase 3 구현 예정

## 핵심 기능

- 웹페이지 변경 감지 (diff)
- API 응답 변경 모니터링
- 가격 변동 추적
- 신규 항목 감지
- 변경 이벤트 → Alert Agent 또는 Data Transformer에 전달

## 파이프라인 연동

```
Change Detector → Data Transformer → 디렉토리 DB 자동 업데이트
```

## 상태: Phase 3 (Week 9~12)
