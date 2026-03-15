# Trading System Project Memory

## 프로젝트 개요

체계적 증권 트레이딩 시스템 - 정량적 스코어링, 스킬 체이닝, 자동 자기 개선, 검증된 방법론 기반.
CLI 도구 + Codex Skill + REST API 형태로 개인 사용과 상업 제품을 동시 서빙.

## 확정된 전략 (strategy-recommendation.md 기반)

### 핵심 원칙
- 단타(데이 트레이딩, 스캘핑) 절대 금지
- 스윙 트레이딩 (수주~수개월) 및 포지션 트레이딩 (수개월~수년) 중심
- 모든 판단은 정량적 스코어 기반 (주관적 판단 배제)
- 검증된 방법론만 사용 (학술 논문 또는 10년+ 백테스트)

### "하나의 코드, 두 개의 제품" 전략
- **공통 기반 (core/)**: Scoring Engine, Regime Detector, Signal Fusion
- **개인 전용 (personal/)**: Position Sizer, Risk Manager, Execution, Self-Improver, Orchestrator
- **상업 제품 (commercial/)**: QuantScore API, RegimeRadar API, SignalFusion API

### 법적 경계
- 상업 제품은 "정보 제공"만 (점수, 데이터, 통계)
- "매수/매도 추천" 및 "포지션 크기 제안"은 개인 전용 (투자 자문 = 라이센스 필요)
- 상업 API 응답에 면책조항 필수

### 상업 제품 3종
| 제품명 | 역할 | 가격 |
|--------|------|------|
| QuantScore | 복합 정량 스코어링 API | $29-$99/mo |
| RegimeRadar | 시장 레짐 감지 API (경쟁 없음) | $19-$49/mo |
| SignalFusion | 4전략 합의 시그널 API | $49-$199/mo |

## 구현 순서
1. Scoring Engine (양쪽 핵심, 1순위)
2. Regime Detection (경쟁 없음, 2순위)
3. Signal Generation (4전략, 3순위)
4. Position Sizer + Risk Manager (개인)
5. Execution (Alpaca Paper Trading)
6. API 서버 (FastAPI, 상업)
7. Performance Analyst + Self-Improver (개인)

## 리스크 한도
- 단일 종목: 최대 8%
- 섹터: 최대 25%
- 거래당 리스크: 자본의 1%
- ATR 스탑: 2.5-3.5x ATR(21)
- Fractional Kelly: 1/4 (절대 Full Kelly 금지)
- 최대 낙폭 20% 초과 시 전량 청산 후 최소 1개월 냉각기

## 낙폭 방어 3단계
- 10%: 신규 진입 중단, 모니터링 강화
- 15%: 포지션 50% 축소, 방어적 전환
- 20%: 전체 청산, 냉각기 후 25%씩 점진 재진입

## 시간축
- 최소 보유 기간: 2주 (스윙), 3개월 (포지션)
- 리밸런싱: 월간 (스윙), 분기 (포지션)
- 데이터 분석: 일간/주간/월간 차트 기반

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

## 문서 위치
- docs/trading-methodology-overview.md (통합 개요)
- docs/quantitative-scoring-methodologies.md (스코어링)
- docs/skill_chaining_and_self_improvement_research.md (스킬 체인)
- docs/verified-methodologies-and-risk-management.md (검증된 방법론)
- docs/strategy-recommendation.md (전략 추천서)
- docs/api-technical-feasibility.md (API 기술 타당성)
- docs/skill-conversion-plan.md (Skill 변환 계획)
- docs/cli-skill-implementation-plan.md (CLI/Skill 구현 플랜)

## 코드 구조
```
trading-system/
├── core/          # 공통 (scoring, regime, signals, data)
├── personal/      # 개인 (sizer, risk, execution, self-improve)
├── commercial/    # 상업 (FastAPI REST API)
├── cli/           # CLI (Typer 명령어)
├── .Codex/       # Codex Skills (12개)
└── tests/
```
