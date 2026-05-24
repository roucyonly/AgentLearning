# 11 UI 与 SVG 编码关联表

本文档用于把 UI 设计、SVG 线框图、前端路由、组件拆分和数据事件绑定到一起。开发时不要只看 SVG 画面，应同时看本文件，避免把 Session 级 UI 做成单轮对话 UI。

## 1. 总览

| 页面 | 用户角色 | 前端路由建议 | SVG 原型 | 主要文档 |
|---|---|---|---|---|
| 移动端咨询 Session | End User | `/sessions/:sessionId/live` | `mobile-ui-wireframe.svg` | `09-mobile-ui-design.md` |
| Debug 控制台 | Admin / QA / Developer | `/debug/sessions/:sessionId` | `debug-ui-wireframe.svg` | `09-mobile-ui-design.md` |
| 管理员 Session 档案 | Admin | `/admin/sessions/:sessionId` | `session-admin-ui-wireframe.svg` | `10-session-admin-report-design.md` |
| 用户最终报告 | End User / Admin | `/sessions/:sessionId/report/:reportId` | `report-ui-wireframe.svg` | `10-session-admin-report-design.md` |

实现时建议给页面根节点和核心组件增加 `data-design-ref`，值使用本文档里的 `Design Ref`。这样 QA、截图回归和前端代码 review 都能快速对照 SVG。

示例：

```tsx
<section data-design-ref="mobile.session.live.locationHeader">
  <LocationHeader session={session} />
</section>
```

## 2. 移动端咨询 Session

SVG：`mobile-ui-wireframe.svg`

页面定位：普通用户站在店门口、街边、商场或自己店里，围绕一个 `ConsultationSession` 进行持续咨询。

| Design Ref | SVG 区域 | 前端组件建议 | 绑定数据 | 说明 |
|---|---|---|---|---|
| `mobile.session.live.shell` | 手机整体容器 | `MobileSessionShell` | `ConsultationSession` | 页面根容器，必须以 `sessionId` 驱动 |
| `mobile.session.live.locationHeader` | 顶部地址条 | `LocationHeader` | `StoreProfile.location`, `LocationEvidence` | 展示坐标、距离、置信度、重选点 |
| `mobile.session.live.publicAgentPath` | 状态芯片 | `PublicAgentPathBar` | `PublicAgentStep[]` | 普通用户只看人话版步骤 |
| `mobile.session.live.chatStream` | 流式对话区 | `StreamingChat` | `Turn[]`, `StreamEvent[]` | 支持文字流、卡片插入、参数确认 |
| `mobile.session.live.financeCard` | 实时算账卡 | `LiveFinanceCard` | `KillLineSnapshot` | 展示日盈亏平衡点、保本达成率、关键缺口 |
| `mobile.session.live.slotSheet` | 实时参数抽屉 | `LiveSlotSheet` | `Slot[]` | 只展示 `public` / `editable` 字段 |
| `mobile.session.live.locationCard` | 地址评估卡 | `LocationScoreCard` | `LocationScoreSnapshot` | 展示地址分、证据来源、待验证项 |
| `mobile.session.live.categoryCard` | 品类判断卡 | `CategoryFitCard` | `CategoryFitSnapshot` | 展示刚需/轻社交/社交、地域适配 |
| `mobile.session.live.inputDock` | 底部输入栏 | `InputDock` | `DraftMessage`, `Attachment[]` | MVP 支持文字、拍照、定位；语音入口 P2 |
| `mobile.session.live.reportEntry` | 报告入口 | `ReportEntrySheet` | `DiagnosisReport.status` | 报告生成后出现，不替代聊天流 |

User UI 不得展示：

- `private_debug` slot。
- 表达能力原始分。
- 执行稳定性原始分。
- 用户判断偏差原始分。
- LLM prompt、tool raw payload。

## 3. Debug 控制台

SVG：`debug-ui-wireframe.svg`

页面定位：给开发、运营、质检看完整 Agent 运行路径。它不是用户侧功能，必须走权限控制。

