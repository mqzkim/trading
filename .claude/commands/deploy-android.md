# Android 배포 (Deploy Android)

Color Sort Master Android AAB 빌드 및 Google Play 제출을 진행합니다.

## 지시사항

### 로컬 빌드 (Unity 에디터 사용)
Unity 에디터에서 수동 빌드가 필요한 경우, 다음 체크리스트를 안내하세요:

1. **Player Settings 확인**:
   - Package Name: `com.colorsortstudio.colorsortmaster`
   - Scripting Backend: IL2CPP
   - Target Architectures: ARMv7 + ARM64
   - Minimum API Level: 24 (Android 7.0)
   - Target API Level: 34+ (Android 14)

2. **빌드 설정**:
   - Build App Bundle (Google Play): 체크
   - Development Build: 해제
   - Script Debugging: 해제

3. **Keystore 설정**:
   - Custom Keystore 체크
   - `.env`의 KEYSTORE_PATH, KEYSTORE_PASSWORD, KEY_ALIAS, KEY_PASSWORD 참조

### CI/CD 빌드 (GitHub Actions)
자동 빌드를 사용하는 경우:
```bash
# GitHub Actions 워크플로우 수동 트리거
gh workflow run build-android.yml \
  -f version="1.0.0" \
  -f build_number="1"
```

### Google Play Console 제출
`docs/deploy/store-submission-guide.md`의 Google Play 섹션을 참조하여:
1. Internal Testing 트랙에 AAB 업로드
2. 앱 콘텐츠 설정 9개 항목 완료 확인
3. 스토어 등록정보 검증
4. Production으로 Promote (Staged Rollout 5% → 20% → 50% → 100%)

결과를 한국어로 요약하세요.
