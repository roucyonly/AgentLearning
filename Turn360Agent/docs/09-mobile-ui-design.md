# 09 移动端 UI 与流式交互设计

UI 图见：

- `mobile-ui-wireframe.svg`：移动端 User UI / Debug UI 概览。
- `debug-ui-wireframe.svg`：Debug UI 控制台详细设计。

## 1. 设计目标

移动端是本产品的主战场。用户很可能站在目标铺位门口、商场里、街边或自己店里，边看现场边问 Agent。

所有 UI 均以一个具体 `ConsultationSession` 为上下文。单轮对话只是 Session 内的事件，不能把参数、隐藏评分、报告和工具调用绑定到单轮消息上。

设计目标：

- 用户能在地址附近直接发起咨询。
- MVP 支持文字对话；语音入口预留，ASR 和 TTS 放到 P2。
- 支持流式输出，让用户看到 Agent 正在算账、查地址、补槽位、调用案例。
- 经营参数、地址评分、品类判断等实时更新。
- 对用户隐藏部分内部判断，例如经营者能力评分、表达能力评分、用户判断偏差评分，让用户自然表达。
- 前端可展示 Agent 调用路径；普通用户看到可理解的分析进度，开发/运营看到完整 Debug UI。

## 2. 产品界面分层

移动端分为两套 UI：

| UI | 使用者 | 目标 |
|---|---|---|
| User UI | 普通用户 | 提问、补参数、看可理解结论 |
| Debug UI | 开发/运营/质检 | 查看状态机、工具调用、隐藏评分、原始事件、模型输入输出 |

User UI 不展示会影响用户自然表达的内部标签。Debug UI 展示完整 Agent 运行路径。

## 3. User UI 总体结构

主界面采用“聊天 + 实时参数面板 + 地址上下文”的结构。

```text
┌────────────────────────────┐
│ 顶部地址条：当前铺位/定位/置信度 │
├────────────────────────────┤
│ 状态芯片：正在算账 / 查地图 / 等你补数 │
├────────────────────────────┤
│ Chat 流式对话区                │
│ - 用户文字输入                  │
│ - Agent 流式回复               │
│ - 关键卡片插入                 │
├────────────────────────────┤
│ 实时参数抽屉：经营/地址/品类       │
├────────────────────────────┤
│ 输入栏：文字 / 拍摄 / 定位 / 语音P2 │
└────────────────────────────┘
```

### 3.1 顶部地址条

内容：

- 当前城市/街道/店铺点位
- 距离当前位置
- 定位置信度
- “重新选点”按钮
- “我就在店门口”按钮

状态：

| 状态 | UI |
|---|---|
| 未定位 | “发定位，别凭感觉看位置” |
| 定位中 | 小型进度条 |
| 已定位未确认 | 地图小卡 + 确认按钮 |
| 已确认 | 地址名 + 坐标置信度 |
| GPS 漂移 | 提示手动拖动点位 |

### 3.2 状态芯片

显示 Agent 当前动作，降低流式等待焦虑。

示例：

- `识别意图`
- `收集房租`
- `计算日盈亏平衡点`
- `查询 500 米 POI`
- `比对用户自评`
- `检索相似案例`
- `生成结论`

用户只看到人话版，不显示内部 prompt 和隐藏评分。

### 3.3 Chat 流式对话区

对话区是主界面核心。

消息类型：

| 类型 | 展示 |
|---|---|
| 用户文字 | 普通气泡 |
| 用户语音 | P2 支持：语音条 + 转写文本 |
| Agent 流式文本 | 边生成边显示 |
| 参数确认卡 | 可编辑小卡 |
| 算账卡 | 表格卡 |
| 地址卡 | 地图/评分卡 |
| 下一步动作卡 | checklist |

Agent 流式文本应能插入卡片。例如：

```text
我先给你把账算出来。

[算账卡实时出现]

日盈亏平衡点是 1010。
你现在日销 800，保本达成率 79.2%。
```

### 3.4 实时参数抽屉

底部可上拉，默认收起，显示当前已识别参数。

