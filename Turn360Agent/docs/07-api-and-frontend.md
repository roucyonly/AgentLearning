# 07 API 与前端交互

## 1. 模块目标

定义前后端接口和核心页面交互，使 Agent 能完成对话、算账、坐标评估、街景上传和报告展示。移动端详细交互见 `09-mobile-ui-design.md`。

## 2. 前端页面

### 2.1 Chat 主页面

功能：

- 文本输入
- 图片/视频上传
- 定位按钮
- 算账表格卡片
- 地址评分卡片
- 品类推荐卡片
- 诊断结论卡片

### 2.2 算账表格

复刻勇哥直播间表格的信息结构：

```text
这家餐饮店能做吗？

项目                 金额
面积(平)
房租元/月
支付方式(月)
押金
转让费/中介费
加盟/技术学习费
装修/广告
设备
首批物料

项目                 金额
每月人工
水/电/杂费
固定运营费用
阶段性投放费用
毛利率
有效毛利率

建店成本
每日固定成本
日盈亏平衡点
```

扩展展示：

- 当前日营业额
- 当前月净利润
- 保本达成率
- 回本周期
- 目标 12 月回本日销
- 现金撑店月数

### 2.3 地址评估页面

流程：

```text
1. 获取定位
2. 地图上确认铺位
3. 输入目标品类、租金、楼层
4. 用户自评周边
5. 上传门头/左右/对街/视频
6. 展示地址报告
```

### 2.4 报告页面

内容：

- 总结论
- 财务表
- 经营者能力评分
- 地址评分
- 品类适配
- 相似案例，高相似才展示
- 下一步动作
- 归零计算器或整改计划

## 3. 后端 API

### 3.1 创建会话

```http
POST /api/sessions
```

响应：

```json
{
  "session_id": "uuid",
  "created_at": "2026-05-25T00:00:00+08:00"
}
```

### 3.2 对话

```http
POST /api/chat
```

请求：

```json
{
  "session_id": "uuid",
  "message": "我开了家奶茶店亏钱",
  "attachments": [],
  "location": null
}
```

### 3.2.1 流式对话

```http
POST /api/chat/stream
Accept: text/event-stream
```

用于移动端主对话。后端以 SSE 发送：

- `message.delta`
- `slot.patch`
- `card.patch`
- `agent.path.patch`
- `tool.started`
- `tool.completed`
- `hidden.patch`
- `message.done`

User UI 只展示 `visibility=public/editable/report_only` 的安全事件。Debug UI 可展示完整事件。

响应：

```json
{
  "reply": "先别讲感受，讲数字...",
  "state": "slot_filling",
  "required_slots": ["daily_revenue", "monthly_rent"],
  "cards": []
}
```

### 3.3 财务计算

```http
POST /api/tools/kill-line
```

请求：

```json
{
  "monthly_rent": 6666,
  "rent_payment_months": 6,
  "deposit": 6666,
  "transfer_fee": 0,
  "franchise_or_training_fee": 0,
  "decoration_and_ads": 30000,
  "equipment": 0,
  "first_batch_material": 5000,
  "monthly_labor": 8000,
  "monthly_utilities": 2000,
  "monthly_fixed_operation_cost": 1500,
  "monthly_campaign_cost": 3000,
  "gross_margin": 0.55,
  "effective_gross_margin": 0.48,
  "platform_commission_rate": 0.18,
  "daily_delivery_subsidy": 80,
  "daily_packaging_cost": 60,
  "daily_marketing_discount": 120,
  "current_daily_revenue": 800
}
```

响应：

```json
{
  "build_cost": 81662,
  "daily_fixed_cost": 555.53,
  "daily_breakeven": 1010.06,
  "effective_gross_margin": 0.48,
  "breakeven_achievement_rate": 0.792,
  "finance_status": "orange",
  "risk_flags": []
}
```

### 3.4 地址评估

```http
POST /api/location/evaluate
```

请求：

```json
{
  "session_id": "uuid",
  "longitude": 116.397,
  "latitude": 39.908,
  "city": "北京",
  "target_category": "奶茶",
  "monthly_rent": 12000,
  "floor": "一楼",
  "user_self_assessment": {
    "same_category_count_500m": 3,
    "nearby_big_brands": "没有",
    "customer_source": "学生"
  },
  "media_ids": []
}
```

响应：

```json
{
  "address_score": 42,
  "address_level": "high_risk",
  "founder_location_judgment_score": 35,
  "contradictions": [
    "用户称 500 米内同品类约 3 家，地图检索为 28 家",
    "用户称无大牌，50 米内检索到蜜雪冰城"
  ],
  "risk_flags": ["big_brand_nearby", "high_competition"],
  "recommended_action": "do_not_open"
}
```

### 3.5 文件上传

```http
POST /api/media/upload
```

支持：

- jpg
- png
- mp4
- mov

响应：

```json
{
  "media_id": "uuid",
  "type": "video",
  "status": "uploaded"
}
```

### 3.6 报告生成

```http
POST /api/reports
```

请求：

```json
{
  "session_id": "uuid",
  "report_type": "diagnosis"
}
```

响应：

```json
{
  "report_id": "uuid",
  "summary": "做不了，建议止损",
  "sections": []
}
```

## 4. 前端状态

```typescript
type AgentState =
  | "start"
  | "intent_classified"
  | "slot_filling"
  | "tool_calculation"
  | "location_check"
  | "capability_check"
  | "decision"
  | "report";
```

## 5. 错误处理

### 5.1 定位失败

提示：

```text
定位没拿到。你可以手动在地图上选点。
但不发位置，我只能低置信判断。
```

### 5.2 地图 API 失败

处理：

- 前端显示“地图数据暂不可用”
- 后端使用缓存或 mock
- 不编造结果
- 继续要求用户上传街景

### 5.3 上传失败

处理：

- 支持重试
- 支持压缩后上传
- 支持先文字评估，但标记低置信

## 6. QA 测试

### 6.1 API 单元测试

- `/api/tools/kill-line` 表格公式正确。
- `/api/location/evaluate` 能处理 mock 地图数据。
- `/api/chat` 缺槽位时返回 required_slots。
- `/api/media/upload` 限制文件类型。

### 6.2 前端交互测试

- 用户能创建会话。
- 用户能输入文字并获得追问。
- 用户能填写算账表。
- 用户能确认地图点位。
- 用户能上传图片/视频。
- 报告卡片能正常展示。

### 6.3 异常测试

- 禁用定位。
- API key 缺失。
- 上传超大视频。
- 用户反复不给数字。
- 后端返回低置信数据。
