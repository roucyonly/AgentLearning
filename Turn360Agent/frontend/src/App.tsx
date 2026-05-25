import { useEffect, useState } from "react";
import { createDemoSession, fetchSessionView, patchSessionSlots, sendChatMessage, streamSessionUrl } from "./api";
import type { ConsultationSession, EvaluationResult, SessionSlot, SessionView, SlotPatchValue, StreamEvent, Verdict } from "./types";

const verdictLabel: Record<Verdict, string> = {
  can_open: "可以开",
  validate_first: "先验证",
  do_not_open: "不建议开",
  insufficient_data: "证据不足"
};

const verdictTone: Record<Verdict, string> = {
  can_open: "账能跑通，继续验证地址。",
  validate_first: "先别交钱，把缺的证据补上。",
  do_not_open: "现在不适合开，先止住损失。",
  insufficient_data: "信息不够，先把关键数补齐。"
};

const viewLabels: Record<SessionView, string> = {
  user: "咨询",
  report: "报告",
  debug: "调试",
  admin: "管理"
};

const financeSlotIds = ["monthly_rent", "monthly_labor", "monthly_utilities", "gross_margin_rate", "average_ticket"];
const locationSlotIds = ["storefront_flow_30min", "comparable_orders", "location_score"];
const categorySlotIds = ["category_name", "category_demand_type"];
const numericSlotIds = new Set([
  "monthly_rent",
  "monthly_labor",
  "monthly_utilities",
  "gross_margin_rate",
  "average_ticket",
  "storefront_flow_30min",
  "comparable_orders"
]);

export default function App() {
  const [view, setView] = useState<SessionView>("user");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [session, setSession] = useState<ConsultationSession | null>(null);
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [patchingSlot, setPatchingSlot] = useState<string | null>(null);
  const [patchMessage, setPatchMessage] = useState("参数已同步");
  const [sendingMessage, setSendingMessage] = useState(false);

  useEffect(() => {
    let active = true;
    createDemoSession().then((created) => {
      if (!active) return;
      setSessionId(created.session_id);
      setSession(created);
      setEvents(created.events.slice(-8));
    });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!sessionId) return;
    let active = true;
    fetchSessionView(sessionId, view).then((nextSession) => {
      if (!active) return;
      setSession(nextSession);
      setEvents(nextSession.events.slice(-8));
    });
    return () => {
      active = false;
    };
  }, [sessionId, view]);

  useEffect(() => {
    if (!sessionId) return;
    const eventSource = new EventSource(streamSessionUrl(sessionId, view));
    eventSource.onmessage = (event) => {
      setEvents((items) => [...items, JSON.parse(event.data) as StreamEvent].slice(-8));
    };
    eventSource.onerror = () => eventSource.close();
    return () => eventSource.close();
  }, [sessionId, view]);

  async function handleSlotPatch(slotId: string, value: SlotPatchValue) {
    if (!sessionId) return;
    setPatchingSlot(slotId);
    setPatchMessage("正在重新计算");
    const nextSession = await patchSessionSlots(sessionId, { [slotId]: value }, view);
    setSession(nextSession);
    setEvents(nextSession.events.slice(-8));
    setPatchMessage("参数已同步");
    setPatchingSlot(null);
  }

  async function handleSendMessage(message: string) {
    if (!sessionId || !message.trim()) return;
    setSendingMessage(true);
    const nextSession = await sendChatMessage(sessionId, message.trim(), view);
    setSession(nextSession);
    setEvents(nextSession.events.slice(-8));
    setSendingMessage(false);
  }

  if (!session) {
    return <main className="loading">正在建立咨询 Session...</main>;
  }

  return (
    <main className="app-shell">
      <nav className="top-tabs" aria-label="视图切换">
        {(Object.keys(viewLabels) as SessionView[]).map((item) => (
          <button key={item} className={view === item ? "active" : ""} onClick={() => setView(item)}>
            {viewLabels[item]}
          </button>
        ))}
      </nav>
      {view === "user" && (
        <UserSession
          session={session}
          events={events}
          onPatchSlot={handleSlotPatch}
          onSendMessage={handleSendMessage}
          patchingSlot={patchingSlot}
          patchMessage={patchMessage}
          sendingMessage={sendingMessage}
        />
      )}
      {view === "report" && <ReportView session={session} />}
      {view === "debug" && <DebugView session={session} events={events} />}
      {view === "admin" && <AdminView session={session} />}
    </main>
  );
}

