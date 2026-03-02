# S1 — Agent Coverage Plan

- Sprint ID: `S1`
- 작성일: 2026-03-03
- 기준: G2 Agent Coverage Gate

---

## 작업-Agent 매핑 테이블

| # | 작업 | 담당 Agent | 보조 Agent | 비고 |
|---|------|-----------|-----------|------|
| 1 | EODHD API 클라이언트 구현 | `data-engineer-agent` | `fullstack-developer` | data-engineer-agent 미응답 시 대행 |
| 2 | SQLite 캐시 구현 | `data-engineer-agent` | `fullstack-developer` | WAL 모드, TTL 정책 |
| 3 | 기술적 지표 계산 | `data-engineer-agent` | `fullstack-developer` | pandas 수동 계산 |
| 4 | 시장 지표 수집 | `data-engineer-agent` | `fullstack-developer` | yfinance ^VIX, ^GSPC 등 |
| 5 | 전처리 파이프라인 | `data-engineer-agent` | `fullstack-developer` | 윈저라이징, 수정주가 |
| 6 | 단위 테스트 작성 | `data-engineer-agent` | `fullstack-developer` | pytest, mocking EODHD |
| 7 | 프로젝트 설정 | `fullstack-developer` | — | pyproject.toml, .env.example |
| 8 | Gate 문서 작성 | `technical-writer` | — | S1-* 문서 6종 |
| 9 | Skill 생성 (G3) | `backend-architect` | `technical-writer` | python-project-setup |
| 10 | Hub 동기화 | `hub-manager` | — | 신규 Skill 등록 |
| 11 | 품질 검증 (G5) | `risk-auditor-agent` | `quality-gate` | 커버리지 + 재현성 |
| 12 | Close-Out (G7) | `technical-writer` | `fullstack-developer` | sprint-closeout |

---

## 담당 Agent 현황

| Agent | 상태 | 파일 경로 |
|-------|------|---------|
| `data-engineer-agent` | ✅ 존재 | `.claude/agents/data-engineer-agent.md` |
| `fullstack-developer` | ✅ 존재 | `.claude/agents/fullstack-developer.md` |
| `backend-architect` | ✅ 존재 | `.claude/agents/backend-architect.md` |
| `technical-writer` | ✅ 존재 | `.claude/agents/technical-writer.md` |
| `risk-auditor-agent` | ✅ 존재 | `.claude/agents/risk-auditor-agent.md` |

**부재 Agent: 0건** — 모든 작업에 담당 Agent 배정 완료.

---

## G2 판정: PASS

- 미배정 작업: 0건
- 담당 Agent 부재: 0건
- G3 진행 가능 (공백 Skill 생성)
