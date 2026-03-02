# S1 Skill Coverage Audit

> Gate: G1 | Sprint: S1 (Data Layer) | Date: 2026-03-03
> Auditor: `skill-auditor`
> Reference: `docs/sprints/S1-context.md`, `.claude/skills/`

---

## 1. Task-to-Skill Mapping Table

판정 기준:
- **PASS**: 전담 Skill이 Hub에 등록되어 있고 파일이 존재하며 해당 작업을 명시적으로 다룸
- **WARN**: Skill이 존재하나 부분 커버 또는 도메인 미스매치 (Node.js/SaaS 중심 설계를 Python 트레이딩에 그대로 적용 불가)
- **FAIL**: 매핑 가능한 Skill이 없거나 작업에 필수적인 동작이 정의되지 않음

| # | 작업 항목 | 담당 Skill | Skill 상태 | 커버 범위 | 판정 |
|---|----------|-----------|-----------|----------|------|
| 1 | EODHD API 클라이언트 구현 (yfinance fallback 포함) | `data-ingest` | Hub 등록 + 파일 존재 | EODHD Phase 1 + yfinance fallback 명시. `client.py` 구현 범위 정의됨 | **PASS** |
| 2 | SQLite 캐시 구현 (가격 24h TTL, 재무 7d TTL) | `data-ingest` | Hub 등록 + 파일 존재 | `cache.py` 파일 목록에 포함. TTL 정책 암묵적으로 포함 (소스 문서에 명시). 단, Skill 본문에 SQLite 스키마 설계 지침이 없음 | **WARN** |
| 3 | 기술적 지표 계산 (ATR21, ADX14, MA50/200, RSI14, OBV, MACD) | `data-ingest` | Hub 등록 + 파일 존재 | 지표 7종 전부 Skill 본문 "기술적 지표" 섹션에 명시적으로 열거됨 | **PASS** |
| 4 | 시장 지표 수집 (VIX, S&P500 vs 200MA, 수익률 곡선) | `data-ingest` | Hub 등록 + 파일 존재 | "시장 지표" 섹션에 VIX, sp500_vs_200ma, yield_curve_slope 명시. yfinance 소스 확정됨 | **PASS** |
| 5 | 전처리 파이프라인 (윈저라이징, 결측값, 수정주가) | `data-ingest` | Hub 등록 + 파일 존재 | "전처리" 섹션에 3가지 항목 명시 (1st/99th 백분위 윈저라이징, forward fill → drop, 수정주가) | **PASS** |
| 6 | 단위 테스트 작성 (pytest) | `test-generator` | Hub 등록 + 파일 존재 | Skill이 Vitest + Playwright 기반으로 설계됨 (JavaScript 프레임워크). pytest/Python 환경에 대한 언급 없음 | **WARN** |
| 7 | 프로젝트 설정 (pyproject.toml, .env.example) | `scaffolding` | Hub 등록 + 파일 존재 | Skill이 Next.js 15 + TypeScript + SaaS 구조 전용으로 설계됨. `pyproject.toml` 또는 Python 프로젝트 구조 생성 능력 없음 | **FAIL** |
| 8 | Gate 문서 작성 (context, skill-check, agent-plan, verify, release-review, retrospective) | `doc-generator` + `sprint-closeout` | Hub 등록 + 파일 존재 | `doc-generator`는 OpenAPI/README 생성 중심(JavaScript). `sprint-closeout`은 G7 회고 + commit/push 워크플로를 커버. Gate 문서 생성 전반은 `doc-generator`의 부분 커버에 의존 | **WARN** |

---

## 2. Gap Analysis — 공백 Skill 목록

### 2.1 FAIL 항목 — 즉시 생성 필요

| 공백 Skill | 대상 작업 | 필요 이유 | 생성 우선순위 |
|-----------|----------|----------|-------------|
| `python-project-setup` | 작업 #7 (pyproject.toml, .env.example) | 기존 `scaffolding` Skill은 Next.js/SaaS 전용. Python 프로젝트 초기화 (pyproject.toml, pytest.ini, .env.example, requirements 관리)를 다루는 Skill이 없음 | 높음 (G3 생성 대상) |

