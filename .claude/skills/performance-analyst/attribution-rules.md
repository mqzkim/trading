# 성과 어트리뷰션 KPI 정의

## 포트폴리오 레벨

| 지표 | 공식 | 목표 |
|------|------|------|
| Sharpe Ratio | (Return - Rf) / σ | > 1.0 |
| Sortino Ratio | (Return - Rf) / σ_downside | > 1.5 |
| Calmar Ratio | CAGR / MDD | > 2.0 |
| Maximum Drawdown | 최대 낙폭 | < 15% |
| Win Rate | 승리 거래 / 전체 거래 | > 50% |
| Profit Factor | 총이익 / 총손실 | > 1.5 |

## 전략 레벨

각 전략(CAN SLIM, Magic Formula, Dual Momentum, Trend Following)별:
- 개별 Sharpe Ratio
- 개별 승률
- 전략 간 상관계수 (< 0.7 목표)
- 레짐별 성과 분해

## 거래 레벨

| 지표 | 설명 |
|------|------|
| P&L | 실현 + 미실현 손익 |
| 슬리피지 | (실제 체결가 - 목표가) / 목표가 |
| 보유기간 | 진입~청산 일수 |
| MAE | Maximum Adverse Excursion (최대 역방향 이탈) |
| MFE | Maximum Favorable Excursion (최대 순방향 이탈) |

## 스킬 레벨

| 지표 | 공식 | 목표 |
|------|------|------|
| 레짐 정확도 | 실제 레짐 == 예측 레짐 비율 | > 55% |
| Information Coefficient | corr(예측, 실제 수익) | > 0.03 |
| Kelly 효율 | 실제 사이즈 vs 최적 사이즈 편차 | > 70% |
| 리스크 관리 효과 | 실제 MDD vs 목표 MDD | < 100% |
