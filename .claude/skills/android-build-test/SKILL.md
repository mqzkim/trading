---
name: android-build-test
description: "Android AAB 빌드 실행, 모니터링, 서명 검증 스킬"
---

# Android Build Test

Android AAB 빌드 실행, 모니터링, 서명 검증을 수행합니다.

## 역할
Android 빌드 엔지니어. CI/CD 파이프라인에서 AAB 빌드를 트리거하고 결과를 검증합니다.

## 수행 가능 작업

### 1. 빌드 트리거
```bash
gh workflow run build-android.yml -f version="1.0.0" -f build_number="1"
```
- self-hosted runner (`unity-builder`)에서 실행
- **주의**: runner가 실행 중이어야 함 (`C:\workspace\actions-runner\run.cmd`)

### 2. 빌드 모니터링
```bash
# 최신 실행 확인
gh run list --workflow=build-android.yml --limit=5

# 실행 로그 실시간 확인
gh run watch <RUN_ID>

# 상세 로그 확인
gh run view <RUN_ID> --log
```

### 3. 아티팩트 다운로드
```bash
gh run download <RUN_ID> -n android-aab-<VERSION>
```

### 4. AAB 서명 검증
```bash
jarsigner -verify -verbose -certs <AAB_FILE>
```
- "jar verified" 메시지가 나와야 정상
- "jar is unsigned" → Keystore 설정 문제

### 5. 일반적인 빌드 에러 대응

| 에러 | 원인 | 해결 |
|------|------|------|
| `Unity Editor not found` | Unity Hub 경로 변경 | build-android.yml의 Unity 탐색 경로 확인 |
| `Build failed: No scenes` | EditorBuildSettings 비어있음 | Unity Editor에서 Scenes in Build 확인 |
| `Keystore not found` | ANDROID_KEYSTORE_BASE64 미설정 | `android-keystore-setup` 스킬 실행 |
| `SDK version mismatch` | Android SDK 미설치/버전 불일치 | Unity Hub에서 Android Build Support 확인 |
| `IL2CPP error` | IL2CPP 빌드 실패 | NDK 설치 확인, 에러 로그 상세 분석 |

## 참고 문서
- `.github/workflows/build-android.yml` (워크플로우 정의)
- `Assets/Editor/CIBuildScript.cs` (BuildAndroid 메서드)
- `.claude/commands/deploy-expert-review.md` (Section 8: Android 서명)

## 제약 조건
- Unity 6 Personal: self-hosted runner만 사용 가능 (cloud CI 불가)
- runner가 오프라인이면 빌드 대기 상태로 멈춤
- 빌드 시간: 약 10~30분 (프로젝트 크기에 따라 다름)

## Workflow 개선사항 (필요 시 적용)
- 빌드 전 `Library/Bee` 클린업 추가
- 빌드 후 서명 검증 step 추가
- `upload_to_playstore` input 추가
