---
status: diagnosed
trigger: "GET /api/v1/signals/AAPL returns 500 - SignalResponse validation error - strength field got 25.0 but schema constraint is le=1"
created: 2026-03-13T00:00:00Z
updated: 2026-03-13T00:00:00Z
---

## Current Focus

hypothesis: SignalStrength.value is a 0-100 float, but SignalResponse.strength expects 0-1. The router passes strength.value directly without dividing by 100.
test: Traced the call chain from handler return value through router to schema.
expecting: Root cause confirmed.
next_action: DIAGNOSED - no fix needed per task scope.

## Symptoms

expected: GET /api/v1/signals/AAPL returns 200 with SignalResponse containing strength in [0, 1].
actual: 500 Internal Server Error - "SignalResponse validation error - strength field got 25.0 but schema constraint is le=1"
errors: "SignalResponse validation error - strength field got 25.0 but schema constraint is le=1. Handler composite_score (0-100 scale) is being passed as strength (0-1 scale) without conversion."
reproduction: Any GET /api/v1/signals/{ticker} call when signal direction is BUY, SELL, or HOLD (non-zero strength).
started: Present in current implementation - structural mismatch never addressed.

## Eliminated

- hypothesis: composite_score is being passed as strength (as the error message suggests)
  evidence: The router reads data["strength"] on line 73, not data["composite_score"]. The handler returns them as separate keys. The error message description is misleading.
  timestamp: 2026-03-13T00:00:00Z

## Evidence

- timestamp: 2026-03-13T00:00:00Z
  checked: src/signals/domain/value_objects.py SignalStrength dataclass
  found: SignalStrength.value is validated in range 0-100 ("if not 0 <= self.value <= 100"). It is a 0-100 scale float.
  implication: The domain model uses 0-100 scale for strength.

- timestamp: 2026-03-13T00:00:00Z
  checked: src/signals/domain/services.py SignalFusionService._compute_strength()
  found: Returns round(weighted_avg * 0.6 + composite_score * 0.4, 1) where both weighted_avg and composite_score are 0-100 values. For HOLD it returns composite_score * 0.5. All outputs are 0-100 range.
  implication: strength.value coming out of fuse() is always in 0-100 range.

- timestamp: 2026-03-13T00:00:00Z
  checked: src/signals/application/handlers.py handle() return value (line 148)
  found: Returns Ok({"strength": strength.value, ...}) where strength is a SignalStrength object. strength.value is the 0-100 float.
  implication: data["strength"] in the router is a 0-100 float.

- timestamp: 2026-03-13T00:00:00Z
  checked: commercial/api/routers/signals.py lines 71-78
  found: The router reads strength_raw = data.get("strength", "MODERATE"). When strength_raw is a float (which it always is from the handler), it takes the branch: strength_val = float(strength_raw) -- NO conversion. A value like 25.0 is passed directly to SignalResponse.
  implication: This is the exact site of the bug. The router forwards the 0-100 value unchanged.

- timestamp: 2026-03-13T00:00:00Z
  checked: commercial/api/schemas/signal.py SignalResponse.strength field (line 37)
  found: strength: float = Field(ge=0, le=1). Pydantic enforces 0 <= strength <= 1.
  implication: Any value > 1.0 triggers a ValidationError, which FastAPI converts to a 500 (because the error originates inside the response_model serialization, not request validation).

## Resolution

root_cause: |
  SignalStrength.value (domain VO) is defined and validated on a 0-100 scale.
  The handler returns it as-is in the result dict under the key "strength".
  The router in commercial/api/routers/signals.py line 74-75 passes the raw float
  directly to SignalResponse without dividing by 100.
  SignalResponse.strength has Field(ge=0, le=1), so any non-trivial signal
  (e.g. 25.0, 60.0, 75.0) causes a Pydantic ValidationError -> 500.

  The comment on router line 71-72 is stale/wrong: it says
  "handler returns STRONG/MODERATE/WEAK string", but the handler has always
  returned a numeric float. The string-path code is dead code.

fix: empty - diagnosis only per task scope.
verification: empty
files_changed: []
