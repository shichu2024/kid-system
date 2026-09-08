# kid-system 设计文档（真相源 · Single Source of Truth）

> 版本：v0.1 ｜ 状态：随阶段演进
> 本文是 kid-system 所有技能、模板、知识库的唯一设计真相源。SKILL.md 通过 frontmatter `source_of_truth` 反向引用本文章节号。

---

## 1. 项目愿景

### 1.1 定位

面向 **0-12 岁儿童家长**的全链路科学育儿实践管理技能包。以儿童个性化成长档案为核心，构建完整闭环：

```
档案初始化 → 知识规则注入 → 每日成长记录 → 个性化方案生成 → 数据沉淀迭代
```

### 1.2 设计哲学（五条原则）

1. **安全绝对优先** — 过敏/禁忌过滤永不妥协；3 岁以下方案禁止细小零件/整颗坚果/果冻；不做医疗诊断
2. **知识/数据分离** — 内置知识库（`references/`）随技能包更新；用户数据（vault）永不被技能覆盖
3. **机械可判定** — 关键流程用可机检条件（文件存在、字段齐全、日期格式）约束，禁止语义绕过
4. **闭环进化** — 日志沉淀标签 → 更新档案 → 影响推荐 → 复盘产出建议 → 建议转规则
5. **可落地输出** — 食材精确到克、步骤按序、道具家用常见；禁止空泛模板化输出

### 1.3 反向边界（不做什么）

- 不做医疗诊断、处方、用药剂量建议（就医指征提示除外）
- 不采集儿童姓名、照片、住址等敏感个人信息（用昵称 + 系统 ID）
- 不评判家长养育方式；不制造育儿焦虑
- 不超出育儿范畴回答无关问题

---

## 2. 总体架构

```
┌─────────────────────────── 技能包（随版本更新） ───────────────────────────┐
│  skills/9 技能        templates/{zh,en} 8 类      references/ 知识库 8 件   │
│  kid-init / profile / rules / journal /            营养标准 / 辅食分龄 /     │
│  menu / learning / games / plan / review           里程碑 / 睡眠 / 安全 /   │
│                                                    游戏库 / 知识索引        │
└───────────────────────────────┬───────────────────────────────────────────┘
                                │ 读写（技能运行时）
┌───────────────────────────────▼───────────────────────────────────────────┐
│  用户数据 vault（用户目录，技能升级永不覆盖）                                 │
│  00_profiles/  01_journal/  02_plans/  03_rules/  04_reviews/  99_system/   │
└────────────────────────────────────────────────────────────────────────────┘
                                │ 只读展示
                    web/dashboard.html 轻量仪表盘
```

三层职责：
- **技能层**：流程编排、个性化推理、安全过滤、输出生成
- **数据层（vault）**：档案、日志、方案、规则、复盘——闭环的全部状态
- **知识层（references）**：分龄权威数据，静态只读，所有推荐的事实依据

---

## 3. 用户数据 vault 结构

kid-init 在用户指定目录（默认 CWD）创建：

```
<vault>/
├── 00_profiles/
│   └── <child-id>/                 # child-id = 昵称拼音或 kebab-case 标识
│       ├── profile.md              # 五维度档案（frontmatter + 正文）
│       └── tags.md                 # 自动沉淀的动态标签（饮食偏好/能力/兴趣）
├── 01_journal/
│   └── <child-id>/
│       └── YYYY-MM/
│           └── YYYY-MM-DD.md       # 每日成长日志（按儿童分目录，v1.3）
├── 02_plans/
│   └── <child-id>/
│       └── YYYY-MM-DD.md           # 每日方案（菜单/学习/游戏三节合一单文件，v1.3）
├── 03_rules/
│   ├── rules.md                    # 家长规则库（全局共享，优先级排序）
│   └── conflicts-log.md            # 冲突处理记录
├── 04_reviews/
│   └── <child-id>/
│       ├── weekly/YYYY-Www.md      # 周复盘（v1.3）
│       ├── monthly/YYYY-MM.md      # 月复盘（v1.3）
│       └── milestones.md           # 该儿童的发育里程碑时间轴（v1.3）
├── 99_system/
│   ├── kid.config.yaml             # 全局配置
│   └── templates/{zh,en}/          # 输出模板副本（init 铺设）
└── .kid-initialized                # 初始化标记
```

