# Reviewer Skill Specification

> 30년 이상 경력의 서버/백엔드 시니어 아키텍트 수준의 심층 코드 리뷰를 수행하는 Claude Code Skill
>
> 작성일: 2026-02-27 | 버전: 1.0-draft

---

## 목차

1. [개요](#1-개요)
2. [설계 원칙](#2-설계-원칙)
3. [Skill 구조](#3-skill-구조)
4. [SKILL.md 설계](#4-skillmd-설계)
5. [리뷰 프레임워크](#5-리뷰-프레임워크)
6. [리뷰 영역별 상세 체크리스트](#6-리뷰-영역별-상세-체크리스트)
7. [심각도 분류 체계](#7-심각도-분류-체계)
8. [출력 형식](#8-출력-형식)
9. [언어별 참조 가이드 전략](#9-언어별-참조-가이드-전략)
10. [기존 솔루션 분석 및 차별화](#10-기존-솔루션-분석-및-차별화)
11. [고급 기능](#11-고급-기능-advanced-features)
12. [구현 로드맵](#12-구현-로드맵)
13. [참고 자료](#13-참고-자료)

---

## 1. 개요

### 1.1 배경

코드 리뷰는 소프트웨어 품질의 가장 효과적인 게이트키퍼다. Google의 엔지니어링 프랙티스에 따르면, 코드 리뷰의 핵심 목적은 "코드베이스의 전반적인 건강 상태가 시간이 지남에 따라 개선되도록 하는 것"이다. 하지만 대부분의 리뷰는 포맷팅, 네이밍 같은 표면적 이슈에 머무르며, 아키텍처적 결함, 숨겨진 보안 취약점, 성능 병목, 동시성 버그 같은 **진짜 치명적인 문제**를 놓친다.

이 Skill은 30년 이상의 서버/백엔드 개발 경험을 가진 시니어 아키텍트의 관점을 체계적으로 인코딩하여, 표면적 리뷰가 아닌 **심층적 구조 분석**을 수행한다.

GitHub Staff Engineer의 통찰에 따르면: *"최고의 리뷰 코멘트는 diff 자체와는 거의 관련이 없다. 시스템의 나머지 부분을 이해하는 것에서 나온다."* 예를 들어, "이 메서드를 여기에 추가할 필요 없습니다, 저쪽에 이미 존재하니까요"와 같은 코멘트는 diff만 봐서는 절대 나올 수 없다. 이것이 바로 시니어 리뷰어의 가치다.

또한, 2026년 AI 생성 코드 시대에서 코드 리뷰의 중요성은 더욱 커졌다. 470개 PR을 분석한 업계 연구에 따르면, AI가 생성한 코드는 인간이 작성한 코드보다 **1.7배 더 많은 결함**을 포함한다. "코드는 이제 쉽게 생성할 수 있지만, 리뷰하기는 여전히 어렵다." 이 Skill은 바로 이 격차를 메운다.

### 1.2 목표

| 목표 | 설명 |
|------|------|
| **심층 분석** | 단순 코드 스타일이 아닌, 아키텍처/보안/성능/동시성/데이터 무결성 수준의 리뷰 |
| **30년 경험의 인코딩** | 시니어 백엔드 엔지니어가 본능적으로 감지하는 패턴과 안티패턴을 체계화 |
| **실행 가능한 피드백** | "이건 문제가 있다"가 아닌 "이렇게 수정하라"는 구체적 해법 제시 |
| **맥락 인식** | 코드의 변경 범위와 영향도를 파악하여 전체 시스템 관점에서 판단 |
| **교육적 가치** | 왜 이것이 문제인지, 어떤 원칙을 위반하는지 근거와 함께 설명 |

### 1.3 비-목표 (Non-Goals)

- 코드 포맷팅, 린팅 이슈 지적 (이것은 자동화 도구의 역할)
- 모든 파일에 대한 무차별적 전수검사 (변경된 코드와 그 영향 범위에 집중)
- 개인 취향 기반의 스타일 강제 (Google 원칙: "Nit:"로 구분, PR 블로킹 금지)
- 프론트엔드 UI/UX 리뷰 (서버/백엔드에 특화)

---

## 2. 설계 원칙

### 2.1 Skill 설계 원칙 (Claude Code Skill Best Practices 기반)

| 원칙 | 적용 |
|------|------|
| **간결함 (Concise is key)** | SKILL.md는 500줄 이하. Claude가 이미 아는 것은 반복하지 않음 |
| **점진적 공개 (Progressive Disclosure)** | 메타데이터만 먼저 로드 → 관련 참조 파일만 필요시 로드 |
| **적절한 자유도** | 아키텍처 분석은 높은 자유도, 보안 체크리스트는 낮은 자유도 |
| **3인칭 서술** | description은 "Performs deep code review..."로 시작 |
| **피드백 루프** | 리뷰 → 심각도 분류 → 우선순위 정렬 → 최종 출력 |

### 2.2 리뷰 철학 (시니어 아키텍트의 관점)

```
30년 경력 시니어의 코드 리뷰 우선순위:

1. [치명적] 이 코드가 프로덕션에서 장애를 일으킬 수 있는가?
2. [보안]   이 코드가 공격 표면을 넓히는가?
3. [데이터] 이 코드가 데이터를 잃거나 오염시킬 수 있는가?
4. [설계]   이 코드가 시스템을 유지보수 불가능하게 만드는가?
5. [성능]   이 코드가 규모 확장 시 병목이 되는가?
6. [운영]   이 코드가 장애 시 디버깅/복구를 어렵게 하는가?
```

핵심 마인드셋: **"이 코드가 새벽 3시에 나를 깨울 것인가?"**

---

## 3. Skill 구조

### 3.1 디렉토리 레이아웃

```
.claude/skills/deep-reviewer/
├── SKILL.md                          # 메인 진입점 (필수, ~300줄)
│
├── references/                        # 참조 문서 (필요시 로드)
│   ├── architecture-review.md         # 아키텍처 리뷰 가이드
│   ├── security-review.md             # 보안 리뷰 가이드 (OWASP 기반)
│   ├── performance-review.md          # 성능 리뷰 가이드
│   ├── concurrency-review.md          # 동시성/병렬 처리 리뷰
│   ├── database-review.md             # DB/쿼리/데이터 무결성 리뷰
│   ├── api-review.md                  # API 설계 리뷰
│   ├── error-handling-review.md       # 에러 처리/복원력 리뷰
│   └── observability-review.md        # 로깅/모니터링/운영 리뷰
│
├── languages/                         # 언어별 특화 가이드 (필요시 로드)
│   ├── java-spring.md                 # Java/Spring Boot 특화
│   ├── python-django.md               # Python/Django/FastAPI 특화
│   ├── go.md                          # Go 특화
│   ├── nodejs-typescript.md           # Node.js/TypeScript 특화
│   ├── rust.md                        # Rust 특화
│   └── csharp-dotnet.md               # C#/.NET 특화
│
├── assets/                            # 리뷰 템플릿
│   ├── review-output-template.md      # 리뷰 결과 출력 템플릿
│   └── severity-guide.md             # 심각도 분류 레퍼런스
│
└── scripts/
    └── diff-analyzer.sh               # 변경 범위/복잡도 사전 분석
```

### 3.2 점진적 공개 전략

```
[항상 로드] SKILL.md (name + description)
     │
     ├─ [1단계] SKILL.md 본문 (~300줄)
     │   핵심 리뷰 프레임워크, 심각도 체계, 출력 형식
     │
     ├─ [2단계] 관련 references/ 파일
     │   코드의 특성에 따라 선택적 로드
     │   예: DB 쿼리가 포함된 PR → database-review.md 로드
     │
     └─ [3단계] languages/ 파일
         감지된 프로그래밍 언어에 따라 로드
         예: Java/Spring PR → java-spring.md 로드
```

토큰 효율성: React PR 리뷰 시 Go/Rust 가이드는 로드하지 않음. 이 전략으로 평균 컨텍스트 소비를 60-70% 절감.

---

## 4. SKILL.md 설계

### 4.1 Frontmatter

```yaml
---
name: deep-reviewer
description: Performs deep, expert-level code review from the perspective of a senior backend architect with 30+ years of experience. Focuses on architecture, security, performance, concurrency, data integrity, and operational concerns rather than superficial style issues. Use when reviewing PRs, code changes, or when the user asks for code review, architecture review, or security review.
allowed-tools: Read, Grep, Glob, Bash(git diff:*), Bash(git log:*), Bash(git show:*)
---
```

**설계 결정 근거:**

| 필드 | 값 | 근거 |
|------|-----|------|
| `name` | `deep-reviewer` | 일반적인 `review`가 아닌, 심층 리뷰를 강조. 하이픈으로 연결 |
| `description` | 위 참조 | 3인칭 서술. "30+ years", "architecture", "security", "performance" 등 키 트리거 단어 포함. 1024자 이내 |
| `allowed-tools` | Read, Grep, Glob, git | 코드를 읽고 검색할 수 있되, 수정은 불가 (리뷰어는 코드를 변경하지 않음) |
| `disable-model-invocation` | 미설정 (기본값 false) | Claude가 리뷰 요청을 감지하면 자동 로드 가능 |
| `context` | 미설정 (인라인) | 대화 맥락을 유지하여 후속 질문에 대응 가능 |

### 4.2 본문 설계 방향

SKILL.md 본문은 다음 구조로 구성:

1. **페르소나 정의** — 30년 경력 시니어 아키텍트의 관점과 우선순위
2. **리뷰 워크플로우** — 단계별 분석 프로세스 (체크리스트 포함)
3. **심각도 분류 체계** — 발견 이슈의 분류 및 우선순위 기준
4. **출력 형식** — 리뷰 결과의 표준 포맷
5. **참조 파일 네비게이션** — 상세 가이드로의 진입점

---

## 5. 리뷰 프레임워크

### 5.1 리뷰 워크플로우 (7단계)

```
┌─────────────────────────────────────────────────────────────┐
│                    DEEP REVIEW WORKFLOW                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Step 1: 변경 범위 파악 (Scope Analysis)                     │
│  ├─ git diff 분석                                            │
│  ├─ 변경된 파일/모듈 목록화                                   │
│  └─ 영향 범위(blast radius) 평가                             │
│           │                                                  │
│  Step 2: 컨텍스트 수집 (Context Gathering)                   │
│  ├─ 관련 코드 읽기 (변경 주변부 포함)                         │
│  ├─ 호출자/피호출자 파악                                      │
│  └─ 관련 테스트 코드 확인                                     │
│           │                                                  │
│  Step 3: 아키텍처 분석 (Architecture Analysis)               │
│  ├─ 설계 원칙 준수 여부 (SOLID, DRY, KISS)                   │
│  ├─ 계층 간 의존성 방향                                       │
│  ├─ 추상화 수준의 적절성                                      │
│  └─ 변경이 기존 아키텍처와 일관적인가                          │
│           │                                                  │
│  Step 4: 보안 분석 (Security Analysis)                       │
│  ├─ OWASP Top 10 (2025) 기준 점검                            │
│  ├─ 입력 검증, 인증/인가, 데이터 보호                          │
│  ├─ 하드코딩된 비밀값, 노출된 민감 정보                        │
│  └─ 공급망 보안 (의존성)                                      │
│           │                                                  │
│  Step 5: 성능 및 확장성 분석 (Performance & Scalability)     │
│  ├─ 시간/공간 복잡도                                          │
│  ├─ DB 쿼리 효율성 (N+1, 인덱스, 쿼리 플랜)                  │
│  ├─ 메모리 관리 및 리소스 누수                                 │
│  └─ 동시 사용자 증가 시 병목점                                 │
│           │                                                  │
│  Step 6: 동시성 및 데이터 무결성 (Concurrency & Data)        │
│  ├─ Race condition, Deadlock 가능성                           │
│  ├─ 트랜잭션 경계 및 격리 수준                                 │
│  ├─ 분산 시스템에서의 일관성 보장                               │
│  └─ 캐시 무효화 전략                                          │
│           │                                                  │
│  Step 7: 운영 및 복원력 (Operability & Resilience)           │
│  ├─ 에러 처리의 적절성                                         │
│  ├─ 로깅/모니터링 충분성                                       │
│  ├─ 장애 시 디버깅 가능성                                      │
│  ├─ 배포 안전성 (롤백 가능, 하위 호환성)                       │
│  └─ 그레이스풀 디그레이데이션                                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 "Diff 너머를 보라" — 시스템 컨텍스트 분석

시니어 리뷰어의 핵심 역량은 변경된 코드 자체가 아니라, 그것이 **전체 시스템에 미치는 파급 효과**를 파악하는 것이다:

```
[Diff 너머 분석 체크리스트]

• 이 변경의 호출자(caller)는 누구인가? 호출 패턴이 바뀌는가?
• 이 코드가 이미 다른 곳에 존재하지는 않는가? (중복 방지)
• 이 변경이 기존 계약(contract/interface)을 깨지는 않는가?
• 이 코드를 모르는 사람이 6개월 후에 유지보수할 수 있는가?
• 배포 순서에 의존성이 있는가? (DB 마이그레이션 → 코드 배포)
• 롤백 시 이 변경을 안전하게 되돌릴 수 있는가?
• 이 코드가 예상치 못한 부하 상황(바이럴, 대규모 사용자)에서 어떻게 동작하는가?
```

### 5.3 "시니어의 직관" 패턴 — 경험에서 오는 감지 포인트

30년 경력의 시니어가 본능적으로 감지하는 것들을 명시적으로 코딩:

```
[위험 신호 - 즉시 깊이 파고들 것]

• 트랜잭션 없이 다중 테이블 업데이트
• catch 블록에서 예외를 삼키는 코드 (빈 catch 또는 로그만)
• 사용자 입력이 직접 SQL/명령어/경로에 삽입됨
• synchronized/lock 없이 공유 상태 변경
• 무한 성장 가능한 컬렉션/큐/캐시 (메모리 누수)
• 외부 API 호출에 타임아웃/재시도/서킷브레이커 없음
• 환경 변수나 설정 파일의 하드코딩된 비밀값
• 삭제/업데이트 쿼리에 WHERE 절 없음 또는 검증 없음
• 분산 환경에서 로컬 메모리 기반 상태 관리
• 비동기 처리에서 에러 핸들링 누락
• 배포 시 하위 호환성이 깨지는 스키마 변경
• 로그에 PII(개인정보)나 토큰이 포함됨
```

---

## 6. 리뷰 영역별 상세 체크리스트

### 6.1 아키텍처 리뷰 (`references/architecture-review.md`)

| 범주 | 점검 항목 |
|------|-----------|
| **SOLID 원칙** | SRP: 하나의 클래스/함수가 하나의 책임만 갖는가? OCP: 확장에 열려 있고 수정에 닫혀 있는가? LSP: 서브타입이 부모 타입을 대체할 수 있는가? ISP: 불필요한 의존성을 강제하지 않는가? DIP: 고수준 모듈이 저수준 모듈에 직접 의존하지 않는가? |
| **계층 구조** | 프레젠테이션 ↔ 비즈니스 ↔ 데이터 계층의 의존성 방향이 올바른가? 계층을 건너뛰는 직접 호출이 없는가? |
| **결합도/응집도** | 모듈 간 결합도가 낮은가? 모듈 내 응집도가 높은가? 변경의 파급 효과(ripple effect)가 제한적인가? |
| **설계 패턴** | 패턴이 올바르게 적용되었는가? 과도한 패턴 적용(over-engineering)은 없는가? 패턴의 의도가 명확한가? |
| **경계 컨텍스트** | 도메인 경계가 명확한가? 바운디드 컨텍스트 간 통신이 적절한가? |

### 6.2 보안 리뷰 (`references/security-review.md`)

**OWASP Top 10 (2025) 기반 체크리스트:**

| OWASP 항목 | 점검 내용 |
|------------|-----------|
| **A01: Broken Access Control** | 모든 엔드포인트에 인가 검증이 있는가? IDOR(Insecure Direct Object Reference)가 가능한가? URL 파라미터의 소유권 검증? `@PermitAll` 또는 `@AllowAnonymous`가 민감한 엔드포인트에 있지 않은가? |
| **A02: Security Misconfiguration** | 기본 계정/비밀번호가 변경되었는가? 불필요한 서비스/포트/기능이 비활성화되었는가? 에러 메시지에 스택 트레이스가 노출되지 않는가? CORS 설정이 적절한가? |
| **A03: Injection** | SQL/NoSQL/OS 명령어/LDAP 인젝션 방어? 파라미터화된 쿼리/프리페어드 스테이트먼트 사용? ORM을 우회하는 Raw 쿼리의 입력 검증? |
| **A04: Insecure Design** | 비즈니스 로직 결함? 레이스 컨디션을 악용한 인가 우회? Rate limiting 부재? |
| **A05: Security Logging & Monitoring** | 인증 실패, 접근 거부, 입력 검증 실패 로깅? 로그에 민감 정보(PII, 토큰, 비밀번호) 미포함? 감사 추적(audit trail) 가능? |
| **A06: Vulnerable Components** | 알려진 취약점이 있는 라이브러리 사용? 의존성 버전 고정? |
| **A07: Authentication Failures** | 세션 토큰의 엔트로피 충분 (64비트 이상)? 로그인 후 세션 재생성? 쿠키에 Secure, HttpOnly, SameSite 설정? |
| **A08: Software Supply Chain** | 악성 패키지 감지? 빌드 파이프라인의 무결성? Lock 파일 존재? |
| **A09: SSRF** | 서버 측 URL 요청에서 사용자 입력 검증? 내부 네트워크 접근 차단? |
| **A10: Insufficient Logging** | 보안 관련 이벤트의 적절한 로깅? 모니터링 및 알림 설정? |

### 6.3 성능 리뷰 (`references/performance-review.md`)

| 범주 | 점검 항목 |
|------|-----------|
| **알고리즘 복잡도** | O(n²) 이상의 연산이 대용량 데이터에 적용되지 않는가? 불필요한 중첩 루프? |
| **DB 쿼리** | N+1 쿼리 문제? 인덱스가 적절한가? Full table scan이 발생하지 않는가? SELECT *를 피하고 필요한 컬럼만? 대량 데이터 페이지네이션? |
| **메모리** | 대용량 데이터를 한 번에 메모리에 로드하지 않는가? 스트리밍/청크 처리? 리소스 누수 (Connection, Stream, File handle)? |
| **네트워크** | 외부 호출 최소화? 배치 처리 활용? Connection pooling? |
| **캐싱** | 반복 접근 데이터의 캐싱 전략? 캐시 무효화 정책? Thundering herd 방지? |
| **비동기** | I/O 바운드 작업의 비동기 처리? CPU 바운드 작업의 적절한 스레드 풀? |

### 6.4 동시성 리뷰 (`references/concurrency-review.md`)

| 범주 | 점검 항목 |
|------|-----------|
| **경쟁 조건** | 공유 가변 상태에 대한 동기화? Check-then-act 패턴의 원자성? |
| **데드락** | 잠금 순서의 일관성? 중첩 잠금 최소화? 타임아웃 설정? |
| **트랜잭션** | 트랜잭션 경계의 적절성? 격리 수준 선택이 맞는가? 장기 트랜잭션으로 인한 Lock contention? |
| **분산 환경** | 분산 락의 적절한 사용? 이벤추얼 일관성 모델의 명시적 처리? 멱등성 보장? |
| **스레드 안전** | 싱글톤의 스레드 안전성? Mutable static 변수? ThreadLocal 사용의 적절성? |

### 6.5 DB/데이터 무결성 리뷰 (`references/database-review.md`)

| 범주 | 점검 항목 |
|------|-----------|
| **스키마** | 마이그레이션의 하위 호환성? 대형 테이블 ALTER의 Lock 영향? NOT NULL 제약 조건의 적절성? |
| **쿼리 품질** | EXPLAIN 플랜 확인? 서브쿼리 대신 JOIN? WHERE 절의 인덱스 활용? 파티셔닝/샤딩 전략? |
| **데이터 보호** | 민감 데이터 암호화? 소프트 삭제 vs 하드 삭제 정책? 백업/복구 전략? |
| **Connection 관리** | Connection pool 크기의 적절성? Connection leak 방지? Read replica 활용? |

### 6.6 API 설계 리뷰 (`references/api-review.md`)

| 범주 | 점검 항목 |
|------|-----------|
| **설계** | RESTful 원칙 준수? 리소스 명명 일관성? 적절한 HTTP 메서드/상태 코드? API 버저닝 전략? |
| **입력 검증** | 모든 입력 파라미터의 유효성 검증? 타입/범위/길이 제한? 깊은 객체의 검증? |
| **응답** | 일관된 에러 응답 형식? 페이지네이션? Rate limiting 헤더? |
| **하위 호환성** | 기존 클라이언트 영향? 필드 추가는 안전하지만 제거/변경은 위험? 마이그레이션 경로 제공? |

### 6.7 에러 처리/복원력 리뷰 (`references/error-handling-review.md`)

| 범주 | 점검 항목 |
|------|-----------|
| **에러 처리** | 적절한 예외 계층? 빈 catch 블록 없음? 에러 컨텍스트 보존? |
| **외부 의존성** | 타임아웃 설정? 재시도 로직 (지수 백오프)? 서킷 브레이커 패턴? 폴백 전략? |
| **데그레이데이션** | 부분 장애 시 전체 시스템 영향 최소화? Feature flag으로 비활성화 가능? |
| **복구** | 실패한 작업의 재시도 가능? 멱등성? 보상 트랜잭션? |

### 6.8 운영/관측 가능성 리뷰 (`references/observability-review.md`)

| 범주 | 점검 항목 |
|------|-----------|
| **로깅** | 적절한 로그 레벨? 구조화된 로깅(JSON)? Correlation ID/Trace ID? |
| **메트릭** | 비즈니스 메트릭? 기술 메트릭 (레이턴시, 에러율, 처리량)? SLI/SLO 추적 가능? |
| **알림** | 임계값 기반 알림? 알림 피로 방지? 에스컬레이션 경로? |
| **배포 안전성** | 롤백 가능한 배포? 카나리/블루-그린? Feature flag? Health check 엔드포인트? |

### 6.9 분산 시스템 패턴 리뷰 (아키텍처 리뷰의 확장)

분산 시스템에서의 리뷰 포인트 (Martin Fowler의 Patterns of Distributed Systems 기반):

| 패턴 | 리뷰 관점 |
|------|-----------|
| **API Gateway** | 단일 장애점(SPOF) 가능성? Rate limiting/인증이 게이트웨이 수준에서 처리되는가? |
| **Circuit Breaker** | 외부 서비스 장애 시 적절히 차단하는가? 반-열림(half-open) 상태의 복구 로직? |
| **Bulkhead** | 장애가 다른 서비스로 전파되지 않도록 격리되는가? 스레드 풀/커넥션 풀 분리? |
| **Saga** | 분산 트랜잭션의 보상 로직이 완전한가? 부분 실패 시 일관성 보장? |
| **CQRS** | 읽기/쓰기 모델 분리의 일관성? 이벤추얼 컨시스턴시 처리? |
| **Outbox Pattern** | DB 쓰기와 이벤트 발행의 원자성? 중복 이벤트 처리(멱등성)? |
| **Idempotency** | 모든 쓰기 연산이 멱등성을 보장하는가? 분산 시스템은 exactly-once 배달을 거의 보장하지 않음 |

---

## 7. 심각도 분류 체계

### 7.1 4단계 심각도 레벨

```
🔴 CRITICAL (P0) — 반드시 수정 후 머지. 프로덕션 장애/데이터 유실/보안 취약점
🟠 HIGH (P1)     — 강력히 수정 권고. 성능 병목/설계 결함/운영 장애 가능성
🟡 MEDIUM (P2)   — 수정 권장. 유지보수성 저하/잠재적 버그/모범 사례 미준수
🔵 LOW (P3)      — 참고 사항. 개선 제안/대안 제시/교육적 코멘트
```

### 7.2 심각도 판단 기준 매트릭스

| | 영향 범위 높음 (시스템 전체) | 영향 범위 중간 (모듈/서비스) | 영향 범위 낮음 (함수/클래스) |
|---|---|---|---|
| **발생 확률 높음** | 🔴 CRITICAL | 🟠 HIGH | 🟡 MEDIUM |
| **발생 확률 중간** | 🟠 HIGH | 🟡 MEDIUM | 🔵 LOW |
| **발생 확률 낮음** | 🟡 MEDIUM | 🔵 LOW | 🔵 LOW |

### 7.3 카테고리별 기본 심각도

| 카테고리 | 기본 심각도 | 예시 |
|----------|------------|------|
| 보안 취약점 (인젝션, 인증 우회) | 🔴 CRITICAL | SQL 인젝션, 하드코딩된 시크릿 |
| 데이터 유실/오염 가능성 | 🔴 CRITICAL | 트랜잭션 없는 다중 테이블 변경 |
| 동시성 버그 (레이스 컨디션) | 🟠 HIGH ~ 🔴 CRITICAL | 동기화 없는 공유 상태 변경 |
| 성능 병목 (확장 시) | 🟠 HIGH | N+1 쿼리, O(n²) 대용량 처리 |
| 에러 처리 누락 | 🟠 HIGH | 빈 catch 블록, 타임아웃 없는 외부 호출 |
| 아키텍처 위반 | 🟡 MEDIUM ~ 🟠 HIGH | 순환 의존성, 계층 우회 |
| API 설계 문제 | 🟡 MEDIUM | 하위 호환성 미고려, 부적절한 상태 코드 |
| 관측 가능성 부족 | 🟡 MEDIUM | 로깅 부족, 메트릭 미노출 |
| 코드 복잡도/가독성 | 🔵 LOW | 과도한 중첩, 불명확한 네이밍 |
| 최적화 제안 | 🔵 LOW | 더 나은 알고리즘 제안, 캐싱 가능 |

---

## 8. 출력 형식

### 8.1 리뷰 결과 표준 포맷

```markdown
# Deep Code Review Report

## 요약 (Executive Summary)
- **리뷰 범위**: 변경된 파일 N개, 추가 M줄, 삭제 K줄
- **전체 평가**: [APPROVE / REQUEST CHANGES / NEEDS DISCUSSION]
- **발견 이슈**: 🔴 N개 | 🟠 N개 | 🟡 N개 | 🔵 N개

## 핵심 발견 (Critical Findings)

### 🔴 [CRITICAL] 이슈 제목
**파일**: `path/to/file.java:42`
**카테고리**: 보안 > SQL 인젝션
**설명**: [문제가 무엇인지 명확히 설명]
**영향**: [이 문제가 왜 위험한지, 어떤 시나리오에서 문제가 발생하는지]
**수정 제안**:
```[언어]
// Before (문제 코드)
String query = "SELECT * FROM users WHERE id = " + userId;

// After (수정 코드)
PreparedStatement stmt = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
stmt.setString(1, userId);
```
**근거**: OWASP A03:2025 - Injection. 사용자 입력이 SQL 쿼리에 직접 결합되면
공격자가 임의의 SQL을 실행할 수 있음.

---

### 🟠 [HIGH] 이슈 제목
(동일 형식)

---

## 아키텍처 관점 (Architecture Perspective)
[전체적인 설계에 대한 의견. 변경이 기존 아키텍처와 일관적인지,
장기적으로 유지보수 가능한 방향인지 서술]

## 칭찬할 점 (What's Done Well)
[잘된 부분을 명시적으로 언급. Google 원칙: "좋은 것을 보면 칭찬하라"]

## 추가 고려 사항 (Additional Considerations)
[직접적인 이슈는 아니지만 알아두면 좋은 점, 후속 작업 제안]
```

### 8.2 신뢰도 점수

각 이슈에 대해 내부적으로 신뢰도 점수를 부여하고, 80점 이상인 이슈만 최종 출력에 포함:

```
신뢰도 기준:
  90-100: 확실한 문제 (코드에서 직접 확인 가능)
  80-89:  높은 확률의 문제 (패턴 기반 추론)
  60-79:  가능성 있는 문제 (컨텍스트 부족으로 확신 어려움) → 조건부 코멘트
  <60:    추측 수준 → 출력에서 제외
```

이 기준은 Anthropic의 공식 code-review 플러그인에서 사용하는 ≥80 신뢰도 컷오프와 동일한 접근.

### 8.3 Conventional Comments 레이블 체계

[Conventional Comments](https://conventionalcomments.org/) 표준을 채택하여 각 코멘트에 의도를 명시:

| 레이블 | 의미 | 블로킹 여부 |
|--------|------|------------|
| `issue` | 반드시 해결해야 할 문제 | 블로킹 |
| `suggestion` | 개선 제안 | 비블로킹 (blocking 데코레이터로 변경 가능) |
| `question` | 의도/근거 확인 | 비블로킹 |
| `thought` | 코드에서 촉발된 아이디어 공유 | 비블로킹 |
| `nitpick` | 사소한 선호도 차이 | 비블로킹 |
| `praise` | 잘한 부분 칭찬 | 비블로킹 |

**데코레이터** 활용: `(blocking)`, `(non-blocking)`, `(security)`, `(performance)`

**출력 예시:**
```
🔴 issue (blocking, security): SQL 인젝션 취약점
  path/to/UserRepository.java:42

🟡 suggestion (performance): N+1 쿼리를 JOIN으로 변경 권장
  path/to/OrderService.java:87

🔵 praise: 트랜잭션 경계가 잘 설정되어 있음
  path/to/PaymentService.java:23
```

### 8.4 리뷰 결정 기준

| 결정 | 조건 |
|------|------|
| **APPROVE** | 🔴 CRITICAL 0개, 🟠 HIGH 0개 |
| **APPROVE with comments** | 🔴 CRITICAL 0개, 🟠 HIGH가 있으나 non-blocking |
| **REQUEST CHANGES** | 🔴 CRITICAL 1개 이상 또는 블로킹 🟠 HIGH 존재 |
| **NEEDS DISCUSSION** | 아키텍처적 결정이 필요하여 팀 논의가 필요한 경우 |

---

## 9. 언어별 참조 가이드 전략

### 9.1 커버리지 우선순위

**Tier 1 (초기 구현):** 가장 많이 사용되는 백엔드 언어

| 파일 | 커버리지 |
|------|---------|
| `java-spring.md` | Java 17/21, Spring Boot 3, JPA/Hibernate, Virtual Threads |
| `python-django.md` | Python 3.11+, Django/FastAPI, SQLAlchemy, asyncio |
| `nodejs-typescript.md` | Node.js 20+, TypeScript 5+, Express/NestJS, Prisma |

**Tier 2 (2차 구현):** 성장하는 백엔드 생태계

| 파일 | 커버리지 |
|------|---------|
| `go.md` | Go 1.22+, goroutine/channel, database/sql |
| `rust.md` | Rust ownership, async/await, unsafe code 리뷰 |
| `csharp-dotnet.md` | C# 12, .NET 8, Entity Framework Core |

### 9.2 언어별 가이드 구조 (공통 템플릿)

각 언어 파일은 동일한 구조를 따름:

```markdown
# [언어/프레임워크] Review Guide

## 이 언어의 핵심 리뷰 포인트
[해당 언어에서 특히 주의할 패턴들]

## 흔한 실수 TOP 10
[해당 언어에서 가장 빈번한 버그 패턴]

## 성능 안티패턴
[해당 언어/런타임에서의 성능 함정]

## 보안 체크리스트
[해당 프레임워크의 보안 특화 체크리스트]

## 테스트 관점
[해당 프레임워크의 테스트 모범 사례]
```

---

## 10. 기존 솔루션 분석 및 차별화

### 10.1 기존 코드 리뷰 도구/Skill 분석

| 도구/Skill | 특징 | 한계 |
|-----------|------|------|
| **Anthropic code-review plugin** | 4개 에이전트 병렬 실행 (CLAUDE.md 준수 2개, 버그 감지 1개, git blame 컨텍스트 1개), ≥80 신뢰도 필터링. 기존 이슈/린터가 잡을 이슈 자동 제외 | 범용적. 백엔드 심층 분석 부족. 아키텍처/동시성/데이터 무결성 리뷰 미지원 |
| **code-review-expert** (sanyuan0704) | 7단계 리뷰: preflight → SOLID → 제거 후보 → 보안 → 코드 품질 → P0-P3 심각도 → 확인. 별도 체크리스트 파일 (solid, security, quality, removal-plan) | 백엔드 특화 분석이 얕음. 동시성/분산시스템/DB 무결성 미커버 |
| **awesome-skills/code-review-skill** | 11개 언어 커버, 모듈형 (~9500줄). 언어별 on-demand 로드 | 프론트엔드 비중 높음 (React 19, Vue 3 등). 백엔드 특화 분석 미흡 |
| **SpillwaveSolutions/pr-reviewer-skill** | 6단계 워크플로우: PR 데이터 수집 → 분석 → 리뷰 파일 생성 → 검토/편집 → 승인/게시 → 기준 적용. 3종 출력 (review.md, human.md, inline.md) | 코드 분석의 깊이보다 워크플로우에 초점 |
| **aidankinzett/claude-git-pr-skill** | GitHub PR 워크플로우 통합, pending review 배치 코멘트 | PR 관리에 초점. 코드 분석 자체의 깊이 부족 |
| **CodeRabbit** (외부 도구) | 40+ 코드 분석기, 자세한 워크스루 요약, 팀 피드백 학습 | SaaS 종속. 오픈소스지만 클라우드 의존 |
| **Kodus AI (Kody)** | 자연어 규칙 정의, GitHub/GitLab/Bitbucket/Azure DevOps 통합 | 범용적. 백엔드 전문 리뷰 로직 없음 |

### 10.2 본 Skill의 차별점

```
┌──────────────────────────────────────────────────────┐
│              차별화 포인트 (핵심 3가지)                  │
├──────────────────────────────────────────────────────┤
│                                                       │
│  1. 백엔드/서버 전문성                                  │
│     ├─ 동시성/병렬 처리 심층 분석                        │
│     ├─ DB/트랜잭션/데이터 무결성 전문 리뷰               │
│     ├─ 분산 시스템 패턴 검증                             │
│     └─ 운영/관측 가능성/복원력 분석                      │
│                                                       │
│  2. "새벽 3시 테스트" — 시니어의 직관                    │
│     ├─ 30년 경험에서 축적된 위험 신호 감지                │
│     ├─ 프로덕션 장애로 이어질 패턴 사전 포착              │
│     ├─ 확장 시 깨질 코드 예측                            │
│     └─ "지금은 작동하지만 곧 문제될" 코드 식별            │
│                                                       │
│  3. 교육적 피드백                                       │
│     ├─ 단순 지적이 아닌 원칙과 근거 설명                  │
│     ├─ 수정 전/후 코드 비교 제시                         │
│     ├─ 관련 원칙 (SOLID, OWASP, CAP 등) 인용            │
│     └─ "왜" 이것이 문제인지 시나리오 기반 설명            │
│                                                       │
└──────────────────────────────────────────────────────┘
```

### 10.3 리뷰 안티패턴 (회피 대상)

이 Skill이 의도적으로 피해야 할 안티패턴 (AWS Well-Architected, HackerNoon, Google 기반):

| 안티패턴 | 설명 | 본 Skill의 대응 |
|----------|------|-----------------|
| **Syntax Nitpicking** | 포맷팅, 네이밍 같은 사소한 스타일 이슈에 시간 낭비 | 린터/자동화 도구의 영역. 본 Skill은 아키텍처/보안/성능에 집중 |
| **Rubber Stamping** | 리뷰를 형식적 승인으로 처리 | 7단계 체계적 워크플로우로 방지 |
| **Perfectionism** | 완벽을 요구하며 머지 차단 | Google 원칙: "완벽한 코드는 없다, 더 나은 코드만 있다" |
| **False Positive 과다** | 확실하지 않은 이슈까지 보고하여 신뢰도 저하 | ≥80 신뢰도 컷오프로 노이즈 필터링 |
| **Knowledge Silos** | 특정 분야만 리뷰하고 전체 시스템 맥락 무시 | 8개 리뷰 영역 전방위 분석 |
| **Unconstructive Feedback** | "이건 안 됨"만 지적, 해법 미제시 | 모든 이슈에 Before/After 수정 제안 포함 |

### 10.4 업계 표준 프레임워크와의 정합성

| 프레임워크 | 핵심 원칙 | 본 Skill 반영 |
|-----------|-----------|--------------|
| **Google Eng Practices** | 8개 차원 (설계, 기능, 복잡도, 테스트, 네이밍, 코멘트, 스타일, 문서). "기술적 사실과 데이터가 개인 의견보다 우선" | 7단계 워크플로우의 설계/기능/복잡도 분석 직접 반영 |
| **Microsoft Code Review** | "코드 리뷰는 에고 싸움이 아니다." 비즈니스 로직, 정확성, 유지보수성 중심. SRP, 인수 3개 이하 권장 | 교육적 피드백 원칙, Conventional Comments 채택 |
| **OWASP Secure Coding** | 14개 보안 리뷰 카테고리 (입력 검증, 출력 인코딩, 인증, 세션, 접근제어, 암호화, 에러처리, 데이터 보호 등) | security-review.md에 전체 14개 카테고리 매핑 |
| **Conventional Comments** | 구조화된 코멘트 레이블 (issue, suggestion, question, praise 등) | 출력 형식에 직접 채택 |
| **Netlify Feedback Ladder** | Mountain → Boulder → Pebble → Sand → Dust 5단계 | P0-P3 심각도 체계와 매핑 |

---

## 11. 고급 기능 (Advanced Features)

### 11.1 Extended Thinking (ultrathink) 활용

SKILL.md 본문에 "ultrathink" 키워드를 포함하여 복잡한 리뷰 시 Claude의 확장 사고 모드를 활성화한다. 특히 다음 시나리오에서 효과적:

- 복잡한 동시성 코드의 레이스 컨디션 분석
- 다중 서비스 간 트랜잭션 흐름 추적
- 보안 취약점의 공격 시나리오 구성

### 11.2 동적 컨텍스트 주입

`!`command`` 문법으로 리뷰 전 사전 데이터를 수집:

```yaml
# SKILL.md 내부
## 리뷰 대상 컨텍스트
- 변경 파일: !`git diff --name-only HEAD~1`
- 변경 통계: !`git diff --stat HEAD~1`
- 최근 커밋: !`git log --oneline -5`
```

### 11.3 diff-analyzer.sh 스크립트

리뷰 전 변경 범위와 복잡도를 사전 분석하여, 리뷰 전략을 자동 결정:

```bash
# 출력 예시
Files changed: 12
Lines added: 345, Lines deleted: 89
Languages detected: Java (8), SQL (2), YAML (2)
Complexity indicators:
  - Database migrations detected: 2 files
  - API endpoint changes: 3 files
  - Security-sensitive files: 1 (AuthService.java)
Recommended review focus: security, database, api-compatibility
```

이 분석 결과를 바탕으로 관련 references/ 파일을 자동 선택하여 로드.

### 11.4 평가 시나리오 (Evaluations)

Anthropic Best Practices에 따라, Skill 작성 전에 평가를 먼저 구축:

```json
[
  {
    "scenario": "SQL 인젝션이 포함된 Java Spring PR",
    "expected": ["A03 Injection 식별", "PreparedStatement 사용 제안", "CRITICAL 분류"],
    "files": ["UserRepository.java"]
  },
  {
    "scenario": "N+1 쿼리가 포함된 Django PR",
    "expected": ["N+1 패턴 감지", "select_related/prefetch_related 제안", "HIGH 분류"],
    "files": ["views.py", "serializers.py"]
  },
  {
    "scenario": "트랜잭션 없는 다중 테이블 업데이트",
    "expected": ["트랜잭션 누락 감지", "@Transactional 추가 제안", "CRITICAL 분류"],
    "files": ["OrderService.java"]
  }
]
```

---

## 12. 구현 로드맵

> Anthropic Best Practice: "평가를 먼저 구축하고, 그 다음에 Skill을 작성하라"

### Phase 1: MVP (핵심 프레임워크)

- [ ] `SKILL.md` 작성 (페르소나, 워크플로우, 심각도, 출력 형식)
- [ ] `references/security-review.md` (OWASP 2025 기반)
- [ ] `references/architecture-review.md`
- [ ] `references/performance-review.md`
- [ ] `assets/review-output-template.md`
- [ ] `assets/severity-guide.md`
- [ ] 실 프로젝트 PR 3개로 테스트

### Phase 2: 언어별 확장

- [ ] `languages/java-spring.md`
- [ ] `languages/python-django.md`
- [ ] `languages/nodejs-typescript.md`
- [ ] `references/concurrency-review.md`
- [ ] `references/database-review.md`
- [ ] Haiku/Sonnet/Opus 모델별 테스트

### Phase 3: 고급 기능

- [ ] `languages/go.md`, `languages/rust.md`, `languages/csharp-dotnet.md`
- [ ] `references/api-review.md`
- [ ] `references/error-handling-review.md`
- [ ] `references/observability-review.md`
- [ ] `scripts/diff-analyzer.sh` (변경 복잡도 사전 분석)
- [ ] 평가 시나리오 구축 및 반복 개선

---

## 13. 참고 자료

### Skill 구조 및 작성법
- [Claude Code Skills 공식 문서](https://code.claude.com/docs/en/skills)
- [Skill 작성 모범 사례 (Anthropic)](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Agent Skills 오픈 표준](https://agentskills.io)
- [Anthropic Skills Repository (공식)](https://github.com/anthropics/skills)
- [Claude Agent Skills: 심층 분석 (Han Lee)](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)
- [Inside Claude Code Skills (Mikhail Shilkov)](https://mikhail.io/2025/10/claude-code-skills/)
- [Equipping Agents for the Real World (Anthropic Engineering Blog)](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

### 코드 리뷰 프레임워크
- [Google Engineering Practices — Code Review](https://google.github.io/eng-practices/review/)
- [Google: What to Look for in a Code Review](https://google.github.io/eng-practices/review/reviewer/looking-for.html)
- [Software Engineering at Google — Chapter 9: Code Review](https://abseil.io/resources/swe-book/html/ch09.html)
- [Microsoft Engineering Fundamentals — Code Reviews](https://microsoft.github.io/code-with-engineering-playbook/code-reviews/)
- [Microsoft Reviewer Guidance](https://microsoft.github.io/code-with-engineering-playbook/code-reviews/process-guidance/reviewer-guidance/)
- [GitHub Staff Engineer's Review Philosophy](https://github.blog/developer-skills/github/how-to-review-code-effectively-a-github-staff-engineers-philosophy/)
- [Backend Code Review Checklist (DEV Community)](https://dev.to/markadel/backend-code-review-checklist-280h)
- [DX Code Review Checklist Guide](https://getdx.com/blog/code-review-checklist/)
- [Conventional Comments](https://conventionalcomments.org/)
- [Netlify Feedback Ladders](https://www.netlify.com/blog/2020/03/05/feedback-ladders-how-we-encode-code-reviews-at-netlify/)

### 보안
- [OWASP Top 10: 2025](https://owasp.org/Top10/2025/)
- [OWASP Secure Coding Practices Quick Reference](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)
- [OWASP Code Review Guide v2](https://owasp.org/www-project-code-review-guide/)
- [OWASP Secure Code Review Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Code_Review_Cheat_Sheet.html)
- [Secure Code Review Checklist: OWASP-Aligned (Augment Code)](https://www.augmentcode.com/guides/secure-code-review-checklist-owasp-aligned-framework)
- [Code Review Security Checklist (Axolo)](https://axolo.co/blog/p/code-review-security-checklist)

### 성능, 동시성 및 백엔드
- [Backend Performance Best Practices (Roadmap.sh)](https://roadmap.sh/backend-performance-best-practices)
- [High-Concurrency Backend Systems Guide](https://charleswan111.medium.com/comprehensive-guide-to-high-concurrency-backend-systems-architecture-optimization-and-best-1ed1d623a48e)
- [SQL Optimization Checklist (Explo)](https://www.explo.co/encyclopedia/sql-optimization-checklist)
- [Martin Fowler — Patterns of Distributed Systems](https://martinfowler.com/articles/patterns-of-distributed-systems/)
- [Java Concurrency Code Review Checklist (GitHub)](https://github.com/code-review-checklists/java-concurrency)
- [Futurice Backend Best Practices](https://github.com/futurice/backend-best-practices)

### 기존 코드 리뷰 Skill/플러그인
- [Anthropic code-review plugin](https://github.com/anthropics/claude-code/blob/main/plugins/code-review/README.md)
- [code-review-expert (sanyuan0704)](https://github.com/sanyuan0704/code-review-expert)
- [pr-reviewer-skill (SpillwaveSolutions)](https://github.com/SpillwaveSolutions/pr-reviewer-skill)
- [awesome-skills/code-review-skill](https://github.com/awesome-skills/code-review-skill)
- [claude-git-pr-skill (aidankinzett)](https://github.com/aidankinzett/claude-git-pr-skill)
- [claude-code-skills 102개 컬렉션 (levnikolaevich)](https://github.com/levnikolaevich/claude-code-skills)
- [Awesome Claude Skills 컬렉션](https://github.com/travisvn/awesome-claude-skills)
- [VoltAgent Awesome Agent Skills](https://github.com/VoltAgent/awesome-agent-skills)

### AI 코드 리뷰 트렌드
- [AI Coding Workflow (Addy Osmani)](https://addyosmani.com/blog/ai-coding-workflow/)
- [5 AI Code Review Pattern Predictions 2026 (Qodo)](https://www.qodo.ai/blog/5-ai-code-review-pattern-predictions-in-2026/)
- [Good Code Reviews (Sean Goedecke)](https://www.seangoedecke.com/good-code-reviews/)
- [AI Prompts for Code Review (5ly.co)](https://5ly.co/blog/ai-prompts-for-code-review/)
- [Code Review Anti-Patterns (AWS Well-Architected)](https://docs.aws.amazon.com/wellarchitected/latest/devops-guidance/anti-patterns-for-code-review.html)