function UserSession({
  session,
  events,
  onPatchSlot,
  onSendMessage,
  patchingSlot,
  patchMessage,
  sendingMessage
}: {
  session: ConsultationSession;
  events: StreamEvent[];
  onPatchSlot: (slotId: string, value: SlotPatchValue) => Promise<void>;
  onSendMessage: (message: string) => Promise<void>;
  patchingSlot: string | null;
  patchMessage: string;
  sendingMessage: boolean;
}) {
  const result = session.evaluation;
  const [draftMessage, setDraftMessage] = useState("");
  const latestEvent = events[events.length - 1] ?? session.events[session.events.length - 1];
  const financeSlots = pickSlots(session.visible_slots, financeSlotIds);
  const locationSlots = pickSlots(session.visible_slots, locationSlotIds);
  const categorySlots = pickSlots(session.visible_slots, categorySlotIds);

  return (
    <section className="mobile-session" data-design-ref="mobile.session.live.shell">
      <header className="consult-header" data-design-ref="mobile.session.live.locationHeader">
        <div>
          <span className="eyebrow">开店前评估</span>
          <h1>{result.location.address_text}</h1>
          <p>{result.location.city} · {result.location.floor ?? "楼层待补"} · {result.location.evidence_level}</p>
        </div>
        <VerdictPill verdict={result.verdict} />
      </header>

      <section className="decision-panel">
        <div>
          <span>结论</span>
          <strong>{verdictLabel[result.verdict]}</strong>
          <p>{verdictTone[result.verdict]}</p>
        </div>
        <div className="decision-metrics">
          <Metric label="日平衡点" value={money(result.finance.daily_breakeven)} />
          <Metric label="回本日销" value={money(result.finance.target_daily_revenue)} />
          <Metric label="目标单量" value={`${result.finance.target_order_count} 单`} />
          <Metric label="地址分" value={`${result.location.score}`} />
        </div>
      </section>

      <div className="agent-path" data-design-ref="mobile.session.live.publicAgentPath">
        {result.agent_path.map((step) => (
          <span key={step.engine}>{step.engine}</span>
        ))}
      </div>

      <section className="conversation-panel" data-design-ref="mobile.session.live.chatStream">
        <header>
          <h2>勇哥式引导</h2>
          <small>{session.current_question}</small>
        </header>
        <div className="message-list">
          {session.messages.slice(-6).map((message, index) => (
            <div className={`message ${message.role}`} key={`${message.created_at}-${index}`}>
              <p>{message.content}</p>
              {message.slot_updates.length > 0 && <small>已更新：{message.slot_updates.join("、")}</small>}
            </div>
          ))}
        </div>
        <div className="starter-chips">
          {["我要开店", "房租12000，人工7000，毛利率60，客单25", "门前30分钟80人，同类店订单100单"].map((item) => (
            <button key={item} disabled={sendingMessage} onClick={() => void onSendMessage(item)}>
              {item}
            </button>
          ))}
        </div>
      </section>

      <section className="workbench" data-design-ref="mobile.session.live.slotSheet">
        <header>
          <h2>实时参数</h2>
          <small>{patchingSlot ? patchMessage : latestEvent?.message ?? patchMessage}</small>
        </header>
        <SlotGroup title="算账" slots={financeSlots} onPatchSlot={onPatchSlot} patchingSlot={patchingSlot} />
        <SlotGroup title="地址" slots={locationSlots} onPatchSlot={onPatchSlot} patchingSlot={patchingSlot} />
        <SlotGroup title="品类" slots={categorySlots} onPatchSlot={onPatchSlot} patchingSlot={patchingSlot} />
      </section>

      <FinancePanel result={result} compact />

      <section className="next-actions">
        <h2>下一步</h2>
        {result.report.next_actions.slice(0, 3).map((item, index) => (
          <div key={item}>
            <span>{index + 1}</span>
            <p>{item}</p>
          </div>
        ))}
      </section>

      <footer className="input-dock" data-design-ref="mobile.session.live.inputDock">
        <button title="定位">定位</button>
        <input
          value={draftMessage}
          placeholder="直接说：我要在南京开咖啡店，房租..."
          disabled={sendingMessage}
          onChange={(event) => setDraftMessage(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              void onSendMessage(draftMessage).then(() => setDraftMessage(""));
            }
          }}
        />
        <button
          title="发送"
          disabled={sendingMessage || !draftMessage.trim()}
          onClick={() => void onSendMessage(draftMessage).then(() => setDraftMessage(""))}
        >
          {sendingMessage ? "分析中" : "发送"}
        </button>
      </footer>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function SlotGroup({
  title,
  slots,
  onPatchSlot,
  patchingSlot
}: {
  title: string;
  slots: SessionSlot[];
  onPatchSlot: (slotId: string, value: SlotPatchValue) => Promise<void>;
  patchingSlot: string | null;
}) {
  return (
    <section className="slot-group">
      <h3>{title}</h3>
      {slots.map((slot) => (
        <LiveSlot
          key={slot.id}
          slot={slot}
          onPatchSlot={onPatchSlot}
          isPatching={patchingSlot === slot.id}
          disabled={Boolean(patchingSlot)}
        />
      ))}
    </section>
  );
}

function FinancePanel({ result, compact = false }: { result: EvaluationResult; compact?: boolean }) {
  const rows = [
    ["建店成本", money(result.finance.build_cost)],
    ["每月固定成本", money(result.finance.monthly_fixed_cost)],
    ["日盈亏平衡点", money(result.finance.daily_breakeven)],
    ["目标回本日销", money(result.finance.target_daily_revenue)],
    ["3个月现金预留", money(result.finance.minimum_cash_reserve_3m)]
  ];
  return (
    <section className={compact ? "finance-card compact" : "finance-card"} data-design-ref="mobile.session.live.financeCard">
      <header>
        <h2>算账表</h2>
        <VerdictPill verdict={result.verdict} />
      </header>
      {rows.map(([label, value]) => (
        <div className="metric-row" key={label}>
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
      ))}
    </section>
  );
}

function ReportView({ session }: { session: ConsultationSession }) {
  const result = session.evaluation;
  return (
    <section className="report-page" data-design-ref="report.session.result.shell">
      <header className="report-verdict" data-design-ref="report.session.result.verdict">
        <VerdictPill verdict={result.verdict} />
        <h1>{verdictLabel[result.verdict]}</h1>
        <p>{result.report.executive_summary}</p>
      </header>
      <FinancePanel result={result} />
      <section className="analysis-grid">
        {result.report.sections.map((section) => (
          <article className="analysis-section" key={section.id}>
            <h2>{section.title}</h2>
            {section.items.map((item) => <p key={item}>{item}</p>)}
          </article>
        ))}
      </section>
      <section className="action-list" data-design-ref="report.session.result.actionPlan">
        <h2>下一步</h2>
        {result.report.next_actions.map((item, index) => (
          <div key={item}><span>{index + 1}</span>{item}</div>
        ))}
      </section>
    </section>
  );
}

function DebugView({ session, events }: { session: ConsultationSession; events: StreamEvent[] }) {
  const result = session.evaluation;
  const hiddenSlots = session.hidden_slots ?? [];
  return (
    <section className="debug-page" data-design-ref="debug.session.console.shell">
      <aside>
        <h2>Session</h2>
        <p>{session.session_id}</p>
        <VerdictPill verdict={result.verdict} />
        <pre>{JSON.stringify(session.debug_summary, null, 2)}</pre>
      </aside>
      <section data-design-ref="debug.session.console.engineDag">
        <h2>Agent DAG</h2>
        <div className="dag">
          {result.agent_path.map((item) => <span key={item.engine}>{item.engine}</span>)}
        </div>
        <h2>Raw Events</h2>
        <pre>{JSON.stringify(events, null, 2)}</pre>
      </section>
      <section data-design-ref="debug.session.console.hiddenScores">
        <h2>Hidden Slots</h2>
        <SlotList slots={hiddenSlots} emptyText="暂无隐藏评分" />
        <h2>Internal Flags</h2>
        <FlagList title="Finance Risks" flags={result.finance.risk_flags} />
        <FlagList title="Location Flags" flags={result.location.flags} />
      </section>
    </section>
  );
}

function AdminView({ session }: { session: ConsultationSession }) {
  const result = session.evaluation;
  const riskFlags = session.admin_summary?.risk_flags ?? [];
  return (
    <section className="admin-page" data-design-ref="admin.session.case.shell">
      <aside data-design-ref="admin.session.case.inbox">
        <h2>待审核 Session</h2>
        <button className="session-item active">{shortId(session.session_id)}</button>
      </aside>
      <section data-design-ref="admin.session.case.profile">
        <h1>Session 档案</h1>
        <p>场景：开店前地址评定 + 选品 + 算账</p>
        <p>状态：{session.status}</p>
        <p>结论：{verdictLabel[result.verdict]}</p>
        <p>人工复核：{session.admin_summary?.requires_human_review ? "需要" : "暂不需要"}</p>
      </section>
      <section data-design-ref="admin.session.case.reportReview">
        <h2>报告审核</h2>
        <label><input type="checkbox" checked readOnly /> 财务公式完整</label>
        <label><input type="checkbox" checked readOnly /> User UI 已隐藏内部评分</label>
        <label><input type="checkbox" checked={riskFlags.length > 0} readOnly /> 存在需复核风险项</label>
        <FlagList title="Review Flags" flags={riskFlags} />
      </section>
    </section>
  );
}

function LiveSlot({
  slot,
  onPatchSlot,
  isPatching,
  disabled
}: {
  slot: SessionSlot;
  onPatchSlot: (slotId: string, value: SlotPatchValue) => Promise<void>;
  isPatching: boolean;
  disabled: boolean;
}) {
  const [draft, setDraft] = useState(slot.value === null || slot.value === undefined ? "" : String(slot.value));

  useEffect(() => {
    setDraft(slot.value === null || slot.value === undefined ? "" : String(slot.value));
  }, [slot.id, slot.value]);

  const current = slot.value === null || slot.value === undefined ? "" : String(slot.value);
  const changed = draft !== current;

  async function commit() {
    if (!slot.editable || !changed) return;
    const value = normalizeDraftValue(draft, slot);
    if (value === undefined) {
      setDraft(current);
      return;
    }
    await onPatchSlot(slot.id, value);
  }

  return (
    <div className={slot.editable ? "slot-row editable" : "slot-row"}>
      <div>
        <span>{slot.label}</span>
        <small>{slot.unit ?? slot.source}</small>
      </div>
      {slot.editable ? (
        <div className="slot-control">
          <input
            value={draft}
            inputMode={numericSlotIds.has(slot.id) ? "decimal" : "text"}
            disabled={disabled}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                void commit();
              }
            }}
          />
          <button disabled={!changed || disabled} onClick={() => void commit()}>
            {isPatching ? "更新中" : "更新"}
          </button>
        </div>
      ) : (
        <strong>{formatSlotValue(slot)}</strong>
      )}
    </div>
  );
}

