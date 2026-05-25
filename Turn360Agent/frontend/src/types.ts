export type Verdict = "can_open" | "validate_first" | "do_not_open" | "insufficient_data";

export type FinanceResult = {
  mode: "pre_opening";
  build_cost: number;
  monthly_fixed_cost: number;
  daily_fixed_cost: number;
  effective_gross_margin_rate: number;
  daily_breakeven: number;
  target_daily_revenue: number;
  target_order_count: number;
  minimum_cash_reserve_3m: number;
  minimum_cash_reserve_6m: number;
  cash_gap_3m: number | null;
  cash_gap_6m: number | null;
  finance_status: string;
  pre_opening_verdict: Verdict;
  risk_flags: string[];
  positive_flags: string[];
};

export type LocationResult = {
  city: string;
  address_text: string;
  target_customer_flow_30min: number | null;
  comparable_store_orders_per_day: number | null;
  evidence_level: string;
  score: number;
  flags: string[];
  notes: string[];
};

export type CategoryResult = {
  name: string;
  major_type: string;
  demand_type: string;
  operation_complexity: string;
  default_gross_margin_rate: number;
  notes: string[];
};

export type Report = {
  verdict: Verdict;
  executive_summary: string;
  sections: Array<{ id: string; title: string; items: string[] }>;
  next_actions: string[];
};

export type EvaluationResult = {
  session_id: string;
  verdict: Verdict;
  finance: FinanceResult;
  location: LocationResult;
  category: CategoryResult;
  report: Report;
  agent_path: Array<{ engine: string; status: string }>;
};

export type StreamEvent = {
  sessionId: string;
  type: string;
  step: string;
  message: string;
};

