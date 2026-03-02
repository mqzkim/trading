# Retrospective & Continuous Learning Rules

## The Learning Loop

Every mistake is an opportunity to improve CLAUDE.md. Follow this cycle:

1. **Detect** -- Notice when something goes wrong or could be better
2. **Reflect** -- Identify the root cause, not just the symptom
3. **Abstract** -- Extract a general principle from the specific case
4. **Document** -- Write a concise, prescriptive rule
5. **Verify** -- Confirm the rule prevents the issue in future sessions

## When to Update CLAUDE.md

- Claude makes the same mistake twice -> add a rule
- A code review catches a pattern issue -> add a convention
- A new architectural decision is made -> document the decision and rationale
- An existing rule is consistently followed without needing the reminder -> remove it

## Session Retrospective Prompts

Use these prompts at session end to trigger learning:

- "What mistakes did you make this session? Abstract them into rules."
- "Were there any instructions in CLAUDE.md that were unclear or contradictory?"
- "What context was missing that would have helped you work faster?"
- "Save the key learnings from this session to memory."

## Anti-Patterns to Watch For

- **Rule bloat**: CLAUDE.md growing past 300 lines -> prune aggressively
- **Stale rules**: Instructions that no longer match the codebase -> remove them
- **Vague rules**: "Write clean code" -> replace with specific, actionable instructions
- **Redundant rules**: Rules that duplicate what linters/formatters enforce -> delete them
- **Prohibition without alternative**: "Never use X" -> always specify what to use instead

## Monthly Maintenance

- Review all rules: are they still relevant?
- Check for contradictions between rules
- Consolidate similar rules into clearer statements
- Verify commands still work with current tooling
- Gather team feedback on rule effectiveness
