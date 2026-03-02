---
name: performance-analyst
description: "4단계 성과 어트리뷰션을 수행합니다. 포트폴리오/전략/거래/스킬 레벨의 성과를 Team Agent 4개로 병렬 분석합니다. Layer 8. 개인 전용."
argument-hint: "[--period N] [--level all|portfolio|strategy|trade|skill]"
user-invocable: true
allowed-tools: "Read, Bash, Agent"
---

# Performance Analyst Skill (Layer 8)

> 4단계 성과 어트리뷰션 코디네이터. 다각적 성과 분석으로 개선 포인트를 식별합니다.
> **개인 전용** — 투자 자문 영역으로 상업 제품에서 제외.

## 역할

4개 Team Agent를 병렬 실행하여 포트폴리오/전략/거래/스킬 레벨의
성과를 종합 분석합니다.

## Team Agent 설계

| Agent | 분석 레벨 | 모델 | 핵심 지표 |
|-------|---------|------|---------|
| Portfolio Attribution | 포트폴리오 | haiku | Sharpe, Sortino, Calmar, MDD |
| Strategy Attribution | 전략별 | haiku | 전략별 Sharpe, 승률, 상관 |
| Trade Attribution | 거래별 | haiku | P&L, 슬리피지, 보유기간 |
| Skill Attribution | 스킬별 | sonnet | IC, Kelly 효율, 레짐 정확도 |

## Portfolio Attribution Agent

```
핵심 지표:
  - Sharpe Ratio (연율화)
  - Sortino Ratio (하방 리스크 조정)
  - Calmar Ratio (MDD 대비 수익)
  - Maximum Drawdown
  - 팩터 어트리뷰션 (시장, 가치, 모멘텀, 크기, 품질)
```

## Strategy Attribution Agent

```
전략별 분석:
  - 전략별 Sharpe Ratio
  - 전략별 승률
  - 전략 간 상관관계 (0.7 초과 시 경고)
  - 전략별 MDD
  - 레짐별 전략 성과
```

## Trade Attribution Agent

```
거래별 분석:
  - 거래별 P&L (실현/미실현)
  - 슬리피지 (예상 vs 실제)
  - 보유기간 분포
  - 진입/청산 타이밍 평가
  - 최대 승리/최대 손실 거래
```

## Skill Attribution Agent

```
스킬별 진단:
  - 레짐 정확도 (55% 이상 목표)
  - Information Coefficient (0.03 이상 목표)
  - Kelly 효율 (70% 이상 목표)
  - 리스크 관리 효과 (낙폭 방어 성공률)
  - 각 스킬의 기여도
```

## 출력 포맷

```json
{
  "skill": "performance-analyst",
  "status": "success",
  "data": {
    "period": "2025-01-01 to 2026-03-01",
    "portfolio": {
      "sharpe": 1.45,
      "sortino": 1.82,
      "calmar": 2.10,
      "mdd": -0.12,
      "total_return": 0.28,
      "factor_attribution": {}
    },
    "strategy": {
      "canslim": { "sharpe": 1.2, "win_rate": 0.62 },
      "magic_formula": { "sharpe": 0.9, "win_rate": 0.58 },
      "dual_momentum": { "sharpe": 1.5, "win_rate": 0.55 },
      "trend_following": { "sharpe": 1.1, "win_rate": 0.48 }
    },
    "skill_diagnostics": {
      "regime_accuracy": 0.68,
      "signal_ic": 0.045,
      "kelly_efficiency": 0.75,
      "risk_management_score": 0.82
    },
    "flags": [],
    "recommendations": []
  }
}
```

## 참조 문서

- `docs/skill_chaining_and_self_improvement_research.md` §8 — 성과 분석 프레임워크
