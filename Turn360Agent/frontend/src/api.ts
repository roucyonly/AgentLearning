import type { EvaluationResult } from "./types";

const sampleRequest = {
  session_id: "demo-pre-opening",
  finance: {
    area_sqm: 25,
    monthly_rent: 6666,
    rent_payment_months: 6,
    deposit: 6666,
    transfer_fee: 0,
    franchise_or_training_fee: 0,
    decoration_and_ads: 30000,
    equipment: 0,
    first_batch_material: 5000,
    monthly_labor: 8000,
    monthly_utilities: 2000,
    monthly_fixed_operation_cost: 0,
    monthly_campaign_cost: 0,
    gross_margin_rate: 55,
    estimated_average_ticket: 22,
    target_payback_months: 12,
    cash_available: 130000,
    debt_monthly_payment: 0
  },
  location: {
    city: "上海",
    district: "徐汇区",
    address_text: "目标铺位门口",
    target_customer_flow_30min: 90,
    comparable_store_orders_per_day: 95,
    evidence_level: "mock"
  },
  category: {
    category_name: "米饭快餐"
  }
};

export async function fetchEvaluation(): Promise<EvaluationResult> {
  try {
    const response = await fetch("/api/sessions/pre-opening/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(sampleRequest)
    });
    if (!response.ok) {
      throw new Error(`backend responded ${response.status}`);
    }
    return (await response.json()) as EvaluationResult;
  } catch {
    return fallbackEvaluation;
  }
}

export const fallbackEvaluation: EvaluationResult = {
  session_id: "demo-pre-opening",
  verdict: "can_open",
  finance: {
    mode: "pre_opening",
    build_cost: 81662,
    monthly_fixed_cost: 16666,
    daily_fixed_cost: 555.53,
    effective_gross_margin_rate: 0.55,
    daily_breakeven: 1010.06,
    target_daily_revenue: 1422.18,
    target_order_count: 64.64,
    minimum_cash_reserve_3m: 131660,
    minimum_cash_reserve_6m: 181658,
    cash_gap_3m: -1660,
    cash_gap_6m: -51658,
    finance_status: "finance_validate_first",
    pre_opening_verdict: "validate_first",
    risk_flags: ["cash_below_3m_reserve"],
    positive_flags: ["target_order_count_not_extreme", "build_cost_light_or_moderate"]
  },
  location: {
    city: "上海",
    address_text: "目标铺位门口",
    target_customer_flow_30min: 90,
    comparable_store_orders_per_day: 95,
    evidence_level: "mock",
    score: 85,
    flags: [],
    notes: ["门前客群数据对目标订单数有一定支撑。", "同类店订单水位可支撑目标订单数。"]
  },
  category: {
    name: "米饭快餐",
    major_type: "meal",
    demand_type: "rigid",
    operation_complexity: "medium",
    default_gross_margin_rate: 0.55,
    notes: ["刚需强，但选址、出餐效率和午晚高峰承接能力关键。"]
  },
  report: {
    verdict: "validate_first",
    executive_summary: "账面可能成立，但还要补现金预留和现场验证。",
    sections: [
      {
        id: "finance",
        title: "财务测算",
        items: ["建店成本：81662", "日盈亏平衡点：1010.06", "目标订单数：64.64"]
      }
    ],
    next_actions: ["补齐门前人流。", "观察 3 家相似店订单水位。", "压租金支付方式。"]
  },
  agent_path: [
    { engine: "finance", status: "completed" },
    { engine: "location", status: "completed" },
    { engine: "category", status: "completed" },
    { engine: "report", status: "completed" }
  ]
};