### 2.2 WARN 항목 — 보강 또는 신규 생성 권고

| 기존 Skill | 대상 작업 | 문제 | 권고 |
|-----------|----------|------|------|
| `data-ingest` | 작업 #2 (SQLite 캐시) | Skill 본문에 SQLite 스키마 설계 (`prices` 테이블, `fundamentals` 테이블, TTL 컬럼), WAL 모드 설정, 캐시 무효화 로직이 정의되어 있지 않음. `db-architect` Skill은 Supabase PostgreSQL 전용 | `data-ingest` SKILL.md에 SQLite 캐시 설계 섹션 추가 또는 `market-data-qc` Skill에 캐시 검증 항목 포함 |
| `test-generator` | 작업 #6 (pytest) | Skill이 JavaScript 생태계(Vitest, Playwright) 전용으로 작성됨. pytest fixtures, conftest.py, mock 전략 (unittest.mock, pytest-mock), pandas DataFrame 어서션 패턴 없음 | `test-generator` Skill 내에 Python/pytest 섹션 추가, 또는 `python-test-generator` Skill 신규 생성 |
| `doc-generator` | 작업 #8 (Gate 문서) | Skill이 OpenAPI 스펙 추출 및 README 자동 생성 중심. Gate 문서 포맷 (context, verify, release-review, retrospective 표준 템플릿)을 인식하지 못함 | `sprint-closeout` Skill이 G7 회고를 다루므로 G5-G6 문서(verify, release-review)는 Gate Runbook 참조로 직접 작성 허용. 현재 WARN으로 유지 |

---

## 3. Skill 커버리지 요약

| 항목 | 수치 |
|------|------|
| S1 총 작업 수 | 8건 |
| PASS (완전 커버) | 4건 |
| WARN (부분 커버) | 3건 |
| FAIL (미커버) | 1건 |
| 공백 Skill (FAIL 기준) | 1종 (`python-project-setup`) |
| 보강 권고 Skill | 2종 (`data-ingest` 보강, `test-generator` Python 섹션 추가) |

---

## 4. Gate G3 생성 대상

S1-context.md §3에서 G3 Exit Criteria는 "누락 Skill 0건"이다. 아래를 G3에서 처리한다.

| 순서 | 조치 | 대상 | 담당 Agent |
|------|------|------|----------|
| 1 | 신규 생성 | `python-project-setup` SKILL.md | `data-engineer-agent` (대행: `fullstack-developer`) |
| 2 | Skill 보강 | `data-ingest` SKILL.md — SQLite 캐시 설계 섹션 추가 | `data-engineer-agent` |
| 3 | Skill 보강 | `test-generator` SKILL.md — Python/pytest 섹션 추가 | `data-engineer-agent` |
| 4 | Hub 동기화 | `hub-manager sync` 실행 | 자동 |

> S1-context.md §3 G3 항목에서 `market-data-qc` Skill 생성 가능성을 언급한다. 현 감사 기준으로는 `data-ingest`가 시장 지표 수집을 커버하므로 `market-data-qc`는 G3에서 선택 항목으로 분류한다. G4 빌드 진행 후 데이터 품질 검증 요건이 확인되면 G5 이전에 생성한다.

---

## 5. G1 Exit Criteria 판정

| Exit Criteria | 결과 |
|--------------|------|
| `S1-skill-check.md` 문서 존재 | PASS |
| 모든 S1 작업에 Skill 매핑 완료 | PASS (미매핑 0건 — FAIL 항목도 Skill 지정됨, 단 생성 전) |
| 공백 Skill 목록 명시 완료 | PASS (1종 FAIL, 2종 WARN 식별) |
| G3 생성 대상 우선순위 정의 | PASS |

**G1 판정: PASS**

다음 Gate: G2 (Agent Coverage). G3에서 `python-project-setup` 생성 및 `data-ingest`, `test-generator` Skill 보강 후 G4(Build) 진입한다.
