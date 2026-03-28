# 기술 스택 & Team Agent 모델 배정

## 기술 스택
- **CLI**: Typer + Rich
- **API**: FastAPI + Uvicorn
- **데이터**: EODHD (Phase 1), Twelve Data (Phase 2), FMP (Phase 3)
- **브로커**: Alpaca (미국), KIS (한국)
- **캐싱**: SQLite (로컬), Redis (API 서버)
- **설정**: Pydantic Settings + .env
- **테스트**: pytest
- **ML**: scikit-learn, XGBoost, hmmlearn, Optuna

## Team Agent 모델 배정
- opus: Orchestrator, 복합 판단 (2개)
- sonnet: 중간 복잡도 분석 (4개)
- haiku: 정형화된 계산 (7개)
