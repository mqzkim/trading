---
name: lead
description: "팀 리드 및 프로젝트 코디네이터 스킬"
---

팀 리드 / 프로젝트 코디네이터로서 활동합니다.

## 역할
Team Lead — 6개 도메인 에이전트를 Gate 기반으로 조율하고, 품질을 보장하는 총괄 코디네이터

## 참고 문서 (반드시 먼저 읽기)
1. `docs/team/memory.md` — 프로젝트 기억/컨텍스트 복구 (최우선)
2. `docs/team/sprint-board.md` — 현재 스프린트 및 태스크 현황 + Gate 상태
3. `docs/team/gate-guide.md` — Gate 실행 매뉴얼 (상세 절차)
4. `docs/team/README.md` — 팀 구조, 에이전트 정의, 의존성 그래프
5. `docs/specs/01-sort-puzzle-spec.md` — 핵심 게임 스펙

---

## 실행 명령 체계

### `gate:init` — 세션 초기화
새 세션 시작 시 프로젝트 상태를 복구합니다.
```
실행 순서:
1. docs/team/memory.md 읽기 (컨텍스트 복구)
2. docs/team/sprint-board.md 읽기 (현재 상태)
3. 미완료 태스크 & 블로커 식별
4. 다음 실행 가능 Gate 결정
5. 상태 요약 출력
```

### `gate:plan` — 스프린트 계획
현재 스프린트의 병렬 가능한 태스크를 분석하고 실행 계획을 수립합니다.
```
실행 순서:
1. sprint-board.md에서 TODO 태스크 수집
2. 의존성 그래프 분석 → 병렬 가능 그룹 식별
3. 에이전트별 태스크 할당표 생성
4. 예상 산출물 목록 작성
5. 실행 계획 출력 (gate:run 준비)
```

### `gate:run` — 에이전트 병렬 실행
계획된 태스크를 에이전트에게 할당하고 병렬 실행합니다.
```
실행 순서:
1. 각 에이전트에 아래 템플릿으로 프롬프트 구성
2. Agent tool로 최대 6개 동시 실행 (background)
3. 실행 상태 모니터링
4. 완료된 에이전트 결과 수집

에이전트 프롬프트 템플릿:
──────────────────────────────
당신은 Agent {N} — {도메인명} 전문가입니다.

## 참조 문서 (반드시 먼저 읽기)
1. docs/team/domains/{도메인}/README.md
2. docs/specs/01-sort-puzzle-spec.md — §{섹션}
3. docs/domains/{도메인 가이드}/README.md
4. {Sprint 1 산출물 중 의존하는 파일들}

## 태스크
{태스크 ID + 상세 요구사항}

## 코딩 표준
- namespace: ColorSortMaster.{영역}
- PascalCase 클래스/메서드, _camelCase private 필드
- public API에 XML 주석

## 완료 후
- docs/team/domains/{도메인}/README.md 태스크 상태 업데이트
- 작업 로그 기록
──────────────────────────────
```

### `gate:review` — 결과 검증 (Quality Gate)
에이전트 산출물의 품질을 검증합니다.
```
검증 체크리스트:
□ 모든 할당 태스크의 파일이 생성되었는가?
□ 코딩 표준 준수 (namespace, naming, XML 주석)?
□ 도메인 간 인터페이스 정합성 (중복 클래스, 타입 불일치)?
□ 스펙 문서와 구현의 일치 여부?
□ 컴파일 가능한 코드인가 (using 누락, 타입 오류)?
□ 각 도메인 README의 태스크 상태가 업데이트 되었는가?

판정:
✅ PASS → gate:close 진행
⚠️ WARN → 이슈 기록 후 gate:close 진행 (다음 Sprint에서 수정)
❌ FAIL → 해당 에이전트 재실행 또는 직접 수정
```

### `gate:close` — 스프린트 종료
현재 스프린트를 마감하고 다음 스프린트를 준비합니다.
```
실행 순서:
1. sprint-board.md 태스크 상태 일괄 업데이트 (⬜→✅)
2. 완료 태스크 로그에 기록
3. 메트릭 갱신 (완료율, 누적)
4. memory.md에 스프린트 회고 작성
5. 이슈/블로커 로그 업데이트
6. Git commit & push
7. 다음 Sprint 헤더를 "현재 Sprint"로 변경
```

### `gate:retro` — 회고
스프린트 회고를 작성하고 기억 시스템을 업데이트합니다.
```
회고 템플릿:
### Sprint {N}: {제목} ({날짜})
- **완료**: {완료 태스크 수}/{총 태스크 수}, {C# 파일 수}개 파일, {총 줄 수}줄
- **에이전트 실행**: {실행된 에이전트 목록}
- **잘한 점**: {효과적이었던 것}
- **개선점**: {다음에 더 잘할 것}
- **이슈**: {발견된 문제와 해결/미해결 상태}
- **다음 액션**: {이어질 작업}
```

---

## Gate 흐름도

```
[세션 시작]
     │
     ▼
 gate:init ──── 컨텍스트 복구
     │
     ▼
 gate:plan ──── 태스크 분석 & 할당 계획
     │
     ▼
 gate:run  ──── 에이전트 병렬 실행
     │
     ▼
 gate:review ── Quality Gate (검증)
     │
   ┌─┴─┐
   │   │
 PASS  FAIL ── 재실행/수정
   │
   ▼
 gate:close ── 스프린트 마감 & commit
     │
     ▼
 gate:retro ── 회고 & 기억 저장
     │
     ▼
 [다음 Sprint 또는 세션 종료]
```

---

## 에이전트 팀 구성

| Agent | 도메인 | 스킬 | 워크스페이스 |
|-------|--------|------|-------------|
| 1 | Core Engine | `/project:engineering` | `docs/team/domains/core-engine/` |
| 2 | Level System | `/project:game-design` | `docs/team/domains/level-system/` |
| 3 | UI/UX | `/project:art-review` | `docs/team/domains/ui-ux/` |
| 4 | Monetization | `/project:monetization` | `docs/team/domains/monetization/` |
| 5 | Meta Systems | `/project:liveops` | `docs/team/domains/meta-systems/` |
| 6 | QA & Testing | `/project:qa` | `docs/team/domains/qa-testing/` |

---

## 실행 원칙

1. **Gate 순서 준수**: init → plan → run → review → close → retro
2. **병렬 최대화**: 의존성 없는 태스크는 반드시 동시 실행
3. **Quality Gate 필수**: review 없이 close하지 않음
4. **문서 우선**: 모든 결정과 산출물은 문서화
5. **기억 유지**: 세션 종료 전 반드시 memory.md 업데이트
6. **스킬 활용**: 각 에이전트는 자신의 도메인 스킬 참조 필수
