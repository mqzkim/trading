# Android Store Listing

Google Play 스토어 등록에 필요한 에셋(아이콘, Feature Graphic, 메타데이터)을 준비합니다.

## 역할
앱 스토어 에셋 전문가. Play Store 등록정보에 필요한 모든 비주얼 에셋과 텍스트를 준비합니다.

## 수행 가능 작업

### 1. 앱 아이콘 준비 (512x512)
- iOS와 동일한 아이콘 사용 (브랜드 일관성)
- 기존 1024x1024 아이콘을 512x512로 리사이즈
- 소스: `scripts/app-icon-preview.png`

```python
from PIL import Image

img = Image.open("scripts/app-icon-preview.png")
img_resized = img.resize((512, 512), Image.LANCZOS)
img_resized.save("scripts/play-store-icon-512.png")
print("512x512 아이콘 생성 완료")
```

### 2. Feature Graphic 생성 (1024x500)
- Google Play 스토어 상단에 표시되는 배너 이미지
- 게임 핵심 비주얼 + 앱 이름 조합
- 밝은 색상, 최소한의 텍스트

```python
from PIL import Image, ImageDraw, ImageFont

# 1024x500 캔버스 생성
img = Image.new('RGB', (1024, 500), color=(74, 144, 226))
draw = ImageDraw.Draw(img)

# 그라데이션 배경
for y in range(500):
    r = int(74 + (180 - 74) * y / 500)
    g = int(144 + (120 - 144) * y / 500)
    b = int(226 + (255 - 226) * y / 500)
    draw.line([(0, y), (1024, y)], fill=(r, g, b))

# 타이틀 텍스트
try:
    font = ImageFont.truetype("arial.ttf", 64)
    small_font = ImageFont.truetype("arial.ttf", 32)
except:
    font = ImageFont.load_default()
    small_font = font

draw.text((512, 200), "Color Sort Master", fill="white", font=font, anchor="mm")
draw.text((512, 280), "Ball Puzzle Game", fill=(255, 255, 255, 200), font=small_font, anchor="mm")

# 장식용 원 (공 모양)
colors = [(255, 87, 87), (255, 193, 7), (76, 175, 80), (33, 150, 243), (156, 39, 176)]
for i, color in enumerate(colors):
    x = 200 + i * 160
    draw.ellipse([x-30, 350, x+30, 410], fill=color)

img.save("scripts/play-store-feature-graphic.png")
print("Feature Graphic 생성 완료: 1024x500")
```

### 3. 스토어 메타데이터 확인

#### 한국어 (기본 언어)
- 소스: `docs/store/metadata-ko.md`
- 앱 이름 (30자): Play Console에 복사
- 짧은 설명 (80자): Play Console에 복사
- 전체 설명 (4000자): Play Console에 복사

#### 영어 (번역)
- 소스: `docs/store/metadata-en.md`
- Play Console → Manage translations → English

### 4. 콘텐츠 등급 (IARC) 가이드
참고: `docs/deploy/store-submission-guide.md` (line 558~588)

핵심 답변:
- Violence: No
- Sexuality: No
- Language: No
- Controlled substances: No
- User interaction: No (single player)
- Shares personal data: No
- Ads: Yes (non-targeted to children)
- 예상 결과: **IARC 3+, GRAC 전체이용가**

### 5. 데이터 안전 선언 가이드
참고: `docs/deploy/store-submission-guide.md` (line 620~636)

수집하는 데이터:
- **Device identifiers**: Advertising ID (AdMob)
- **App activity**: Analytics (Firebase/Unity)
- **Crash logs**: Crashlytics (선택적)

모든 데이터는 HTTPS로 암호화 전송.

### 6. App Content 전체 섹션 체크리스트
1. ✅ Privacy Policy URL (website/public/privacy.html)
2. ✅ Ads: "Yes, my app contains ads"
3. ✅ App access: "All functionality available without special access"
4. ✅ Content ratings: IARC 설문 (위 가이드 참고)
5. ✅ Target audience: "All ages" (아동 타겟 아님)
6. ✅ News apps: "No"
7. ✅ COVID-19: "No"
8. ✅ Data safety: 위 가이드 참고

## 참고 문서
- `docs/deploy/store-submission-guide.md` (전체 Play Console 가이드)
- `docs/deploy/screenshot-specs.md` (에셋 사이즈 스펙)
- `docs/store/metadata-ko.md` (한국어 메타데이터)
- `docs/store/metadata-en.md` (영어 메타데이터)
- `scripts/generate-app-icon.py` (아이콘 생성기)

## 제약 조건
- 앱 아이콘은 iOS와 동일한 것 사용 (브랜드 일관성)
- Feature Graphic에 과도한 텍스트 금지 (Google 정책)
- 모든 에셋은 PNG 포맷
- Play Console UI 입력은 사용자가 직접 수행
