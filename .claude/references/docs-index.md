# 문서 위치 & 코드 구조

## 문서 위치
- docs/trading-methodology-overview.md (통합 개요)
- docs/quantitative-scoring-methodologies.md (스코어링)
- docs/skill_chaining_and_self_improvement_research.md (스킬 체인)
- docs/verified-methodologies-and-risk-management.md (검증된 방법론)
- docs/strategy-recommendation.md (전략 추천서)
- docs/api-technical-feasibility.md (API 기술 타당성)
- docs/skill-conversion-plan.md (Skill 변환 계획)
- docs/cli-skill-implementation-plan.md (CLI/Skill 구현 플랜)

## 코드 구조
```
trading-system/
├── core/          # 공통 (scoring, regime, signals, data)
├── personal/      # 개인 (sizer, risk, execution, self-improve)
├── commercial/    # 상업 (FastAPI REST API)
├── cli/           # CLI (Typer 명령어)
├── .claude/       # Claude Skills (12개)
└── tests/
```
