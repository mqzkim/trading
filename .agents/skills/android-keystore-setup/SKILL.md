# Android Keystore Setup

Android 앱 서명을 위한 Keystore 생성 및 GitHub Secrets 등록을 자동화합니다.

## 역할
Android 앱 서명 전문가. Keystore 생성, 관리, CI/CD Secret 연동을 담당합니다.

## 수행 가능 작업

### 1. Keystore 생성
- `keytool` 명령어로 `.keystore` 파일 생성
- 프로젝트 기본값:
  - Keystore 파일명: `colorsortmaster.keystore`
  - Alias: `colorsortmaster`
  - Algorithm: RSA 2048
  - Validity: 10000일 (약 27년)
  - DN: `CN=Color Sort Master, OU=Development, O=ColorSortStudio, L=Seoul, ST=Seoul, C=KR`
- 사용자에게 비밀번호 입력 요청 (강력한 비밀번호 권장)

생성 명령어:
```bash
keytool -genkey -v \
  -keystore colorsortmaster.keystore \
  -alias colorsortmaster \
  -keyalg RSA -keysize 2048 \
  -validity 10000 \
  -storepass "<PASSWORD>" \
  -keypass "<PASSWORD>" \
  -dname "CN=Color Sort Master, OU=Development, O=ColorSortStudio, L=Seoul, ST=Seoul, C=KR"
```

### 2. Keystore 검증
```bash
keytool -list -v -keystore colorsortmaster.keystore -storepass "<PASSWORD>"
```

### 3. GitHub Secrets 등록
`.env` 파일에 다음 변수 설정 후 `scripts/deploy/setup-github-secrets.sh` 실행:
```
KEYSTORE_PATH=colorsortmaster.keystore
KEYSTORE_PASSWORD=<password>
KEY_ALIAS=colorsortmaster
KEY_PASSWORD=<password>
```

등록되는 Secrets:
- `ANDROID_KEYSTORE_BASE64` (keystore 파일의 base64 인코딩)
- `KEYSTORE_PASSWORD`
- `KEY_ALIAS`
- `KEY_PASSWORD`

등록 확인: `gh secret list`

### 4. 백업 안내
- Keystore 분실 시 앱 업데이트 불가 (Google Play App Signing 사용 시 완화)
- 최소 2곳에 백업 권장 (USB, 클라우드)

## 참고 문서
- `.Codex/commands/deploy-setup.md` (Step 5: Keystore)
- `scripts/deploy/setup-github-secrets.sh` (자동 Secret 등록)
- `docs/deploy/store-submission-guide.md` (line 454-461: 백업 프로토콜)

## 제약 조건
- `.gitignore`에 `*.keystore`, `*.jks` 이미 포함 → 레포에 커밋되지 않음
- 비밀번호는 절대 하드코딩 금지 → `.env` + GitHub Secrets만 사용
- 로컬 `.env` 파일은 커밋하지 않음

## 실행 전 확인
- Java JDK가 설치되어 있어야 함 (`keytool`은 JDK에 포함)
- `gh` CLI가 인증되어 있어야 함 (GitHub Secrets 등록용)