分组：

- 经营参数
- 地址参数
- 品类参数
- 资金参数
- 证据与置信度

每个参数显示：

```text
字段名
当前值
来源
置信度
是否可编辑
最后更新时间
```

示例：

```text
房租元/月       6666     用户口述     低置信  可改
每月人工        8000     用户口述     低置信  可改
毛利率          55%      用户口述     低置信  可改
日盈亏平衡点    1010.06  系统计算     高置信  不可改
地址评分        78       地图+街景     中置信  不可改
```

## 4. 参数可见性设计

系统内部参数分为四类：

| 可见性 | User UI | Debug UI | 示例 |
|---|---|---|---|
| `public` | 展示 | 展示 | 房租、人工、毛利率、地址评分 |
| `editable` | 展示且可改 | 展示 | 日销、租金、支付方式 |
| `report_only` | 沟通过程隐藏，报告阶段展示 | 展示 | 经营能力建议 |
| `private_debug` | 不给用户展示 | 展示 | 表达能力分、用户判断偏差、疑似附和倾向 |

### 4.1 沟通过程需要隐藏的参数

这些参数在用户对话期间不展示，避免用户“表演”：

- 表达清晰度分
- 数据掌握分
- 调研执行力分
- 运营认知分
- 用户位置判断偏差分
- 用户是否附和 Agent
- 用户是否只停留在口头

可以在最终报告中转化为温和表达：

```text
你现在最大短板是数据记录和连续执行。
如果要救店，先用 7 天证明你能每天固定完成动作。
```

不要在对话中直接展示：

```text
你的经营者能力分 37。
```

## 5. 实时参数更新机制

前端维护两个模型：

```typescript
type PublicSessionModel = {
  visibleSlots: Slot[];
  visibleCards: Card[];
  agentPath: PublicAgentStep[];
  currentVerdictPreview?: VerdictPreview;
};

type DebugSessionModel = {
  allSlots: Slot[];
  hiddenScores: HiddenScore[];
  rawEvents: StreamEvent[];
  toolCalls: ToolCall[];
  ragHits: RagHit[];
  llmRuns: LlmRun[];
};
```

后端通过流式事件持续 patch：

```text
slot.patch
card.patch
agent.path.patch
tool.started
tool.completed
hidden.patch
message.delta
message.done
```

User UI 只消费允许展示的事件。Debug UI 消费全部事件。

## 6. 流式协议

建议使用 SSE 作为 MVP。ASR/TTS 不进入 MVP；P2 需要语音实时双向时再升级 WebSocket。

### 6.1 SSE 接口

```http
POST /api/chat/stream
Accept: text/event-stream
```

请求：

```json
{
  "session_id": "uuid",
  "message": "我现在就在这个铺子门口，房租 8000",
  "input_mode": "text",
  "location": {
    "longitude": 116.397,
    "latitude": 39.908,
    "accuracy_m": 18
  },
  "attachments": []
}
```

### 6.2 事件类型

#### `message.delta`

```json
{
  "type": "message.delta",
  "text": "先别急，我先把房租和人工算进去。"
}
```

#### `slot.patch`

```json
{
  "type": "slot.patch",
  "slot": {
    "key": "monthly_rent",
    "label": "房租元/月",
    "value": 8000,
    "source": "user_text",
    "confidence": 0.7,
    "visibility": "editable"
  }
}
```

#### `card.patch`

```json
{
  "type": "card.patch",
  "card": {
    "id": "finance_card",
    "kind": "finance_table",
    "patch": {
      "daily_breakeven": 1010.06,
      "breakeven_achievement_rate": 0.792
    }
  }
}
```

#### `agent.path.patch`

User UI 版本：

```json
{
  "type": "agent.path.patch",
  "step": {
    "id": "finance_calc",
    "label": "计算盈亏平衡点",
    "status": "running"
  },
  "visibility": "public"
}
```

Debug UI 版本：

```json
{
  "type": "agent.path.patch",
  "step": {
    "id": "tool.kill_line",
    "engine": "KillLineEngine",
    "input_ref": "payload_123",
    "status": "running",
    "started_at": "2026-05-25T00:00:00+08:00"
  },
  "visibility": "debug"
}
```

