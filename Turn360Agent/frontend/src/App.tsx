import { useEffect, useMemo, useState } from "react";
import { fetchEvaluation } from "./api";
import type { EvaluationResult, StreamEvent, Verdict } from "./types";

type View = "user" | "report" | "debug" | "admin";

const verdictLabel: Record<Verdict, string> = {
  can_open: "可以开",
  validate_first: "先验证",
  do_not_open: "不建议开",
  insufficient_data: "证据不足"
};

export default function App() {
  const [view, setView] = useState<View>("user");
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [events, setEvents] = useState<StreamEvent[]>([]);

  useEffect(() => {
    fetchEvaluation().then(setResult);
  }, []);

  useEffect(() => {
    const eventSource = new EventSource("/api/chat/stream?session_id=demo-pre-opening");
    eventSource.onmessage = (event) => {
      setEvents((items) => [...items, JSON.parse(event.data) as StreamEvent].slice(-8));
    };
    eventSource.onerror = () => eventSource.close();
    return () => eventSource.close();
  }, []);

  if (!result) {
    return <main className="loading">正在建立咨询 Session...</main>;
  }

  return (
    <main className="app-shell">
      <nav className="top-tabs" aria-label="视图切换">
        <button className={view === "user" ? "active" : ""} onClick={() => setView("user")}>User</button>
        <button className={view === "report" ? "active" : ""} onClick={() => setView("report")}>Report</button>
        <button className={view === "debug" ? "active" : ""} onClick={() => setView("debug")}>Debug</button>
        <button className={view === "admin" ? "active" : ""} onClick={() => setView("admin")}>Admin</button>
      </nav>
      {view === "user" && <UserSession result={result} events={events} />}
      {view === "report" && <ReportView result={result} />}
      {view === "debug" && <DebugView result={result} events={events} />}
      {view === "admin" && <AdminView result={result} />}
    </main>
  );
}

function UserSession({ result, events }: { result: EvaluationResult; events: StreamEvent[] }) {
  return (
    <section className="phone-page" data-design-ref="mobile.session.live.shell">
      <header className="location-header" data-design-ref="mobile.session.live.locationHeader">
        <div>
          <span className="eyebrow">当前铺位</span>
          <h1>{result.location.address_text}</h1>
          <p>{result.location.city} · 置信度 {result.location.evidence_level}</p>
        </div>
        <button>重选点</button>
      </header>

      <div className="agent-path" data-design-ref="mobile.session.live.publicAgentPath">
        {result.agent_path.map((step) => (
          <span key={step.engine}>{step.engine}</span>
        ))}
      </div>

      <section className="chat-stream" data-design-ref="mobile.session.live.chatStream">
        <div className="bubble user">我在这个位置想开店，先帮我算能不能做。</div>
        <div className="bubble agent">
          先算账。你这不是看感觉，先看每天至少要卖多少，地址再来证明它能不能支撑。
        </div>
        <FinancePanel result={result} compact />
        <div className="bubble agent strong">{result.report.executive_summary}</div>
      </section>

      <section className="slot-sheet" data-design-ref="mobile.session.live.slotSheet">
        <div>
          <span>房租/月</span>
          <strong>{result.finance.monthly_fixed_cost - 10000 > 0 ? "已识别" : "待补"}</strong>
        </div>
        <div>
          <span>地址评分</span>
          <strong>{result.location.score}</strong>
        </div>
        <div>
          <span>品类</span>
          <strong>{result.category.name}</strong>
        </div>
      </section>

      <footer className="input-dock" data-design-ref="mobile.session.live.inputDock">
        <button title="定位">⌖</button>
        <input placeholder="补充房租、人工、毛利率或现场人流..." />
        <button title="发送">↗</button>
        <button title="语音 P2" disabled>声</button>
      </footer>
      {events.length > 0 && <small className="stream-note">最新：{events[events.length - 1].message}</small>}
    </section>
  );
}

function FinancePanel({ result, compact = false }: { result: EvaluationResult; compact?: boolean }) {
  const rows = [
    ["建店成本", money(result.finance.build_cost)],
    ["日盈亏平衡点", money(result.finance.daily_breakeven)],
    ["目标回本日销", money(result.finance.target_daily_revenue)],
    ["目标订单数", `${result.finance.target_order_count} 单/天`],
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

function ReportView({ result }: { result: EvaluationResult }) {
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

function DebugView({ result, events }: { result: EvaluationResult; events: StreamEvent[] }) {
  return (
    <section className="debug-page" data-design-ref="debug.session.console.shell">
      <aside>
        <h2>Session</h2>
        <p>{result.session_id}</p>
        <VerdictPill verdict={result.verdict} />
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
        <h2>Internal Flags</h2>
        <FlagList title="Finance Risks" flags={result.finance.risk_flags} />
        <FlagList title="Location Flags" flags={result.location.flags} />
      </section>
    </section>
  );
}

function AdminView({ result }: { result: EvaluationResult }) {
  const evidenceCount = result.location.notes.length + result.finance.positive_flags.length;
  return (
    <section className="admin-page" data-design-ref="admin.session.case.shell">
      <aside data-design-ref="admin.session.case.inbox">
        <h2>待审核 Session</h2>
        <button className="session-item active">demo-pre-opening</button>
      </aside>
      <section data-design-ref="admin.session.case.profile">
        <h1>Session 档案</h1>
        <p>场景：开店前地址评定 + 选品 + 算账</p>
        <p>证据数：{evidenceCount}</p>
        <p>结论：{verdictLabel[result.verdict]}</p>
      </section>
      <section data-design-ref="admin.session.case.reportReview">
        <h2>报告审核</h2>
        <label><input type="checkbox" checked readOnly /> 财务公式完整</label>
        <label><input type="checkbox" checked readOnly /> 地址证据可追踪</label>
        <label><input type="checkbox" readOnly /> 需要人工复核地图 API</label>
      </section>
    </section>
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

function money(value: number) {
  return `¥${value.toLocaleString("zh-CN")}`;
}

