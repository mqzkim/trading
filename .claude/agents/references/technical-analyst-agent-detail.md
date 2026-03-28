## Sub-Score Definitions

### Trend Score (weight: 40%)

Assess the primary trend direction and strength.

| Signal | Condition | Score Contribution |
|--------|-----------|-------------------|
| Price vs MA(200) | Price > MA(200) | Base bullish; distance % normalized |
| ADX(14) | ADX > 25 | Trending regime confirmed |
| MACD Direction | MACD line > Signal line | Bullish momentum direction |

Calculation:
```
trend_raw = (pct_above_ma200 * 0.5) + (adx_normalized * 0.3) + (macd_direction_binary * 0.2)
trend_score = percentile_rank(trend_raw, sector_universe) * 100
```

### Momentum Score (weight: 40%)

Assess price momentum using the Jegadeesh-Titman (1993) 12-1 month return factor.

| Signal | Method | Notes |
|--------|--------|-------|
| 12-1M Return | (P_t-1 / P_t-12) - 1 | Skip most recent month to avoid reversal |
| RSI(14) | 40-70 range = positive; < 30 or > 70 = penalized | Extremes reduce score |
| Sector Relative Strength | Stock 12M return vs sector median | Relative outperformance |

Calculation:
```
momentum_raw = (return_12_1m_pct * 0.5)
             + (rsi_normalized * 0.25)
             + (sector_relative_strength_pct * 0.25)
momentum_score = percentile_rank(momentum_raw, sector_universe) * 100
```

RSI normalization: RSI in [40, 70] maps to 50-100; outside maps 0-50 with penalty for extremes.

### Volume Score (weight: 20%)

Confirm price moves with volume participation.

| Signal | Condition | Interpretation |
|--------|-----------|----------------|
| OBV Trend | OBV rising over 21 days | Accumulation |
| Volume Ratio | Current volume / 20D avg volume | > 1.2 confirms breakout |

Calculation:
```
volume_raw = (obv_trend_binary * 0.6) + (volume_ratio_normalized * 0.4)
volume_score = percentile_rank(volume_raw, sector_universe) * 100
```

## Composite Technical Score

```
technical_score = (trend_score * 0.40)
                + (momentum_score * 0.40)
                + (volume_score * 0.20)
```

Clamped to [0, 100]. Sector-neutral percentile rank applied at the composite level for final normalization.

## ATR-Based Volatility Context

ATR(21) is not a scoring input but provides stop-loss sizing for downstream agents:

```
stop_distance = ATR(21) * multiplier

Multiplier by regime:
  Low-Vol Bull:  2.5x ATR
  High-Vol Bull: 3.0x ATR
  Low-Vol Range: 2.5x ATR
  High-Vol Bear: 3.5x ATR
  Transition:    3.5x ATR
```

Include `atr21` and `suggested_stop_distance` in output for position-sizer-agent consumption.

## Regime Consistency Check

After scoring, verify alignment with the current regime from regime-detect:

- Low-Vol Bull: expect trend_score > 60 and momentum_score > 55 for STRONG signal
- High-Vol Bear: technical signals are discounted by 30% in composite weighting
- Transition: flag any technical score > 75 as potentially unreliable

Add `regime_consistency: true/false` and note to output.

## Output Schema

```json
{
  "agent": "technical-analyst-agent",
  "symbol": "AAPL",
  "technical_score": 74,
  "sub_scores": {
    "trend_score": 78,
    "momentum_score": 72,
    "volume_score": 65
  },
  "raw_indicators": {
    "price": 185.50,
    "ma50": 178.20,
    "ma200": 165.40,
    "rsi14": 58.3,
    "atr21": 4.25,
    "adx14": 31.2,
    "macd_line": 2.15,
    "macd_signal": 1.80,
    "obv_trend": "rising",
    "volume_ratio": 1.35,
    "return_12_1m": 0.287
  },
  "stop_sizing": {
    "atr21": 4.25,
    "regime": "Low-Vol Bull",
    "multiplier": 2.5,
    "suggested_stop_distance": 10.63
  },
  "trend_direction": "bullish",
  "regime_consistency": true,
  "sector": "Information Technology",
  "sector_peer_count": 145,
  "warnings": []
}
```

## Failure Modes

- Missing indicator (ATR, ADX, OBV not yet calculated): request data-engineer-agent to recalculate; do not estimate
- Insufficient price history (< 252 days): set all momentum scores to 50 (neutral), add WARNING
- Sector peer count < 10: fall back to market-wide normalization, add WARNING
- No regime context provided: assume Low-Vol Bull defaults, add WARNING

## Reference Documents

- `docs/quantitative-scoring-methodologies.md` §1 — momentum factor (Jegadeesh-Titman) and technical models
- `.claude/skills/scoring-engine/SKILL.md` — Technical Analyst role in Layer 4 pipeline
- `.claude/skills/data-ingest/SKILL.md` — indicator data fields available
- `docs/verified-methodologies-and-risk-management.md` — ATR stop-loss sizing rules
- `.claude/CLAUDE.md` — confirmed ATR multiplier range (2.5-3.5x ATR(21))