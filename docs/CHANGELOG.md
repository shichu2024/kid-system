# Changelog

本项目的所有显著变更记录于此。格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本遵循 [SemVer](https://semver.org/lang/zh-CN/)。

## [1.2.0] - 2026-09-08

### Added · SkillOpt 行为评测体系
- `bench/kidsys/` 四件套：DataLoader / EnvAdapter / rollout（chat 后端单轮 + fixture 内联 + skill 路由）/ scoring（routing/frontmatter/behavior/flow，hard=合取 soft=均值）
- golden cases：menu 22（安全滤网/分龄/护理/查重/降级/结构）+ journal 16（就医红线/异常识别/不编造/标签沉淀/触发）+ flow 6（J1-J6 闭环端到端，零容忍）+ unseen 8（泛化探针）
- 入口三件套：`run_eval.py` / `run_unseen_eval.py` / `repro_case.py`；configs 按 split 策略区分（3:1:1 vs 0:0:N）
- `.github/workflows/skillopt.yml`：nightly 非阻塞（schema 静态校验 + aggregate sanity 零 LLM + 可选真实评测 + artifact 30 天）
- `docs/dev/v1.2-skillopt-integration.md` 设计文档；铁律 deploy_skill: false

## [1.1.0] - 2026-09-08

### Added · knowledge/ 精选方法论知识层（zh + en）
- `books-guide.md`：12 本经典育儿书导读（核心方法/适用年龄/话术级技巧）+ 问题域速查表
- `communication-playbook.md`：五步沟通框架 + 10 个高频场景话术（✅/❌ 对照）+ 表达白/黑名单
- `picture-books.md`：0-12 岁分龄绘本库（经典书单/共读要点/六维度对应建议）
- `quick-rescue-games.md`：10 个狼狈场景 × 5 分钟救场游戏（零道具/家用常见物品）
- `problem-navigation.md`：四大类高频问题导航（L1 即时应对/L2 习惯策略/深入资源/红旗信号）
- `index.json`：knowledge 层检索索引

### Changed
- kid-learning：绘本选题接入 picture-books.md 书单（禁止捏造书名）
- kid-games：救场场景接入 quick-rescue-games.md，新增触发词
- kid-journal：行为困扰可引用 problem-navigation.md 给 L1 即时应对
- DESIGN.md §7 拆分为 references/（权威标准）与 knowledge/（方法论）两层规范

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
