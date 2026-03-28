---
name: android-screenshot
description: "Google Play 스토어용 스크린샷 촬영 및 후처리 스킬"
---

# Android Screenshot

Google Play 스토어용 스크린샷 촬영 및 후처리를 수행합니다.

## 역할
모바일 앱 스크린샷 전문가. Play Store 등록에 필요한 스크린샷을 캡처하고 최적화합니다.

## 수행 가능 작업

### 1. 스크린샷 사양

| 디바이스 | 해상도 | 필수 여부 | 최소/최대 |
|----------|--------|----------|----------|
| Phone | 1080 x 1920 (9:16) | **필수** | 2~8장 |
| 7" Tablet | 1200 x 1920 | 권장 | 최대 8장 |
| 10" Tablet | 1600 x 2560 | 권장 | 최대 8장 |

### 2. 8-스크린샷 촬영 계획

| # | 화면 | 설명 | 촬영 포인트 |
|---|------|------|------------|
| 1 | Hero Shot | 메인 게임플레이 | 공이 정렬되는 중인 순간 |
| 2 | Level Selection | 레벨 선택 화면 | 다양한 난이도 표시 |
| 3 | Daily Challenge | 일일 챌린지 | 보상 표시 |
| 4 | Theme Showcase | 테마/스킨 | 화려한 테마 선택 |
| 5 | Game Modes | 게임 모드 | 여러 모드 표시 |
| 6 | Tutorial | 도움말/튜토리얼 | 쉬운 접근성 |
| 7 | Shop/VIP | 상점 화면 | VIP 혜택 표시 |
| 8 | Achievements | 업적/보상 | 달성감 표현 |

### 3. Unity Editor에서 캡처 방법

1. Unity Editor 열기
2. Game View 탭 선택
3. 해상도를 `1080 x 1920`으로 설정:
   - Game View → Resolution 드롭다운 → `+` 버튼
   - Label: `Play Store Phone`
   - Width: 1080, Height: 1920
4. Play 모드 진입
5. 원하는 화면에서 캡처:
   - Windows: `Win + Shift + S` (Snipping Tool)
   - 또는 Unity 스크립트로 자동 캡처

### 4. Unity 스크립트로 자동 캡처 (선택)

```csharp
// Assets/Editor/ScreenshotCapture.cs
using UnityEngine;
using UnityEditor;

public class ScreenshotCapture
{
    [MenuItem("Tools/Capture Screenshot")]
    static void CaptureScreenshot()
    {
        string filename = $"Screenshots/screenshot_{System.DateTime.Now:yyyyMMdd_HHmmss}.png";
        ScreenCapture.CaptureScreenshot(filename, 1);
        Debug.Log($"Screenshot saved: {filename}");
    }
}
```

### 5. ADB로 디바이스에서 캡처 (물리적 기기)

```bash
# 스크린샷 촬영
adb shell screencap -p /sdcard/screenshot.png

# PC로 복사
adb pull /sdcard/screenshot.png ./screenshots/

# 연속 촬영 스크립트
for i in $(seq 1 8); do
    echo "Press Enter to capture screenshot $i..."
    read
    adb shell screencap -p /sdcard/screenshot_$i.png
    adb pull /sdcard/screenshot_$i.png ./screenshots/
done
```

### 6. Android 에뮬레이터에서 캡처

1. Android Studio → AVD Manager
2. Pixel 6 (1080x2400) 또는 Pixel 4 (1080x2280) 선택
3. APK 사이드로드 또는 AAB → APK 변환 후 설치
4. 에뮬레이터 사이드바 → 카메라 아이콘으로 캡처

### 7. 후처리 (선택)

```python
from PIL import Image

# 리사이즈 (필요시)
img = Image.open("screenshot_raw.png")
img_resized = img.resize((1080, 1920), Image.LANCZOS)
img_resized.save("screenshot_final.png")
```

## 참고 문서
- `docs/deploy/screenshot-specs.md` (상세 사양)
- `docs/deploy/store-submission-guide.md` (스크린샷 요구사항)

## 제약 조건
- 최소 2장, 권장 8장
- PNG 또는 JPEG 포맷
- 최소 320px, 최대 3840px (한 변)
- 스크린샷에 디바이스 프레임 포함 금지 (Google 정책)
- 테스트 데이터가 아닌 실제 게임 화면 사용

## 출력 위치
- `screenshots/` 디렉토리에 저장
- 파일명 규칙: `phone_01_hero.png`, `phone_02_levels.png`, ...
