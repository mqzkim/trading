# iOS 서명 검증 (Verify iOS Signing)

iOS 빌드의 프로비저닝 프로필 및 코드 서명 설정을 검증합니다.
Playwright로 Apple Developer Console을 확인하거나, 로컬 프로필을 디코딩하여 Entitlement을 점검합니다.

## 지시사항

다음 3단계를 순서대로 수행하세요:

### 1단계: Xcode 프로젝트 Entitlement 확인

GitHub Actions 빌드 로그에서 Xcode 프로젝트가 요구하는 Capability를 확인합니다:
```bash
# 최신 iOS 빌드 실행 로그에서 서명 관련 오류 추출
gh run list --workflow="Build & Deploy iOS" --limit=1 --json databaseId --jq '.[0].databaseId' | xargs -I{} gh run view {} --log 2>&1 | grep -i -E "provisioning|signing|capability|entitlement|requires a|code.sign" | head -20
```

### 2단계: 프로비저닝 프로필 Entitlement 검증

로컬에 `.mobileprovision` 파일이 있으면 디코딩하여 IAP 등 필요한 Entitlement이 포함되어 있는지 확인합니다:

```bash
# 로컬 프로필 파일 탐색
find /c/workspace -name "*.mobileprovision" 2>/dev/null

# macOS에서만 가능: 프로필 디코딩
# security cms -D -i profile.mobileprovision | grep -A5 "Entitlements"
```

프로필이 로컬에 없으면, Playwright로 Apple Developer Console에서 확인합니다.

### 3단계: Playwright로 Apple Developer Console 확인

`scripts/verify-ios-profile.js` 스크립트를 실행하여 Apple Developer Console에서 프로비저닝 프로필의 Capability를 확인합니다:

```bash
cd /c/workspace/unity-game
node scripts/verify-ios-profile.js
```

이 스크립트는:
1. Apple Developer Console (developer.apple.com) 접속
2. 사용자에게 로그인/2FA 처리 시간 제공 (headful 모드)
3. Certificates, Identifiers & Profiles 페이지 이동
4. App ID의 Capability 목록 확인 (In-App Purchase 포함 여부)
5. Provisioning Profile의 상태 및 만료일 확인
6. 결과를 콘솔에 출력

**참고**: Apple 2FA 때문에 `headless: false`로 실행됩니다. 브라우저가 열리면 수동 로그인 후 자동으로 진행됩니다.

### 결과 보고

검증 결과를 아래 형식으로 요약하세요:

| 항목 | 상태 | 비고 |
|------|------|------|
| App ID (Bundle ID) | ✅/❌ | IAP Capability 여부 |
| Provisioning Profile | ✅/❌ | 유형, 만료일 |
| 인증서 | ✅/❌ | Distribution/Development |
| Xcode 프로젝트 설정 | ✅/❌ | CODE_SIGN_STYLE, TEAM_ID |

결과를 한국어로 요약하세요.
