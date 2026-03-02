# S2 — Scoring Engine Sprint: Context Document

- Sprint ID: `S2`
- 작성일: 2026-03-03
- 상태: 진행 중
- 선행 조건: S1 PASS ✅

---

## 1. 목표

F/Z/M/G 4개 스코어 + 3축(기본적/기술적/센티먼트) 복합 점수로 0-100 종합 스코어 엔진 구현.

---

## 2. 핵심 품질 기준

| 항목 | 기준 |
|------|------|
| 안전성 필터 하드게이트 | Z-Score > 1.81 AND M-Score < -1.78 |
| 스코어 범위 | 0-100 (정규화) |
| 섹터 중립 랭킹 | 동일 섹터 내 백분위 |
| 재현성 | 동일 입력 → 동일 출력 |

---

## 3. 구현 범위

```
core/scoring/
├── __init__.py
├── fundamental.py   # F-Score(Piotroski), Z-Score(Altman), M-Score(Beneish), G-Score(Mohanram)
├── technical.py     # 추세/모멘텀/거래량 점수
├── sentiment.py     # 추정치 변경/내부자/공매도 (proxy 기반)
├── composite.py     # 3축 가중합 + 리스크 조정
└── safety.py        # 하드게이트 필터

tests/unit/
├── test_scoring_fundamental.py
├── test_scoring_technical.py
├── test_scoring_composite.py
└── test_scoring_safety.py
```

---

## 4. 성공 기준

| Gate | Exit Criteria |
|------|--------------|
| G0 | 이 문서 완성 |
| G1 | scoring-engine Skill 커버 확인 |
| G2 | fundamental/technical/sentiment Agent 배정 |
| G3 | 누락 Skill 0건 |
| G4 | core/scoring/ 구현 + 테스트 |
| G5 | 단위테스트 PASS, 안전성 필터 경계값 테스트 |
| G6 | PASS/WARN 판정 |
| G7 | commit + push 완료 |
