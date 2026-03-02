---
name: data-enricher
description: "기본 데이터(이름, URL)에 AI 기반으로 카테고리, 태그, 요약, 장단점을 자동 보강. IDEA 3 디렉토리 프로필 자동 작성의 핵심. Agent 2-4."
argument-hint: "[데이터 파일 또는 URL 목록]"
user-invocable: false
---

# Data Enricher Agent (2-4)

> Layer 2 — 데이터 & 수집 에이전트군 | Tier: Balanced
> 위험 등급: Low | Phase 2 구현 예정

## 핵심 기능

- 카테고리 자동 분류
- 태그 생성
- 요약 작성
- 장단점 비교 분석
- 유사 제품 연결
- SEO 최적화된 프로필 페이지 생성

## IDEA 3 시너지

```
기존: 수동으로 각 도구 프로필 작성 (주 20시간+)
Enricher: URL만 입력하면 → 카테고리/태그/요약/가격 자동 생성
결과: 운영 시간 주 2~3시간 (검수만)
```

## 파이프라인 연동

```
Web Scraper → Data Enricher → SEO Optimizer → DB 저장
```

## 상태: Phase 2 (Week 4)