### 3.1 kid.config.yaml

```yaml
language: zh                # zh / en，驱动模板选择与生成内容语言
active_child: <child-id>    # 当前活跃儿童（多孩家庭切换）
children: [<child-id>]      # 全部儿童 ID 列表
initialized_at: YYYY-MM-DD
skill_version: v1.3.0
review:                     # kid-review 量化阈值（v1.3，可省略走默认值）
  min_coverage: 0.5         # 数据覆盖率下限，低于则报告降级为「初步观察版」
  warning_days: 3           # 连续异常天数达到该值必须触发预警（机械判定）
```

### 3.3 多儿童路径规则（v1.3）

所有**按儿童归属**的数据（日志/方案/复盘）一律带 `<child-id>` 目录层，单双儿童一致——添加二孩时不迁移既有文件：

- `01_journal/<child-id>/YYYY-MM/YYYY-MM-DD.md`
- `02_plans/<child-id>/YYYY-MM-DD.md`（**三节合一单文件**，禁止按模块拆分文件或加 menu-/learning- 前缀）
- `04_reviews/<child-id>/{weekly|monthly|milestones.md}`

全局共享数据不带儿童层：`00_profiles/`（自带 child-id 子目录）、`03_rules/`（规则全家适用）、`99_system/`。

### 3.2 .kid-initialized 标记

```yaml
schema_version: 1
skill_version: v1.0.0
language: zh
initialized_at: YYYY-MM-DD
```

幂等守门：存在该标记或 `99_system/` 目录时，init 不得覆盖任何文件。

---

## 4. 数据模型（frontmatter 规范）

> JSON Schema 落盘于 `references/profile-schema.json` 与 `references/journal-schema.json`，为本节的机器可校验形式。

### 4.1 儿童档案 profile.md

五维度：

| 维度 | 字段（frontmatter） | 说明 |
|------|--------------------|------|
| 基础身份 | `child_id` `nickname` `birthdate` `age_months`（派生） `gender` `personality` | 月龄精确，每次读写时按当前日期重算 |
| 健康禁忌 | `allergies[]` `diet_restrictions[]` `chronic_conditions[]` `medical_notes` | **绝对过滤项，优先级最高** |
| 发展状态 | `motor_level` `language_level` `cognitive_level` `routine` | 粗粒度自评 + 里程碑对照 |
| 偏好习惯 | `food_likes[]` `food_dislikes[]` `interests[]` `skills_mastered[]` `habits_target[]` | 部分由日志自动沉淀 |
| 家庭条件 | `parent_time_daily_min` `family_diet_style` `activity_spaces[]` `pantry_scope[]` | 方案可落地性约束 |

### 4.2 动态标签 tags.md

由 kid-journal 自动维护，结构化为条目列表：

```markdown
## 饮食偏好
- **喜欢** 西兰花（近30天出现8次，接受度 高）`updated: 2026-09-08`
- **拒绝** 胡萝卜（近30天出现5次，接受度 低）`updated: 2026-09-01`

## 能力观察
- **强项** 精细动作（积木垒高 10 块）`evidence: 2026-09-05 日志`
- **短板** 语言表达（词汇量偏少）`evidence: 2026-09-06 日志`

## 兴趣点
- 工程车（游戏选择倾向 6/10 次）`updated: 2026-09-07`
```

### 4.3 每日日志 01_journal/<child-id>/YYYY-MM/YYYY-MM-DD.md

frontmatter：`date` `child_id` `health_status`（healthy/ill/recovering） `illness_notes` `mood_summary`（happy/calm/fussy/crying） `tags[]`