| Design Ref | SVG 区域 | 前端组件建议 | 绑定数据 | 说明 |
|---|---|---|---|---|
| `debug.session.console.shell` | Debug 页面整体 | `DebugSessionConsole` | `ConsultationSession` | Debug 页面根容器 |
| `debug.session.console.sessionList` | 左侧 Session 列表 | `DebugSessionList` | `SessionListItem[]` | 支持状态、风险、场景筛选 |
| `debug.session.console.traceHeader` | 顶部环境和模型栏 | `TraceHeader` | `TraceMeta` | 展示环境、模型、traceId、导出入口 |
| `debug.session.console.engineDag` | Agent 调用 DAG | `EngineDagPanel` | `EngineTraceNode[]` | 展示 Router、Engine、工具调用顺序 |
| `debug.session.console.hiddenScores` | 隐藏评分区 | `HiddenScorePanel` | `PrivateScoreSnapshot` | 仅 Debug 可见 |
| `debug.session.console.toolCalls` | 工具调用列表 | `ToolCallPanel` | `ToolCall[]` | 展示地图、RAG、Vision、计算器调用 |
| `debug.session.console.ragHits` | RAG 命中 | `RagHitPanel` | `RagHit[]` | 不强行匹配案例，低相似度要标记不用 |
| `debug.session.console.rawEvents` | 原始事件流 | `RawEventLogPanel` | `StreamEvent[]` | 用于排查前后端状态不一致 |
| `debug.session.console.promptViewer` | Prompt/Response | `PromptViewer` | `ModelInvocation[]` | 生产环境需脱敏和权限审计 |

Debug UI 可以展示完整路径，但不能绕过业务结论生成逻辑。管理员修正 slot 时必须生成 audit log。

## 4. 管理员 Session 档案

SVG：`session-admin-ui-wireframe.svg`

页面定位：内部管理员围绕一个具体 Session 做审核、补证据、看报告是否能发。这个页面不是 Debug 替代品，而是业务审核工作台。

| Design Ref | SVG 区域 | 前端组件建议 | 绑定数据 | 说明 |
|---|---|---|---|---|
| `admin.session.case.shell` | 管理员页面整体 | `AdminSessionShell` | `ConsultationSession` | 页面根容器 |
| `admin.session.case.inbox` | 左侧用户/Session 列表 | `AdminSessionInbox` | `AssignedSession[]` | 按风险、状态、场景排序 |
| `admin.session.case.profile` | Session 档案 | `SessionProfilePanel` | `User`, `StoreProfile`, `ConsultationSession` | 展示用户、店铺、地址、场景 |
| `admin.session.case.timeline` | 会话与证据时间线 | `EvidenceTimeline` | `Turn[]`, `EvidenceItem[]` | 展示用户提交材料和关键对话 |
| `admin.session.case.slots` | 参数表 | `SlotReviewTable` | `Slot[]` | 支持发起修正，保留审计 |
| `admin.session.case.engineSummary` | Engine 摘要 | `EngineSnapshotSummary` | `EngineSnapshot[]` | 展示财务、地址、品类、能力快照 |
| `admin.session.case.hiddenScores` | 内部评分 | `AdminPrivateScorePanel` | `PrivateScoreSnapshot` | 管理员可看，但不能原样发给用户 |
| `admin.session.case.actions` | 管理员操作区 | `AdminActionPanel` | `AdminAction[]` | 补材料、打标签、转 QA、审核报告 |
| `admin.session.case.reportReview` | 报告审核 | `ReportReviewPanel` | `DiagnosisReport` | 校验是否有理有据、可执行 |

Admin 页面必须清楚区分：

- 用户原始事实。
- Agent 抽取/推断。
- 地图或工具结果。
- 管理员备注。
- 最终可展示给用户的报告内容。

## 5. 用户最终报告

SVG：`report-ui-wireframe.svg`

页面定位：对当前 Session 的结构化诊断报告。报告必须能独立阅读，不能只是聊天总结。

