# 00 技术总览

## 1. 总体目标

本系统把现有餐饮 skill 升级为一个完整的餐饮创业 Agent。系统不只生成话术，而是通过结构化数据、地图情报、财务公式、经营者能力评分和案例库，输出可解释的经营判断。

系统必须保持中立：不预设用户一定会失败，也不附和用户的乐观判断。数据支持能开就明确支持，数据不支持才给出整改、止损或维权建议。

核心输出有三类：

- 开店前：能不能开，怎么选址，选什么品类；能开时说明为什么能开。
- 已亏损：能不能救，怎么救，不能救怎么止损。
- 小赚：如何提升营业额和利润。

MVP 第一阶段锁定 `开店前：地址评定 + 选品 + 算账`。已亏损和小赚场景保留数据结构与模块接口，但不作为第一版闭环目标。

## 2. 总体架构

```text
前端 Web/小程序
  - Chat 对话
  - 算账表格
  - 坐标选择
  - 360 图片/视频上传
  - 诊断报告展示
        |
        v
后端 API
  - Session 管理
  - Intent Router
  - Dialogue State Machine
  - Tool Orchestrator
        |
        +--> KillLineEngine
        +--> FounderCapabilityEngine
        +--> LocationIntelligenceEngine
        +--> CategoryIntelligenceEngine
        +--> QuackRiskEngine
        +--> CaseMatchEngine
        +--> RAG Retriever
        |
        v
LLM Response Composer
  - 事实整理
  - 结论生成
  - 勇哥式表达
  - 安全边界过滤
```

## 3. 推荐技术栈

### 3.1 后端

MVP：

- Python 3.11+
- FastAPI
- Pydantic
- SQLite
- httpx
- pytest

生产版：

- Postgres
- Redis
- Celery/RQ
- Qdrant 或 Milvus
- 对象存储
- OpenTelemetry

### 3.2 前端

MVP：

- React + Vite
- TypeScript
- Tailwind 或轻量 CSS
- Web Geolocation API
- 文件上传
- SSE 或 fetch stream 消费后端流式事件

生产版：

- Next.js 或微信小程序
- 地图 SDK
- 视频压缩与断点上传
- 报告导出

### 3.3 模型与数据

- LLM：OpenAI-compatible provider adapter
- 多模态：可后置接入
- Embedding：中文向量模型或 OpenAI embedding
- 地图：高德、百度、腾讯位置服务适配器
- 行业数据：国家统计局、协会报告、美团指数、地方统计年鉴、自建案例库

## 4. 服务边界

| 服务 | 职责 |
|---|---|
| `agent-service` | 对话状态机、意图识别、模块编排 |
| `finance-service` | 开店前保本测算、目标回本日销、目标订单数、已开店斩杀线与正向通过条件 |
| `founder-service` | 经营者表达、执行、运营能力评分 |
| `location-service` | 坐标、地图 API、POI、热力、街景情报 |
| `category-service` | 品类库、地域适配、成本毛利参数 |
| `rag-service` | skill/corpus/cases 检索 |
| `report-service` | 诊断报告生成 |

MVP 可以放在同一个 FastAPI 项目里，但代码结构要按服务边界拆模块。

## 5. 核心数据流

### 5.1 已开店亏损诊断

```text
用户输入：我店亏钱，救救我
  -> IntentRouter 识别为 losing_store
  -> SlotFiller 收集财务槽位
  -> KillLineEngine 计算财务斩杀线
  -> FounderCapabilityEngine 继续追问能力
  -> LocationIntelligenceEngine 如果有坐标则查地址
  -> CaseMatchEngine 尝试匹配高相似案例
  -> DecisionEngine 合并结论
  -> ResponseComposer 输出勇哥式方案
```

### 5.2 开店前评估

```text
用户输入：想开一家店
  -> 识别 not_opened
  -> 收集品类、预算、资金来源、地址
  -> CategoryIntelligenceEngine 判断品类适配
  -> LocationIntelligenceEngine 判断地址
  -> KillLineEngine 预估日盈亏平衡点、目标回本日销、目标订单数
  -> FounderCapabilityEngine 判断用户是否适合创业
  -> 输出能不能开；能开给开店条件，不能开给修改建议或验证线
```

### 5.3 小赚但增长乏力

```text
用户输入：能赚钱但不多
  -> 识别 low_profit_store
  -> 财务表确认真实利润
  -> 拆增长公式
  -> 判断瓶颈：客流/进店/下单/客单/复购/产能
```

## 6. 状态机

基础状态：

```text
START
  -> INTENT_CLASSIFIED
  -> SLOT_FILLING
  -> TOOL_CALCULATION
  -> CAPABILITY_CHECK
  -> DECISION
  -> RESPONSE
  -> FOLLOW_UP
```

特殊分支：

- 命中加盟/总部/招商，插入 `QUACK_RISK_CHECK`
- 地址信息不足，插入 `LOCATION_CHECK`
- 用户情绪异常，插入 `SAFETY_ESCALATION`
- 用户要求详细方法论，进入 `DEEP_EXPLANATION`

## 7. 可解释性要求

每个正式结论必须能输出：

```json
{
  "verdict": "close|fix_7_days|fix_30_days|optimize|can_open|do_not_open",
  "finance": {},
  "founder_capability": {},
  "location": {},
  "category": {},
  "quack_risk": {},
  "matched_cases": [],
  "evidence": [],
  "next_actions": []
}
```

LLM 只负责组织语言，不负责无依据地产生结论。

## 8. QA 测试

### 8.1 单元测试

- 财务公式输入固定表格，输出应和直播表格一致。
- 经营者能力评分输入标准答案，输出分档稳定。
- 地址 POI 统计输入 mock 数据，输出地址评分稳定。
- 品类匹配输入城市/品类/商圈，输出合理分档。

### 8.2 集成测试

- 已亏损案例从用户输入到最终报告完整跑通。
- 开店前带坐标完整跑通。
- 加盟快招分支完整跑通。
- 小赚提升分支完整跑通。

### 8.3 对话测试

检查正式输出是否包含：

- 算账
- 结论
- 可选案例类比，高相似才引用
- 下一步动作
- 必要的风险边界

不能出现：

- 没算账就支持或否定
- 只说“看情况”
- 没有数字
- 强行引用不相干案例
- 承诺一定赚钱
