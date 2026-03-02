# 스토어 등록정보 준비 (Store Listing)

Color Sort Master의 App Store / Google Play 등록정보를 준비합니다.

## 지시사항

### 1. 메타데이터 확인
다음 파일들의 내용을 읽고 스토어 제출에 필요한 형태로 정리하세요:
- `docs/store/metadata-ko.md` (한국어)
- `docs/store/metadata-en.md` (영어)

### 2. App Store Connect 메타데이터 정리
아래 형식으로 출력하세요:

**한국어:**
| 필드 | 내용 | 글자 수 |
|------|------|---------|
| App Name | (30자 이내) | |
| Subtitle | (30자 이내) | |
| Keywords | (100자 이내, 쉼표 구분) | |
| Promotional Text | (170자 이내) | |
| Description | (4000자 이내) | |
| What's New | 초기 버전 텍스트 | |

**영어:** 동일 형식

### 3. Google Play Console 메타데이터 정리
| 필드 | 내용 | 글자 수 |
|------|------|---------|
| App Name | (30자 이내) | |
| Short Description | (80자 이내) | |
| Full Description | (4000자 이내) | |
| Release Notes | (500자 이내) | |

### 4. 스크린샷 체크리스트
`docs/deploy/screenshot-specs.md`를 참조하여:
- iOS 필수 사이즈 목록과 필요 장수
- Android 필수 사이즈 및 Feature Graphic
- 각 스크린샷의 권장 내용

### 5. IAP 상품 목록
`docs/deploy/deployment-guide.md` Phase 2의 IAP 상품 목록을 정리하여
iOS/Android 양쪽 스토어에 등록해야 할 상품 ID, 타입, 가격을 표로 출력하세요.

결과를 복사해서 바로 스토어에 붙여넣을 수 있는 형태로 만드세요.
