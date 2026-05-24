# 10 Session、用户角色、管理员与报告设计

## 1. 核心修正

本产品的 UI 和 Debug UI 都应围绕一个具体 `Session` 展开，而不是围绕一轮对话。

一轮对话只是 `Session` 中的一个事件。一个 `Session` 是一次完整咨询案件，通常绑定一个用户、一个店铺或目标铺位、一组经营参数、一组地址数据、一组工具调用轨迹，以及最终报告。

```text
User
  -> StoreProfile / TargetLocation
      -> ConsultationSession
          -> Turns
          -> Attachments
          -> Locations
          -> Slots
          -> EngineSnapshots
          -> ToolCalls
          -> Reports
          -> AuditLogs
```

## 2. 核心对象

### 2.1 User

用户身份。

```typescript
type User = {
  id: string;
  phone?: string;
  displayName?: string;
  role: "end_user" | "admin" | "qa_reviewer" | "developer" | "super_admin";
  createdAt: string;
  lastActiveAt: string;
};
```

### 2.2 StoreProfile

用户自己的已开店档案，或准备开的目标店。

```typescript
type StoreProfile = {
  id: string;
  ownerUserId: string;
  name?: string;
  status: "not_opened" | "opened_losing" | "opened_low_profit" | "opened_healthy" | "closed";
  category?: string;
  city?: string;
  addressText?: string;
  location?: GeoPoint;
  createdAt: string;
};
```

### 2.3 ConsultationSession

一次完整咨询。

```typescript
type ConsultationSession = {
  id: string;
  ownerUserId: string;
  storeProfileId?: string;
  scenario: "pre_opening" | "losing_store" | "low_profit_growth" | "quack_risk" | "location_eval";
  status: "active" | "waiting_user" | "tools_running" | "report_ready" | "closed" | "needs_admin_review";
  currentVerdict?: "can_open" | "can_continue" | "fix_7_days" | "fix_30_days" | "do_not_open" | "close_or_stop_loss" | "insufficient_data";
  publicSummary?: string;
  riskLevel?: "green" | "yellow" | "orange" | "red" | "black";
  createdAt: string;
  updatedAt: string;
};
```

### 2.4 Turn

一次用户或 Agent 消息。

```typescript
type Turn = {
  id: string;
  sessionId: string;
  actor: "user" | "agent" | "admin";
  inputMode?: "text" | "voice" | "image" | "video" | "system";
  content: string;
  transcript?: string;
  createdAt: string;
};
```

### 2.5 Slot

Session 级参数，而不是单轮消息级参数。

```typescript
type Slot = {
  key: string;
  label: string;
  value: unknown;
  source: "user_text" | "user_voice" | "admin_edit" | "tool_result" | "map_api" | "vision" | "llm_extract";
  confidence: number;
  visibility: "public" | "editable" | "report_only" | "private_debug";
  version: number;
  updatedAt: string;
};
```

## 3. 用户区分

### 3.1 End User

普通用户。

能做：

- 创建自己的 Session。
- 查看自己的历史 Session。
- 提供文字、图片、视频、定位。P2 支持语音。
- 修改公开参数，如房租、人工、毛利率。
- 查看公开分析进度和最终报告。
- 导出自己的报告。

不能做：

- 查看隐藏评分。
- 查看原始工具调用 payload。
- 查看 LLM prompt。
- 修改系统结论。
- 查看其他用户 Session。

### 3.2 Admin

管理员是内部运营/顾问角色，不是普通用户。

能做：

- 查看被分配或权限范围内的 Session。
- 查看 User UI 看到的内容。
- 查看 Debug UI 的隐藏评分、工具调用、RAG 命中、Agent 路径。
- 给 Session 打标签，例如 `needs_evidence`、`high_risk`、`report_reviewed`。
- 向用户发起补充材料请求。
- 写内部备注。
- 审核最终报告是否满足“有理有据、可执行”。
- 对明显错误的 slot 发起修正，但必须保留审计记录。

不能做：

- 静默篡改用户提交事实。
- 删除原始会话和证据。
- 绕过系统生成无依据结论。
- 向用户展示隐藏评分原始分。
- 冒充用户发言。

### 3.3 QA Reviewer

质检角色。

能做：

- 查看抽样 Session。
- 评估输出是否中立、是否有证据、是否安全。
- 标记 bad case。

不能做：

- 直接干预用户会话。
- 修改参数或结论。

### 3.4 Developer

开发角色。

能做：

- 查看完整 trace。
- 查看工具错误、延迟、模型输入输出。
- 导出调试包。

不能做：

- 查看不必要的用户敏感信息，生产环境需脱敏。
- 直接给用户发消息。

## 4. Admin 权限矩阵

| 能力 | End User | Admin | QA | Developer |
|---|---|---|---|---|
| 查看自己的 Session | 是 | 否 | 否 | 否 |
| 查看分配的 Session | 否 | 是 | 是 | 是 |
| 查看公开参数 | 是 | 是 | 是 | 是 |
| 查看隐藏评分 | 否 | 是 | 是 | 是 |
| 查看工具调用 | 否 | 是 | 是 | 是 |
| 查看 LLM prompt/response | 否 | 受限 | 是 | 是 |
| 修改用户参数 | 自己可改 | 可发起修正 | 否 | 否 |
| 写内部备注 | 否 | 是 | 是 | 是 |
| 审核报告 | 否 | 是 | 是 | 否 |
| 导出用户报告 | 是 | 是 | 否 | 否 |
| 导出 trace | 否 | 受限 | 是 | 是 |

