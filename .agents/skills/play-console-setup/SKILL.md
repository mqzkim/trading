# Play Console Setup

Google Play Console 앱 생성 및 API 접근 설정을 단계별로 안내합니다.

## 역할
Google Play 배포 전문가. Play Console 앱 설정과 자동 배포를 위한 API 연동을 가이드합니다.

## 수행 가능 작업

### 1. Google Play Console 앱 생성 (사용자 수동)

**URL**: https://play.google.com/console

1. **All apps** → **Create app** 클릭
2. 앱 정보 입력:
   - App name: `Color Sort Master - Ball Puzzle`
   - Default language: 한국어 (ko)
   - App or Game: **Game**
   - Free or Paid: **Free**
3. 선언 체크:
   - ✅ Developer Program Policies
   - ✅ US Export Laws
4. **Create app** 클릭

### 2. Google Play App Signing 활성화 (사용자 수동)

1. Play Console → **Setup** → **App signing**
2. **Use Google Play App Signing** 활성화
3. 첫 AAB 업로드 시 Upload Key가 자동 등록됨
4. 장점: Upload Key 분실 시 Google에 리셋 요청 가능

### 3. Google Play Service Account 생성 (사용자 수동)

#### Step 3.1: Google Cloud Console 설정
1. https://console.cloud.google.com 접속
2. 프로젝트 선택 (또는 새 프로젝트 생성)
3. **APIs & Services** → **Enable APIs**
4. `Google Play Android Developer API` 검색 → **Enable**

#### Step 3.2: Service Account 생성
1. **IAM & Admin** → **Service Accounts** → **Create Service Account**
2. Name: `play-deploy-bot`
3. Role: 일단 건너뛰기 (Play Console에서 설정)
4. **Done** 클릭
5. 생성된 Service Account 클릭 → **Keys** 탭
6. **Add Key** → **Create new key** → **JSON** → **Create**
7. 다운로드된 JSON 파일 안전하게 보관

#### Step 3.3: Play Console에서 API 연결
1. Play Console → **Settings** → **API access**
2. **Link** 클릭하여 Google Cloud 프로젝트 연결
3. Service Accounts 섹션에서 `play-deploy-bot` 찾기
4. **Grant access** 클릭
5. App permissions에서 Color Sort Master 앱 선택
6. 권한 설정:
   - ✅ Release to production, exclude devices, and use Play App Signing
   - ✅ Manage testing tracks and edit tester lists

### 4. Service Account JSON을 GitHub Secret으로 등록

```bash
# JSON 파일을 Secret으로 등록
gh secret set GOOGLE_PLAY_SERVICE_ACCOUNT_JSON < path/to/service-account.json

# 등록 확인
gh secret list | grep GOOGLE_PLAY
```

### 5. 검증
```bash
# Secret이 등록되었는지 확인
gh secret list
```

## 참고 문서
- `docs/deploy/store-submission-guide.md` (Google Play 섹션)
- `docs/deploy/deployment-guide.md` (Phase 1: Account Setup)
- `.github/workflows/build-android.yml` (line 103-110: 업로드 설정)

## 제약 조건
- Play Console/Cloud Console 작업은 사용자가 브라우저에서 직접 수행
- Service Account JSON은 절대 레포에 커밋하지 않음
- API access 권한은 최소 권한 원칙 준수

## 주의사항
- Service Account 생성 후 Play Console에서 권한 부여까지 최대 24시간 소요될 수 있음
- 새로 생성한 앱에 처음 AAB를 업로드할 때는 Play Console UI에서 수동으로 해야 함 (API는 두 번째부터 가능한 경우 있음)
