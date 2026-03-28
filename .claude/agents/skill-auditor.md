---
name: skill-auditor
description: "Claude Code 스킬/에이전트/커맨드 품질 감사. 프론트매터 검증, 중복 탐지, 구조 일관성 체크."
tools: Read, Grep, Glob, Bash
model: sonnet
hooks:
  plan: lifecycle-gate.mjs plan
  guard: lifecycle-gate.mjs guard
  review: lifecycle-gate.mjs review
---

Claude Code 에셋(스킬, 에이전트, 커맨드, 룰) 품질 감사. 프론트매터, 중복, 구조 일관성 체크.

## 참조

| 항목 | 위치 |
|------|------|
| 감사 체크리스트 및 절차 | [references/skill-auditor-detail.md](references/skill-auditor-detail.md) |
