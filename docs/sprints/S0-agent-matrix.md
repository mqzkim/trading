# S0 Agent Coverage Matrix

> Gate: G2 | Date: 2026-03-03 | Status: In Progress

---

## 1. Gate별 Agent 배정

Gate 수행에 필요한 주담당 Agent와 대행 Agent의 현재 존재 여부를 나타낸다.
존재 여부는 `.claude/agents/` 디렉터리 내 정의 파일 확인 기준이다.

| Gate | 이름 | 주담당 Agent | 현재 존재 | 대행 Agent | 대행 존재 | 상태 |
|------|------|------------|:-------:|-----------|:-------:|------|
| G0 | Context Init | `trading-orchestrator-lead` | 아니오 | `fullstack-developer` | 예 | WARN — 대행 수행 |
| G1 | Skill Coverage | `skill-auditor` | 예 | — | — | OK |
| G2 | Agent Coverage | `backend-architect` | 예 | — | — | OK |
| G3 | Bootstrap | `backend-architect` + `technical-writer` | 예 / 예 | — | — | OK |
| G4 | Build | `fullstack-developer` | 예 | — | — | OK |
| G5 | Verify | `skill-auditor` | 예 | — | — | OK |
| G6 | Release Review | `trading-orchestrator-lead` | 아니오 | `fullstack-developer` | 예 | WARN — 대행 수행 |
| G7 | Full Close-Out | `technical-writer` + `fullstack-developer` | 예 / 예 | — | — | OK |

**상태 범례**

- `OK` — 주담당 Agent가 존재하며 즉시 수행 가능
- `WARN` — 주담당 Agent 부재, 대행으로 진행 가능하나 G3 생성 필수

---

## 2. 현재 등록된 Agent 전체 목록

`.claude/agents/` 기준 실제 존재하는 Agent 파일 목록이다.

| Agent 이름 | 파일 경로 | 도메인 |
|-----------|----------|-------|
| `backend-architect` | `.claude/agents/backend-architect.md` | 백엔드 / API 설계 |
| `frontend-developer` | `.claude/agents/frontend-developer.md` | UI / 프론트엔드 |
| `fullstack-developer` | `.claude/agents/fullstack-developer.md` | 풀스택 범용 |
| `technical-writer` | `.claude/agents/technical-writer.md` | 문서 / 콘텐츠 |
| `ui-ux-designer` | `.claude/agents/ui-ux-designer.md` | 디자인 |
| `hub-manager` | `.claude/agents/hub-manager.md` | Skill Hub 관리 |
| `skill-auditor` | `.claude/agents/skill-auditor.md` | Skill 감사 |
| `llms-maintainer` | `.claude/agents/llms-maintainer.md` | LLM 모델 관리 |

총 8개 Agent 등록됨.

---

## 3. 부재 Agent — G3 생성 대상

S0 Gate 수행 및 S1 이후 트레이딩 도메인 작업을 위해 필요하나 현재 존재하지 않는 Agent 목록이다.
이 10종은 G3(Bootstrap Gate)에서 반드시 생성되어야 한다.

| Agent 이름 | 역할 요약 | 모델 배정 | 생성 책임 |
|-----------|----------|:-------:|---------|
| `trading-orchestrator-lead` | 스프린트 전체 조율, Gate 판정, 복합 의사결정 | opus | `backend-architect` + `technical-writer` |
| `data-engineer-agent` | 시장 데이터 수집, 정제, 캐싱 파이프라인 관리 | haiku | `backend-architect` |
| `fundamental-analyst-agent` | F-Score, Z-Score, M-Score 등 기본적 분석 수행 | haiku | `backend-architect` |
| `technical-analyst-agent` | 추세, 모멘텀, 차트 패턴 기술적 분석 수행 | haiku | `backend-architect` |
| `sentiment-analyst-agent` | 시장 심리, 뉴스 감성, 내부자 거래 분석 | haiku | `backend-architect` |
| `regime-analyst-agent` | 시장 레짐 감지 (Bull / Bear / Sideways / Crisis) | sonnet | `backend-architect` |
| `risk-auditor-agent` | 리스크 한도 준수 감사, 낙폭 방어 단계 모니터링 | sonnet | `backend-architect` |
| `execution-ops-agent` | Alpaca Paper Trading 주문 실행, 포지션 관리 | sonnet | `backend-architect` |
| `backtest-methodology-agent` | 백테스트 설계, 검증, 과최적화 방지 감사 | sonnet | `backend-architect` + `technical-writer` |
| `performance-attribution-agent` | 성과 귀속 분석, Sharpe / MDD / Alpha 측정 | opus | `backend-architect` + `technical-writer` |