正文五节：饮食记录 / 运动记录 / 学习记录 / 睡眠记录 / 情绪与健康（+ 今日备注）。

### 4.4 每日方案 02_plans/<child-id>/YYYY-MM-DD.md

frontmatter：`date` `child_id` `age_months_at_plan` `plan_type`（daily/weekly_batch） `adjustments[]`（调整记录：指令+原因） `health_mode`（normal/care）

正文三节：今日菜单 / 今日学习计划 / 今日游戏推荐，各自符合 `templates/<lang>/` 对应模板。

### 4.5 规则库 03_rules/rules.md

每条规则一个条目块：

```markdown
### [R001] 不吃海鲜（优先级 1）
- 类型：diet_restriction（饮食禁忌/喂养要求/教育要求/作息要求/通用养育）
- 生效范围：menu, games
- 来源：家长注入 2026-09-01「孩子海鲜过敏」
- 状态：active ｜ 冲突：无
```

优先级数字越小越高；冲突项在 `conflicts-log.md` 记录裁决。

### 4.6 复盘报告 04_reviews/

frontmatter：`period`（weekly/monthly） `date_range` `child_id` `summary_tags[]`

正文：数据统计（饮食多样性/运动时长/学习完成率）→ 里程碑达成 → 异常预警 → 优化建议（可转规则）。

---

## 5. 技能清单与职责边界

