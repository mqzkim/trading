---
name: data-transformer
description: "비정형 데이터(PDF, 이미지, HTML)를 정형 데이터(JSON)로 변환. Codex Vision API 기반. IDEA 2 문서 파싱 API와 웹→마크다운 API의 핵심 엔진. Agent 2-2."
argument-hint: "[파일 경로 또는 URL] --schema [출력 스키마]"
user-invocable: false
---

# Data Transformer Agent (2-2)

> Layer 2 — 데이터 & 수집 에이전트군 | Tier: Fast → Balanced (복잡한 스키마)
> 위험 등급: Low | Phase 3 구현 예정

## 핵심 기능

- PDF 파싱 → 구조화 JSON
- 이미지 OCR → 텍스트 추출
- HTML → Markdown 변환
- 데이터 정규화 및 스키마 매핑
- Zod 스키마로 출력 검증

## 구현 기술

- **Codex Vision API** — PDF/이미지 → 텍스트 추출
- **pdf-parse + sharp** — 전처리
- **Zod** — 출력 스키마 검증

## 상태: Phase 3 (Week 9~12)
