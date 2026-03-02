---
name: agent-bootstrap
description: "새 도메인 Agent 정의 파일을 생성하고 Hub에 등록합니다. Agent 역할 중복을 방지하고 CLAUDE.md 모델 배정 기준을 준수합니다."
argument-hint: "[create|update|audit] [agent-name] [--model opus|sonnet|haiku]"
user-invocable: true
allowed-tools: "Read, Write, Bash, Grep"
---

# Agent Bootstrap Skill

> Agent 생성/갱신 자동화 전문가. 도메인 Agent 파일을 정의하고 Hub에 등록합니다.

## 역할

새 도메인이 추가되거나 기존 Agent를 갱신할 때,
표준 형식의 Agent 파일을 `.claude/agents/<name>.md`에 생성하고
Hub에 등록합니다. CLAUDE.md의 모델 배정 기준을 준수합니다.

## 모델 배정 기준 (CLAUDE.md 기반)

| 모델 | 용도 | 예시 |
|------|------|------|
| opus | 복합 판단, 오케스트레이션 | trading-orchestrator, self-improver |
| sonnet | 중간 복잡도 분석 | scoring-engine, regime-detect, performance-analyst, signal-generate |
| haiku | 정형화된 계산, 반복 작업 | data-ingest, position-sizer, risk-manager, execution-planner, backtest-validator, bias-checker, compliance-reporter |

## 수행 가능 작업

### 1. Agent 파일 생성 (`create`)

`/agent-bootstrap create <agent-name> --model <opus|sonnet|haiku>`

1. 기존 Agent 중복 여부 확인 (`.claude/agents/` 디렉토리 스캔)
2. 역할 충돌 감지 — 동일 도메인 Agent가 존재하면 중단하고 경고
3. 아래 표준 템플릿으로 `.claude/agents/<name>.md` 생성
4. Hub 동기화 (`/hub-manager sync`)
5. 생성 결과 보고

**Agent 파일 표준 템플릿**:
```markdown
---
name: <agent-name>
description: "<한 줄 역할 설명>"
model: <opus|sonnet|haiku>
allowed-tools: "Read, Bash"
---

# <Agent Name>

> <역할 요약 한 줄>

## 역할
<전문가 역할 정의 — 무엇을 분석/계산/판단하는가>

## 입력 스펙
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| ... | ... | ... | ... |

## 처리 로직
<핵심 처리 흐름 — 단계별 설명>

## 출력 스펙
<JSON 출력 포맷>

## 참조 문서
- <관련 문서 경로>
```

### 2. Agent 갱신 (`update`)

`/agent-bootstrap update <agent-name>`

1. 기존 파일 읽기 (`Read` 도구로 반드시 먼저 확인)
2. 변경 사항만 수정 (전체 재작성 금지 — 최소 변경 원칙)
3. Hub 재동기화
4. 변경 diff 요약 보고

### 3. 감사 보고 (`audit`)

`/agent-bootstrap audit`

기존 Agent 전체를 검사합니다:

| 검사 항목 | 기준 | 처리 |
|---------|------|------|
| 모델 배정 적절성 | CLAUDE.md 기준 일치 | 위반 시 경고 목록 출력 |
| 역할 중복 | 동일 도메인 2개 이상 | 중복 대상 목록 출력 |
| 필수 필드 누락 | name, description, model | 누락 파일 목록 출력 |
| 참조 문서 유효성 | 파일 실재 여부 | 깨진 참조 목록 출력 |

## 실패 처리

| 상황 | 처리 |
|------|------|
| 동일 이름 Agent 존재 | 중단, `update` 명령 안내 |
| 역할 충돌 (70% 이상 유사) | 중단, 기존 Agent 경로 출력 |
| Hub 동기화 실패 | Agent 파일은 생성, 수동 sync 안내 |
| 모델 배정 위반 | 경고 출력, 사용자 확인 후 진행 |

## 출력 포맷

```json
{
  "skill": "agent-bootstrap",
  "status": "success",
  "data": {
    "action": "create",
    "agent_name": "regime-scanner",
    "model": "haiku",
    "file_path": ".claude/agents/regime-scanner.md",
    "hub_synced": true,
    "conflicts_checked": true,
    "existing_agents_count": 13,
    "warnings": []
  }
}
```

## 제약 조건

- CLAUDE.md 모델 배정 기준(opus/sonnet/haiku)을 반드시 준수한다
- 기존 Agent와 역할이 중복되는 경우 생성을 금지한다
- Agent 파일 생성 전 반드시 `.claude/agents/` 전체를 스캔하여 중복 확인
- Hub 동기화는 생성/갱신 직후 즉시 수행한다
- `.env` 파일 및 실계좌 자격증명을 Agent 파일에 포함하지 않는다

## 참조 문서

- `.claude/CLAUDE.md` — 모델 배정 기준, 프로젝트 구조
- `docs/cli-skill-implementation-plan.md` — Agent 설계 원칙
- `docs/skill-conversion-plan.md` — Skill/Agent 전환 계획