#### `hidden.patch`

只给 Debug UI。

```json
{
  "type": "hidden.patch",
  "key": "founder_capability.execution_score",
  "value": 4,
  "reason": "用户只说准备做账号，没有实际发布记录",
  "visibility": "private_debug"
}
```

#### `tool.completed`

```json
{
  "type": "tool.completed",
  "tool": "LocationIntelligenceEngine",
  "duration_ms": 1240,
  "summary": "500 米内同品类 28 家，50 米内 1 家大牌",
  "visibility": "debug"
}
```

## 7. 语音交互设计（P2）

语音能力不进入 MVP。MVP 只预留入口和数据结构，不接 ASR/TTS 模型，不做语音测试作为上线阻断项。

### 7.1 输入方式

P2 底部输入栏包含：

- 按住说话
- 点击键盘
- 拍门头
- 发定位
- 更多参数

语音状态：

| 状态 | UI |
|---|---|
| idle | 麦克风按钮 |
| listening | 声波动画 + 松开发送 |
| transcribing | “正在转文字” |
| confirm | 展示转写文本，可编辑 |
| sent | 进入流式回复 |

### 7.2 语音转写策略

P2 第一版：

- 录音结束后上传
- 后端 ASR 转写
- 用户可点开修正

进阶：

- WebSocket 实时 ASR
- partial transcript 实时显示
- 用户打断 Agent

### 7.3 语音回复

TTS 放到 P2，且默认不自动朗读，避免公共场景尴尬。

可选：

- 用户点击“听回复”
- 只朗读结论和下一步动作
- 长报告不自动朗读

## 8. Agent 调用路径展示

### 8.1 User UI 分析路径

用户看到的是可理解路径：

```text
已识别：开店前地址评估
正在收集：房租、人工、毛利率
已完成：建店成本计算
正在查询：周边商铺
已完成：竞品密度分析
正在生成：结论和下一步动作
```

展示为顶部横向 stepper 或聊天中的折叠小条。

### 8.2 Debug UI 调用路径

Debug UI 展示完整 DAG：

```text
IntentRouter
  -> SlotFiller
  -> KillLineEngine
  -> LocationIntelligenceEngine
      -> AmapProvider.searchAround
      -> PoiNormalizer
      -> CompetitorScorer
  -> FounderCapabilityEngine
      -> LLMExtractor
      -> RuleScorer
  -> CaseMatchEngine
  -> ResponseComposer
```

每个节点展示：

- 输入
- 输出
- 耗时
- 错误
- 置信度
- 是否影响最终结论

## 9. User UI 核心页面

### 9.1 地址现场模式

入口文案：

```text
你在铺子附近？
发定位，我先看周边，再让你 360 度转一圈。
```

主操作：

- “我就在店门口”
- “地图选点”
- “拍门头”
- “开始问”

### 9.2 会话模式

适合持续问答。

布局：

- 顶部地址条
- 中部聊天流
- 底部输入
- 可上拉参数抽屉

### 9.3 参数校正模式

用户点开某个参数后进入：

```text
房租元/月
当前值：8000
来源：你刚才说的
置信度：低

[输入新值]
[保存]
```

### 9.4 报告模式

展示最终结论：

- 可以做 / 可整改 / 不建议 / 建议止损
- 财务表
- 地址表
- 品类表
- 经营者执行建议
- 相似案例，高相似才展示
- 下一步 checklist

报告阶段可以展示部分 `report_only` 参数，但仍不展示原始隐藏分数。

## 10. Debug UI 设计

Debug UI 可以是移动端隐藏入口，也可以是 Web 控制台。

建议 Web 控制台优先。

### 10.1 页面布局

```text
┌──────────────────────┬──────────────────────┐
│ 左：会话与事件流       │ 右：当前 Session State │
├──────────────────────┼──────────────────────┤
│ Agent DAG            │ Slots / Hidden Scores │
├──────────────────────┼──────────────────────┤
│ Tool Calls           │ RAG Hits / LLM Runs   │
└──────────────────────┴──────────────────────┘
```

