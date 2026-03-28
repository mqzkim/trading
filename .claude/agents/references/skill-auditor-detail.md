# Skill Auditor — Detail

## 감사 체크리스트

### 1. 프론트매터 검증
- `name` 필드 존재 여부
- `description` 충분한 설명인지
- `allowed-tools` / `tools` 적절한지
- `model` 유효한 값인지 (opus, sonnet, haiku)

### 2. 구조 일관성
- 스킬 디렉토리: `SKILL.md` 파일 존재
- 플랫 스킬: `.md` 확장자
- 에이전트: 표준 프론트매터 준수
- 커맨드: `argument-hint` 포함

### 3. 중복 탐지
- 레지스트리 기반 이름 충돌 검사
- description 유사성 분석
- 레포 간 동일 이름 다른 내용 탐지

### 4. 내용 품질
- 지시사항 명확성
- 입출력 형식 정의 여부
- 예제 포함 여부

## 감사 절차

1. `/c/workspace/.claude/hub/registry.json` 읽기
2. 각 에셋 파일 순회하며 체크리스트 적용
3. 심각도 분류 (ERROR / WARN / INFO)
4. 감사 리포트 생성

## 출력 형식

```
=== Claude Asset Audit Report ===
Scanned: X assets across Y repos

[ERROR] skill/name: 구체적 문제
[WARN]  agent/name: 개선 제안
[INFO]  command/name: 참고 사항

Summary: X errors, Y warnings, Z info
```