| # | 技能 | 职责 | 写入域 |
|---|------|------|--------|
| 1 | kid-init | vault 初始化 + 5 步建档引导 | 全 vault 骨架、00_profiles |
| 2 | kid-profile | 档案查看/修改、影响提示 | 00_profiles |
| 3 | kid-rules | 规则解析/冲突校验/生命周期管理 | 03_rules |
| 4 | kid-journal | 五维日志记录、标签沉淀、异常标记 | 01_journal、00_profiles/*/tags.md |
| 5 | kid-menu | 每日菜单生成/调整/批量 | 02_plans（菜单节） |
| 6 | kid-learning | 每日学习计划（双难度版本） | 02_plans（学习节） |
| 7 | kid-games | 亲子游戏推荐（多维筛选） | 02_plans（游戏节） |
| 8 | kid-plan | 完整方案聚合、方案调整、批量 3-7 天 | 02_plans |
| 9 | kid-review | 周月复盘、里程碑追踪、异常预警 | 04_reviews |

详细规格见 `docs/SKILLS_SPEC.md`。

---

## 6. 核心机制

### 6.1 指令优先级（所有方案类技能必须遵守，从高到低）

1. 档案中的过敏、禁忌、健康限制（**绝对不可违反**）
2. 家长明确注入的规则（03_rules 中 active 条目）
3. 对应年龄的科学育儿标准与安全规范（references/）
4. 儿童偏好与历史行为数据（tags.md + 近期日志）
5. 通用育儿知识与默认推荐

### 6.2 闭环数据流

```
journal 提交
  → 提取标签（食物接受度/能力表现/兴趣点）→ 更新 tags.md
  → health_status=ill 时标记护理模式
  → 下次方案生成读取最新 tags + health_mode
      → ill：菜单转清淡易消化、游戏暂停剧烈运动、学习减量
  → review 周期汇总 → 优化建议 → 家长确认 → kid-rules 注入
```

### 6.3 安全滤网（menu/games 生成时强制过）

- 过敏原：档案 `allergies[]` + 规则库饮食禁忌，命中的食材/菜品直接排除（含交叉污染提示）
- 窒息风险：3 岁以下禁整颗坚果、果冻、整粒葡萄/樱桃番茄（须切四瓣）、细小零件游戏道具
- 就医红线：`references/safety-rules.json` 中的紧急就医指征，触发时提示立即就医
- 免责声明：涉及健康的输出附带「不能替代专业医疗建议」

### 6.4 周期均衡控制（menu）

- 查询近 3 天 `02_plans/` 与 `01_journal/` 中的菜品记录，同菜品不得连续出现
- 周维度保证食材多样性：谷物 ≥3 种、蔬菜 ≥5 种、蛋白源 ≥4 种/周
- 每道菜必须附 2-3 种等价替换方案（标注过敏原替换逻辑）

### 6.5 难度动态调整（learning）

- 日志中学习环节「接受度」连续 ≥3 天为低 → 下调一档
- 连续 ≥3 天全部完成且接受度高 → 上调一档
- 基础版（15-30 分钟）/ 进阶版（30-60 分钟）双版本并存输出

### 6.6 异常健康预警（review/journal）

- 连续 3 天日志出现：饮食量偏少 / 睡眠质量差 / 情绪烦躁或哭闹 → 生成预警条目 + 护理调整建议 + 就医指征提示
- `health_status=ill` 当日：所有方案自动进入护理模式

### 6.7 多语言策略

- 模板：`templates/{zh,en}/` 双份，字段一一对应
- 知识库：zh 主源在 `references/`，en 副本在 `references/en/`
- 运行时由 `kid.config.yaml.language` 决定生成语言；frontmatter 字段名恒英文

---

## 7. 知识库文件规范（references/ 与 knowledge/）

两层知识：**references/ 为权威标准数据**（分龄营养/里程碑/睡眠/安全，推荐引擎的事实依据）；**knowledge/ 为精选方法论层**（经典书籍导读/绘本库/救场游戏/问题导航/沟通话术，内容与咨询类输出的素材库）。

### 7.1 references/（权威标准数据）

| 文件 | 内容 | 数据结构要点 |
|------|------|-------------|
| `nutrition-standards.md` | 0-12 岁分龄能量/宏量/微量营养素 + 食物种类克数表（基于《中国居民膳食指南 2022》） | 表格，年龄段为行 |
| `feeding-stages.json` | 辅食分龄（6-8m 吞咽期 → 36m），每阶段：特征/频次/单餐量/食谱/添加顺序 | `stages[] → {age_band, characteristics, frequency, amount, recipes[], introduction_order[]}` |
| `milestones.json` | 四域发育里程碑（大运动/精细动作/语言/社交认知），0-12 岁 | `domains{} → stages[] → {age, items[], red_flags[]}` |
| `sleep-guide.json` | 分月龄睡眠总时长（夜/日）+ 清醒窗口 | `bands[] → {age_range, night_hours, day_naps, wake_windows[]}` |
| `safety-rules.json` | 就医红线/窒息风险清单/居家安全 | `categories[] → {rules[], severity}` |
| `games-library.json` | 游戏库索引：领域×月龄×场景×时长×道具 | `games[] → {id, name, domains[], age_range, scene, duration_min, props[], safety}` |
| `knowledge-index.json` | 问题关键词 → 知识文件/章节映射（含 knowledge/ 条目） | `entries[] → {keywords[], resource, section}` |
| `profile-schema.json` `journal-schema.json` | §4 数据模型的 JSON Schema（draft-07） | CI 校验依据 |

### 7.2 knowledge/（精选方法论层，zh 主源 + en/ 副本）

| 文件 | 内容 | 消费方 |
|------|------|--------|
| `books-guide.md` | 12 本经典育儿书导读（核心方法/适用年龄/话术级技巧/一句话精华）+ 问题域速查表 | 问题解答、家长咨询 |
| `communication-playbook.md` | 五步沟通框架 + 10 个高频场景话术（✅/❌ 对照）+ 表达白/黑名单 | 话术建议、复盘建议 |
| `picture-books.md` | 0-12 岁分龄绘本库（选书原则/每本共读要点/六维度对应） | kid-learning 绘本选题 |
| `quick-rescue-games.md` | 10 个狼狈场景 × 2-3 个 5 分钟救场游戏（零道具/家常用具） | kid-games 场景推荐 |
| `problem-navigation.md` | 四大类高频问题导航（L1 即时应对/L2 习惯策略/深入资源/红旗信号） | 问题分流、journal 异常应对 |
| `index.json` | knowledge 层索引（问题/方法名/绘本年龄/救场场景 → 文件章节） | 全技能检索 |

引用规则：知识条目与安全红线冲突时以 references/safety-rules.json 为准；书籍方法引用必须标注来源书名。

---

## 8. 输出规范（全技能通用）

1. **结构清晰**：分级标题/项目符号/分隔线，关键信息加粗
2. **分龄适配**：严格匹配月龄；辅食必须标注适用月龄
3. **安全提示**：饮食/游戏/运动方案必附；模板中安全字段不可省略
4. **可落地**：用量精确到克/勺；道具家用优先
5. **中立科学**：基于权威指南；不确定的内容明确说明；区分「护理建议」与「医疗诊断」
6. **个性化**：推荐必须引用档案偏好/禁忌/历史，禁止通用模板话术

---

## 9. 异常与兜底

| 场景 | 行为 |
|------|------|
| 缺少核心信息（年龄/过敏史） | 主动询问补全，不盲目生成方案 |
| 需求冲突（规则 vs 科学标准） | 列出冲突点 + 2-3 种折中方案，家长决断 |
| 无法识别指令 | 列出可用功能清单与标准指令 |
| 记录生病 | 自动切护理模式：清淡饮食/暂停剧烈运动/护理提示/就医指征 |
| vault 未初始化 | 引导先执行 kid-init |
| 超出边界请求 | 说明能力边界，引导专业渠道 |

---

## 10. 质量保障

双层：**静态结构校验（ci.yml，阻塞）** + **行为评测（skillopt.yml，nightly 非阻塞）**。

### 10.1 静态结构校验（阻塞）

- `scripts/check-frontmatter.mjs`：校验 vault/示例数据 frontmatter 合规
- `scripts/check-links.mjs`：wikilink/相对链接死链检测
- `examples/demo-vault/`：全链路示例（档案→7 天日志→方案→复盘），CI 校验载体
- CI（`.github/workflows/ci.yml`）：JSON 解析 + schema 校验 + 技能清单一致性 + frontmatter + 死链 + 占位符

### 10.2 SkillOpt 行为评测（v1.2）

- golden case 回归：`bench/cases/`（menu 22 / journal 16 / flow 6 / unseen 8），chat 后端单轮（SKILL.md 作 system、case input 作 user），评分 hard=合取 / soft=均值
- 闭环链路端到端：J1-J6（journal→tags→menu→review→rules，零容忍 split 0:0:6）
- 泛化探针：unseen 集（U1-U8）不进主 split
- 入口：`python bench/run_eval.py --skill menu --split test` / `python bench/repro_case.py <case-id>`
- 设计文档：`docs/dev/v1.2-skillopt-integration.md`；铁律：`deploy_skill: false`、reports 不入库、flow 全 held-out

---

## 11. 版本路线图

| 阶段 | 内容 | 状态 |
|------|------|------|
| v0.1 | 骨架 + 设计文档 + 插件清单 | done |
| v0.2 | 数据模型 + 知识库（zh/en）+ 模板 | done |
| v0.3 | kid-init + kid-profile | done |
| v0.4 | kid-journal | done |
| v0.5 | kid-menu/learning/games/plan | done |
| v0.6 | kid-rules + kid-review | done |
| v1.0 | 校验脚本 + CI + demo-vault + 文档定版 + Web 仪表盘 | done |
| v1.1 | knowledge 精选方法论层（书籍导读/绘本库/救场游戏/问题导航/话术库，zh+en） | done |
| v1.2 | SkillOpt 行为评测体系（bench 四件套 + 52 golden cases + nightly CI） | done |
| v1.3 | 验证报告迭代：多儿童路径规范 + init 安装健壮性 + review 量化 + 评测防回归（docs/dev/v1.3-iteration-verification-review.md） | done |
