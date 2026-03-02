# iOS 배포 (Deploy iOS)

Color Sort Master iOS 빌드 및 App Store 제출을 진행합니다.

## 지시사항

### 로컬 빌드 (macOS + Xcode 필요)

1. **Unity에서 iOS 프로젝트 생성**:
   - Build Settings → Platform: iOS
   - Development Build: OFF
   - Scripting Backend: IL2CPP
   - Architecture: ARM64
   - Build → `Builds/iOS/` 출력

2. **Xcode 설정 확인**:
   - `Builds/iOS/Unity-iPhone.xcworkspace` 열기
   - Signing & Capabilities:
     - Team: Apple Developer Team 선택
     - Bundle Identifier: `com.colorsortstudio.colorsortmaster`
     - Provisioning Profile: `ColorSortMaster_AppStore_Distribution`
   - Capabilities: Push Notifications, In-App Purchase 활성화

3. **Archive & Upload**:
   - Product → Archive
   - Organizer → Distribute App → App Store Connect → Upload

### CI/CD 빌드 (GitHub Actions)
```bash
gh workflow run build-ios.yml \
  -f version="1.0.0" \
  -f build_number="1"
```

### App Store Connect 제출
`docs/deploy/store-submission-guide.md`의 App Store 섹션을 참조하여:
1. 스크린샷 업로드 (모든 필수 사이즈)
2. 메타데이터 입력 (한국어 + 영어)
3. 빌드 선택 및 심사 정보 입력
4. App Privacy 데이터 설정
5. Submit for Review

결과를 한국어로 요약하세요.