**모델 배정 기준** (CLAUDE.md 참조)

- `opus` — Orchestrator 및 복합 판단이 필요한 Agent (2개)
- `sonnet` — 중간 복잡도 분석 Agent (4개)
- `haiku` — 정형화된 계산 중심 Agent (4개)

---

## 4. S0 전체 작업 — Agent 매핑

S0 각 Gate의 세부 작업과 담당 Agent 매핑이다.

| 작업 ID | 작업 내용 | 담당 Agent | 비고 |
|--------|---------|----------|-----|
| S0-G0-01 | S0-context.md 작성 (범위, 성공기준, 리스크) | `fullstack-developer` | `trading-orchestrator-lead` 부재로 대행 |
| S0-G1-01 | 전체 작업 Skill 매핑 감사 수행 | `skill-auditor` | — |
| S0-G1-02 | S0-skill-matrix.md 작성 | `skill-auditor` | — |
| S0-G2-01 | 전체 작업 Agent 매핑 수행 | `backend-architect` | 이 문서 |
| S0-G2-02 | 부재 Agent 식별 목록 작성 | `backend-architect` | — |
| S0-G3-01 | 공백 Skill 4종 파일 생성 | `backend-architect` + `technical-writer` | agent-bootstrap, sprint-closeout, integration-tester, paper-trading-ops |
| S0-G3-02 | 도메인 Agent 10종 정의 파일 생성 | `backend-architect` + `technical-writer` | 이 표 3번 목록 전체 |
| S0-G3-03 | hub-manager 동기화 실행 | `hub-manager` | 신규 Skill + Agent 전체 등록 |
| S0-G3-04 | skill-auditor 재감사 (누락 0건 확인) | `skill-auditor` | G3 Exit Criteria 조건 |
| S0-G4-01 | gate-runbook.md 작성 (G0~G7 표준 절차) | `fullstack-developer` | `technical-writer` 보조 |
| S0-G5-01 | Gate 드라이런 시나리오 설계 | `skill-auditor` | — |
| S0-G5-02 | 드라이런 실행 및 S0-validation.md 기록 | `skill-auditor` | — |
| S0-G6-01 | 전 Gate 판정 결과 수집 | `fullstack-developer` | `trading-orchestrator-lead` 부재로 대행 |
| S0-G6-02 | S0-release-review.md 작성 (최종 PASS/WARN/FAIL) | `fullstack-developer` | — |
| S0-G7-01 | MEMORY.md 업데이트 | `technical-writer` | — |
| S0-G7-02 | S0-retrospective.md 작성 | `technical-writer` | — |
| S0-G7-03 | git commit (Conventional Commit 형식) | `fullstack-developer` | `git add -A` 금지 |
| S0-G7-04 | git push 및 원격 반영 확인 | `fullstack-developer` | 강제 push 금지 |

---

## 5. 결론

| 항목 | 수치 |
|------|------|
| Gate 수 (G0 ~ G7) | 8개 |
| 총 요구 Agent (Hub 등록 기준) | 18개 |
| 현재 존재 | 8개 |
| 현재 부재 | 10개 |
| G3 생성 필수 | 10개 |
| 대행으로 진행 가능한 WARN Gate | 2개 (G0, G6) |
| 즉시 수행 가능한 OK Gate | 6개 (G1, G2, G3, G4, G5, G7) |

**대행 수행 조건 (WARN Gate)**

G0와 G6는 `trading-orchestrator-lead` 부재로 인해 `fullstack-developer`가 대행한다.
G3 완료 후 `trading-orchestrator-lead`가 생성되면 이후 스프린트(S1~)부터 정식 담당으로 전환한다.

**G3 진입 조건**

이 문서(G2)가 완성되면 G3 진입이 허용된다.
G3에서 도메인 Agent 10종 생성과 hub-manager 동기화가 완료되어야 부재 상태가 해소된다.
