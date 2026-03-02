# S1 — Sprint Retrospective

- Sprint ID: `S1`
- 작성일: 2026-03-03
- 기간: 2026-03-03 (단일 세션)
- 최종 판정: PASS

---

## 잘된 것 (Went Well)

1. **21/21 테스트 전체 통과** — 첫 실행에서 모든 단위테스트 PASS
2. **외부 라이브러리 없는 지표 계산** — pandas/numpy만으로 ATR/ADX/MA/RSI/OBV/MACD 순수 구현, 재현성 보장
3. **yfinance 폴백** — EODHD API 키 없이도 개발/테스트 환경에서 완전 동작
4. **SQLite WAL 캐시** — 동시 접근 안전, TTL 정책 완성
5. **python-project-setup Skill 생성** — G3에서 공백 Skill 즉시 보완

---

## 개선점 (Improvement)

1. **market.py 단위테스트 없음** — yfinance 네트워크 의존, mock 없이는 테스트 불가. S9에서 통합 테스트 추가 예정
2. **EODHD 통합테스트 불가** — API 키 필요. 실제 데이터 검증은 실환경에서만 가능
3. **sprint-closeout Skill Hub 미등록** — G7마다 4단계 수동 실행 필요. 다음 스프린트 전 등록 권장

---

## 패턴 학습

- `quality-gate` Skill은 Bash pytest 실행을 가이드하는 용도. 직접 테스트를 실행하진 않음
- `skill-auditor` Agent로 G1 Skill Coverage 감사 → 공백 Skill 식별 패턴이 효과적
- 지표 재현성 테스트(`test_indicator_reproducibility`)가 핵심 품질 검증 패턴으로 확립됨

---

## 다음 스프린트 (S2) 준비사항

- `core/data.DataClient`를 S2 Scoring Engine의 데이터 소스로 사용
- F-Score: 9항목 Piotroski (revenueGrowth, ROA, CFO, accrual 등) — fundamentals에서 추출
- Z-Score: Altman (WC/TA, RE/TA, EBIT/TA, MktCap/TotalLiab, Rev/TA)
- M-Score: 8항목 Beneish — 회계 조작 감지
- G-Score: Mohanram — 성장주 스코어
