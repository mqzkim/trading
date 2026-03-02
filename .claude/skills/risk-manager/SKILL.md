---
name: risk-manager
description: "다중 레벨 리스크 검증을 수행합니다. Risk Auditor와 Bias Checker 에이전트가 병렬로 리스크를 점검합니다. Layer 6. 개인 전용."
argument-hint: "[--portfolio path] [--proposed-trade JSON]"
user-invocable: true
allowed-tools: "Read, Bash, Agent"
---

# Risk Manager Skill (Layer 6)

> 다중 레벨 리스크 검증 코디네이터. 거래와 포트폴리오 리스크를 체계적으로 점검합니다.
> **개인 전용** — 투자 자문 영역으로 상업 제품에서 제외.

## 역할

Risk Auditor와 Bias Checker 2개 Team Agent를 병렬 실행하여
거래 레벨 + 포트폴리오 레벨 리스크를 종합 검증합니다.

## Team Agent 병렬 실행

### Risk Auditor Agent (sonnet)

```
거래 레벨 점검:
  [ ] ATR 스탑로스 설정 완료? (2.5-3.5x ATR)
  [ ] 리스크/거래 <= 1%?

포트폴리오 레벨 점검:
  [ ] 단일 종목 비중 <= 8%?
  [ ] 섹터 집중도 <= 25%?
  [ ] 상관 클러스터 <= 20%?
  [ ] 현재 낙폭 상태 확인
```

### Bias Checker Agent (haiku)

```
행동재무학 편향 점검:
  [ ] 손실 회피: 손실 종목 이유 없이 보유?
  [ ] 처분 효과: 이익 종목 너무 일찍 매도?
  [ ] 과신: Kelly 한도 초과?
  [ ] 확증 편향: 특정 팩터만 강조?
  [ ] 앵커링: 매수가 기준 의사결정?
  [ ] 최근 편향: 최근 성과에 과도 반응?
```

## 낙폭 방어 3단계

| Level | 낙폭 | 조치 |
|-------|------|------|
| 0 Normal | < 10% | 정상 운영 |
| 1 Warning | 10-15% | 신규 진입 중단, 모니터링 강화 |
| 2 Defensive | 15-20% | 포지션 50% 축소, 방어적 전환 |
| 3 Emergency | > 20% | **전량 청산**, 최소 1개월 냉각기 후 25%씩 점진 재진입 |

## 리스크 한도 요약

| 항목 | 한도 |
|------|------|
| 단일 종목 | 최대 8% |
| 섹터 | 최대 25% |
| 거래당 리스크 | 자본의 1% |
| ATR 스탑 | 2.5-3.5x ATR(21) |
| Kelly fraction | 1/4 (Full Kelly 절대 금지) |

## 출력 포맷

```json
{
  "skill": "risk-manager",
  "status": "success",
  "data": {
    "risk_level": 0,
    "risk_level_name": "Normal",
    "passed": true,
    "risk_audit": {
      "violations": [],
      "warnings": ["sector_tech_at_22pct"],
      "checklist_passed": 6,
      "checklist_total": 6
    },
    "bias_check": {
      "detected_biases": [],
      "mitigations": [],
      "bias_score": 0
    },
    "drawdown": {
      "current": -0.05,
      "level": 0,
      "action": "normal_operation"
    },
    "recommendations": []
  }
}
```

## 참조 문서

- `docs/verified-methodologies-and-risk-management.md` §4-§5 — 리스크 관리 상세
- `.claude/skills/bias-checker/SKILL.md` — 편향 체크 독립 스킬
