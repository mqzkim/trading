# 배포 환경 설정 (Deploy Setup)

Color Sort Master 배포를 위한 환경 설정을 진행합니다.

## 지시사항

다음 단계를 순서대로 진행하세요:

### 1단계: .env 파일 확인
- `.env.example`이 존재하는지 확인
- `.env` 파일이 없으면 사용자에게 생성을 안내
- `.env`에 설정된 값 중 placeholder가 남아있는 항목을 알려주기

### 2단계: GitHub Secrets 설정
- 사용자에게 GitHub Secrets로 등록해야 할 키 목록을 보여주기
- `scripts/deploy/setup-github-secrets.sh` 사용법 안내
- 수동으로 등록해야 하는 시크릿 (UNITY_LICENSE, 인증서 등) 별도 안내

### 3단계: Firebase 설정
- Firebase Console에서 다운로드할 파일 안내:
  - `GoogleService-Info.plist` → `Assets/`
  - `google-services.json` → `Assets/`
- Remote Config 기본값이 `Assets/StreamingAssets/firebase_remote_config_defaults.json`에 있는지 확인

### 4단계: AdMob 설정
- `.env`의 AdMob ID가 설정되었으면 `scripts/deploy/swap-production-ids.sh` 실행
- `AdConfig.cs`에 프로덕션 ID가 반영되었는지 확인
- `AndroidManifest.xml`의 AdMob App ID 확인

### 5단계: Android Keystore
- Keystore 파일 존재 여부 확인
- 없으면 생성 명령어 안내:
```bash
keytool -genkey -v -keystore colorsortmaster.keystore \
  -alias colorsortmaster -keyalg RSA -keysize 2048 -validity 10000
```

모든 단계를 점검한 뒤 요약 결과를 보고하세요.