## 5. Admin Session UI

UI 图：`session-admin-ui-wireframe.svg`

编码关联见：`11-ui-svg-coding-map.md` 中的 `admin.session.case.*`。

管理员看的不是“这一轮问答”，而是一个完整 Session 档案。

核心区域：

- 左侧：用户与 Session 列表。
- 中部：Session 档案、时间线、参数、证据。
- 右侧：Admin 操作、隐藏评分、报告审核。

管理员核心任务：

1. 确认这个 Session 属于哪个用户、哪个店、哪个地址。
2. 看用户提供了什么证据。
3. 看 Agent 调用了哪些 Engine。
4. 看隐藏评分和工具结果是否支持最终结论。
5. 审核报告是否有理有据、能不能发给用户。

## 6. 最终报告设计

UI 图：`report-ui-wireframe.svg`

编码关联见：`11-ui-svg-coding-map.md` 中的 `report.session.result.*`。

报告不是聊天总结，而是对当前 Session 的结构化诊断。

必须包含：

1. 当前状况摘要。
2. 最终结论。
3. 财务逐条分析。
4. 地址逐条分析。
5. 品类与地域适配分析。
6. 经营者执行能力分析，用户侧只展示建议，不展示原始分。
7. 风险与证据。
8. 后续行动方案。
9. 验证指标和止损线。
10. 附录：数据来源、用户补充材料、地图/案例依据。

## 7. 报告结构

```typescript
type DiagnosisReport = {
  id: string;
  sessionId: string;
  ownerUserId: string;
  generatedAt: string;
  verdict: ReportVerdict;
  confidence: number;
  executiveSummary: string;
  currentSituation: SituationSummary;
  sections: ReportSection[];
  actionPlan: ActionPlan;
  stopLossLine?: StopLossLine;
  evidence: EvidenceItem[];
  caveats: string[];
};
```

### 7.1 最终结论

可选值：

- `可以开`
- `可以继续做`
- `先 7 天验证`
- `30 天整改`
- `不建议开`
- `建议止损`
- `证据不足，暂不下结论`

结论必须配理由：

```text
结论：可以开，但只按轻资产版本做。

理由：
1. 地址数据支持：500 米内客流源明确，同品类不过密。
2. 财务模型支持：日盈亏平衡点 1010，目标日销 1800 才值得做。
3. 用户能力支持：有同品类经验，能讲清执行动作。
4. 风险可控：自有资金，没有抵押和高额加盟费。
```

## 8. 后续建议格式

建议必须是可执行的，不写空话。

### 8.1 立即动作

用户今天就能做：

- 去铺位门口蹲点，记录经过人数、目标客群人数、进店人数。
- 选附近 3 家相似店，观察进店人数；能拿小票号就用首尾小票号估算单量。
- 办公楼看早高峰、午餐、晚高峰进出人数；小区看晚间亮灯、出入口、外卖快递和停车。
- 拍门头、左右、对街各一张。
- 问 3 家相邻店铺：工作日和周末峰值。
- 把租金付款方式谈成押一付三。

### 8.2 7 天验证

用于短期验证：

- 每天同一时间蹲点。
- 记录 3 个核心数据。
- 做 1 次小范围菜单测试。
- 不装修、不签长约、不交大额加盟费。

### 8.3 30 天整改

用于已开店可救场景：

- 第 1 周：校准菜单与价格。
- 第 2 周：门头和套餐测试。
- 第 3 周：外卖 SKU 与团购。
- 第 4 周：复盘数据，达不到止损线就停。

### 8.4 止损线

必须量化：

```text
如果连续 14 天日销低于 1200，且没有稳定增长，就停止加投。
如果 30 天内保本达成率仍低于 90%，开始转让止损。
如果需要再投入超过 2 万才能继续试，先停。
```

## 9. 报告可见性

报告中可以展示：

- 财务结果
- 地址评分
- 品类适配
- 行动建议
- 用户执行建议
- 证据与数据来源

报告中不展示：

- 原始隐藏评分
- LLM prompt
- 工具 raw payload
- 管理员内部备注
- 用户“被评估”的敏感标签

隐藏评分应转译为建议。

例如：

```text
内部：execution_score = 34
用户报告：目前你最大问题不是产品，而是动作没有连续记录。后续只给 7 天验证，不建议直接 30 天大投入整改。
```

## 10. QA 测试

### 10.1 Session 范围测试

- 一次 Session 多轮对话后，参数应持续累计。
- 用户修正房租后，财务表和报告应重算。
- 新开 Session 不应污染旧 Session。
- 同一用户多个店铺应分开建档。

### 10.2 权限测试

- End User 不能访问隐藏评分。
- Admin 能看到隐藏评分和工具调用。
- Admin 修改 slot 必须生成 audit log。
- QA 不能给用户发消息。
- Developer 生产环境导出 trace 必须脱敏。

### 10.3 报告质量测试

报告必须：

- 有最终结论。
- 有当前状况摘要。
- 有逐条分析。
- 有证据来源。
- 有可执行建议。
- 有止损线或验证指标。

报告不得：

- 只写泛泛建议。
- 没有数字。
- 没有依据。
- 把隐藏评分原样展示给用户。
