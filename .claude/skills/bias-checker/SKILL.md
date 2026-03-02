---
name: bias-checker
description: "행동재무학 기반 투자 편향을 감지합니다. 손실 회피, 처분 효과, 과신, 확증 편향, 앵커링, 최근 편향 등 6가지 편향을 체크합니다. Layer 8. 개인 전용."
argument-hint: "[--portfolio path] [--decision JSON]"
user-invocable: true
allowed-tools: "Read, Bash"
---

# Bias Checker Skill (Layer 8)

> 행동재무학 편향 감지 전문가. 투자 의사결정에서 인지적 편향을 식별하고 완화책을 제안합니다.
> **개인 전용** — 독립 실행 또는 risk-manager의 서브 에이전트로 동작.

## 역할

포트폴리오 상태와 의사결정 컨텍스트를 분석하여
6가지 주요 투자 편향을 감지하고, 각각에 대한 완화 전략을 제안합니다.

## 6가지 편향 감지

### 1. 손실 회피 (Loss Aversion)
- **감지**: 손실 종목을 스코어 하락에도 불구하고 계속 보유
- **기준**: 손실 > 15% AND 스코어 < 50
- **완화**: "스탑로스 규칙을 재확인하세요. 매수가는 무관합니다."

### 2. 처분 효과 (Disposition Effect)
- **감지**: 이익 종목을 스코어 상승 중인데 조기 매도
- **기준**: 이익 > 20% AND 스코어 > 70 AND 매도 의향
- **완화**: "트레일링 스탑을 사용하세요. 승자는 더 달리게 두세요."

### 3. 과신 (Overconfidence)
- **감지**: 포지션 크기가 Kelly 한도 초과, 또는 집중도 과다
- **기준**: 단일 종목 > 8% 또는 최근 연승 후 사이즈 증가
- **완화**: "Kelly 1/4 규칙을 준수하세요. 연승은 스킬이 아닐 수 있습니다."

### 4. 확증 편향 (Confirmation Bias)
- **감지**: 스코어링에서 특정 팩터만 강조, 부정적 팩터 무시
- **기준**: 3축 중 1축만 높고 나머지 낮은데 매수 결정
- **완화**: "3축 모두 확인하세요. 약한 축의 원인을 분석하세요."

### 5. 앵커링 (Anchoring)
- **감지**: 매수가 기준으로 손절/익절 결정 (본전 심리)
- **기준**: 의사결정 근거에 매수가 언급
- **완화**: "현재 스코어와 ATR 스탑만 기준으로 판단하세요."

### 6. 최근 편향 (Recency Bias)
- **감지**: 최근 1-2주 성과에 과도하게 반응하여 전략 변경
- **기준**: 최소 보유 기간(2주/3개월) 미달 시 매도 시도
- **완화**: "최소 보유 기간을 준수하세요. 단기 노이즈입니다."

## 출력 포맷

```json
{
  "skill": "bias-checker",
  "status": "success",
  "data": {
    "detected_biases": [
      {
        "bias": "loss_aversion",
        "severity": "high",
        "evidence": "TSLA 보유 중, 손실 -22%, 스코어 38",
        "mitigation": "스탑로스 규칙 재확인. ATR 스탑 기준 이미 손절 대상."
      }
    ],
    "bias_score": 1,
    "total_checked": 6,
    "clean": false
  }
}
```

## 참조 문서

- `docs/verified-methodologies-and-risk-management.md` — 행동 편향 관리
- `.claude/skills/risk-manager/SKILL.md` — 리스크 매니저 통합
