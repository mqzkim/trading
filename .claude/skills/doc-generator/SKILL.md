---
name: doc-generator
description: "코드에서 API 문서, 설치 가이드, CHANGELOG를 자동 생성. tRPC + Zod → OpenAPI 스펙 추출. IDEA 2 API 문서와 IDEA 4 MCP 서버 문서의 핵심. Agent 1-5."
argument-hint: "[소스 디렉토리 또는 파일 경로]"
allowed-tools: "Read, Grep, Glob, Bash, Write"
---

# Documentation Generator Agent (1-5)

> Layer 1 — 개발 에이전트군 | Tier: Fast → Balanced (API 레퍼런스)
> 위험 등급: Low | Phase 2 구현 예정

## 핵심 기능

- tRPC + Zod 스키마에서 OpenAPI 스펙 자동 추출
- API 엔드포인트별 자연어 설명 + 예시 코드 생성
- README.md 자동 작성/업데이트
- CHANGELOG.md 자동 업데이트 (git log 기반)
- 설치/셋업 가이드 생성
- MCP 서버 도구 문서 생성

## 출력 형식

- OpenAPI 3.1 JSON/YAML
- 마크다운 문서 (README, CHANGELOG, 가이드)
- 인터랙티브 API 문서 페이지 (Mintlify/Fumadocs)

## 상태: Phase 2 (Week 5~6)
