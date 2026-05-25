import { useEffect, useState } from "react";
import { createDemoSession, fetchSessionView, streamSessionUrl } from "./api";
import type { ConsultationSession, EvaluationResult, SessionSlot, SessionView, StreamEvent, Verdict } from "./types";

const verdictLabel: Record<Verdict, string> = {
  can_open: "可以开",
  validate_first: "先验证",
  do_not_open: "不建议开",
  insufficient_data: "证据不足"
};

const viewLabels: Record<SessionView, string> = {
  user: "User",
  report: "Report",
  debug: "Debug",
  admin: "Admin"
};

export default function App() {
  const [view, setView] = useState<SessionView>("user");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [session, setSession] = useState<ConsultationSession | null>(null);
  const [events, setEvents] = useState<StreamEvent[]>([]);

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

  if (!session) {
    return <main className="loading">正在建立咨询 Session...</main>;
  }

  const result = session.evaluation;

  return (
    <main className="app-shell">
      <nav className="top-tabs" aria-label="视图切换">
        {(Object.keys(viewLabels) as SessionView[]).map((item) => (
          <button key={item} className={view === item ? "active" : ""} onClick={() => setView(item)}>
            {viewLabels[item]}
          </button>
        ))}
      </nav>
      {view === "user" && <UserSession session={session} events={events} />}
      {view === "report" && <ReportView session={session} />}
      {view === "debug" && <DebugView session={session} events={events} />}
      {view === "admin" && <AdminView session={session} />}
      <small className="session-footnote">
        Session {shortId(session.session_id)} · {verdictLabel[result.verdict]}
      </small>
    </main>
  );
}

function UserSession({ session, events }: { session: ConsultationSession; events: StreamEvent[] }) {
  const result = session.evaluation;
  const importantSlots = pickSlots(session.visible_slots, [
    "monthly_rent",
    "daily_breakeven",
    "target_order_count",
    "location_score",
    "category_name"
  ]);
  const latestEvent = events[events.length - 1] ?? session.events[session.events.length - 1];

  return (
    <section className="phone-page" data-design-ref="mobile.session.live.shell">
      <header className="location-header" data-design-ref="mobile.session.live.locationHeader">
        <div>
          <span className="eyebrow">当前铺位</span>
          <h1>{result.location.address_text}</h1>
          <p>
            {result.location.city} · {result.location.floor ?? "楼层待补"} · 置信度 {result.location.evidence_level}
          </p>
        </div>
        <button>重选点</button>
      </header>

      <div className="agent-path" data-design-ref="mobile.session.live.publicAgentPath">
        {result.agent_path.map((step) => (
          <span key={step.engine}>{step.engine}</span>
        ))}
      </div>

      <section className="chat-stream" data-design-ref="mobile.session.live.chatStream">
        <div className="bubble user">我在这个位置想开店，先帮我判断能不能做。</div>
        <div className="bubble agent">
          先算账。别凭感觉看铺子，先看每天至少要卖多少，再让地址来证明它能不能撑住。
        </div>
        <FinancePanel result={result} compact />
        <div className="bubble agent strong">{result.report.executive_summary}</div>
      </section>

      <section className="slot-sheet" data-design-ref="mobile.session.live.slotSheet">
        {importantSlots.map((slot) => (
          <div key={slot.id}>
            <span>{slot.label}</span>
            <strong>{formatSlotValue(slot)}</strong>
          </div>
        ))}
      </section>

      <footer className="input-dock" data-design-ref="mobile.session.live.inputDock">
        <button title="定位">⌖</button>
        <input placeholder="补充房租、人工、毛利率或现场人流..." />
        <button title="发送">↗</button>
        <button title="语音 P2" disabled>声</button>
      </footer>
      {latestEvent && <small className="stream-note">最新：{latestEvent.message}</small>}
    </section>
  );
}

function FinancePanel({ result, compact = false }: { result: EvaluationResult; compact?: boolean }) {
  const rows = [
    ["建店成本", money(result.finance.build_cost)],
    ["日盈亏平衡点", money(result.finance.daily_breakeven)],
    ["目标回本日销", money(result.finance.target_daily_revenue)],
    ["目标订单数", `${result.finance.target_order_count} 单/日`],
    ["3个月现金预留", money(result.finance.minimum_cash_reserve_3m)]
  ];
  return (
    <section className={compact ? "finance-card compact" : "finance-card"} data-design-ref="mobile.session.live.financeCard">
      <header>
        <h2>实时算账</h2>
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

function shortId(sessionId: string) {
  return sessionId.length > 8 ? sessionId.slice(0, 8) : sessionId;
}

function money(value: number) {
  return `¥${value.toLocaleString("zh-CN")}`;
}
