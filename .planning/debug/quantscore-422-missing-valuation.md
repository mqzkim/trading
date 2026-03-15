---
status: diagnosed
trigger: "GET /api/v1/quantscore/AAPL returns 422 with error: compute_fundamental_score() missing 1 required positional argument: 'valuation'"
created: 2026-03-13T00:00:00Z
updated: 2026-03-13T00:00:00Z
---

## Current Focus

hypothesis: CONFIRMED - handlers.py _get_fundamental() fallback calls compute_fundamental_score(symbol) with one arg, but the function signature requires two args (highlights: dict, valuation: dict)
test: read core/scoring/fundamental.py signature vs handlers.py call site
expecting: mismatch between call and signature
next_action: DONE - root cause confirmed, diagnosis returned

## Symptoms

expected: GET /api/v1/quantscore/AAPL returns 200 with score breakdown
actual: returns 422 Unprocessable Entity with message "compute_fundamental_score() missing 1 required positional argument: 'valuation'"
errors: "compute_fundamental_score() missing 1 required positional argument: 'valuation'"
reproduction: GET /api/v1/quantscore/AAPL with valid JWT
started: Since API endpoint was first deployed

## Eliminated

- hypothesis: API router invokes handler incorrectly (wrong command args)
  evidence: commercial/api/routers/quantscore.py line 30 calls handler.handle(ScoreSymbolCommand(symbol=ticker, strategy=strategy)) correctly
  timestamp: 2026-03-13

- hypothesis: Bootstrap does not wire fundamental_client into score_handler, causing fallback, but the fallback itself is correct
  evidence: src/bootstrap.py line 91: ScoreSymbolHandler(score_repo=score_repo, regime_adjuster=regime_adjuster) - fundamental_client is NOT passed, so _get_fundamental() uses fallback. The fallback is the bug, not the absence of the client.
  timestamp: 2026-03-13

## Evidence

- timestamp: 2026-03-13
  checked: core/scoring/fundamental.py line 120
  found: def compute_fundamental_score(highlights: dict, valuation: dict) -> dict — TWO required positional arguments
  implication: Any caller passing only one argument will raise TypeError

- timestamp: 2026-03-13
  checked: src/scoring/application/handlers.py lines 190-191
  found: return compute_fundamental_score(symbol) — called with a STRING (the ticker symbol) as the sole argument
  implication: (1) wrong number of args — passes 1 instead of 2; (2) wrong type — passes str instead of dict

- timestamp: 2026-03-13
  checked: src/bootstrap.py line 91
  found: ScoreSymbolHandler(score_repo=score_repo, regime_adjuster=regime_adjuster) — fundamental_client=None (default)
  implication: _get_fundamental() always hits the fallback path (no client injected), triggering the broken call every time via the API

- timestamp: 2026-03-13
  checked: CLI path (cli/main.py lines 185-186) vs API path
  found: CLI uses the same bootstrap() → same score_handler → same broken fallback. Hypothesis "works in CLI" may be incorrect or CLI doesn't reach AAPL under normal test conditions.
  implication: The bug exists in both paths; the difference is likely that CLI was tested with a mock/client or never hit the fallback

- timestamp: 2026-03-13
  checked: src/scoring/infrastructure/core_scoring_adapter.py lines 194-209
  found: compute_full_fundamental(highlights, valuation) — correctly calls compute_fundamental_score(highlights, valuation) with two dict args. This is the RIGHT pattern, not used by the handler fallback.
  implication: A correct wrapper exists in infrastructure but the handler's fallback bypasses it entirely

## Resolution

root_cause: |
  In src/scoring/application/handlers.py, the _get_fundamental() method (lines 190-191)
  calls `compute_fundamental_score(symbol)` — passing the raw ticker string as the first
  (and only) argument. But core/scoring/fundamental.py defines:

    def compute_fundamental_score(highlights: dict, valuation: dict) -> dict

  This requires TWO dict arguments (highlights, valuation). The call passes:
    - One argument instead of two (missing 'valuation')
    - A str instead of a dict (wrong type for 'highlights')

  The fallback is reached because bootstrap.py wires ScoreSymbolHandler with
  fundamental_client=None, so _get_fundamental() always falls through to the
  broken inline import. The correct calling convention is demonstrated in
  src/scoring/infrastructure/core_scoring_adapter.py which fetches highlights
  and valuation dicts first, then calls compute_fundamental_score(highlights, valuation).

fix: ""
verification: ""
files_changed: []
