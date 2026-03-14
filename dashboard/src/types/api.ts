export interface Position {
  symbol: string;
  qty: number;
  current_price: number;
  pnl_pct: number;
  pnl_dollar: number;
  stop_price: number;
  target_price: number;
  composite_score: number;
  market_value: number;
}

export interface TradeHistoryItem {
  symbol: string;
  direction: string;
  entry_price: number;
  stop_loss_price: number;
  take_profit_price: number;
  quantity: number;
  position_value: number;
  composite_score: number;
  signal_direction: string;
  status: string;
  created_at: string;
}

export interface EquityCurve {
  dates: string[];
  values: number[];
}

export interface RegimePeriod {
  start: string;
  end: string;
  regime: string;
}

export interface LastPipeline {
  run_id: string;
  status: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface OverviewData {
  total_value: number;
  today_pnl: number;
  drawdown_pct: number;
  last_pipeline: LastPipeline | null;
  positions: Position[];
  trade_history: TradeHistoryItem[];
  equity_curve: EquityCurve;
  regime_periods: RegimePeriod[];
}
