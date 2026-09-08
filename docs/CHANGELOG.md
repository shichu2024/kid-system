# Changelog

本项目的所有显著变更记录于此。格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本遵循 [SemVer](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2026-09-08

### v1.0 · 定版

#### Added
- `scripts/check-frontmatter.mjs` + `check-links.mjs` 数据与链接校验
- `.github/workflows/ci.yml`：JSON/Schema/技能清单一致性/frontmatter/死链/占位符六项检查
- `examples/demo-vault/`：糖糖（23 月龄·鸡蛋过敏）完整一周示例（档案 + 7 日志 + 3 方案 + 规则 + 周复盘 + 里程碑时间轴）
- 触发指令集文档、版本定版 1.0.0

### v0.6 · kid-rules + kid-review 技能
- kid-rules：自然语言规则解析、安全红线否决、逐条冲突校验（家长裁决 + conflicts-log）、全生命周期管理、复盘建议转规则
- kid-review：周/月复盘多维统计、四域里程碑对照（红旗提示儿保评估）、连续 3 天异常预警、建议一键转规则

### v0.5 · 方案生成技能（menu/learning/games/plan）
- kid-menu：安全滤网（过敏→窒息→规则）、分龄营养对齐、3 天窗口查重、每菜 5 要素 + 替换方案、四种调整模式
- kid-learning：六维度选题、基础/进阶双版本、基于日志反馈的难度升降、屏幕时间红线
- kid-games：games-library id 引用筛选、四维匹配 + 个性化评分、兴趣注入、护理模式限制
- kid-plan：聚合编排、批量 7 天滚动窗口、自然语言调整路由、adjustments 沉淀

### v0.4 · kid-journal 技能
- 五维度日志（饮食/运动/学习/睡眠/情绪健康），未提及标注「未记录」不编造
- 异常识别强制化（ill → 护理模式；就医红线置顶提示）、标签沉淀机械规则（N≥3 升级、证据日期）

### v0.3 · kid-init + kid-profile 技能
- kid-init：vault 初始化（幂等守门/模板铺设）+ 5 步聊天式建档
- kid-profile：五维度查看/修改、健康字段二次确认、影响提示矩阵、多孩切换

### v0.2 · 数据模型与内置知识库（zh+en）
- profile/journal schema（draft-07）、营养标准（0-12 岁 8 段）、辅食 5 阶段 30 食谱、四域里程碑 15 节点、睡眠 9 档 + 3 训练法、14 就医红线 + 窒息清单、50 游戏 × 5 域 × 6 场景、35 条知识索引
- templates/{zh,en} 8 类输出模板 ×2 语言

### v0.1 · 仓库骨架与设计文档（2026-09-08）

#### Added
- 仓库骨架：目录结构（skills/templates/references/docs/scripts/web/examples）
- `docs/DESIGN.md` 真相源：架构、vault 结构、数据模型、指令优先级、核心机制
- `docs/SKILLS_SPEC.md`：9 技能五段式规格
- `.claude-plugin/marketplace.json` + `plugin.json`：技能包清单
- 双语 `README.md`、`LICENSE`（MIT）、`.gitignore`
