---
name: self-improver
description: "성과 분석 결과를 기반으로 시스템 파라미터 개선을 제안합니다. Walk-Forward 결과와 스킬별 진단을 분석하여 구체적 조정안을 도출합니다. Layer 9. 개인 전용."
argument-hint: "[--performance-report path]"
user-invocable: true
allowed-tools: "Read, Bash"
---

# Self Improver Skill (Layer 9)

> 파라미터 최적화 및 시스템 개선 전문가. 성과 피드백을 기반으로 개선안을 제안합니다.
> **개인 전용** — 투자 자문 영역으로 상업 제품에서 제외.

## 역할

performance-analyst의 출력(4레벨 어트리뷰션)을 분석하여
시스템 파라미터 조정, 전략 교체, 리스크 규칙 변경 등 구체적 개선안을 도출합니다.

## 절대 규칙

**라이브 파라미터를 자동으로 수정하지 않습니다.**
항상 제안만 하고, 사용자 승인 후 적용합니다.

## 진단 → 처방 매핑

| 진단 | 임계값 | 처방 |
|------|--------|------|
| 레짐 정확도 낮음 | < 55% | HMM 재학습, 피처 추가 제안 |
| 시그널 IC 낮음 | < 0.03 | Walk-Forward 재최적화, 피처 중요도 드리프트 체크 |
| Kelly 효율 낮음 | < 70% | Kelly 파라미터 재보정, 변동성 추정 검토 |
| 전략 상관관계 높음 | > 0.7 | 전략 교체/추가 필요 |
| MDD 과대 | > 15% | 스탑 타이트닝, 레짐 필터 강화 |
| WFE 미달 | < 50% | 오버피팅 의심, 파라미터 수 축소 |

## 개선 주기

| 시간축 | 주기 | 범위 |
|--------|------|------|
| 스윙 트레이딩 | 월간 | 시그널 가중치, 스탑 파라미터 |
| 포지션 트레이딩 | 분기 | 전략 구성, 레짐 모델, 리스크 한도 |

## 출력 포맷

```json
{
  "skill": "self-improver",
  "status": "success",
  "data": {
    "diagnostics": {
      "regime_accuracy": { "value": 0.52, "threshold": 0.55, "status": "BELOW" },
      "signal_ic": { "value": 0.025, "threshold": 0.03, "status": "BELOW" },
      "kelly_efficiency": { "value": 0.75, "threshold": 0.70, "status": "OK" },
      "strategy_correlation_max": { "value": 0.65, "threshold": 0.70, "status": "OK" },
      "mdd": { "value": -0.12, "threshold": -0.15, "status": "OK" },
      "wfe": { "value": 0.58, "threshold": 0.50, "status": "OK" }
    },
    "flags": ["regime_accuracy_low", "signal_ic_low"],
    "recommended_actions": [
      {
        "action": "retrain_hmm_model",
        "priority": "high",
        "description": "레짐 정확도 52%로 임계값 미달. HMM 재학습 권고.",
        "expected_impact": "레짐 정확도 5-10% 개선"
      },
      {
        "action": "walk_forward_reoptimize_signals",
        "priority": "medium",
        "description": "시그널 IC 0.025로 임계값 미달. 피처 중요도 드리프트 체크.",
        "expected_impact": "시그널 품질 개선"
      }
    ],
    "next_review_date": "2026-04-01"
  }
}
```

## 참조 문서

- `docs/skill_chaining_and_self_improvement_research.md` §4-§5 — 자기 개선 루프
