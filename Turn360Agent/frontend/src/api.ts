import type { ConsultationSession, CreatedSession, EvaluationResult, SessionView, SlotPatchValue } from "./types";

const demoPreOpeningRequest = {
  session_id: "demo",
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
    longitude: 121.43,
    latitude: 31.18,
    floor: "一楼临街",
    target_customer_flow_30min: 90,
    comparable_store_orders_per_day: 95,
    evidence_level: "mock"
  },
  category: {
    category_name: "米饭快餐"
  }
};

export async function createDemoSession(): Promise<ConsultationSession> {
  try {
    const response = await fetch("/api/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario: "pre_opening", pre_opening: demoPreOpeningRequest })
    });
    if (!response.ok) {
      throw new Error(`create session responded ${response.status}`);
    }
    const created = (await response.json()) as CreatedSession;
    return await fetchSessionView(created.session_id, "user");
  } catch {
    return fallbackSession("user");
  }
}

export async function fetchSessionView(sessionId: string, view: SessionView): Promise<ConsultationSession> {
  try {
    const response = await fetch(`/api/sessions/${encodeURIComponent(sessionId)}?view=${view}`);
    if (!response.ok) {
      throw new Error(`session view responded ${response.status}`);
    }
    return (await response.json()) as ConsultationSession;
  } catch {
    return { ...fallbackSession(view), session_id: sessionId };
  }
}

export async function patchSessionSlots(
  sessionId: string,
  updates: Record<string, SlotPatchValue>,
  view: SessionView
): Promise<ConsultationSession> {
  try {
    const response = await fetch(`/api/sessions/${encodeURIComponent(sessionId)}/slots`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ updates, view })
    });
    if (!response.ok) {
      throw new Error(`slot patch responded ${response.status}`);
    }
    return (await response.json()) as ConsultationSession;
  } catch {
    return { ...fallbackSession(view), session_id: sessionId };
  }
}

export async function sendChatMessage(
  sessionId: string,
  message: string,
  view: SessionView
): Promise<ConsultationSession> {
  try {
    const response = await fetch(`/api/sessions/${encodeURIComponent(sessionId)}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, view })
    });
    if (!response.ok) {
      throw new Error(`chat responded ${response.status}`);
    }
    return (await response.json()) as ConsultationSession;
  } catch {
    const fallback = fallbackSession(view);
    return {
      ...fallback,
      session_id: sessionId,
      messages: [
        ...fallback.messages,
        {
          role: "user",
          content: message,
          created_at: new Date().toISOString(),
          visibility: "public",
          slot_updates: []
        },
        {
          role: "assistant",
          content: "我这边暂时没连上后端，但你可以继续补房租、人工、毛利率和现场人流。",
          created_at: new Date().toISOString(),
          visibility: "public",
          slot_updates: []
        }
      ]
    };
  }
}

export function streamSessionUrl(sessionId: string, view: SessionView) {
  const streamView = view === "debug" ? "debug" : "user";
  return `/api/sessions/${encodeURIComponent(sessionId)}/chat/stream?view=${streamView}`;
}

export const fallbackEvaluation: EvaluationResult = {
  session_id: "fallback-pre-opening",
  verdict: "validate_first",
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
    longitude: 121.43,
    latitude: 31.18,
    floor: "一楼临街",
    target_customer_flow_30min: 90,
    comparable_store_orders_per_day: 95,
    evidence_level: "mock",
    score: 85,
    flags: [],
    notes: ["门前客群数据对目标订单数有一定支撑。", "同类店订单水平可支撑目标订单数。"]
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

function fallbackSession(view: SessionView): ConsultationSession {
  const now = new Date().toISOString();
  const sessionId = fallbackEvaluation.session_id;
  return {
    session_id: sessionId,
    scenario: "pre_opening",
    status: "active",
    created_at: now,
    updated_at: now,
    view,
    evaluation: fallbackEvaluation,
    visible_slots: [
      slot("monthly_rent", "房租/月", 6666, "元", "finance", "editable", "user_input", "low", true, now),
      slot("daily_breakeven", "日盈亏平衡点", 1010.06, "元/日", "finance", "public", "system_calculated", "high", false, now),
      slot("target_order_count", "目标订单数", 64.64, "单/日", "finance", "public", "system_calculated", "high", false, now),
      slot("location_score", "地址评分", 85, "分", "location", "public", "system_calculated", "medium", false, now),
      slot("category_name", "品类", "米饭快餐", null, "category", "editable", "user_input", "low", true, now)
    ],
    hidden_slots:
      view === "debug" || view === "admin"
        ? [
            slot("founder_expression_score", "表达清晰度", null, "分", "founder", "private_debug", "conversation_analysis", "pending", false, now),
            slot("founder_location_bias_score", "选址判断偏差", null, "分", "founder", "private_debug", "map_cross_check", "pending", false, now)
          ]
        : undefined,
    events: [
      {
        sessionId,
        type: "message.done",
        step: "report",
        message: fallbackEvaluation.report.executive_summary,
        visibility: "public",
        payload: {}
      }
    ],
    messages: [
      {
        role: "assistant",
        content: "你要开店，先别急着看感觉。你直接告诉我：在哪个城市/位置，想做什么品类，房租、人工、毛利率、客单价大概多少。",
        created_at: now,
        visibility: "public",
        slot_updates: []
      }
    ],
    current_question: "先告诉我城市、位置、品类、房租和人工。",
    raw_input: view === "debug" || view === "admin" ? demoPreOpeningRequest : undefined,
    debug_summary: view === "debug" || view === "admin" ? { event_count: 1, hidden_slot_count: 2 } : undefined,
    admin_summary:
      view === "admin"
        ? {
            requires_human_review: true,
            risk_flags: fallbackEvaluation.finance.risk_flags,
            report_ready: true
          }
        : undefined
  };
}

function slot(
  id: string,
  label: string,
  value: string | number | null,
  unit: string | null,
  group: string,
  visibility: "public" | "editable" | "report_only" | "private_debug",
  source: string,
  confidence: string,
  editable: boolean,
  updated_at: string
) {
  return { id, label, value, unit, group, visibility, source, confidence, editable, updated_at };
}
