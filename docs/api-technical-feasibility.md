# 트레이딩 API 기술적 타당성 분석

## Trading API Technical Feasibility Study

**목적**: 미국 NYSE 및 주요 5대 글로벌 증권시장에 대한 데이터 검색 + 매매 실행 API의 기술적 타당성 평가
**범위**: 정보 조회 API, 매매 실행 API, CLI/Skill 통합, 비용, 할당량, 자격증명 관리
**원칙**: 빠르고 파워풀하며 API quota가 충분한 솔루션 우선

---

## 목차

1. [대상 시장 및 거래소](#1-대상-시장-및-거래소)
2. [API 카테고리 분류](#2-api-카테고리-분류)
3. [미국 브로커 API 비교](#3-미국-브로커-api-비교)
4. [글로벌 시장 데이터 API 비교](#4-글로벌-시장-데이터-api-비교)
5. [한국/아시아 브로커 API 비교](#5-한국아시아-브로커-api-비교)
6. [종합 비교 매트릭스](#6-종합-비교-매트릭스)
7. [추천 아키텍처](#7-추천-아키텍처)
8. [.env 자격증명 관리 설계](#8-env-자격증명-관리-설계)
9. [API Quota 분석](#9-api-quota-분석)
10. [CLI 도구 & Claude Skill 통합 설계](#10-cli-도구--claude-skill-통합-설계)
11. [비용 분석](#11-비용-분석)
12. [리스크 및 제약사항](#12-리스크-및-제약사항)
13. [구현 로드맵](#13-구현-로드맵)

---

## 1. 대상 시장 및 거래소

### 주요 5대 + 미국 증권시장

| 순위 | 거래소 | 국가 | 시가총액 (2024) | 통화 | 거래시간 (현지) |
|------|--------|------|-----------------|------|----------------|
| 1 | **NYSE** (New York Stock Exchange) | 미국 | ~$28.4T | USD | 09:30-16:00 ET |
| 2 | **NASDAQ** | 미국 | ~$25.5T | USD | 09:30-16:00 ET |
| 3 | **Shanghai Stock Exchange (SSE)** | 중국 | ~$6.9T | CNY | 09:30-15:00 CST |
| 4 | **Euronext** | EU (프랑스/네덜란드 등) | ~$7.3T | EUR | 09:00-17:30 CET |
| 5 | **Japan Exchange Group (JPX/TSE)** | 일본 | ~$6.5T | JPY | 09:00-15:30 JST |
| 6 | **Hong Kong Exchange (HKEX)** | 홍콩 | ~$4.2T | HKD | 09:30-16:00 HKT |
| 7 | **Korea Exchange (KRX)** | 한국 | ~$1.8T | KRW | 09:00-15:30 KST |

> **참고**: LSE(런던), TSX(토론토), BSE(인도) 등도 IBKR/Twelve Data를 통해 접근 가능

---

## 2. API 카테고리 분류

트레이딩 시스템에 필요한 API는 크게 3가지 카테고리로 분류됨:

```
┌─────────────────────────────────────────────────────────┐
│                   Trading System APIs                    │
├────────────────┬──────────────────┬─────────────────────┤
│  Market Data   │  Trading/Broker  │   Analytics/Alt     │
│  (정보 조회)     │  (매매 실행)       │   (부가 분석)         │
├────────────────┼──────────────────┼─────────────────────┤
│ • 실시간 시세    │ • 주문 제출/취소   │ • 재무제표           │
│ • 히스토리컬     │ • 포트폴리오 조회  │ • 뉴스/센티먼트      │
│ • 틱/분봉/일봉   │ • 계좌 잔고       │ • 섹터/산업 분류      │
│ • WebSocket     │ • 주문 상태 추적   │ • 스크리너            │
│ • 펀더멘탈       │ • 마진/레버리지    │ • ETF 구성종목        │
└────────────────┴──────────────────┴─────────────────────┘
```

### 핵심 요구사항

| 요구사항 | 우선순위 | 비고 |
|---------|---------|------|
| REST API (동기 호출) | **필수** | CLI/Skill 기본 인터페이스 |
| WebSocket (실시간 스트리밍) | 높음 | 실시간 시세, 주문 상태 알림 |
| Python SDK | **필수** | CLI 도구 및 Claude Agent 연동 |
| Paper Trading (모의 거래) | **필수** | 검증 단계 필수 |
| 펀더멘탈 데이터 | 높음 | 스코어링 엔진(F-Score 등) 입력 |
| 글로벌 멀티마켓 | 높음 | 5대 시장 커버리지 |
| 합리적 비용 | 중간 | 월 $300 이내 목표 |

---

## 3. 미국 브로커 API 비교

### 3.1 Alpaca Markets

| 항목 | 세부사항 |
|------|---------|
| **유형** | 브로커 + 데이터 (통합형) |
| **지원 시장** | 미국 (NYSE, NASDAQ) |
| **Python SDK** | `alpaca-py` (공식), `alpaca-trade-api` (레거시) |
| **인증** | API Key + Secret Key |
| **REST API Rate** | 200 req/min (무료), 더 높은 플랜 가능 |
| **WebSocket** | 실시간 틱/호가/바, IEX 무료 / SIP 유료 |
| **Paper Trading** | ✅ 무료 (별도 엔드포인트) |
| **주문 유형** | Market, Limit, Stop, Stop-Limit, Trailing Stop |
| **수수료** | $0 커미션 |
| **펀더멘탈** | ❌ (외부 데이터 소스 필요) |
| **설치** | `pip install alpaca-py` |

**장점**:
- 개발자 경험 최고 (깔끔한 REST API, 우수한 문서)
- 무료 Paper Trading으로 즉시 검증 가능
- 커미션 무료, 최소 잔고 없음
- 빠른 주문 실행

**단점**:
- 미국 시장만 지원 (글로벌 확장 불가)
- 펀더멘탈 데이터 없음 (별도 API 필요)
- 무료 실시간 데이터는 IEX만 (SIP은 유료)

**코드 예시**:
```python
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

client = TradingClient(api_key, secret_key, paper=True)

# 매수 주문
order = MarketOrderRequest(
    symbol="AAPL",
    qty=10,
    side=OrderSide.BUY,
    time_in_force=TimeInForce.DAY
)
result = client.submit_order(order)
```

### 3.2 Interactive Brokers (IBKR)

| 항목 | 세부사항 |
|------|---------|
| **유형** | 풀서비스 브로커 (글로벌) |
| **지원 시장** | 160+ 시장, 36개국, 27개 통화 |
| **Python SDK** | `ib_insync` / `ib_async` (커뮤니티), TWS API (공식) |
| **인증** | TWS/Gateway + Client ID (로컬), Client Portal API (웹) |
| **REST API Rate** | 50 msg/sec (TWS API), Client Portal은 별도 |
| **WebSocket** | TWS API 이벤트 기반, Client Portal WebSocket |
| **Paper Trading** | ✅ 무료 (TWS Paper Trading 모드) |
| **주문 유형** | 100+ 주문 유형 (가장 다양) |
| **수수료** | 주식 $0.0035/주 (미국), 시장별 상이 |
| **펀더멘탈** | ✅ Reuters 펀더멘탈 (유료 구독) |
| **설치** | `pip install ib_async` + TWS/Gateway 필수 |

**장점**:
- **가장 넓은 글로벌 커버리지** (160+ 시장)
- 모든 자산클래스 (주식, 옵션, 선물, 외환, 채권, CFD)
- 기관급 주문 라우팅 및 실행
- 낮은 수수료, 포트폴리오 마진

**단점**:
- TWS/Gateway 상시 실행 필요 (headless 서버 설정 복잡)
- API 설정이 복잡 (IB Gateway + 포트 설정)
- 인증 체계가 CLI/클라우드 환경에 부적합 (2FA + 클라이언트 앱 필요)
- 연결 불안정 시 재연결 로직 필요

**코드 예시**:
```python
from ib_async import IB, Stock, MarketOrder

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)  # Paper: 7497, Live: 7496

contract = Stock('AAPL', 'SMART', 'USD')
order = MarketOrder('BUY', 10)
trade = ib.placeOrder(contract, order)

# 글로벌 주식 (도쿄)
toyota = Stock('7203', 'TSEJ', 'JPY')
ib.qualifyContracts(toyota)
```

### 3.3 Schwab (구 TD Ameritrade)

| 항목 | 세부사항 |
|------|---------|
| **유형** | 브로커 (미국) |
| **지원 시장** | 미국 (NYSE, NASDAQ) |
| **Python SDK** | `schwab-py` (커뮤니티) |
| **인증** | OAuth 2.0 (App Key + Secret) |
| **REST API Rate** | 120 orders/min |
| **WebSocket** | ✅ 실시간 스트리밍 |
| **Paper Trading** | ❌ 없음 |
| **수수료** | $0 커미션 (온라인 주식) |

**장점**:
- 대형 브로커의 안정성, $0 커미션
- OAuth 2.0 표준 인증

**단점**:
- Paper Trading 미지원 (치명적)
- 미국 시장만
- TD Ameritrade → Schwab 전환으로 API 불안정 우려

### 3.4 Tradier

| 항목 | 세부사항 |
|------|---------|
| **유형** | 브로커 API 전문 |
| **지원 시장** | 미국 (주식 + 옵션) |
| **인증** | OAuth Bearer Token |
| **REST API Rate** | 60 req/min (무료), 120 req/min (유료) |
| **Paper Trading** | ✅ Sandbox 환경 |
| **수수료** | $0 주식, $0.35/계약 옵션 |

**장점**:
- API 전문 브로커 (개발자 친화적)
- Sandbox 무료 제공
- 깔끔한 REST API

**단점**:
- 미국 시장만
- Rate limit 상대적으로 낮음
- 펀더멘탈 데이터 제한적

### 3.5 Webull

| 항목 | 세부사항 |
|------|---------|
| **유형** | 리테일 브로커 |
| **지원 시장** | 미국, HK (일부) |
| **Python SDK** | `webull` (비공식), 공식 API 2025년 출시 |
| **인증** | DID + Access Token |
| **REST API Rate** | 150 req/10s (공식 API 기준) |
| **Paper Trading** | ✅ 앱 내 Paper Trading |
| **수수료** | $0 커미션 |

**장점**:
- $0 커미션, 사전/사후 시장 거래
- 2025년 공식 API 출시로 안정성 개선 기대

**단점**:
- 공식 API 성숙도 낮음
- 비공식 SDK 의존 시 불안정
- 기관급 기능 부족

---

## 4. 글로벌 시장 데이터 API 비교

### 4.1 Twelve Data ⭐ (글로벌 데이터 추천)

| 항목 | 세부사항 |
|------|---------|
| **커버리지** | **84+ 거래소, 60+ 국가** |
| **데이터 유형** | 실시간, 히스토리컬, 펀더멘탈, 기술적 지표, WebSocket |
| **인증** | API Key |
| **무료 티어** | 8 req/min, 800 req/day |
| **Grow 플랜** | $29/mo: 30 req/min, 3,000 req/day |
| **Pro 플랜** | $229/mo: 120 req/min, unlimited, WebSocket 10 symbols |
| **Enterprise** | 맞춤형: 무제한 |
| **Python SDK** | `twelvedata` (공식) |
| **특장점** | 내장 기술적 지표 100+, 타임시리즈 API 우수 |
| **설치** | `pip install twelvedata` |

**장점**:
- **가장 넓은 글로벌 커버리지** (데이터 API 중)
- NYSE, NASDAQ, TSE, SSE, HKEX, Euronext, KRX 모두 지원
- 100+ 내장 기술적 지표 (SMA, RSI, MACD 등)
- WebSocket 실시간 스트리밍
- 깔끔한 SDK와 문서

**단점**:
- Pro 플랜($229/mo) 필요 시 비용 부담
- 무료 티어 매우 제한적
- 실시간 데이터 15분 지연 (무료)

**코드 예시**:
```python
from twelvedata import TDClient

td = TDClient(apikey="YOUR_API_KEY")

# 글로벌 히스토리컬 데이터
ts = td.time_series(
    symbol="7203.T",  # 도요타 (도쿄)
    interval="1day",
    outputsize=252,
    timezone="Asia/Tokyo"
)
df = ts.as_pandas()

# 기술적 지표
rsi = td.rsi(symbol="AAPL", interval="1day", time_period=14).as_json()
```

### 4.2 EODHD (End of Day Historical Data) ⭐ (가성비 추천)

| 항목 | 세부사항 |
|------|---------|
| **커버리지** | **60+ 거래소, 주요 시장 모두** |
| **데이터 유형** | EOD, 인트라데이, 펀더멘탈, 배당, 분할, 매크로 |
| **인증** | API Token |
| **무료 티어** | 20 req/day (매우 제한) |
| **All-World** | $49.99/mo: 100K req/day, EOD 전 시장 |
| **All-In-One** | $99.99/mo: 100K req/day, 인트라데이 + 펀더멘탈 포함 |
| **Python SDK** | `eodhd` (공식) |
| **특장점** | 가격 대비 가장 넓은 데이터 커버리지 |
| **설치** | `pip install eodhd` |

**장점**:
- **최고 가성비** ($99.99에 글로벌 EOD + 인트라데이 + 펀더멘탈)
- 60+ 거래소 (우리 대상 5대 시장 모두 포함)
- 재무제표, 배당, 분할 데이터 포함 (스코어링 엔진 입력)
- 100K req/day 넉넉한 할당량

**단점**:
- 실시간 스트리밍(WebSocket) 없음 (EOD/인트라데이 폴링만)
- 스윙/포지션 트레이딩에는 충분하나 실시간 모니터링에는 부족
- SDK 성숙도가 Twelve Data보다 낮음

**코드 예시**:
```python
from eodhd import APIClient

api = APIClient("YOUR_API_TOKEN")

# EOD 데이터 (글로벌)
df = api.get_eod_data("7203.T")          # 도쿄: 도요타
df = api.get_eod_data("MC.PA")           # 파리: LVMH
df = api.get_eod_data("005930.KO")       # 한국: 삼성전자

# 펀더멘탈 데이터
fundamentals = api.get_fundamentals("AAPL.US")
```

### 4.3 Financial Modeling Prep (FMP)

| 항목 | 세부사항 |
|------|---------|
| **커버리지** | 주요 글로벌 시장 (미국 중심) |
| **데이터 유형** | 주가, 재무제표, SEC 파일링, ETF, 암호화폐 |
| **인증** | API Key |
| **무료 티어** | 250 req/day |
| **Starter** | $14.99/mo: 300 req/min |
| **Professional** | $49.99/mo: 750 req/min |
| **Ultimate** | $149.99/mo: 3000 req/min, 전체 데이터 |
| **Python SDK** | 비공식 (`fmpsdk`) |
| **특장점** | **가장 깊은 펀더멘탈 데이터** |

**장점**:
- 재무제표 데이터 최고 (Income Statement, Balance Sheet, Cash Flow)
- F-Score, Z-Score 계산에 필요한 모든 항목 직접 제공
- SEC 파일링, 내부자 거래, 기관 보유 데이터
- 3000 req/min (Ultimate) 매우 넉넉

**단점**:
- 글로벌 커버리지가 Twelve Data/EODHD보다 좁음
- 실시간 데이터 품질이 전문 데이터 업체보다 낮음
- Ultimate 플랜 필요 시 $149.99/mo

### 4.4 Polygon.io

| 항목 | 세부사항 |
|------|---------|
| **커버리지** | **미국 전용** (SIP 풀 마켓 데이터) |
| **데이터 유형** | 틱, 바, 호가, 뉴스, 레퍼런스 |
| **인증** | API Key |
| **무료 티어** | 5 req/min, 2년 지연 히스토리 |
| **Starter** | $29/mo: 무제한 API, 2년 히스토리 |
| **Developer** | $79/mo: 5년 히스토리 |
| **Advanced** | $199/mo: 풀 히스토리, WebSocket |
| **Python SDK** | `polygon-api-client` (공식) |
| **특장점** | 미국 시장 데이터 품질 최고 (SIP) |

**장점**:
- 미국 시장 데이터 품질/정확도 최고
- WebSocket 실시간 스트리밍 우수
- 충실한 공식 Python SDK

**단점**:
- **미국 시장만** (글로벌 불가)
- 글로벌 시스템에는 보조 역할만 가능

### 4.5 Alpha Vantage

| 항목 | 세부사항 |
|------|---------|
| **커버리지** | 글로벌 (미국 중심) |
| **무료 티어** | 25 req/day |
| **Premium** | $49.99/mo: 75 req/min |
| **특장점** | 기술적 지표 내장, 센티먼트 API |

**평가**: 무료 티어 매우 제한, 유료 대비 가성비 낮음. 권장하지 않음.

### 4.6 yfinance (Yahoo Finance 비공식)

| 항목 | 세부사항 |
|------|---------|
| **커버리지** | 글로벌 (야후 파이낸스 범위) |
| **비용** | 무료 (비공식 스크래핑) |
| **Python SDK** | `yfinance` |
| **Rate Limit** | 비공식 (과도 사용 시 차단) |

**장점**: 무료, 글로벌 커버리지, 간편한 사용
**단점**: **프로덕션 부적합** (비공식 API, 언제든 차단 가능, SLA 없음, 데이터 정확도 보장 불가)
**용도**: 리서치/프로토타이핑 전용, 프로덕션에서는 유료 API 사용 필수

---

## 5. 한국/아시아 브로커 API 비교

### 5.1 한국투자증권 (KIS) OpenAPI ⭐ (한국 시장 추천)

| 항목 | 세부사항 |
|------|---------|
| **유형** | 증권사 OpenAPI |
| **지원 시장** | KRX (한국), 해외주식 (미국/중국/일본/홍콩) |
| **인증** | App Key + App Secret + 접근토큰 |
| **REST API Rate** | 20 req/sec |
| **WebSocket** | ✅ 실시간 시세, 호가, 체결 |
| **Paper Trading** | ✅ 모의투자 환경 별도 제공 |
| **Python SDK** | `python-kis` (커뮤니티), REST 직접 호출 |
| **수수료** | 0.015% ~ 0.5% (거래소/상품별) |
| **해외주식** | ✅ 미국, 중국, 일본, 홍콩, 베트남 |
| **계좌 요건** | 한국투자증권 계좌 필수 |

**장점**:
- **한국 시장 최우수 API** (안정성, 기능, 문서)
- REST + WebSocket 모두 지원
- 해외주식 매매도 가능 (미국/일본/홍콩/중국)
- 모의투자 환경으로 안전한 테스트
- 20 req/sec 충분한 Rate Limit

**단점**:
- 한국 증권 계좌 필수 (해외 거주자 개설 어려움)
- 접근 토큰 24시간마다 갱신 필요
- API 문서가 한국어만 제공

**코드 예시**:
```python
import requests

# 접근토큰 발급
token_url = "https://openapi.koreainvestment.com:9443/oauth2/tokenP"
token_body = {
    "grant_type": "client_credentials",
    "appkey": APP_KEY,
    "appsecret": APP_SECRET
}
token = requests.post(token_url, json=token_body).json()["access_token"]

# 국내 주식 현재가 조회
headers = {
    "authorization": f"Bearer {token}",
    "appkey": APP_KEY,
    "appsecret": APP_SECRET,
    "tr_id": "FHKST01010100"
}
params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": "005930"}  # 삼성전자
resp = requests.get(
    "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/quotations/inquire-price",
    headers=headers, params=params
)
```

### 5.2 키움증권 OpenAPI+

| 항목 | 세부사항 |
|------|---------|
| **유형** | 증권사 OpenAPI |
| **지원 시장** | KRX (한국) |
| **인증** | COM/OCX 기반 (Windows 전용) |
| **Python SDK** | `pykiwoom` (COM 래퍼) |
| **제약** | **Windows 전용** (COM/OCX), 32bit Python 필요 |

**장점**: 한국 개인투자자 점유율 1위, 데이터 풍부
**단점**: **Windows/COM 전용** → Linux CLI 환경 부적합, 자동 트레이딩 제약 많음
**결론**: ❌ Linux 기반 CLI/Skill 환경에 **부적합**

### 5.3 LS증권 OpenAPI

| 항목 | 세부사항 |
|------|---------|
| **유형** | 증권사 OpenAPI (HTTP REST) |
| **지원 시장** | KRX, 해외 일부 |
| **인증** | App Key + Token |
| **특장점** | REST API 기반 (플랫폼 독립적) |

**장점**: REST 기반으로 Linux 호환, 비교적 새로운 API
**단점**: 커뮤니티/SDK 생태계 미성숙, 문서 품질 불안정

### 5.4 Futu/moomoo ⭐ (홍콩/중국 시장 추천)

| 항목 | 세부사항 |
|------|---------|
| **유형** | 인터넷 브로커 (글로벌) |
| **지원 시장** | 홍콩 (HKEX), 미국 (NYSE/NASDAQ), 중국 A주 (Stock Connect) |
| **인증** | OpenD Gateway + RSA Key |
| **Python SDK** | `moomoo-api` (공식) |
| **REST API Rate** | 30 req/30sec (주문), 데이터 별도 |
| **WebSocket** | ✅ OpenD 게이트웨이 경유 |
| **Paper Trading** | ✅ 모의투자 환경 |
| **수수료** | HK: HK$3/주문, US: $0.99/주문 |

**장점**:
- 홍콩 시장 접근성 최고
- Stock Connect로 중국 A주 접근
- 미국 시장도 지원 (멀티마켓)
- 우수한 Python SDK

**단점**:
- OpenD 게이트웨이 데몬 상시 실행 필요
- 중국 규제 리스크
- Rate limit 상대적으로 낮음

**코드 예시**:
```python
from moomoo import OpenQuoteContext, OpenSecTradeContext, TrdSide, TrdEnv

# 시세 조회
quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
ret, data = quote_ctx.get_market_snapshot(['HK.00700'])  # 텐센트
quote_ctx.close()

# 홍콩 주식 매수 (모의투자)
trade_ctx = OpenSecTradeContext(host='127.0.0.1', port=11111)
ret, data = trade_ctx.place_order(
    price=350.0, qty=100, code='HK.00700',
    trd_side=TrdSide.BUY, trd_env=TrdEnv.SIMULATE
)
trade_ctx.close()
```

### 5.5 Tiger Brokers (老虎证券)

| 항목 | 세부사항 |
|------|---------|
| **유형** | 인터넷 브로커 (싱가포르 기반) |
| **지원 시장** | 미국, 홍콩, 중국 A주, 싱가포르 |
| **인증** | Tiger ID + Private Key (RSA) |
| **Python SDK** | `tigeropen` (공식) |
| **Paper Trading** | ✅ 모의투자 |
| **수수료** | US: $0.01/주, HK: HK$15/주문 |

**장점**: 아시아 멀티마켓 접근, 깔끔한 SDK, Paper Trading
**단점**: 글로벌 커버리지 제한 (유럽/일본 미지원), 싱가포르 규제

### 5.6 pykrx (데이터 전용)

| 항목 | 세부사항 |
|------|---------|
| **유형** | KRX 데이터 스크래핑 (비공식) |
| **지원** | 한국 시장 데이터만 (매매 불가) |
| **비용** | 무료 |

**용도**: 한국 시장 히스토리컬 데이터 보조, 프로덕션 매매에는 KIS 사용

---

## 6. 종합 비교 매트릭스

### 6.1 매매 실행 API 비교

| API | 미국 | 한국 | 일본 | 중국 | 홍콩 | 유럽 | Paper | Rate Limit | 월비용 | CLI적합 | 총점 |
|-----|------|------|------|------|------|------|-------|-----------|--------|---------|------|
| **Alpaca** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | 200/min | $0 | ⭐⭐⭐ | 7/10 |
| **IBKR** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 50/sec | ~$10 | ⭐ | 8/10 |
| **KIS** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | 20/sec | $0 | ⭐⭐ | 7/10 |
| **Futu** | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ | 1/sec | ~$5 | ⭐⭐ | 6/10 |
| **Tiger** | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ | varies | ~$5 | ⭐⭐ | 5/10 |
| **Schwab** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 120/min | $0 | ⭐⭐ | 4/10 |
| **Tradier** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | 120/min | $0 | ⭐⭐ | 5/10 |

### 6.2 시장 데이터 API 비교

| API | 글로벌 커버리지 | 펀더멘탈 | 실시간 | WebSocket | 기술지표 | Rate Limit | 월비용 | 총점 |
|-----|---------------|---------|--------|-----------|---------|-----------|--------|------|
| **Twelve Data** | 84+ 거래소 | ✅ | ✅ | ✅ | 100+ | 120/min | $229 | 9/10 |
| **EODHD** | 60+ 거래소 | ✅ | 지연 | ❌ | ❌ | ~100K/day | $100 | 8/10 |
| **FMP** | 중간 | ⭐⭐⭐ | ✅ | ❌ | 일부 | 3000/min | $150 | 7/10 |
| **Polygon** | 미국만 | ❌ | ✅ | ✅ | ❌ | 무제한 | $199 | 6/10 |
| **Alpha Vantage** | 중간 | ✅ | 지연 | ❌ | ✅ | 75/min | $50 | 5/10 |
| **yfinance** | 넓음 | ✅ | 지연 | ❌ | ❌ | 비공식 | $0 | 4/10 |

---

## 7. 추천 아키텍처

### 7.1 아키텍처 옵션

#### Option A: "Best of Breed" (추천)

각 역할에 최적의 API를 조합하는 전략:

```
┌─────────────────────────────────────────────────────────────┐
│                    Trading System Architecture               │
│                     (Best of Breed)                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────┐           │
│  │           Market Data Layer                   │           │
│  │  ┌──────────────┐  ┌────────────────────┐    │           │
│  │  │  Twelve Data  │  │      EODHD         │    │           │
│  │  │  (실시간+글로벌)│  │  (EOD+펀더멘탈보조) │    │           │
│  │  │  $229/mo      │  │  $100/mo           │    │           │
│  │  └──────────────┘  └────────────────────┘    │           │
│  │  ┌──────────────┐                             │           │
│  │  │     FMP      │                             │           │
│  │  │ (펀더멘탈심화) │                             │           │
│  │  │  $150/mo     │                             │           │
│  │  └──────────────┘                             │           │
│  └──────────────────────────────────────────────┘           │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────┐           │
│  │           Scoring & Analysis Engine           │           │
│  │   (Claude Skills: /scoring-engine, etc.)      │           │
│  └──────────────────────────────────────────────┘           │
│                          │                                   │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────┐           │
│  │           Trading Execution Layer             │           │
│  │  ┌──────────┐  ┌────────┐  ┌──────────┐     │           │
│  │  │  Alpaca   │  │  KIS   │  │  Futu    │     │           │
│  │  │  (미국)    │  │ (한국)  │  │ (홍콩)   │     │           │
│  │  │  무료      │  │ 무료   │  │  ~$5/mo  │     │           │
│  │  └──────────┘  └────────┘  └──────────┘     │           │
│  └──────────────────────────────────────────────┘           │
│                                                              │
│  월 총비용: ~$479 + 거래 수수료                                │
└─────────────────────────────────────────────────────────────┘
```

| 역할 | 선택 | 이유 |
|------|------|------|
| **글로벌 실시간 데이터** | Twelve Data Pro | 84+ 거래소, WebSocket, 기술지표 내장 |
| **EOD + 보조 펀더멘탈** | EODHD All-In-One | 60+ 거래소, $100에 풍부한 데이터 |
| **펀더멘탈 심화** | FMP Ultimate | F-Score/Z-Score 계산용 재무제표 |
| **미국 매매** | Alpaca | 무료, 최고 DX, Paper Trading |
| **한국 매매** | KIS OpenAPI | 한국 시장 유일한 선택, 해외주식도 지원 |
| **홍콩/중국 매매** | Futu/moomoo | HK 접근성, Stock Connect |

#### Option B: "IBKR All-in-One" (단순)

IBKR 하나로 모든 시장 매매 + 보조 데이터 API:

```
┌─────────────────────────────────────────────┐
│           IBKR All-in-One Architecture       │
├─────────────────────────────────────────────┤
│  Data: Twelve Data ($229) + IBKR 내장       │
│  Trading: IBKR 단일 (160+ 시장)              │
│  월 총비용: ~$240 + IBKR 수수료               │
│                                              │
│  장점: 단일 계좌, 단일 포트폴리오 관리          │
│  단점: TWS Gateway 의존, CLI 연동 복잡        │
└─────────────────────────────────────────────┘
```

#### Option C: "Budget" (최소 비용)

```
┌─────────────────────────────────────────────┐
│           Budget Architecture                │
├─────────────────────────────────────────────┤
│  Data: EODHD ($100) + yfinance (무료 보조)   │
│  Trading: Alpaca (미국 무료)                  │
│  월 총비용: ~$100                             │
│                                              │
│  장점: 최소 비용으로 시작 가능                  │
│  단점: 실시간 데이터 부족, 미국만 매매 가능     │
└─────────────────────────────────────────────┘
```

### 7.2 추천: 단계적 확장 전략

```
Phase 1 (MVP):     Option C ($100/mo)  → 미국 시장 + EOD 데이터
Phase 2 (확장):    Option A-lite ($330/mo) → Twelve Data 추가 + KIS
Phase 3 (풀스펙):  Option A ($479/mo)  → 전체 글로벌 커버리지
```

---

## 8. .env 자격증명 관리 설계

### 8.1 .env 파일 구조

```bash
# ========================================
# Trading System Credentials
# ========================================

# --- Market Data APIs ---
TWELVE_DATA_API_KEY=your_twelve_data_key
EODHD_API_TOKEN=your_eodhd_token
FMP_API_KEY=your_fmp_key

# --- US Broker: Alpaca ---
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # paper 또는 live
ALPACA_PAPER=true

# --- Korea Broker: KIS ---
KIS_APP_KEY=your_kis_app_key
KIS_APP_SECRET=your_kis_app_secret
KIS_ACCOUNT_NO=your_account_number
KIS_ACCOUNT_PRODUCT=01
KIS_BASE_URL=https://openapivts.koreainvestment.com:29443  # 모의투자
# KIS_BASE_URL=https://openapi.koreainvestment.com:9443     # 실전

# --- HK/CN Broker: Futu/moomoo ---
FUTU_HOST=127.0.0.1
FUTU_PORT=11111
FUTU_RSA_KEY_PATH=~/.futu/rsa_private_key.pem
FUTU_TRD_ENV=SIMULATE  # SIMULATE 또는 REAL

# --- IBKR (Alternative) ---
IBKR_HOST=127.0.0.1
IBKR_PORT=7497          # 7497=paper, 7496=live
IBKR_CLIENT_ID=1

# --- System Settings ---
TRADING_MODE=paper       # paper | live
LOG_LEVEL=INFO
MAX_POSITION_SIZE=0.05   # 포트폴리오 대비 최대 5%
MAX_DAILY_LOSS=0.02      # 일일 최대 손실 2%
```

### 8.2 자격증명 관리 규칙

```python
# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 로딩 우선순위
# 1. .env.local (개인 설정, gitignore)
# 2. .env (기본 설정)
env_local = Path(__file__).parent / '.env.local'
env_default = Path(__file__).parent / '.env'

if env_local.exists():
    load_dotenv(env_local)
else:
    load_dotenv(env_default)

class Config:
    # Trading mode safety check
    TRADING_MODE = os.getenv('TRADING_MODE', 'paper')

    @classmethod
    def is_live(cls) -> bool:
        return cls.TRADING_MODE == 'live'

    @classmethod
    def require_confirmation(cls) -> bool:
        """실전 모드에서는 주문 전 확인 필요"""
        return cls.is_live()
```

### 8.3 보안 규칙

```
.gitignore에 반드시 포함:
  .env
  .env.local
  .env.production
  *.pem
  *_private_key*

추가 보안:
  - .env.example 파일로 필요한 키 목록 문서화 (값은 비움)
  - 실전 모드 전환 시 이중 확인 메커니즘
  - API 키 로테이션 주기 설정 (90일)
  - 토큰 자동 갱신 로직 (KIS 24h 토큰 등)
```

---

## 9. API Quota 분석

### 9.1 트레이딩 시스템의 예상 API 사용량

우리 시스템은 **스윙/포지션 트레이딩** (단타 아님) 기반이므로:

| 기능 | 호출 빈도 | 일일 예상 호출수 | 비고 |
|------|----------|----------------|------|
| 일봉 데이터 갱신 | 1회/일 | ~500 | 글로벌 유니버스 500종목 |
| 펀더멘탈 갱신 | 분기 1회 | ~15/일 평균 | 재무제표 발표 시즌 집중 |
| 기술적 지표 계산 | 1회/일 | ~1,500 | 종목당 3개 지표 |
| 스코어링 갱신 | 1회/일 | ~500 | 복합점수 계산 |
| 포트폴리오 조회 | 수시 | ~50 | 잔고/포지션 확인 |
| 주문 실행 | 수시 | ~10-30 | 스윙 트레이딩 (빈도 낮음) |
| 시세 모니터링 | 30분 간격 | ~800 | 보유 종목 50개 × 16시간 |
| **일일 총 예상** | | **~3,400** | |

### 9.2 API별 Quota 충분성

| API | 할당량 (선택 플랜) | 일일 필요량 | 여유율 | 판정 |
|-----|-------------------|-----------|--------|------|
| **Twelve Data** Pro | 무제한 (120/min) | ~2,000 | 충분 | ✅ |
| **EODHD** All-In-One | 100,000/day | ~500 | 200x 여유 | ✅✅ |
| **FMP** Ultimate | 3,000/min → ~4.3M/day | ~500 | 8,600x 여유 | ✅✅✅ |
| **Alpaca** Free | 200/min → ~288K/day | ~50 | 5,760x 여유 | ✅✅✅ |
| **KIS** | 20/sec → ~1.7M/day | ~100 | 17,000x 여유 | ✅✅✅ |

> **결론**: 스윙/포지션 트레이딩 시스템에서는 모든 추천 API의 Quota가 **넉넉히 충분**

---

## 10. CLI 도구 & Claude Skill 통합 설계

### 10.1 CLI 도구 구조

```
trading-cli/
├── cli.py                    # 메인 CLI 엔트리포인트 (Click/Typer)
├── config.py                 # .env 로딩, Config 클래스
├── clients/
│   ├── __init__.py
│   ├── alpaca_client.py      # Alpaca 래퍼
│   ├── kis_client.py         # KIS 래퍼
│   ├── futu_client.py        # Futu 래퍼
│   ├── twelve_data_client.py # Twelve Data 래퍼
│   ├── eodhd_client.py       # EODHD 래퍼
│   └── fmp_client.py         # FMP 래퍼
├── commands/
│   ├── data.py               # 데이터 조회 명령어
│   ├── trade.py              # 매매 실행 명령어
│   ├── portfolio.py          # 포트폴리오 조회
│   ├── score.py              # 스코어링 실행
│   └── screen.py             # 종목 스크리닝
├── models/
│   ├── order.py              # 주문 모델
│   ├── position.py           # 포지션 모델
│   └── quote.py              # 시세 모델
└── utils/
    ├── formatting.py         # 출력 포매팅
    └── safety.py             # 안전 장치 (확인, 리밋)
```

### 10.2 CLI 명령어 설계

```bash
# === 데이터 조회 ===
trading data price AAPL                    # 현재가
trading data price 005930.KRX              # 삼성전자
trading data history AAPL --days 252       # 1년 일봉
trading data fundamentals AAPL             # 재무제표
trading data indicators AAPL --type rsi,macd  # 기술적 지표

# === 스코어링 ===
trading score fscore AAPL                  # Piotroski F-Score
trading score zscore AAPL                  # Altman Z-Score
trading score composite AAPL              # 복합 점수
trading score screen --min-fscore 7 --market US  # 스크리닝

# === 매매 실행 ===
trading buy AAPL --qty 10 --type market    # 시장가 매수
trading buy AAPL --amount 5000             # 금액 기준 매수
trading sell AAPL --qty 5 --type limit --price 200
trading order status ORDER_ID              # 주문 상태

# === 포트폴리오 ===
trading portfolio show                     # 전체 포지션
trading portfolio pnl                      # 수익률
trading portfolio risk                     # 리스크 메트릭스
trading portfolio rebalance --strategy dual-momentum

# === 시장 ===
trading market status                      # 개장/폐장 상태
trading market movers --market US --type gainers
```

### 10.3 Claude Skill 매핑

기존 `docs/skill-conversion-plan.md`의 9개 스킬과 통합:

```yaml
# .claude/skills/market-data/SKILL.md
---
name: market-data
description: 글로벌 시장 데이터 조회 및 분석
arguments:
  - name: symbol
    description: 종목 심볼 (예: AAPL, 005930.KRX, 7203.T)
  - name: data_type
    description: "price | history | fundamentals | indicators"
  - name: exchange
    description: "US | KRX | TSE | HKEX | SSE | Euronext"
---

## 실행 흐름
1. symbol에서 거래소 자동 감지
2. 적절한 데이터 API 클라이언트 선택
3. 데이터 조회 및 정규화된 JSON 반환
```

```yaml
# .claude/skills/trade-execute/SKILL.md
---
name: trade-execute
description: 주문 실행 (매수/매도)
arguments:
  - name: action
    description: "buy | sell"
  - name: symbol
    description: 종목 심볼
  - name: quantity
    description: 수량 또는 금액
  - name: order_type
    description: "market | limit | stop"
  - name: price
    description: 지정가 (limit/stop 주문 시)
---

## 안전 장치
1. TRADING_MODE 확인 (paper/live)
2. MAX_POSITION_SIZE 검증
3. MAX_DAILY_LOSS 검증
4. live 모드 시 사용자 확인 요청
5. 주문 실행 및 결과 반환
```

```yaml
# .claude/skills/scoring-engine/SKILL.md
---
name: scoring-engine
description: 정량적 스코어링 엔진 (F-Score, Z-Score, 복합점수)
arguments:
  - name: symbol
    description: 종목 심볼
  - name: score_type
    description: "fscore | zscore | mscore | gscore | composite"
---

## Team Agent 활용
- Signal Agent (haiku): 기술적 지표 계산
- Fundamental Agent (sonnet): F-Score/Z-Score 계산
- Sentiment Agent (haiku): 뉴스 센티먼트 분석
- 결과 종합 → 복합 점수 산출
```

### 10.4 Team Agent 통합

```
┌─────────────────────────────────────────────────────┐
│            Claude Skill: /analyze-trade              │
│                                                      │
│  User: /analyze-trade AAPL                           │
│                                                      │
│  ┌─────────────────────────────────────────┐        │
│  │     Orchestrator Agent (sonnet)          │        │
│  │     - 분석 계획 수립                      │        │
│  │     - 팀 에이전트 디스패치                  │        │
│  └──────────┬──────────────────────────────┘        │
│             │                                        │
│    ┌────────┼────────┬──────────┐                    │
│    ▼        ▼        ▼          ▼                    │
│  ┌─────┐ ┌─────┐ ┌─────┐  ┌─────────┐              │
│  │Data │ │Score│ │Tech │  │Sentiment│              │
│  │Agent│ │Agent│ │Agent│  │Agent    │              │
│  │haiku│ │snnt │ │haiku│  │haiku    │              │
│  └──┬──┘ └──┬──┘ └──┬──┘  └────┬────┘              │
│     │       │       │          │                     │
│     ▼       ▼       ▼          ▼                     │
│  ┌──────────────────────────────────────┐           │
│  │       Result Aggregator (sonnet)      │           │
│  │  - 종합 분석 리포트 생성                 │           │
│  │  - 매수/매도/보유 추천                   │           │
│  │  - 리스크 평가                          │           │
│  └──────────────────────────────────────┘           │
└─────────────────────────────────────────────────────┘
```

---

## 11. 비용 분석

### 11.1 Phase별 월간 비용

#### Phase 1: MVP (미국 시장만)

| 항목 | 비용/월 |
|------|--------|
| EODHD All-In-One | $99.99 |
| Alpaca (무료) | $0 |
| yfinance (보조, 무료) | $0 |
| **합계** | **~$100** |

#### Phase 2: 확장 (미국 + 한국 + 글로벌 데이터)

| 항목 | 비용/월 |
|------|--------|
| Twelve Data Pro | $229 |
| EODHD All-In-One | $99.99 |
| Alpaca (무료) | $0 |
| KIS (무료) | $0 |
| **합계** | **~$330** |

#### Phase 3: 풀스펙 (5대 시장 전체)

| 항목 | 비용/월 |
|------|--------|
| Twelve Data Pro | $229 |
| EODHD All-In-One | $99.99 |
| FMP Ultimate | $149.99 |
| Alpaca (무료) | $0 |
| KIS (무료) | $0 |
| Futu (최소) | ~$5 |
| **합계** | **~$484** |

### 11.2 연간 비용 비교

| Phase | 월간 | 연간 | 커버리지 |
|-------|------|------|---------|
| MVP | $100 | $1,200 | 미국 (EOD) |
| 확장 | $330 | $3,960 | 미국+한국+글로벌 실시간 |
| 풀스펙 | $484 | $5,808 | 글로벌 5대 시장 + 심화 펀더멘탈 |

> **참고**: Claude API 비용은 별도 (스킬 실행 시 Opus/Sonnet/Haiku 사용량에 따라)

---

## 12. 리스크 및 제약사항

### 12.1 기술적 리스크

| 리스크 | 심각도 | 대응 |
|--------|--------|------|
| API 장애/다운타임 | 높음 | 폴백 데이터 소스, 캐싱 레이어 |
| Rate Limit 초과 | 중간 | 요청 큐잉, 지수 백오프, 로컬 캐시 |
| WebSocket 연결 끊김 | 중간 | 자동 재연결, heartbeat 모니터링 |
| 토큰 만료 (KIS 24h) | 낮음 | 자동 갱신 스케줄러 |
| 데이터 불일치 | 중간 | 크로스 체크 (2+ 소스 비교) |

### 12.2 규제 및 법률 리스크

| 리스크 | 심각도 | 대응 |
|--------|--------|------|
| 한국 계좌 해외 접근 제한 | 높음 | VPN/프록시 사용 시 약관 위반 가능성 확인 |
| 미국 패턴 데이 트레이딩 규칙 | 중간 | 스윙 전략으로 회피 (5일 이내 3회 이하) |
| 중국 A주 접근 제한 | 높음 | Stock Connect 경유만 가능 |
| 데이터 재배포 제한 | 낮음 | 개인용도 내 사용 |

### 12.3 아키텍처 제약

| 제약 | 영향 | 해결 |
|------|------|------|
| IBKR TWS Gateway 필요 | 서버리스 환경 불가 | 상시 서버 또는 Docker 컨테이너 |
| Futu OpenD 게이트웨이 | 로컬 데몬 필요 | Docker 컨테이너화 |
| 키움 Windows 전용 | Linux 환경 불가 | ❌ 사용 불가 → KIS 대체 |
| 거래소 시간대 차이 | 스케줄링 복잡 | UTC 기반 통합 스케줄러 |

---

## 13. 구현 로드맵

### Phase 1: MVP (2-3주)

```
Week 1:
  ☐ 프로젝트 구조 생성 (trading-cli/)
  ☐ .env 관리 및 Config 클래스
  ☐ EODHD 클라이언트 구현 (EOD + 펀더멘탈)
  ☐ Alpaca 클라이언트 구현 (Paper Trading)

Week 2:
  ☐ CLI 기본 명령어 (data, trade, portfolio)
  ☐ F-Score / Z-Score 계산 로직
  ☐ 기본 안전 장치 (paper/live 구분, 확인 프롬프트)

Week 3:
  ☐ Claude Skill 3개 생성 (/market-data, /trade-execute, /scoring-engine)
  ☐ 통합 테스트 (Paper Trading 검증)
  ☐ 문서화
```

### Phase 2: 확장 (3-4주)

```
Week 4-5:
  ☐ Twelve Data 클라이언트 (실시간 + WebSocket)
  ☐ KIS 클라이언트 (한국 시장)
  ☐ 글로벌 심볼 해석기 (AAPL, 005930.KRX, 7203.T)

Week 6-7:
  ☐ 복합 스코어링 엔진 (3축 통합)
  ☐ Team Agent 구현 (Signal, Score, Sentiment)
  ☐ /analyze-trade 통합 스킬
  ☐ 스크리닝 명령어
```

### Phase 3: 풀스펙 (4-5주)

```
Week 8-9:
  ☐ FMP 클라이언트 (심화 펀더멘탈)
  ☐ Futu 클라이언트 (홍콩/중국)
  ☐ 멀티마켓 포트폴리오 통합 뷰

Week 10-11:
  ☐ Dual Momentum / CAN SLIM 전략 인코딩
  ☐ 리스크 관리 시스템 (Kelly, 드로다운 방어)
  ☐ 자기개선 피드백 루프 (Walk-Forward)

Week 12:
  ☐ 전체 스킬 체인 통합 테스트
  ☐ 성능 최적화 및 캐싱
  ☐ 프로덕션 배포 준비
```

---

## 부록 A: API 가입 안내 (Quick Start)

### Alpaca (미국 매매)
1. https://alpaca.markets → Sign Up
2. Paper Trading API Keys 생성
3. `.env`에 `ALPACA_API_KEY`, `ALPACA_SECRET_KEY` 설정

### Twelve Data (글로벌 데이터)
1. https://twelvedata.com → Sign Up
2. API Key 생성
3. `.env`에 `TWELVE_DATA_API_KEY` 설정

### EODHD (EOD 데이터)
1. https://eodhd.com → Register
2. All-In-One 플랜 구독
3. `.env`에 `EODHD_API_TOKEN` 설정

### KIS (한국 매매)
1. 한국투자증권 계좌 개설
2. https://apiportal.koreainvestment.com → API 신청
3. App Key/Secret 발급
4. `.env`에 `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_ACCOUNT_NO` 설정

### FMP (펀더멘탈)
1. https://financialmodelingprep.com → Sign Up
2. Ultimate 플랜 구독
3. `.env`에 `FMP_API_KEY` 설정

### Futu/moomoo (홍콩 매매)
1. https://www.futunn.com → 계좌 개설
2. OpenD 게이트웨이 설치
3. RSA 키 쌍 생성
4. `.env`에 `FUTU_HOST`, `FUTU_PORT`, `FUTU_RSA_KEY_PATH` 설정

---

## 부록 B: 결정 포인트 (사용자 검토 필요)

아래 항목은 구현 전 결정이 필요합니다:

### 1. 아키텍처 선택
- [ ] **Option A**: Best of Breed (~$484/mo) — 최적 성능, 높은 비용
- [ ] **Option B**: IBKR All-in-One (~$240/mo) — 단순, TWS 의존
- [ ] **Option C**: Budget (~$100/mo) — 최소 비용, 미국만

### 2. 데이터 API 우선순위
- [ ] Twelve Data (글로벌 실시간) vs EODHD (가성비 EOD)
- [ ] FMP 추가 여부 (펀더멘탈 심화)

### 3. 글로벌 매매 범위
- [ ] 미국만 (Phase 1에 집중)
- [ ] 미국 + 한국 (KIS 추가)
- [ ] 미국 + 한국 + 홍콩/중국 (Futu 추가)
- [ ] 전체 5대 시장 (IBKR 또는 조합)

### 4. 일본/유럽 시장 접근 방식
- [ ] IBKR 경유 (가장 확실)
- [ ] Twelve Data (데이터만) + 현지 브로커
- [ ] Phase 3로 후순위

### 5. Paper Trading 기간
- [ ] 2주
- [ ] 1개월 (권장)
- [ ] 3개월 (보수적)

### 6. CLI 프레임워크
- [ ] Click (안정적, 성숙)
- [ ] Typer (모던, Click 기반, 타입 힌트)
- [ ] argparse (기본, 의존성 없음)
