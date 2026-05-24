# 技术开发文档索引

这套文档用于指导餐饮创业 Agent 的产品化开发。阅读顺序建议如下：

1. `../project.md`：项目总方案、目标用户、模块划分和里程碑。
2. `00-technical-overview.md`：总体架构、服务边界、核心数据流。
3. `01-kill-line-engine.md`：盈亏与斩杀线财务公式、建店成本、日盈亏平衡点、回本周期和正向通过条件。
4. `02-founder-capability-engine.md`：经营者表达能力、执行力、运营认知和复盘能力评分。
5. `03-location-intelligence-engine.md`：坐标、地图 API、POI、热力、街景和用户判断力校验。
6. `04-category-intelligence-engine.md`：刚需/轻社交/社交品类、产品大类、地域适配和数据源。
7. `05-dialogue-style-agent.md`：意图路由、对话状态机、勇哥式表达和安全边界。
8. `06-data-rag-and-sources.md`：skill/corpus/cases 入库、案例结构化、RAG 与信源可信度。
9. `07-api-and-frontend.md`：API、前端页面、算账表、地址评估和报告展示。
10. `08-qa-test-plan.md`：单元、集成、对话、安全、前端和回归测试计划。
11. `09-mobile-ui-design.md`：移动端 UI、流式交互、文字输入、语音 P2 预留、实时参数、User UI 和 Debug UI。
12. `mobile-ui-wireframe.svg`：移动端 User UI / Debug UI 线框图。
13. `debug-ui-wireframe.svg`：Debug UI 控制台线框图。
14. `10-session-admin-report-design.md`：Session 档案、用户区分、管理员角色、报告结构。
15. `session-admin-ui-wireframe.svg`：管理员 Session 控制台线框图。
16. `report-ui-wireframe.svg`：用户最终诊断报告 UI 图。
17. `11-ui-svg-coding-map.md`：UI、SVG 原型、前端路由、组件和流式事件的编码关联表。

开发时建议先实现：

- `KillLineEngine`
- `FounderCapabilityEngine`
- `CategoryIntelligenceEngine` 的基础品类库
- `DialogueStyleAgent` 的三条主流程

然后再接入真实地图 API 和多模态街景识别。

重要原则：这是中立决策项目，不是泼冷水项目。Agent 不附和用户，也不预设劝退；地址好、用户靠谱、账算得过来时，必须明确支持用户可以做。
