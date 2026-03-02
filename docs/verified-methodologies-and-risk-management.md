# 검증된 트레이딩 방법론 인코딩 및 포트폴리오 리스크 관리

## Verified Trading Methodology Encoding & Portfolio Risk Management

**초점**: 중장기 트레이딩 (스윙 트레이딩: 수주~수개월, 포지션 트레이딩: 수개월~수년)
**원칙**: 단타(데이 트레이딩, 스캘핑) 배제, 학술적 검증 기반 방법론 우선

---

## 목차

1. [학술적으로 검증된 팩터 모델](#1-학술적으로-검증된-팩터-모델)
2. [검증된 트레이딩 방법론](#2-검증된-트레이딩-방법론)
3. [트레이딩 규칙의 체계적 인코딩](#3-트레이딩-규칙의-체계적-인코딩)
4. [포트폴리오 리스크 관리](#4-포트폴리오-리스크-관리)
5. [행동재무학과 시스템적 대응](#5-행동재무학과-시스템적-대응)
6. [성과 측정 지표](#6-성과-측정-지표)
7. [리밸런싱 전략](#7-리밸런싱-전략)
8. [세금 효율적 트레이딩](#8-세금-효율적-트레이딩)
9. [오픈소스 도구 및 데이터 소스](#9-오픈소스-도구-및-데이터-소스)
10. [백테스팅 함정과 회피 방법](#10-백테스팅-함정과-회피-방법)
11. [통합 방법론 시스템 설계](#11-통합-방법론-시스템-설계)

---

## 1. 학술적으로 검증된 팩터 모델

### 1.1 Fama-French 3팩터 모델 (1993)

```
R_i - R_f = alpha + beta_M * (R_M - R_f) + beta_S * SMB + beta_V * HML + epsilon

팩터:
  R_M - R_f = 시장 초과수익률 (Market Risk Premium)
  SMB = Small Minus Big (소형주 프리미엄)
  HML = High Minus Low B/M (가치주 프리미엄)
```

- 분산 포트폴리오 수익률의 90% 이상 설명 (CAPM의 70% 대비)
- 가치(HML)와 규모(SMB) 팩터의 장기 프리미엄 학술적 입증

### 1.2 Fama-French 5팩터 모델 (2015)

```
R_i - R_f = alpha + beta_M*(R_M - R_f) + beta_S*SMB + beta_V*HML
            + beta_P*RMW + beta_I*CMA + epsilon

추가 팩터:
  RMW = Robust Minus Weak (수익성 프리미엄: 높은 영업이익률 - 낮은 영업이익률)
  CMA = Conservative Minus Aggressive (투자 프리미엄: 보수적 투자 - 공격적 투자)
```

**핵심 발견**:
- RMW와 CMA 추가 시 HML(가치 팩터)이 중복됨
- 모멘텀 팩터 미포함 (Carhart 4팩터에서 추가)
- 2010-2019년 "잃어버린 10년" 동안 대부분의 팩터가 부진했으나, 1990년대 유사 부진 후 2000년대 강한 회복 선례 존재

### 1.3 Carhart 4팩터 모델 (1997)

```
R_i - R_f = alpha + beta_M*(R_M - R_f) + beta_S*SMB + beta_V*HML
            + beta_W*WML + epsilon

WML = Winners Minus Losers (12-1개월 모멘텀 프리미엄)
```

### 1.4 검증된 팩터 프리미엄 요약

| 팩터 | 설명 | 연간 프리미엄 | 지속성 | 주요 논문 |
|------|------|-------------|--------|---------|
| Market | 주식 리스크 프리미엄 | 5-8% | 매우 높음 | Sharpe (1964) |
| Value | 저평가 vs 고평가 | 3-5% | 높음 (순환적) | Fama & French (1993) |
| Size | 소형주 vs 대형주 | 2-3% | 보통 | Fama & French (1993) |
| Momentum | 승자 vs 패자 (12-1개월) | 6-8% | 높음 | Jegadeesh & Titman (1993) |
| Quality | 고수익 vs 저수익 기업 | 3-5% | 높음 | Novy-Marx (2013) |
| Low Volatility | 저위험 vs 고위험 | 4-6% | 높음 | Blitz & van Vliet (2007) |
| Investment | 보수적 vs 공격적 투자 | 2-4% | 보통 | Fama & French (2015) |

### 1.5 팩터 순환성 (Regime Dependence)

팩터 효과는 시장 환경에 따라 달라짐:
- **고금리 + 높은 투자심리**: 가치 팩터 우세
- **저금리 + 낮은 투자심리**: 규모 팩터 우세
- **저변동성 팩터**: 2010-2019 "잃어버린 10년"에서도 6-10% 프리미엄 유지
- 팩터 분산은 멱법칙(power-law) 행동을 보임 → 분산투자 효과에 한계 존재

---

## 2. 검증된 트레이딩 방법론

### 2.1 CAN SLIM (William O'Neil)

**핵심**: 성장주 선별을 위한 7가지 기준의 체계적 인코딩

| 기준 | 의미 | 정량적 인코딩 |
|------|------|-------------|
| **C** - Current Quarterly Earnings | 분기 EPS 성장 | EPS YoY 성장률 >= 25% |
| **A** - Annual Earnings | 연간 수익 성장 | 연간 EPS 성장률 >= 25%, 5년 연속 |
| **N** - New Products/Management | 신제품/혁신 | 52주 신고가 근접 (95% 이내) |
| **S** - Supply and Demand | 수급 | 거래량 급증 (50일 평균 대비 150%+) |
| **L** - Leader or Laggard | 선도주 여부 | 상대강도(RS) 점수 >= 80 (상위 20%) |
| **I** - Institutional Sponsorship | 기관 보유 | 기관 보유 비율 증가 추세, 우량 펀드 보유 |
| **M** - Market Direction | 시장 방향 | 시장 지수가 200일 MA 위, 상승 추세 확인 |

**체계적 스코어링 인코딩**:
```
CAN_SLIM_Score = (
    1 * (quarterly_eps_growth >= 0.25) +
    1 * (annual_eps_growth >= 0.25 and consecutive_years >= 3) +
    1 * (price >= 0.95 * high_52week) +
    1 * (volume_ratio >= 1.5) +
    1 * (relative_strength >= 80) +
    1 * (institutional_increase == True) +
    1 * (market_above_200ma == True)
)
# Score range: 0-7, Buy when >= 5 and M = 1
```

**보유 기간**: 전형적으로 수주~수개월 (스윙 트레이딩에 적합)
**검증 성과**: O'Neil의 연구에 따르면 역대 최고 수익률 주식의 공통 특성

### 2.2 Magic Formula (Joel Greenblatt)

**핵심**: 가치와 품질의 결합 → "좋은 기업을 싼 가격에"

**공식**:
```
두 가지 지표로 순위 매김:

1. Earnings Yield (수익률) = EBIT / Enterprise Value
   - 높을수록 좋음 (저평가)
   - P/E보다 우수: 부채 수준과 세금 차이 보정

2. Return on Capital (자본수익률) = EBIT / (Net Working Capital + Net Fixed Assets)
   - 높을수록 좋음 (고품질 비즈니스)
   - ROE보다 우수: 레버리지 효과 제거

Combined Rank = Rank(Earnings_Yield) + Rank(Return_on_Capital)
→ Combined Rank가 가장 낮은 (= 두 지표 모두 상위) 종목 매수
```

**구현 프로세스**:
```
1. 유니버스 정의: 시가총액 > $50M (유틸리티, 금융주 제외)
2. Earnings Yield 계산 및 순위 (1등 = 가장 높은 수익률)
3. Return on Capital 계산 및 순위 (1등 = 가장 높은 자본수익률)
4. 두 순위 합산
5. 합산 순위 상위 20-30개 종목 매수
6. 1년 보유 후 리밸런싱
7. 세금 최적화: 손실 종목은 11개월에 매도, 이익 종목은 13개월에 매도
```

**검증 성과**: Greenblatt의 연구 (1988-2004): 연평균 30.8% vs S&P 500 12.4%
**보유 기간**: 1년 (포지션 트레이딩에 적합)

### 2.3 Dual Momentum (Gary Antonacci)

**핵심**: 절대 모멘텀 + 상대 모멘텀의 결합

```
1. 상대 모멘텀 (Relative Momentum):
   - 12개월 수익률 비교: 미국 주식 vs 국제 주식
   - 더 높은 쪽 선택

2. 절대 모멘텀 (Absolute Momentum):
   - 선택된 자산의 12개월 수익률 > 무위험 수익률(T-Bill)?
   - Yes → 해당 자산 보유
   - No → 채권(Aggregate Bond)으로 이동

의사 결정 트리:
  IF US_12m_return > INTL_12m_return:
    IF US_12m_return > TBill_12m_return:
      HOLD US Stocks (e.g., SPY)
    ELSE:
      HOLD Bonds (e.g., AGG)
  ELSE:
    IF INTL_12m_return > TBill_12m_return:
      HOLD International Stocks (e.g., EFA)
    ELSE:
      HOLD Bonds (e.g., AGG)
```

**구현 코드 (의사코드)**:
```python
def dual_momentum_signal(us_returns_12m, intl_returns_12m, tbill_returns_12m):
    if us_returns_12m > intl_returns_12m:
        if us_returns_12m > tbill_returns_12m:
            return "US_EQUITY"  # SPY, VTI
        else:
            return "BONDS"      # AGG, BND
    else:
        if intl_returns_12m > tbill_returns_12m:
            return "INTL_EQUITY"  # EFA, VXUS
        else:
            return "BONDS"        # AGG, BND

# 리밸런싱: 월 1회 (매월 말)
# 거래비용: 최소화 (연 4-6회 전환 발생)
```

**검증 성과**:
- 1974-2013 백테스트: 연 17.5%, 샤프비율 0.98, 최대 낙폭 -19.6%
- S&P 500 대비 높은 수익률 + 낮은 낙폭
- 단순함이 강점: 오버피팅 리스크 최소

**보유 기간**: 평균 6-12개월 (포지션 트레이딩에 적합)

### 2.4 트렌드 팔로잉 (Trend Following)

중장기 트렌드 팔로잉은 가장 오래 검증된 전략 중 하나.

#### 이동평균 시스템

```
1. 200일 이동평균 시스템 (가장 단순):
   - Price > 200-day MA → 매수
   - Price < 200-day MA → 현금/채권

2. 골든/데드 크로스:
   - 50-day MA > 200-day MA (골든 크로스) → 매수
   - 50-day MA < 200-day MA (데드 크로스) → 매도

3. 듀얼 이동평균 시스템 (Meb Faber):
   - 10개월(약 200일) MA 위 → 매수
   - 10개월 MA 아래 → 국채로 이동
   - 월 1회 체크
```

#### 브레이크아웃 시스템

```
Donchian Channel Breakout (터틀 트레이딩 변형):
  - 20일 고가 돌파 → 진입
  - 10일 저가 하회 → 청산

중장기 변형 (포지션 트레이딩):
  - 55일 고가 돌파 → 진입
  - 20일 저가 하회 → 청산
  - ATR(20) 기반 포지션 사이징
```

**검증 성과**: AQR, Man Group, Winton 등 CTA 펀드들의 장기 수익률이 트렌드 팔로잉의 유효성을 실증
**보유 기간**: 수주~수개월 (다양한 시장에 적용 가능)

### 2.5 Risk Parity & All-Weather 포트폴리오

#### Risk Parity (리스크 패리티)

```
원칙: 각 자산군의 위험 기여도(risk contribution)를 동일하게 배분

w_i * sigma_i * rho_i,portfolio = 동일 (모든 i에 대해)

단순 구현 (Inverse Volatility Weighting):
  w_i = (1 / sigma_i) / SUM(1 / sigma_j)

  여기서 sigma_i = 자산 i의 표준편차 (연환산)

정교한 구현:
  최적화: min SUM_i,j [ (w_i * (Cov * w)_i - w_j * (Cov * w)_j)^2 ]
  제약: SUM(w_i) = 1, w_i >= 0
```

#### All-Weather 포트폴리오 (Ray Dalio / Bridgewater 영감)

```
환경 매트릭스:
                  인플레이션 상승    인플레이션 하락
경제 성장 상승     주식, 원자재       주식, 채권
경제 성장 하락     금, TIPS           국채, 금

전형적 배분:
  장기 국채: 40%
  미국 주식: 30%
  중기 국채: 15%
  금: 7.5%
  원자재: 7.5%

각 경제 환경에서 포트폴리오의 일부가 작동하도록 설계
→ 어떤 환경에서든 극심한 손실 방지
```

**검증 성과**:
- 전통적 60/40 대비 낮은 변동성, 유사한 장기 수익률
- 2008년 금융위기에서 60/40 대비 현저히 낮은 낙폭
- 리스크 조정 수익률(샤프비율) 우수

---

## 3. 트레이딩 규칙의 체계적 인코딩

### 3.1 인코딩 원칙

검증된 방법론을 시스템으로 전환하는 핵심 원칙:

```
1. 명확한 진입/청산 규칙 (Explicit Rules)
   - 모든 조건은 수치화 가능해야 함
   - "주가가 저렴해 보인다" → "P/E < 15 AND ROE > 15%"
   - 주관적 판단 배제

2. 결정론적 실행 (Deterministic Execution)
   - 동일한 데이터 → 동일한 결정
   - 재현 가능한 결과

3. 파라미터 최소화 (Parameter Parsimony)
   - 파라미터가 많을수록 오버피팅 위험 증가
   - 전략당 2-4개 핵심 파라미터로 제한
   - 파라미터 안정성: 약간의 변경에도 성과가 유지되어야 함

4. 계층적 필터링 (Hierarchical Filtering)
   - Layer 1: 시장 방향 필터 (매크로)
   - Layer 2: 유니버스 필터링 (유동성, 재무건전성)
   - Layer 3: 스코어링/순위 (복합 점수)
   - Layer 4: 포지션 사이징 (켈리/변동성 기반)
   - Layer 5: 리스크 관리 (스탑, 집중도 한도)
```

### 3.2 방법론 인코딩 템플릿

```python
class MethodologyEncoder:
    """검증된 방법론을 체계적 규칙으로 인코딩하는 프레임워크"""

    def __init__(self, name, holding_period, rebalance_freq):
        self.name = name
        self.holding_period = holding_period    # 'monthly', 'quarterly', 'annual'
        self.rebalance_freq = rebalance_freq
        self.entry_rules = []
        self.exit_rules = []
        self.position_rules = {}
        self.risk_rules = {}

    def add_entry_rule(self, rule_name, condition_fn, weight=1.0):
        """진입 규칙 추가 (조건 함수 + 가중치)"""
        self.entry_rules.append({
            'name': rule_name,
            'condition': condition_fn,
            'weight': weight
        })

    def add_exit_rule(self, rule_name, condition_fn, priority='normal'):
        """청산 규칙 추가 (우선순위: 'critical' = 즉시 청산)"""
        self.exit_rules.append({
            'name': rule_name,
            'condition': condition_fn,
            'priority': priority
        })

    def evaluate(self, stock_data):
        """종목에 대해 모든 규칙 평가 → 종합 점수 반환"""
        score = 0
        total_weight = 0
        for rule in self.entry_rules:
            if rule['condition'](stock_data):
                score += rule['weight']
            total_weight += rule['weight']
        return score / total_weight if total_weight > 0 else 0

# 사용 예시: Magic Formula 인코딩
magic_formula = MethodologyEncoder(
    name='Magic Formula',
    holding_period='annual',
    rebalance_freq='annual'
)
magic_formula.add_entry_rule(
    'high_earnings_yield',
    lambda d: d['ebit'] / d['enterprise_value'] > d['median_earnings_yield'],
    weight=1.0
)
magic_formula.add_entry_rule(
    'high_return_on_capital',
    lambda d: d['ebit'] / (d['net_working_capital'] + d['net_fixed_assets']) > d['median_roc'],
    weight=1.0
)
```

### 3.3 복수 방법론 통합 시스템

```
통합 스코어링 프레임워크:

Score_unified = w1 * Score_CANSLIM(정규화)
              + w2 * Score_MagicFormula(정규화)
              + w3 * Score_DualMomentum(정규화)
              + w4 * Score_TrendFollowing(정규화)

가중치 결정 방법:
  1. 등가중 (가장 안전한 시작점)
  2. IC 가중 (각 방법론의 예측력 기반)
  3. 레짐 기반 가중 (시장 상태에 따라 동적 조절)
     - 상승 추세: CAN SLIM + 트렌드 팔로잉 비중 ↑
     - 횡보/하락: Magic Formula + Dual Momentum 비중 ↑
```

---

## 4. 포트폴리오 리스크 관리

### 4.1 리스크 버짓팅 (Risk Budgeting)

```
전체 포트폴리오 리스크를 사전에 배분:

Total Risk Budget = 연간 최대 허용 변동성 (예: 12%)

배분:
  - 전략 A (트렌드 팔로잉): 리스크 예산의 30%
  - 전략 B (팩터 모델): 리스크 예산의 30%
  - 전략 C (모멘텀): 리스크 예산의 25%
  - 현금/채권 버퍼: 리스크 예산의 15%

각 전략의 실제 기여 리스크:
  RC_i = w_i * (Cov * w)_i / sqrt(w^T * Cov * w)

  SUM(RC_i) = Portfolio_Volatility
```

### 4.2 최대 낙폭 관리 (Maximum Drawdown Management)

```
3단계 방어 체계:

Level 1 - 경고 (Warning): 포트폴리오 낙폭 > 10%
  → 신규 포지션 진입 중단
  → 기존 포지션 유지, 모니터링 강화

Level 2 - 방어 (Defensive): 포트폴리오 낙폭 > 15%
  → 전체 포지션 50% 축소
  → 스탑 레벨 타이트하게 조정
  → 안전자산(국채, 금) 비중 확대

Level 3 - 비상 (Emergency): 포트폴리오 낙폭 > 20%
  → 전체 포지션 청산 (현금화)
  → 시스템 재검토 후 점진적 재진입
  → 최소 1개월 냉각기

회복 전략:
  - 재진입 시 정상 포지션의 25%부터 시작
  - 2주마다 25%씩 증가
  - 신고점 도달 시 정상 모드 복귀
```

### 4.3 상관관계 기반 포트폴리오 구성

```
원칙: 낮은 상관관계의 자산/전략 조합으로 분산 효과 극대화

상관계수 매트릭스 모니터링:
  - 목표: 전략 간 평균 상관계수 < 0.3
  - 경고: 임의의 두 전략 상관계수 > 0.7 → 중복 검토 필요

상관관계 분석 프레임워크:
  1. 정상 시장에서의 상관관계 (평시)
  2. 위기 시장에서의 상관관계 (스트레스 시)
  → 위기 시 상관관계가 급등하는 현상(correlation breakdown) 고려

분산 비율 (Diversification Ratio):
  DR = SUM(w_i * sigma_i) / sqrt(w^T * Cov * w)
  DR > 1 → 분산 효과 존재 (높을수록 좋음)
```

### 4.4 Value at Risk (VaR) 및 Conditional VaR

```
Historical VaR (95%):
  VaR_95 = -Percentile(Portfolio_Returns, 5)
  해석: "95% 확률로 일일 손실이 VaR 이하"

Conditional VaR (Expected Shortfall):
  CVaR_95 = -E[R | R <= -VaR_95]
  해석: "최악의 5% 경우에서의 평균 손실"
  → VaR보다 테일 리스크를 더 잘 포착

포트폴리오 레벨 모니터링:
  - 일일 VaR (95%): 포트폴리오 가치의 1.5-2.5% 이내
  - CVaR (95%): VaR의 1.3-1.5배 이내
  - 주간 스트레스 테스트: 2008, 2020, 2022 시나리오 적용
```

---

## 5. 행동재무학과 시스템적 대응

### 5.1 주요 인지 편향과 시스템적 대응

| 편향 | 설명 | 시스템적 대응 |
|------|------|-------------|
| **손실 회피** (Loss Aversion) | 동일 크기의 손실이 이익보다 2배 고통스럽게 느껴짐 | 사전 정의된 스탑로스 자동 실행, 감정적 판단 배제 |
| **처분 효과** (Disposition Effect) | 손실 종목은 보유, 이익 종목은 조기 매도 | 규칙 기반 청산: 스코어 하락 시 매도, 이익 시 트레일링 스탑 |
| **과신** (Overconfidence) | 자신의 예측 능력을 과대평가 | 켈리 기준 + Fractional Kelly(1/4)로 베팅 크기 제한 |
| **확증 편향** (Confirmation Bias) | 기존 신념을 확인하는 정보만 수집 | 정량적 스코어링: 모든 팩터를 동등하게 평가 |
| **앵커링** (Anchoring) | 특정 가격에 고착 | 매수가 무시, 현재 스코어와 모멘텀만으로 판단 |
| **군중 심리** (Herding) | 다수의 행동을 따름 | 역발상 지표 포함 (극단적 낙관 시 경계) |
| **최근 편향** (Recency Bias) | 최근 경험에 과도한 가중치 | 장기 백테스트 결과에 기반, 롤링 윈도우 평균 사용 |

### 5.2 체계적 의사결정 프로세스

```
트레이딩 의사결정 체크리스트 (시스템화):

진입 전:
  [ ] 정량적 스코어가 진입 기준 충족?
  [ ] 시장 레짐 필터 통과? (M 조건)
  [ ] 포지션 사이징이 켈리/변동성 기준 내?
  [ ] 섹터 집중도 한도 내?
  [ ] "이 거래를 왜 하는가"에 대한 정량적 답변 존재?

보유 중:
  [ ] 스코어 재계산 (주간/월간)
  [ ] 스탑로스 레벨 확인
  [ ] 상관관계 변화 모니터링
  [ ] 레짐 변화 감지?

청산 시:
  [ ] 청산 사유가 사전 정의된 규칙에 해당?
  [ ] 감정적 판단이 아닌 시스템 시그널?
  [ ] 세금 영향 고려?
```

---

## 6. 성과 측정 지표

### 6.1 리스크 조정 수익률 지표

```
Sharpe Ratio (샤프비율):
  SR = (R_p - R_f) / sigma_p
  - 총 위험 대비 초과수익
  - 목표: > 1.0 (좋은 전략), > 1.5 (우수), > 2.0 (뛰어남)

Sortino Ratio (소르티노비율):
  SoR = (R_p - R_f) / sigma_downside
  - 하방 위험만 고려 (상방 변동성은 패널티 없음)
  - sigma_downside = sqrt(E[min(R - R_f, 0)^2])
  - 목표: > 1.5

Calmar Ratio (칼마비율):
  CR = (R_p - R_f) / MDD
  - 최대 낙폭 대비 수익률
  - 직관적: "최악의 손실 대비 얼마나 벌었나"
  - 목표: > 0.5 (3년+ 기간)

Information Ratio (정보비율):
  IR = (R_p - R_b) / TE
  - 벤치마크 대비 추적오차당 초과수익
  - 목표: > 0.5

Omega Ratio (오메가비율):
  Omega(r) = ∫[r,∞] (1-F(x))dx / ∫[-∞,r] F(x)dx
  - 전체 수익률 분포 포착 (평균/분산 넘어)
  - Omega > 1: 수익 확률이 손실 확률보다 높음
```

### 6.2 리스크 지표

```
Maximum Drawdown (최대 낙폭):
  MDD = max(HWM_t - NAV_t) / HWM_t
  - 목표: < 20% (보통), < 15% (보수적)

Drawdown Duration (낙폭 지속기간):
  - 전고점에서 회복까지의 기간
  - 목표: < 6개월

Profit Factor (이익 계수):
  PF = 총 이익 / 총 손실
  - 목표: > 1.5

Win Rate (승률):
  WR = 이익 거래 수 / 총 거래 수
  - 스윙 트레이딩 목표: > 55%
  - 트렌드 팔로잉: 35-45%도 허용 (큰 승리로 보상)

Recovery Factor (회복 계수):
  RF = 총 수익 / 최대 낙폭
  - 목표: > 3.0
```

---

## 7. 리밸런싱 전략

### 7.1 리밸런싱 방법 비교

| 방법 | 설명 | 장점 | 단점 | 추천 용도 |
|------|------|------|------|---------|
| **달력 기반** | 고정 주기 리밸런싱 (월, 분기) | 단순, 예측 가능, 낮은 거래비용 | 급격한 변화에 느린 대응 | 포지션 트레이딩 |
| **임계치 기반** | 목표 비중에서 ±X% 이탈 시 | 필요 시에만 거래, 효율적 | 모니터링 필요 | 멀티 전략 포트폴리오 |
| **시그널 기반** | 스코어 변화/레짐 전환 시 | 시장 상황에 적응적 | 높은 거래빈도 가능성 | 스윙 트레이딩 |
| **하이브리드** | 달력 + 임계치 결합 | 균형적 접근 | 규칙 복잡성 | 권장 기본값 |

### 7.2 최적 리밸런싱 주기

```
포지션 트레이딩 (수개월~수년):
  - 기본: 분기 리밸런싱 (3월, 6월, 9월, 12월)
  - 비상: 포지션이 목표 대비 ±50% 이탈 시 즉시
  - 레짐 전환: HMM 레짐 변경 시 즉시 (단, 확신도 > 80%)

스윙 트레이딩 (수주~수개월):
  - 기본: 월 리밸런싱
  - 비상: 주간 스코어 검토, 임계치 이탈 시 즉시
  - 손절: 스탑로스 히트 시 즉시

거래비용 고려:
  - 리밸런싱 이익 > 예상 거래비용 * 2 일 때만 실행
  - 소규모 이탈(< 2%)은 무시 → 불필요한 거래 방지
```

---

## 8. 세금 효율적 트레이딩

### 8.1 장기 보유 세금 최적화

```
한국 세금 체계 (2025년 기준):
  - 국내 주식 양도소득세: 대주주 기준 적용
  - 해외 주식 양도소득세: 250만원 기본공제 후 22% (지방세 포함)
  - 금융투자소득세: 향후 도입 시 5,000만원 기본공제

세금 효율 전략:
  1. 장기 보유 우선: 단기 매매 최소화 (거래세 + 양도세 절감)
  2. 손실 실현 (Tax-Loss Harvesting):
     - 연말 전 미실현 손실 종목 매도
     - 실현된 이익과 상계
     - 30일 후 동일/유사 종목 재매수 (워시세일 규칙 해당 시)
  3. 이익 이연: 연도 전환기에 이익 실현 타이밍 조절
  4. 분할 실현: 기본공제 한도 내에서 연간 이익 분산
```

### 8.2 미국 주식 세금 최적화 (Tax-Loss Harvesting)

```
Tax-Loss Harvesting 프로세스:

1. 모니터링: 포트폴리오 내 미실현 손실 종목 식별
2. 손실 실현: 손실 종목 매도 (단기/장기 구분)
3. 대체 투자: 유사하지만 "실질적으로 동일하지 않은" 종목/ETF 매수
   - 예: AAPL 매도 → QQQ 매수 (워시세일 회피)
4. 30일 후: 원래 종목 재매수 가능
5. 상계: 실현 손실을 실현 이익과 상계

규칙:
  - 단기 손실 → 단기 이익과 먼저 상계
  - 장기 손실 → 장기 이익과 먼저 상계
  - 순 손실 $3,000/년까지 일반 소득과 상계 가능
  - 미사용 손실은 무기한 이월 가능
```

---

## 9. 오픈소스 도구 및 데이터 소스

### 9.1 백테스팅 프레임워크 비교

| 프레임워크 | 속도 | 라이브 트레이딩 | 난이도 | 추천 용도 |
|-----------|------|---------------|--------|---------|
| **VectorBT** | 최고 (벡터화, Numba) | 아니오 | 높음 | 대규모 파라미터 최적화, 팩터 리서치 |
| **Backtrader** | 보통 (이벤트 드리븐) | 예 (IB, Alpaca) | 보통 | 스윙 트레이딩 시스템 + 브로커 연동 |
| **Zipline-reloaded** | 보통 | 아니오 | 보통 | 팩터 기반 주식 리서치, scikit-learn 연동 |
| **QuantConnect/LEAN** | 보통 | 예 | 보통 | 클라우드 기반 전략 개발 |
| **NautilusTrader** | 빠름 (Rust 코어) | 예 | 높음 | 기관급 프로덕션 시스템 |
| **Backtesting.py** | 빠름 | 아니오 | 낮음 | 빠른 프로토타입 |

### 9.2 포트폴리오 최적화 라이브러리

| 라이브러리 | 기능 | 추천 용도 |
|-----------|------|---------|
| **PyPortfolioOpt** | MVO, HRP, Black-Litterman | HRP 구현, 일반 최적화 |
| **Riskfolio-Lib** | MVO, HRP, Risk Parity, 팩터 모델 | 고급 리스크 패리티 |
| **cvxpy** | 범용 볼록 최적화 | 커스텀 최적화 문제 |
| **empyrical** | 성과 지표 계산 | 샤프, 소르티노, MDD 등 |

### 9.3 머신러닝 & 팩터 라이브러리

| 라이브러리 | 용도 |
|-----------|------|
| **scikit-learn** | 일반 ML, 피처 선택, 교차검증 |
| **XGBoost / LightGBM** | 그래디언트 부스팅 (최고 성능 팩터 모델) |
| **hmmlearn** | Hidden Markov Model (레짐 감지) |
| **Optuna** | 베이지안 하이퍼파라미터 최적화 |
| **SHAP** | 모델 해석 (팩터 기여도 분석) |
| **pandas-ta** | 기술적 분석 지표 계산 |

### 9.4 데이터 소스

| 데이터 유형 | 소스 | 비용 | 비고 |
|------------|------|------|------|
| **가격 데이터** | Yahoo Finance (yfinance) | 무료 | 일간 데이터, 제한적 |
| | Alpha Vantage | 무료/유료 | API, 기본적 분석 포함 |
| | Polygon.io | 유료 ($29/월~) | 실시간 + 히스토리컬 |
| | EODHD | 유료 ($20/월~) | 글로벌 데이터, 펀더멘탈 |
| **펀더멘탈 데이터** | Financial Modeling Prep | 무료/유료 | 재무제표, 비율 |
| | SimFin | 무료/유료 | 포인트 인 타임 데이터 |
| | SEC EDGAR | 무료 | 미국 공시 원본 |
| **대안 데이터** | Quandl/Nasdaq Data Link | 유료 | 다양한 대안 데이터 |
| **한국 주식** | KRX 정보데이터시스템 | 무료 | 한국거래소 공식 |
| | pykrx 라이브러리 | 무료 | Python으로 KRX 데이터 |
| | FinanceDataReader | 무료 | 한국 주식 + 글로벌 |

---

## 10. 백테스팅 함정과 회피 방법

### 10.1 오버피팅 (Overfitting)

```
정의: 과거 데이터의 노이즈에 맞추어진 전략이 미래에 실패하는 현상

원인:
  - 과도한 파라미터 최적화
  - 너무 많은 전략을 테스트 (데이터 마이닝)
  - 짧은 백테스트 기간
  - 단일 분할(single split) 검증

탐지 방법:
  1. PBO (Probability of Backtest Overfitting) < 10%
     - CSCV로 계산, 최적 IS 전략이 OOS에서 중위 이하 확률
  2. Deflated Sharpe Ratio (DSR)
     - 시행 횟수, 비정규성 보정된 샤프비율
  3. Walk-Forward Efficiency > 50%
     - OOS 성과 / IS 성과 비율
  4. 파라미터 안정성 테스트
     - 파라미터 ±10% 변경 시 성과 유지 여부

회피 방법:
  - 파라미터 최소화 (전략당 2-4개)
  - Walk-Forward Analysis 또는 CPCV 사용
  - 최소 10년 이상, 다중 시장 사이클 포함
  - 교차 자산/시장 검증
```

### 10.2 생존자 편향 (Survivorship Bias)

```
정의: 상장폐지/파산 종목을 제외하고 백테스팅하여 성과가 과대 추정되는 현상

영향: 연간 1-3%의 성과 과대 추정
  - 가치 전략에 특히 큰 영향 (싼 주식 중 일부가 파산)

회피 방법:
  - 생존자 편향 없는 데이터베이스 사용
  - 상장폐지 종목 포함 (폐지 시 수익률 반영)
  - CRSP, Compustat (미국), 또는 비편향 데이터 소스 사용
  - 자체 데이터 구축 시 폐지 종목 반드시 포함
```

### 10.3 미래 정보 편향 (Look-Ahead Bias)

```
정의: 의사결정 시점에 알 수 없었던 미래 정보를 사용하는 오류

일반적인 실수:
  1. 재수정된(restated) 재무제표 사용
     → 해결: Point-in-Time 데이터 사용 (as-reported)
  2. 리밸런싱 일에 아직 발표되지 않은 데이터 사용
     → 해결: 데이터 발표 지연(lag) 고려 (분기 실적은 ~45일 후)
  3. 전체 기간 통계치(전체 평균, 표준편차)로 정규화
     → 해결: 롤링 윈도우로 해당 시점까지만의 통계치 사용
  4. 최적 종목을 사후적으로 선택
     → 해결: 모든 선택을 과거 데이터만으로 결정

구현 체크리스트:
  [ ] 재무 데이터는 발표일+1일부터 사용?
  [ ] 정규화는 해당 시점까지의 데이터만으로?
  [ ] ML 모델은 미래 데이터 없이 학습?
  [ ] 유니버스는 해당 시점의 상장 종목만?
```

### 10.4 기타 주요 함정

```
거래비용 무시:
  - 수수료, 스프레드, 시장 충격 반드시 포함
  - 소형주: 왕복 0.5-1.0% 비용 가정
  - 대형주: 왕복 0.1-0.3% 비용 가정

용량 제약 무시:
  - 전략이 흡수할 수 있는 자금 규모 한계
  - 소형주 전략: 유동성 부족으로 슬리피지 급증
  - 대규모 자금 시 시장 충격 모델링 필요

레짐 변화 무시:
  - 시장 구조 변화 (금리 환경, 규제 변화)
  - 2000년대 이전 데이터가 현재에도 유효한지 검토
  - 다중 레짐 테스트 (상승장, 하락장, 횡보장)
```

---

## 11. 통합 방법론 시스템 설계

### 11.1 완전한 통합 아키텍처

```
===============================================================================
              통합 검증 방법론 트레이딩 시스템
===============================================================================

PHASE 1: 매크로 필터 (시장 방향 판단)
  ┌─────────────────────────────────────┐
  │ Dual Momentum 시장 필터            │
  │ - 미국 12M 수익률 vs 국제 12M 수익률 │
  │ - 절대 모멘텀 (vs T-Bill)          │
  │ → 주식 ON / 채권 전환 결정           │
  │                                     │
  │ 트렌드 필터                         │
  │ - S&P 500 vs 200-day MA            │
  │ - VIX 수준 및 텀스트럭처            │
  │ → 공격적 / 방어적 모드 결정          │
  └─────────────────────────────────────┘
                    │
                    ▼
PHASE 2: 유니버스 필터링
  ┌─────────────────────────────────────┐
  │ 안전성 필터 (통과/불합격)            │
  │ - Altman Z-Score > 1.81            │
  │ - Beneish M-Score < -1.78          │
  │ - 최소 유동성 충족                  │
  │ - 상장폐지/인수합병 예정 제외        │
  └─────────────────────────────────────┘
                    │
                    ▼
PHASE 3: 멀티 방법론 스코어링
  ┌─────────────────────────────────────┐
  │ 가치 스코어 (Magic Formula 기반)    │
  │ - Earnings Yield 순위              │
  │ - Return on Capital 순위            │
  │                                     │
  │ 성장 스코어 (CAN SLIM 기반)         │
  │ - EPS 성장률                       │
  │ - 상대강도 점수                     │
  │ - 거래량 확인                       │
  │                                     │
  │ 품질 스코어 (Piotroski F-Score)     │
  │ - 재무 건전성 9점 척도              │
  │ - Mohanram G-Score (성장주)         │
  │                                     │
  │ 모멘텀 스코어                       │
  │ - 12-1개월 수익률 모멘텀            │
  │ - 섹터 상대 강도                    │
  │                                     │
  │ → 정규화 (백분위 순위, 섹터 중립)    │
  │ → 복합 점수 = 가중 합산              │
  └─────────────────────────────────────┘
                    │
                    ▼
PHASE 4: 리스크 조정 및 포지션 사이징
  ┌─────────────────────────────────────┐
  │ 리스크 조정 스코어                  │
  │ - 변동성 패널티                     │
  │ - 낙폭 페널티                      │
  │ - 테일 리스크 조정 (CVaR)           │
  │                                     │
  │ 포지션 사이징                       │
  │ - Fractional Kelly (1/4~1/2)       │
  │ - ATR 기반 변동성 조정              │
  │ - 확신도 스코어 반영                │
  │                                     │
  │ 집중도 한도                         │
  │ - 단일 종목: 최대 5-8%             │
  │ - 섹터: 최대 25%                   │
  │ - 상관 클러스터: 최대 20%           │
  └─────────────────────────────────────┘
                    │
                    ▼
PHASE 5: 실행 및 모니터링
  ┌─────────────────────────────────────┐
  │ 실행                                │
  │ - 월간 리밸런싱 (스윙)              │
  │ - 분기 리밸런싱 (포지션)            │
  │                                     │
  │ 리스크 모니터링                     │
  │ - 일일: VaR, 낙폭 체크             │
  │ - 주간: 스코어 재계산              │
  │ - 월간: 성과 어트리뷰션             │
  │                                     │
  │ 자기 개선                           │
  │ - 월간: Walk-Forward 재최적화      │
  │ - 분기: 전체 모델 재학습           │
  │ - 연간: 전략 유효성 종합 검토       │
  └─────────────────────────────────────┘
===============================================================================
```

### 11.2 방법론 선택 가이드

| 투자자 유형 | 추천 주 방법론 | 보유 기간 | 리밸런싱 | 복잡도 |
|------------|--------------|---------|---------|--------|
| 초보 체계적 투자자 | Dual Momentum | 월 단위 | 월 1회 | 낮음 |
| 중급 가치 투자자 | Magic Formula + F-Score | 연 단위 | 연 1회 | 보통 |
| 중급 성장 투자자 | CAN SLIM (정량화) | 수주~수개월 | 월 1회 | 보통 |
| 고급 체계적 투자자 | 멀티팩터 복합 모델 | 월~분기 | 월/분기 | 높음 |
| 고급 + ML | 풀 스킬 체인 시스템 | 주~분기 | 주/월 | 매우 높음 |

### 11.3 점진적 구현 로드맵

```
Stage 1 (최소 실행 가능 시스템 - 1-2개월):
  - Dual Momentum으로 시장 필터
  - Magic Formula로 종목 선별
  - 등가중 포트폴리오 (20-30 종목)
  - 연 1회 리밸런싱

Stage 2 (기본 정량 시스템 - 3-6개월):
  - F-Score/G-Score 필터 추가
  - 복합 스코어링 (가치 + 품질 + 모멘텀)
  - Fractional Kelly 포지션 사이징
  - 월/분기 리밸런싱
  - 기본 리스크 한도 (섹터, 낙폭)

Stage 3 (고급 적응형 시스템 - 6-12개월):
  - HMM 레짐 감지
  - 멀티 전략 앙상블
  - Walk-Forward 최적화
  - 자동 성과 어트리뷰션
  - ATR 기반 적응형 스탑

Stage 4 (풀 스킬 체인 시스템 - 12개월+):
  - ML 기반 메타 러닝
  - 자기 개선 피드백 루프
  - HRP 포트폴리오 최적화
  - 풀 자동화 파이프라인
```

---

## 주요 참고 문헌 및 소스

### 학술 논문
- Fama, E. & French, K. (1993). "Common Risk Factors in the Returns on Stocks and Bonds." Journal of Financial Economics.
- Fama, E. & French, K. (2015). "A Five-Factor Asset Pricing Model." Journal of Financial Economics.
- Carhart, M. (1997). "On Persistence in Mutual Fund Performance." Journal of Finance.
- Jegadeesh, N. & Titman, S. (1993). "Returns to Buying Winners and Selling Losers." Journal of Finance.
- Asness, C., Moskowitz, T. & Pedersen, L. (2013). "Value and Momentum Everywhere." Journal of Finance.
- Novy-Marx, R. (2013). "The Other Side of Value: The Gross Profitability Premium." Journal of Financial Economics.
- Blitz, D. & van Vliet, P. (2007). "The Volatility Effect." Journal of Portfolio Management.
- Piotroski, J. (2000). "Value Investing: The Use of Historical Financial Statement Information." Journal of Accounting Research.
- Lopez de Prado, M. (2018). "Advances in Financial Machine Learning." Wiley.

### 실무 서적
- Greenblatt, J. (2006). "The Little Book That Beats the Market."
- Antonacci, G. (2014). "Dual Momentum Investing."
- O'Neil, W. (2009). "How to Make Money in Stocks." (CAN SLIM)
- Pardo, R. (2008). "The Evaluation and Optimization of Trading Strategies."
- Dalio, R. (2017). "Principles." (All-Weather Portfolio)

### 온라인 소스
- [AQR Factor Investing Research](https://www.aqr.com/Insights/Research)
- [SSRN Quantitative Finance Papers](https://papers.ssrn.com/sol3/JELJOUR_Results.cfm?form_name=journalbrowse&journal_id=3523345)
- [Kenneth French's Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)
- [Quantpedia - Encyclopedia of Quantitative Trading Strategies](https://quantpedia.com/)
- [Alpha Architect - Evidence-Based Investing](https://alphaarchitect.com/)
- [Robeco Factor Investing Research](https://www.robeco.com/en-int/insights)
