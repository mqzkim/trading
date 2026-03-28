# Trading System

체계적 증권 트레이딩 시스템 — 정량적 스코어링 기반. CLI + Claude Skill + REST API로 개인/상업 동시 서빙.

## 참조 문서

| 주제 | 파일 |
|------|------|
| 확정된 전략, 상업 제품 3종 | `.claude/references/strategy.md` |
| 리스크 한도, 낙폭 방어 3단계 | `.claude/references/risk-limits.md` |
| 기술 스택, Team Agent 모델 배정 | `.claude/references/tech-stack.md` |
| 구현 순서 (1~7단계) | `.claude/references/implementation-order.md` |
| 문서 위치, 코드 구조 | `.claude/references/docs-index.md` |

## 핵심 제약

- **단타 절대 금지** — 스윙/포지션 트레이딩만
- **상업 API는 정보 제공만** — 매수/매도 추천은 개인 전용 (법적 경계)
- **Full Kelly 금지** — Fractional Kelly 1/4만 허용
- **낙폭 20% 초과 시 전량 청산** — 냉각기 최소 1개월
