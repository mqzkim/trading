## Output

- Structured final analysis report per symbol (composite score, safety status, position suggestion, risk verdict, bias check)
- Gate judgment record: Gate ID, PASS/WARN/FAIL, evidence, next action
- Agent coordination log: which agents were spawned, results received, timeouts or failures noted
- Drawdown defense status: current level (0-3), active restrictions, triggered actions

## Pipeline Layer Reference

```
Layer 1  data-ingest              Sequential  — market data collection
Layer 2  regime-detect            Sequential  — regime classification + weights
Layer 3  signal-generate          Parallel    — 4 strategy agents (CANSLIM, Magic Formula, Momentum, Trend)
Layer 4  scoring-engine           Parallel    — 3 analyst agents (Fundamental, Technical, Sentiment)
Layer 5  position-sizer           Sequential  — position size calculation (personal only)
Layer 6  risk-manager             Parallel    — 2 risk agents (portfolio risk, drawdown guard)
Layer 7  execution-planner        Sequential  — order plan generation (personal only)
Layer 8  bias-checker             Sequential  — behavioral bias detection
Layer 9  final report             Sequential  — consolidated output
```

## Drawdown Defense Rules

| Level | Threshold | Restriction |
|-------|-----------|-------------|
| 0 Normal   | < 10%  | Full pipeline runs normally |
| 1 Warning  | 10-15% | Block new entries; propagate `defensive_mode: true` |
| 2 Defensive| 15-20% | Instruct execution-planner `reduce_50%` |
| 3 Emergency| > 20%  | Trigger `emergency_liquidate`; enter cooling period |

## Gate Judgment Protocol

1. Collect all exit criteria for the current Gate from the sprint context document
2. Verify each criterion with file existence checks or Bash commands as needed
3. Assign PASS if all criteria met, WARN if minor gaps that do not block progress, FAIL if blocking
4. Write the judgment to the gate record file under `docs/sprints/`
5. On FAIL: halt and return to the corrective gate (G3 for bootstrap issues, G4 for runbook issues)

## Failure Handling

| Situation | Action |
|-----------|--------|
| Agent timeout (60s) | Exclude result, continue with remaining agents, flag in report |
| Missing data for sub-score | Set sub-score to 0, add WARNING to report |
| Safety filter fail (Z or M) | Set composite_score = 0, halt scoring, mark `safety_passed: false` |
| Full pipeline failure | Generate error report with failure layer, inputs at failure point |

## Reference Documents

- `docs/sprints/S0-context.md` — active sprint scope and gate criteria
- `docs/sprints/S0-agent-matrix.md` — agent assignment matrix
- `.claude/skills/trading-orchestrator/SKILL.md` — skill-level workflow definitions
- `docs/strategy-recommendation.md` — confirmed strategy principles
- `docs/verified-methodologies-and-risk-management.md` — risk limit table
- `.claude/CLAUDE.md` — project memory and constraints