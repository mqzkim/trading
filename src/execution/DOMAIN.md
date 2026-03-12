# Execution

## 책임
주문 생성, 브래킷 오더 실행, 거래 계획 관리를 담당하는 바운디드 컨텍스트.
스코어링/밸류에이션 결과를 받아 리스크 체크 후 trade plan을 생성하고,
Alpaca API를 통해 bracket order를 제출한다.

## 핵심 엔티티
- TradePlan: 진입/손절/목표가/수량/근거를 담은 VO
- BracketSpec: Alpaca bracket order 파라미터 VO
- OrderResult: 주문 실행 결과 VO
- TradePlanStatus: 거래 계획 생명주기 상태 (PENDING -> APPROVED -> EXECUTED)

## 외부 의존성
- portfolio 컨텍스트: TakeProfitLevels VO (이벤트가 아닌 공유 VO 참조)
- personal/execution/planner: plan_entry() 함수 위임 (리스크 체크 + 포지션 사이징)
- Alpaca API: alpaca-py SDK를 통한 주문 제출 (infrastructure 레이어)

## 주요 유스케이스
1. Trade plan 생성: 스코어링 데이터 + 리스크 파라미터 -> TradePlanService.generate_plan()
2. Bracket order 제출: BracketSpec -> AlpacaExecutionAdapter.submit_bracket_order()
3. Trade plan 상태 관리: SQLite 기반 persist + 상태 전이
4. CLI 승인 워크플로: PENDING -> (사용자 승인) -> APPROVED -> EXECUTED

## 변경 불가 규칙
- plan_entry()의 리스크 수학 재작성 금지 -- adapter pattern으로 위임만
- Mock 모드 항상 지원 (자격증명 없이도 작동)
- domain/ 레이어에서 alpaca-py 직접 import 금지
