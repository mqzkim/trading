# 출시 후 모니터링 (Post-Launch Monitor)

Color Sort Master 출시 후 모니터링 체크리스트를 실행합니다.

## 지시사항

`docs/deploy/deployment-guide.md`의 Phase 7을 기반으로 모니터링 대시보드를 정리하세요.

### 1. 첫 24시간 체크리스트
- [ ] Firebase Crashlytics 대시보드 확인 (Crash-free >= 99.5%)
- [ ] Android Vitals ANR Rate 확인 (< 0.47%)
- [ ] App Store Connect / Play Console 리뷰 확인
- [ ] IAP 결제 정상 작동 확인
- [ ] 광고 노출 정상 확인 (AdMob 대시보드)
- [ ] Push Notification 수신 확인

### 2. 첫 48시간 체크리스트
- [ ] 1-star 리뷰에 답변 작성
- [ ] D1 Retention 확인 (목표: >= 40%)
- [ ] 핫픽스 필요 여부 판단
- [ ] Remote Config 파라미터 조정 필요 여부

### 3. 1주차 체크리스트
- [ ] D7 Retention 확인 (목표: >= 15%)
- [ ] ARPDAU 확인 (목표: >= $0.10)
- [ ] 크래시 보고서 분석 및 수정
- [ ] A/B 테스트 결과 분석
- [ ] Soft Launch 지표 기반 글로벌 출시 결정

### 4. 핫픽스 대비
핫픽스가 필요한 경우:
```bash
# 핫픽스 브랜치 생성
git checkout -b hotfix/1.0.1 main

# 수정 후 빌드
gh workflow run build-android.yml -f version="1.0.1" -f build_number="2"
gh workflow run build-ios.yml -f version="1.0.1" -f build_number="2"
```

### 5. 대시보드 URL 목록
| 서비스 | URL |
|--------|-----|
| Firebase Console | https://console.firebase.google.com |
| AdMob | https://admob.google.com |
| App Store Connect | https://appstoreconnect.apple.com |
| Google Play Console | https://play.google.com/console |

각 항목의 현재 상태를 한국어로 요약하세요.
