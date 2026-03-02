# S7 — Commercial API v1 Sprint: Context Document

- Sprint ID: `S7`
- 작성일: 2026-03-03
- 선행 조건: S6 PASS ✅

## 목표
- `commercial/api/`: FastAPI REST API 서버 구현
- 3개 상업 엔드포인트: QuantScore / RegimeRadar / SignalFusion

## 구현 범위
```
commercial/
├── __init__.py
└── api/
    ├── __init__.py
    ├── main.py          # FastAPI app + 라이프사이클
    ├── models.py        # Pydantic 요청/응답 모델
    ├── routes/
    │   ├── __init__.py
    │   ├── score.py     # GET /score/{symbol}
    │   ├── regime.py    # GET /regime
    │   └── signal.py    # GET /signal/{symbol}
    └── middleware.py    # CORS + 에러 핸들러

tests/unit/
└── test_api_routes.py   # FastAPI TestClient 테스트
```

## 성공 기준
- `GET /score/{symbol}` → composite_score + 면책조항
- `GET /regime` → 현재 레짐 + 전략 가중치
- `GET /signal/{symbol}` → 4전략 합의 시그널
- `GET /health` → 서버 상태
- 단위테스트 전체 PASS
- 면책조항 모든 응답에 포함
