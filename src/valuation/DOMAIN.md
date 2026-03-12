# Valuation

## Responsibility

Intrinsic value estimation through ensemble valuation models (DCF, EPV, Relative Multiples). Produces confidence-weighted intrinsic value and margin of safety for each stock in the universe.

## Core Entities

- **WACC**: Weighted Average Cost of Capital via CAPM, clipped to 6-14%
- **DCFResult**: Discounted Cash Flow with 2-stage growth and terminal value cap at 40%
- **EPVResult**: Earnings Power Value using 5-year averaged operating margin (Greenwald method)
- **RelativeMultiplesResult**: PER/PBR/EV-EBITDA percentile ranking within GICS sector
- **IntrinsicValue**: Confidence-weighted ensemble of DCF + EPV + Relative
- **MarginOfSafety**: (intrinsic - market) / intrinsic with sector-adjusted thresholds

## External Dependencies

- **data_ingest** (via events): Financial statement data for DCF/EPV inputs
- **scoring** (via events): G-Score and composite scores for signal generation

## Use Cases

1. Single-stock valuation: compute DCF + EPV + Relative for one ticker
2. Batch universe valuation: valuate all stocks in S&P 500+400 universe
3. Margin of safety screening: filter stocks with sufficient margin of safety

## Invariant Rules

- Terminal Value cap: 40% of total DCF value (never exceeded)
- WACC clip: 6-14% range (CAPM result clamped)
- Ensemble weights: DCF 40% + EPV 35% + Relative 25% (fixed, confidence-adjusted)
- EPV uses 5-year averaged operating margin (not single year)
- Negative PER stocks excluded from PER percentile ranking
- Negative EBITDA stocks excluded from EV/EBITDA percentile ranking
- All valuation VOs are immutable frozen dataclasses
