---
status: diagnosed
phase: 11-commercial-fastapi-rest-api
source: [11-01-SUMMARY.md, 11-02-SUMMARY.md]
started: 2026-03-13T05:30:00Z
updated: 2026-03-13T05:40:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: 서버를 새로 시작. `python3 -m uvicorn commercial.api.main:app --port 8000` 에러 없이 부팅. `curl /health` 200 반환.
result: pass

### 2. API 키 → JWT 토큰 교환
expected: POST /api/v1/auth/token에 x-api-key 헤더로 유효한 키를 보내면 200 + access_token, token_type "bearer", expires_in 반환. 잘못된 키는 401.
result: pass

### 3. API 키 CRUD (생성/조회/폐기)
expected: JWT로 POST /api/v1/auth/keys → key_id + raw_key 반환. GET /api/v1/auth/keys → 키 목록 (raw_key 미포함). DELETE /api/v1/auth/keys/{key_id} → 폐기 성공.
result: pass

### 4. 인증 없는 요청 거부
expected: Authorization 헤더 없이 /api/v1/quantscore/AAPL, /api/v1/regime/current, /api/v1/signals/AAPL 호출 시 401 또는 403 반환.
result: pass

### 5. QuantScore 엔드포인트
expected: GET /api/v1/quantscore/AAPL (JWT 포함) → composite_score, fundamental_score, technical_score, sentiment_score, sub_scores, disclaimer 필드가 포함된 JSON 반환.
result: issue
reported: "422 에러 반환: compute_fundamental_score() missing 1 required positional argument: 'valuation'. 스코어링 핸들러가 valuation 데이터 없이 호출됨."
severity: major

### 6. RegimeRadar Current 엔드포인트
expected: GET /api/v1/regime/current (JWT 포함) → regime_type, confidence, vix, adx, yield_spread, detected_at, disclaimer 포함 JSON 반환.
result: pass

### 7. RegimeRadar History 엔드포인트
expected: GET /api/v1/regime/history?days=90 (JWT 포함) → entries 배열 + total 카운트 반환. days=400은 422 반환.
result: pass

### 8. SignalFusion 엔드포인트
expected: GET /api/v1/signals/AAPL (JWT 포함) → direction (Bullish/Bearish/Neutral), strength, consensus_count, methodology_votes 리스트, disclaimer 반환.
result: issue
reported: "500 에러: SignalResponse validation error - strength 필드에 25.0이 들어왔으나 스키마는 le=1 제약. 핸들러의 composite_score(0-100)가 strength(0-1)로 매핑되지 않음."
severity: major

### 9. 시그널 법적 경계 검증
expected: /api/v1/signals 응답에 margin_of_safety, reasoning_trace, position, recommendation, stop_loss, take_profit 필드가 절대 없음. direction은 BUY/SELL이 아닌 Bullish/Bearish/Neutral.
result: skipped
reason: 테스트 8 실패로 응답 자체를 받지 못해 검증 불가. 스키마 레벨에서는 이미 유닛 테스트로 검증 완료 (13개 법적 경계 테스트 통과).

### 10. 티어별 레이트 리미팅
expected: TIER_LIMITS 설정값: free=10/minute, basic=30/minute, pro=100/minute. 한도 초과 시 429 반환.
result: pass

### 11. 면책조항 포함 확인
expected: 모든 데이터 엔드포인트 응답에 disclaimer 필드가 한/영 이중 언어로 포함.
result: pass

## Summary

total: 11
passed: 7
issues: 2
pending: 0
skipped: 2

## Gaps

- truth: "GET /api/v1/quantscore/{ticker}가 composite score breakdown을 반환해야 함"
  status: failed
  reason: "422 에러: compute_fundamental_score() missing 1 required positional argument: 'valuation'. 스코어링 핸들러가 valuation 데이터 없이 호출됨."
  severity: major
  test: 5
  root_cause: "ScoreSymbolHandler._get_fundamental() fallback이 compute_fundamental_score(symbol)로 호출 - str 1개만 전달하나 함수는 (highlights: dict, valuation: dict) 2개 필요. bootstrap.py가 fundamental_client를 주입하지 않아 항상 이 broken fallback 실행됨."
  artifacts:
    - path: "src/scoring/application/handlers.py"
      issue: "_get_fundamental() line 191: compute_fundamental_score(symbol) - 인자 수/타입 불일치"
    - path: "src/bootstrap.py"
      issue: "line 91: ScoreSymbolHandler에 fundamental_client 미주입"
  missing:
    - "handlers.py의 fallback에서 DataClient로 highlights/valuation dict를 가져온 후 compute_fundamental_score(highlights, valuation) 호출"
    - "또는 bootstrap.py에서 fundamental_client (CoreScoringAdapter 등) 주입"
  debug_session: ".planning/debug/quantscore-422-missing-valuation.md"

- truth: "GET /api/v1/signals/{ticker}가 consensus signal을 반환해야 함"
  status: failed
  reason: "500 에러: SignalResponse Pydantic validation - strength 필드에 25.0이 들어왔으나 스키마는 le=1.0 제약. 핸들러 composite_score(0-100 스케일)가 strength(0-1 스케일)로 변환되지 않음."
  severity: major
  test: 8
  root_cause: "SignalStrength.value는 도메인에서 0-100 스케일. 핸들러가 그대로 반환. signals.py 라우터가 float를 받아 그대로 SignalResponse에 전달하나 스키마는 le=1 제약. 100으로 나누는 변환이 누락됨."
  artifacts:
    - path: "commercial/api/routers/signals.py"
      issue: "lines 73-78: float strength_raw를 100으로 나누지 않고 그대로 전달"
  missing:
    - "signals.py에서 strength_val = min(1.0, float(strength_raw) / 100.0) 로 스케일 변환"
  debug_session: ".planning/debug/signals-strength-scale-mismatch.md"
