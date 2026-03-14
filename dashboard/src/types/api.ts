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

// --- Signals page types ---

export interface ScoreRow {
  symbol: string;
  composite: number;
  risk_adjusted: number;
  strategy: string;
  signal: string;
}

export interface SignalItem {
  symbol: string;
  direction: string;
  strength: number;
  metadata: Record<string, unknown> | string;
}

export interface SignalsData {
  scores: ScoreRow[];
  signals: SignalItem[];
}

// --- Risk page types ---

export interface RiskData {
  drawdown_pct: number;
  drawdown_level: string;
  sector_weights: Record<string, number>;
  position_count: number;
  max_positions: number;
  regime: string;
}

// --- Pipeline page types ---

export interface PipelineStage {
  name: string;
  status: string;
  symbol_count: number;
}

export interface PipelineRun {
  run_id: string;
  started_at: string;
  completed_at: string;
  status: string;
  stages: PipelineStage[];
}

export interface ApprovalStatus {
  id: string;
  score_threshold: number;
  allowed_regimes: string[];
  max_per_trade_pct: number;
  daily_budget_cap: number;
  expires_at: string;
  is_active: boolean;
  is_suspended: boolean;
  suspended_reasons: string[];
  status: string;
}

export interface DailyBudget {
  spent: number;
  limit: number;
  remaining: number;
}

export interface ReviewItem {
  id: number;
  symbol: string;
  strategy: string;
  score: number;
  reason: string | null;
  created_at: string;
}

export interface PipelineData {
  pipeline_runs: PipelineRun[];
  next_scheduled: string;
  approval_status: ApprovalStatus | null;
  daily_budget: DailyBudget;
  review_queue: ReviewItem[];
}
