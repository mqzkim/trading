---
name: web-scraper
description: "웹사이트에서 구조화된 데이터를 지능적으로 추출. Playwright + Claude Vision 기반. IDEA 2 AI 스크래핑 API와 IDEA 3 디렉토리의 핵심 엔진. Agent 2-1."
argument-hint: "[URL] --extract pricing|product|contact"
user-invocable: false
---

# Web Scraper Agent (2-1)

> Layer 2 — 데이터 & 수집 에이전트군 | Tier: Balanced
> 위험 등급: Low | Phase 2 구현 예정
> IDEA 2 시너지: AI 강화 웹 스크래핑 API 상품의 핵심 엔진
> IDEA 3 시너지: 디렉토리 데이터 자동 수집

## 핵심 기능

- AI 기반 지능형 스크래핑 (Claude Vision으로 페이지 구조 이해)
- SPA/동적 페이지 대응 (Playwright headless browser)
- 추출 대상 스키마 기반 구조화 JSON 출력
- Redis 기반 Semantic Cache (동일 URL 반복 요청 70% 비용 절감)
- Rate limiting (대상 서버 부하 방지 + 비용 제어)
- 안티봇 대응 (ethical, robots.txt 준수)

## 구현 기술

- **Playwright** — Headless browser, SPA 렌더링
- **Claude Vision API** — 페이지 캡처 → 구조 이해 → 데이터 추출
- **Zod** — 추출 데이터 스키마 검증
- **Redis** — 캐싱, rate limiting

## 파이프라인 연동

```
Web Scraper → Data Transformer → Data Enricher → SEO Optimizer → DB 저장
```

## 상태: Phase 2 (Week 3~4)
