---
name: android-release
description: "Android Internal Testing에서 Production까지 릴리스 파이프라인 관리 스킬"
---

# Android Release

Internal Testing에서 Production까지의 릴리스 파이프라인을 관리합니다.

## 역할
Android 릴리스 매니저. 빌드부터 단계적 출시까지 전체 릴리스 사이클을 관리합니다.

## 수행 가능 작업

### 1. Internal Testing 배포

#### 자동 배포 (GitHub Actions)
```bash
gh workflow run build-android.yml \
  -f version="1.0.0" \
  -f build_number="1" \
  -f upload_to_playstore="true"
```

#### 수동 배포 (Play Console)
1. AAB artifact 다운로드
2. Play Console → Testing → Internal testing
3. **Create new release** → AAB 업로드
4. Release notes 입력 (한국어/영어)
5. **Start rollout to Internal testing**

### 2. 테스터 설정

1. Play Console → Internal testing → **Testers** 탭
2. 이메일 리스트 생성 (또는 Google Group)
3. 테스터 이메일 추가
4. **Opt-in URL** 복사 → 테스터에게 공유
5. 테스터가 URL 클릭 → Play Store에서 설치

### 3. Release Notes 템플릿

#### 한국어
```
🎮 Color Sort Master v1.0.0

첫 출시!
• 500+ 퍼즐 레벨
• 다양한 게임 모드
• 일일 챌린지
• 아름다운 테마

즐거운 퍼즐 타임 되세요! 🧩
```

#### English
```
🎮 Color Sort Master v1.0.0

Initial Release!
• 500+ puzzle levels
• Multiple game modes
• Daily challenges
• Beautiful themes

Enjoy your puzzle time! 🧩
```

### 4. Open Testing 승격 (선택)

1. Play Console → Testing → Open testing
2. **Create new release**
3. **Add from library** → Internal testing 빌드 선택
4. Release notes 입력
5. **Start rollout to Open testing**
6. 더 넓은 사용자 피드백 수집

### 5. Production 출시

#### 단계적 출시 (권장)
1. Play Console → Production
2. **Create new release** → 빌드 선택
3. **Staged rollout percentage**: 5%
4. Release notes 입력
5. **Start rollout to Production**

#### 단계적 출시 스케줄
| 단계 | 비율 | 대기 기간 | 기준 |
|------|------|----------|------|
| 1 | 5% | 24~48시간 | Crash-free >= 99.5% |
| 2 | 20% | 24~48시간 | ANR rate < 0.47% |
| 3 | 50% | 24시간 | 부정적 리뷰 급증 없음 |
| 4 | 100% | - | 모든 지표 안정 |

#### 롤아웃 증가
```
Play Console → Production → Release dashboard → Update rollout percentage
```

#### 긴급 롤백
```
Play Console → Production → Release dashboard → Halt rollout
```

### 6. 버전 관리

| 필드 | 설명 | 규칙 |
|------|------|------|
| versionName | 사용자에게 표시 (1.0.0) | Semantic Versioning |
| versionCode | Play Console 내부 (1, 2, 3...) | 항상 증가, 절대 감소 불가 |

```bash
# 빌드번호 증가하여 새 빌드
gh workflow run build-android.yml \
  -f version="1.0.1" \
  -f build_number="2" \
  -f upload_to_playstore="true"
```

### 7. Hotfix 워크플로우

1. `hotfix/v1.0.1` 브랜치 생성
2. 수정 사항 커밋
3. main에 머지
4. 빌드번호 증가하여 빌드 + 업로드
5. 100% 롤아웃으로 바로 배포 (긴급시)

## 참고 문서
- `.github/workflows/build-android.yml` (빌드 + 업로드 워크플로우)
- `docs/deploy/store-submission-guide.md` (출시 가이드)
- `.claude/commands/deploy-monitor.md` (출시 후 모니터링)

## 제약 조건
- 첫 AAB 업로드는 Play Console UI에서 수동으로 해야 할 수 있음
- versionCode는 절대 감소 불가 (Play Console 거부됨)
- 단계적 출시 중 새 릴리스 생성 시 기존 롤아웃 중단됨
- 프로덕션 출시 후 검토에 최대 7일 소요 (첫 출시 시)

## 출시 전 최종 체크리스트
- [ ] Preflight check 통과 (`/deploy-preflight`)
- [ ] AdMob 프로덕션 ID 확인 (테스트 ID 아닌지)
- [ ] Privacy Policy URL 접속 가능
- [ ] 모든 App Content 섹션 완료
- [ ] 스크린샷 최소 2장 업로드
- [ ] Feature Graphic 업로드
- [ ] Release notes 한국어/영어 작성
