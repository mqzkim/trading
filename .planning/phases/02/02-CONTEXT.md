# Phase 2: Analysis Core - Context

**Gathered:** 2026-03-12
**Status:** Ready for planning

<domain>
## Phase Boundary

사용자가 미국 주식에 대해 기본적 품질 스코어(G-Score 포함)를 산출하고, 앙상블 밸류에이션(DCF/EPV/Relative)으로 내재가치를 추정할 수 있게 한다. 시그널 생성, 리스크 관리, 실행은 다른 페이즈에서 다룬다.

</domain>

<decisions>
## Implementation Decisions

### DCF 모델 파라미터
- 할인율: 하이브리드 방식 — WACC 자동 계산(CAPM 기반)하되, 이상치 범위(6-14%) 벗어나면 섹터 평균으로 클리핑
- 성장률: 2-stage 모델 — Stage 1: 과거 실적 기반(매출/FCF) 5년, Stage 2: GDP 성장률(2-3%)로 수렴
- Terminal Value: Gordon Growth Model + Exit Multiple 둘 다 계산 후 평균
- Terminal Value cap: 총 가치의 40% 초과 불가 (요구사항 VALU-01)
- DCF 이상치 처리: 결과값은 그대로 유지하되, confidence score를 하향 조정하여 앙상블에서 가중치가 자연스럽게 줄어들게 함

### 앙상블 밸류에이션 신뢰도
- Confidence score: 복합 방식 — 모델 합의도(CV 기반) + 데이터 완전성(입력 데이터 충족률) 두 축 반영
- Margin of Safety: 섹터별 차등 적용 — 변동성 높은 섹터(Tech 등)는 높은 MoS(예: 25%), 안정적 섹터(Consumer Staples 등)는 낮은 MoS(예: 15%). 기본 threshold 20%는 중간값
- Relative Multiples 비교 기준: GICS 섹터 내 비교 (Phase 1에서 이미 GICS 11섹터 분류 존재)
- 사용 배수: PER, PBR, EV/EBITDA (요구사항 VALU-03)
- 앙상블 가중치: DCF 40% + EPV 35% + Relative 25% (요구사항 VALU-04, 고정)

### G-Score + Composite 통합
- G-Score 적용 범위: 성장주에만 적용 — Mohanram 원론의 디자인 의도에 부합
- 성장주/가치주 구분: PBR > 3 = 성장주 (Mohanram 논문 기준)
- Composite Score에 G-Score 반영: 성장주인 경우 fundamental 점수 산출 시 G-Score 가중 포함
- Regime 조정 가중치: Phase 3에서 regime 감지와 함께 구현하되, 인터페이스는 준비

### Claude's Discretion
- EPV 정상화 수익력 계산 방법 (데이터 가용성과 학술 연구 기반으로 최적 방법 선택)
- G-Score를 기존 FundamentalScore VO에 통합하는 방식 (필드 추가 vs 별도 VO)
- Regime 조정 가중치의 Phase 2 내 구현 범위 (인터페이스만 vs 기본 감지 포함)

</decisions>

<specifics>
## Specific Ideas

- Terminal Value는 단일 모델 의존 위험을 줄이기 위해 Gordon + Exit Multiple 양쪽 계산 후 평균
- DCF 이상치가 나와도 결과를 버리지 않고, confidence 하향으로 자연스럽게 앙상블에서 비중 감소
- Margin of Safety를 섹터 특성에 맞게 차등 적용하여 변동성 높은 종목에 더 보수적으로 접근

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/scoring/domain/value_objects.py`: FundamentalScore(f_score, z_score, m_score), SafetyGate, CompositeScore VO — G-Score 통합 대상
- `src/scoring/domain/services.py`: CompositeScoringService, SafetyFilterService — 복합 점수 산출 로직
- `src/scoring/infrastructure/core_scoring_adapter.py`: CoreScoringAdapter — core/scoring/ 함수 래핑 패턴 (동일 패턴으로 G-Score, 밸류에이션 어댑터 구축)
- `src/data_ingest/infrastructure/edgartools_client.py`: SEC 재무제표 데이터 접근 (DCF/EPV 입력 데이터)
- `src/data_ingest/infrastructure/duckdb_store.py`: DuckDB 분석 스토어 (밸류에이션 결과 저장)
- `src/data_ingest/infrastructure/universe_provider.py`: S&P 500+400 유니버스 + GICS 섹터 분류

### Established Patterns
- CoreScoringAdapter 패턴: core/ 함수 래핑, 수학 재작성 금지
- Domain VOs: frozen dataclass + _validate(), ValueObject 상속
- DDD 레이어: domain(순수) → application(유스케이스) → infrastructure(구현)
- 이벤트 통신: AsyncEventBus, DomainEvent kw_only=True

### Integration Points
- FundamentalScore VO에 G-Score 필드 추가 또는 확장
- CoreScoringAdapter에 G-Score 계산 메서드 추가
- 새 valuation 바운디드 컨텍스트 생성 (src/valuation/)
- DuckDB에 밸류에이션 결과 테이블 추가
- Pipeline에서 scoring → valuation 데이터 흐름 연결

</code_context>

<deferred>
## Deferred Ideas

None — 논의가 페이즈 범위 내에서 유지됨

</deferred>

---

*Phase: 02-analysis-core*
*Context gathered: 2026-03-12*
