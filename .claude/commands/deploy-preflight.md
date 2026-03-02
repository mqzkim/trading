# 배포 사전점검 (Preflight Check)

Color Sort Master 배포 전 사전점검을 수행합니다.

## 지시사항

1. `scripts/deploy/preflight-check.sh` 스크립트를 실행하여 배포 준비 상태를 점검하세요.
2. FAIL 항목이 있으면 각각에 대해 해결 방법을 안내하세요.
3. WARN 항목은 권장 사항으로 알려주되 필수는 아닙니다.
4. 추가로 다음을 직접 확인하세요:
   - `Assets/Scripts/Monetization/AdConfig.cs`의 프로덕션 Ad Unit ID가 설정되었는지
   - `Assets/Plugins/Android/AndroidManifest.xml`의 AdMob App ID가 실제 값인지
   - `docs/deploy/deployment-guide.md`의 Phase 체크리스트 중 코드로 확인 가능한 항목
5. 모든 점검이 완료되면 결과를 한국어 요약표로 정리하세요.

## 실행 커맨드
```bash
bash scripts/deploy/preflight-check.sh
```
