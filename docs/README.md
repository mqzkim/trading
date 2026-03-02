# 체계적 증권 트레이딩 방법론 문서

## Systematic Securities Trading Methodology Documentation

**목적**: 정량적 스코어링, 스킬 체이닝, 자동 자기 개선, 검증된 방법론 인코딩을 기반으로 한 중장기 증권 트레이딩 시스템 구축을 위한 종합 참고 문서

**원칙**: 단타(데이 트레이딩, 스캘핑) 최대한 지양, 스윙 트레이딩(수주~수개월) 및 포지션 트레이딩(수개월~수년) 중심

---

## 문서 구조

### 핵심 문서

| 문서 | 설명 | 분량 |
|------|------|------|
| [`trading-methodology-overview.md`](trading-methodology-overview.md) | **통합 개요** - 4대 핵심 축의 종합 아키텍처, 구현 로드맵, 시스템 설계 | ~800줄 |
| [`quantitative-scoring-methodologies.md`](quantitative-scoring-methodologies.md) | **정량적 스코어링** - Piotroski F-Score, Altman Z-Score, 복합 점수, ML 접근법, 백테스팅 | ~1,350줄 |
| [`skill_chaining_and_self_improvement_research.md`](skill_chaining_and_self_improvement_research.md) | **스킬 체이닝 & 자기 개선** - HRL 기반 파이프라인, 레짐 감지, 앙상블, 메타러닝 | ~1,150줄 |
| [`verified-methodologies-and-risk-management.md`](verified-methodologies-and-risk-management.md) | **검증된 방법론 & 리스크 관리** - CAN SLIM, Magic Formula, Dual Momentum, 행동재무학 | ~700줄 |

### 읽는 순서 (권장)

```
1. trading-methodology-overview.md     ← 먼저 전체 그림 파악
2. quantitative-scoring-methodologies.md  ← 스코어링 시스템 심화
3. verified-methodologies-and-risk-management.md ← 검증된 전략 + 리스크
4. skill_chaining_and_self_improvement_research.md ← 자동화/적응형 시스템
```

---

## 4대 핵심 축 요약

### 1. 정량적 스코어링 (Quantitative Scoring)
- 멀티팩터 복합 점수 모델 (F-Score, Z-Score, G-Score, M-Score)
- 기본적 + 기술적 + 센티먼트 3축 스코어링 프레임워크
- 정규화 (백분위 순위, 섹터 중립), 가중치 최적화 (IC 가중, 역변동성)
- ML 기반 팩터 스코어링 (XGBoost, 피처 선택, SHAP 해석)

### 2. 스킬 체이닝 (Skill Chaining)
- 계층적 강화학습(HRL) 기반 트레이딩 파이프라인 설계
- 9계층 아키텍처: 데이터 → 레짐감지 → 시그널 → 전략선택 → 포지션 사이징 → 리스크 → 실행 → 성과분석 → 자기개선
- HMM 레짐 감지, 메타러닝 전략 선택, 앙상블 시그널 생성

### 3. 자동 자기 개선 (Automatic Self-Improvement)
- Walk-Forward Optimization으로 주기적 파라미터 최적화
- CPCV(Combinatorial Purged Cross-Validation)로 오버피팅 탐지
- 베이지안 최적화(Optuna)로 효율적 파라미터 탐색
- 성과 어트리뷰션 → 진단 → 개선 자동 피드백 루프

### 4. 검증된 방법론 인코딩 (Verified Methodology Encoding)
- Fama-French 팩터 모델 (학술적 기반)
- CAN SLIM, Magic Formula, Dual Momentum (실전 검증)
- 트렌드 팔로잉, Risk Parity (기관 검증)
- 체계적 규칙 인코딩 및 파라미터 최소화 원칙

---

## 핵심 참고 문헌

### 학술 논문
- Fama & French (1993, 2015) - 팩터 모델
- Jegadeesh & Titman (1993) - 모멘텀
- Piotroski (2000) - F-Score
- Lopez de Prado (2018) - 금융 머신러닝

### 실무 서적
- Greenblatt - "The Little Book That Beats the Market" (Magic Formula)
- Antonacci - "Dual Momentum Investing"
- O'Neil - "How to Make Money in Stocks" (CAN SLIM)
- Pardo - "The Evaluation and Optimization of Trading Strategies"

---

## 기술 스택

| 카테고리 | 도구 |
|---------|------|
| 백테스팅 | VectorBT (리서치), Backtrader (실행), QuantConnect (클라우드) |
| ML/팩터 | scikit-learn, XGBoost, LightGBM, hmmlearn |
| 최적화 | Optuna, PyPortfolioOpt, Riskfolio-Lib |
| 데이터 | yfinance, FinanceDataReader, pykrx, Polygon.io |
| 분석 | pandas, numpy, SHAP, empyrical |