function SlotList({ slots, emptyText }: { slots: SessionSlot[]; emptyText: string }) {
  if (slots.length === 0) {
    return <p>{emptyText}</p>;
  }
  return (
    <div className="flag-list">
      {slots.map((slot) => (
        <span key={slot.id}>{slot.label}: {formatSlotValue(slot)}</span>
      ))}
    </div>
  );
}

function FlagList({ title, flags }: { title: string; flags: string[] }) {
  return (
    <div className="flag-list">
      <h3>{title}</h3>
      {flags.length === 0 ? <p>无</p> : flags.map((flag) => <span key={flag}>{flag}</span>)}
    </div>
  );
}

function VerdictPill({ verdict }: { verdict: Verdict }) {
  return <span className={`verdict ${verdict}`}>{verdictLabel[verdict]}</span>;
}

function pickSlots(slots: SessionSlot[], ids: string[]) {
  const slotMap = new Map(slots.map((slot) => [slot.id, slot]));
  return ids.map((id) => slotMap.get(id)).filter((slot): slot is SessionSlot => Boolean(slot));
}

function formatSlotValue(slot: SessionSlot) {
  if (slot.value === null || slot.value === undefined || slot.value === "") {
    return "待补";
  }
  return `${slot.value}${slot.unit ? ` ${slot.unit}` : ""}`;
}

function normalizeDraftValue(value: string, slot: SessionSlot): SlotPatchValue | undefined {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  if (numericSlotIds.has(slot.id)) {
    const numberValue = Number(trimmed);
    return Number.isFinite(numberValue) ? numberValue : undefined;
  }
  return trimmed;
}

function shortId(sessionId: string) {
  return sessionId.length > 8 ? sessionId.slice(0, 8) : sessionId;
}

function money(value: number) {
  return `¥${value.toLocaleString("zh-CN")}`;
}
