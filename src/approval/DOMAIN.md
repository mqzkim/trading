# Approval

## 책임
자동 파이프라인과 주문 실행 사이의 게이팅 레이어. 사용자가 사전 정의한 전략 파라미터(스코어 임계값, 허용 레짐, 최대 거래 비율, 만료일)와 일일 예산 한도 내에서만 자동 실행을 허용한다. 범위를 벗어나는 거래는 수동 리뷰 대기열로 전환한다.

## 핵심 엔티티
- StrategyApproval: 전략 승인 엔티티. 스코어 임계값, 허용 레짐, 최대 거래 비율, 만료일, 일일 예산 한도를 포함. 복수 정지 사유(suspended_reasons)를 독립적으로 추적.

## 값 객체
- GateResult: 승인 체크 결과 (approved + reason)
- DailyBudgetTracker: 일별 자본 사용 추적 (budget_cap, spent, remaining)
- TradeReviewItem: 거부된 거래의 수동 리뷰 대기 항목
- ApprovalStatus: 승인 상태 열거형 (ACTIVE, SUSPENDED, EXPIRED, REVOKED)

## 외부 의존성
- regime 컨텍스트: RegimeChangedEvent 구독으로 승인 자동 정지 (이벤트 통신만)
- pipeline 컨텍스트: PipelineOrchestrator가 ApprovalGateService.check() 호출

## 주요 유스케이스
1. 전략 승인 생성: 사용자가 거래 파라미터와 예산 한도를 설정
2. 거래 게이트 체크: 파이프라인이 각 거래 계획을 승인 조건과 대조 검증
3. 일일 예산 추적: 거래 제출 시 예산 차감, 일별 리셋
4. 수동 리뷰: 거부된 거래를 리뷰 큐에 추가, approve/reject 처리
5. 자동 정지: 레짐 변경 또는 드로다운 발생 시 승인 자동 정지

## 변경 불가 규칙
- 단일 활성 승인 규칙: 동시에 하나의 활성 승인만 존재 (새 승인 생성 시 이전 승인 비활성화)
- 만료된 승인으로 거래 실행 금지
- suspended_reasons가 하나라도 남아있으면 is_effective = False
- 일일 예산은 UTC 자정 기준 리셋, 이월 없음