| Design Ref | SVG 区域 | 前端组件建议 | 绑定数据 | 说明 |
|---|---|---|---|---|
| `report.session.result.shell` | 报告页面整体 | `DiagnosisReportPage` | `DiagnosisReport` | 报告根容器 |
| `report.session.result.verdict` | 最终结论区 | `ReportVerdictHero` | `ReportVerdict`, `confidence` | 明确可以做、观察、整改、止损或证据不足 |
| `report.session.result.situation` | 当前状况摘要 | `SituationSummaryCard` | `SituationSummary` | 概括开店阶段、经营状态、主要矛盾 |
| `report.session.result.finance` | 财务逐条分析 | `FinanceAnalysisSection` | `KillLineSnapshot` | 展示公式、关键数字、盈亏平衡点 |
| `report.session.result.location` | 地址逐条分析 | `LocationAnalysisSection` | `LocationScoreSnapshot` | 区分 API 证据、现场证据、推断 |
| `report.session.result.category` | 品类适配 | `CategoryAnalysisSection` | `CategoryFitSnapshot` | 展示刚需/轻社交/社交、地域影响 |
| `report.session.result.operator` | 经营者建议 | `OperatorCapabilitySection` | `FounderCapabilityAdvice` | 用户侧展示建议，不展示原始隐藏分 |
| `report.session.result.evidence` | 证据矩阵 | `EvidenceMatrix` | `EvidenceItem[]` | 每条结论必须能追到来源 |
| `report.session.result.actionPlan` | 后续方案 | `ActionPlanTimeline` | `ActionPlan` | 今天、7 天、30 天动作 |
| `report.session.result.stopLoss` | 验证指标和止损线 | `StopLossCard` | `StopLossLine` | 必须量化，避免空话 |
| `report.session.result.appendix` | 附录 | `ReportAppendix` | `SourceRef[]` | 数据源、用户材料、地图/RAG 引用 |

报告页的结论文案必须中立：

- 数据支持开店时，要明确写“可以开/可以继续做”。
- 证据不足时，写清楚缺什么证据。
- 需要止损时，写清楚财务和能力依据，不能用情绪化判断替代数字。

## 6. 事件到 UI 的绑定

流式事件建议按以下方式驱动 UI：

| Event Type | User UI | Debug UI | Admin UI | Report UI |
|---|---|---|---|---|
| `turn.created` | 新增聊天气泡 | 原始事件 | 时间线 | 不直接使用 |
| `slot.extracted` | 可见 slot 更新 | 全量 slot 更新 | 参数表更新 | 作为报告证据 |
| `slot.corrected` | 可见参数重算 | 审计事件 | 参数表和 audit log | 记录来源 |
| `engine.started` | 人话版步骤更新 | DAG 节点 started | Engine 摘要 | 不直接使用 |
| `engine.completed` | 卡片刷新 | DAG 节点 completed | Engine 快照 | 报告章节来源 |
| `tool.called` | 通常不展示 raw | 工具列表 | 工具摘要 | 证据来源 |
| `rag.hit` | 只展示高相似案例 | 全量命中 | 可审核命中 | 高相似才引用 |
| `report.generated` | 报告入口出现 | 事件记录 | 报告审核入口 | 页面主数据 |

## 7. 组件命名建议

前端目录可按页面和共享模块拆分：

```text
src/
  pages/
    MobileSessionPage/
    DebugSessionConsolePage/
    AdminSessionPage/
    DiagnosisReportPage/
  components/
    session/
    slots/
    finance/
    location/
    category/
    report/
    trace/
  models/
    session.ts
    slots.ts
    trace.ts
    report.ts
```

共享组件不要直接读取 `private_debug` 数据。需要隐藏评分的组件放在 `trace/` 或 `admin/` 命名空间下，并通过权限守卫加载。

## 8. QA 对照

截图回归和人工 QA 至少覆盖：

- `mobile.session.live.shell`：普通用户不可见隐藏评分。
- `mobile.session.live.slotSheet`：房租、人工、毛利率等参数修改后，算账卡实时重算。
- `debug.session.console.engineDag`：Agent 路径与后端 trace 顺序一致。
- `admin.session.case.slots`：管理员修正参数后有 audit log。
- `report.session.result.finance`：报告里的盈亏平衡点公式和 `01-kill-line-engine.md` 一致。
- `report.session.result.evidence`：每条关键结论都有证据来源。
- `report.session.result.verdict`：地址好、用户靠谱、财务可行时，必须明确支持“可以做”。