### 10.2 Debug 内容

- 原始 stream events
- 状态机当前节点
- 所有 slot，包括隐藏 slot
- 工具调用输入/输出
- 地图 API 原始返回摘要
- RAG 命中文档
- LLM 抽取结果
- LLM 最终回复
- 安全过滤结果
- 延迟统计

### 10.3 Debug 权限

Debug UI 只允许：

- 开发环境
- 内部运营账号
- 质检账号

用户端不得通过前端参数开启 Debug UI。

## 11. 关键组件清单

### 11.1 User UI 组件

| 组件 | 说明 |
|---|---|
| `LocationHeader` | 当前地址、定位状态、重选点 |
| `AgentStepBar` | 用户可见分析路径 |
| `ChatStream` | 流式对话 |
| `VoiceInputButton` | P2：按住说话 |
| `AttachmentBar` | 拍照、视频、定位 |
| `LiveParameterSheet` | 实时参数抽屉 |
| `FinanceCard` | 算账表 |
| `LocationScoreCard` | 地址评分 |
| `CategoryFitCard` | 品类适配 |
| `VerdictCard` | 最终结论 |
| `ActionChecklist` | 下一步动作 |

### 11.2 Debug UI 组件

| 组件 | 说明 |
|---|---|
| `RawEventStream` | 原始 SSE/WebSocket 事件 |
| `AgentDagViewer` | Agent 调用路径 |
| `SlotInspector` | 全量参数 |
| `HiddenScorePanel` | 隐藏评分 |
| `ToolCallLog` | 工具调用日志 |
| `RagHitPanel` | 检索命中 |
| `LlmRunPanel` | 模型调用 |
| `LatencyPanel` | 耗时统计 |

## 12. 可见参数与隐藏参数示例

### 12.1 用户可见

```json
[
  {"key": "monthly_rent", "label": "房租元/月", "visibility": "editable"},
  {"key": "monthly_labor", "label": "每月人工", "visibility": "editable"},
  {"key": "gross_margin", "label": "毛利率", "visibility": "editable"},
  {"key": "daily_breakeven", "label": "日盈亏平衡点", "visibility": "public"},
  {"key": "location_score", "label": "地址评分", "visibility": "public"},
  {"key": "category_fit", "label": "品类适配", "visibility": "public"}
]
```

### 12.2 沟通过程隐藏

```json
[
  {"key": "founder.clarity_score", "visibility": "private_debug"},
  {"key": "founder.execution_score", "visibility": "private_debug"},
  {"key": "founder.discipline_score", "visibility": "private_debug"},
  {"key": "location.user_judgment_bias", "visibility": "private_debug"},
  {"key": "conversation.user_performance_risk", "visibility": "private_debug"}
]
```

## 13. QA 测试

### 13.1 流式响应测试

- Agent 文本能逐 token 或逐句显示。
- 工具调用期间状态芯片变化。
- 参数卡在工具完成后实时更新。
- 网络中断后可恢复或重新请求。

### 13.2 语音测试（P2）

- 录音权限被拒绝时可回退文字。
- 转写错误时用户可编辑。
- 背景噪音下不应自动提交空文本。
- 语音和定位可以同时携带到请求。

MVP 不跑本节作为阻断测试。

### 13.3 参数可见性测试

- `private_debug` 字段不得出现在 User UI。
- `report_only` 字段不得在沟通过程展示。
- Debug UI 可以查看完整隐藏评分。
- 参数修改后应重新触发相关 Engine。

### 13.4 地址现场测试

- 定位成功后能确认店铺点位。
- 用户站在店门口时可一键进入 360 拍摄引导。
- 地图 API 失败时 User UI 显示低置信，不编造结果。

### 13.5 Agent 路径测试

- User UI 展示人话版路径。
- Debug UI 展示完整 DAG。
- 每个工具节点有 started/completed/error 状态。
- 最终报告能追溯影响结论的关键节点。
