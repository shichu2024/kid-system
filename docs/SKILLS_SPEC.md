# kid-system 技能规格书（SKILLS_SPEC）

> 每技能五段式：触发词 → 输入 → 工作流 → 输出 → 边界。
> 真相源：`docs/DESIGN.md`。各 SKILL.md 以本文 + DESIGN 为准。

## 通用约定

- **路径表达**：一律相对 vault 根（如 `01_journal/tangtang/2026-09/2026-09-08.md`）
- **日期格式**：ISO `YYYY-MM-DD`；周编号 `YYYY-Www`
- **月龄计算**：`age_months = (today - birthdate) 换算月数`，每次读写档案时重算并回写
- **语言**：由 `99_system/kid.config.yaml.language` 决定（zh/en），模板取 `99_system/templates/<lang>/`
- **触发词命名空间**：`kid-*` 前缀；中英双语触发词写在 SKILL.md frontmatter description
- **输出反馈**：技能执行完毕输出简报（做了什么/写了哪些文件/下一步建议）
- **技能资产（v1.3.3）**：SKILL.md 中的 `templates/` `references/` `knowledge/` 路径**相对本技能目录**解析——各技能声明的依赖资产已捆绑于 `skills/<name>/` 下（仓库根为唯一编辑源，`scripts/sync-skill-assets.mjs` 同步）；写入 vault 的路径仍相对 vault 根

---

## §1 kid-init · 初始化与建档

**触发词**：初始化档案 / 建立孩子资料 / 设置宝宝信息 / 建立孩子档案 ｜ init child profile / setup kid vault

**输入**：`vault_root`（默认 CWD）、`language`（默认 zh）、建档信息（分步交互采集）

**工作流**：
1. 幂等守门：存在 `.kid-initialized` 或 `99_system/` → 不覆盖，转为「添加新儿童」或直接退出
2. 铺骨架：§3 目录树 + 模板副本 + `kid.config.yaml` + `.kid-initialized`
3. 5 步建档（聊天式，每步可跳过非必填项）：
   - ① 核心基础：昵称、出生日期/月龄、性别（**必填**）
   - ② 健康禁忌：过敏史、饮食禁忌、慢性疾病、医疗注意事项（**过敏必答，可答「无」**）
   - ③ 性格与偏好：性格特质、饮食喜好/厌恶、兴趣倾向
   - ④ 家庭条件：每日亲子时长、家庭饮食风格、活动场地、常用食材
   - ⑤ 展示档案确认 → 写入 `00_profiles/<child-id>/profile.md` + `tags.md` 空骨架
4. 输出完成简报 + 引导首次使用（「今日方案」）

**输出**：vault 骨架 + `00_profiles/<child-id>/profile.md`（frontmatter 符合 profile-schema）

**边界**：不采集真实姓名/照片/住址；已初始化目录不覆盖；多儿童通过「添加新儿童」走 ①-⑤

---

## §2 kid-profile · 档案查看与修改

**触发词**：查看孩子档案 / 宝宝信息 / 修改年龄 / 添加过敏 / 更新偏好 ｜ view child profile / update profile / add allergy

**输入**：查看（无参）或修改项（字段 + 新值）

**工作流**：
1. 读 `kid.config.yaml.active_child` 定位档案；未初始化 → 引导 kid-init
2. 查看：按五维度分组展示，健康禁忌红色标注
3. 修改：更新对应字段 + `updated` 时间戳 + 重算 `age_months`
4. 影响提示：变更涉及过敏/禁忌/偏好时，明确告知将影响哪些后续模块

**输出**：档案展示或更新后的 diff 摘要 + 影响说明

**边界**：不删除必填字段（昵称/出生日期）；健康禁忌字段修改需家长二次确认

---

## §3 kid-rules · 知识注入与规则管理

**触发词**：注入规则 / 添加育儿知识 / 设定喂养要求 / 查看已注入规则 / 育儿规则列表 / 删除规则 / 调整优先级 ｜ inject rule / add parenting rule / manage rules

**输入**：自然语言规则文本，或管理指令（查看/编辑/删除/启停/排序）

**工作流**：
1. 解析：从自然语言提取规则条目（类型：diet_restriction/feeding/education/routine/general）
2. 冲突校验：与规则库现有条目逐条比对（同类目同对象不同要求 = 冲突；与安全红线冲突 = 拒绝并解释）
3. 无冲突 → 写入规则库，说明生效范围（menu/learning/games 哪些模块受影响）
4. 有冲突 → 列出冲突双方，家长裁决优先级后写入 + 记录 `conflicts-log.md`
5. 管理操作：列表展示（含优先级/状态/生效范围），支持启停与排序

**输出**：`03_rules/rules.md` 更新 + 冲突报告（如有）

**边界**：与安全红线冲突的规则拒绝注入；规则不能违反档案过敏禁忌（那是绝对项）；单次注入 ≤10 条

---

## §4 kid-journal · 每日成长日志

**触发词**：记录今天 / 写日志 / 记录饮食 / 记录运动 / 记录学习 / 查看昨天的日志 / 上周日志 / 搜索xx记录 ｜ log today / daily journal / search journal

**输入**：口述式日记（自然语言，任意维度组合）或结构化片段；`date`（默认今天）

**工作流**：
1. 定位儿童档案 + 读取近 7 天日志（上下文）
2. 按五维度解析口述内容 → 填入日志模板（缺失维度标注「未记录」，不编造）
3. 异常识别：发烧/腹泻/呕吐/受伤 → `health_status=ill` + 护理模式提示
4. 标签沉淀：提取食物接受度/能力表现/兴趣点 → 更新 `tags.md`（带证据引用与日期）
5. 输出日志确认 + 沉淀摘要 + 次日方案优化提示

**输出**：`01_journal/<child-id>/YYYY-MM/YYYY-MM-DD.md` + `tags.md` 增量更新

**边界**：不编造未提及的维度；健康异常只做护理建议 + 就医指征提示；单日日志幂等（重写需确认）

---

## §5 kid-menu · 每日菜单推荐

**触发词**：今日菜单 / 明天吃什么 / 把午餐换成清淡的 / 替换食材 / 生成本周菜单 ｜ today's menu / weekly menu / adjust menu

**输入**：`date`（默认今天）、`mode`（normal/light 清淡/iron 补铁/calcium 补钙/quick 快手菜）、`days`（批量 1-7）

**工作流**：
1. 读档案（过敏/禁忌/偏好）+ 规则库饮食类条目 + 近 3 天菜品记录 + 当前健康模式
2. ill/护理模式 → 强制 `mode=light` + 清淡易消化食材集
3. 按 `nutrition-standards.md` 分龄需求 + `feeding-stages.json`（≤36m）选菜
4. 安全滤网：过敏排除 → 窒息风险排除 → 规则过滤
5. 组装：早/午/晚 + 上午/下午加餐；每菜含食材用量/步骤/营养亮点/喂食注意/替换方案
6. 周期均衡：连续 3 天不重复；输出周食材多样性统计（批量模式）
7. 调整模式：基于调整指令重生成对应餐次，记录 `adjustments[]`

**输出**：`02_plans/<child-id>/YYYY-MM-DD.md` 菜单节（符合 daily-menu + dish 模板）

**边界**：过敏原绝对排除；不推荐保健品/补剂；用量不确定时标注区间并说明

---

## §6 kid-learning · 每日学习计划

**触发词**：今日学习计划 / 今天的启蒙安排 / 学习计划进阶版 ｜ today's learning plan

**输入**：`date`、`level`（basic 基础版/advanced 进阶版/默认双版本输出）

**工作流**：
1. 读档案发展状态 + tags 能力观察 + 近期日志学习反馈 + 规则库教育类条目
2. 六维度选题：绘本阅读/语言启蒙/数学认知/艺术启蒙/常识科普/习惯培养（每日主 1-2 个 + 辅 1-2 个）
3. 难度动态调整（§6.5 DESIGN）：按日志接受度升降档
4. 组装：核心环节（绘本共读含互动提问设计）+ 拓展启蒙 + 习惯培养，标注时长与操作方法
5. 护理模式：时长减半，只保留温和内容（绘本/音乐）

**输出**：`02_plans/<child-id>/YYYY-MM-DD.md` 学习计划节（含完成记录勾选框）

**边界**：不推荐屏幕时间 >30 分钟的内容；不布置强制打卡任务；内容须匹配发展里程碑

---

## §7 kid-games · 亲子游戏推荐

**触发词**：今日游戏推荐 / 增加户外游戏 / 室内玩什么 / 5分钟游戏 ｜ today's games / outdoor games / indoor play

**输入**：`scene`（indoor/outdoor/any）、`domain`（大运动/精细动作/专注力/社交表达/逻辑思维）、`duration`（5/15/30 分钟）、`count`（默认 3 个）

**工作流**：
1. 读档案（兴趣点/能力短板/月龄）+ 场地条件 + 规则库条目
2. 从 `games-library.json` 筛选：月龄 ∧ 场景 ∧ 时长 ∧ 能力目标（短板优先补、强项适度用）
3. 安全滤网：窒息风险道具排除（<3 岁）、剧烈运动排除（护理模式）
4. 组装：每游戏含目标/道具/步骤/安全提示/进阶拓展/能力培养点
5. 兴趣注入：至少 1 个游戏结合 tags.md 兴趣点

**输出**：`02_plans/<child-id>/YYYY-MM-DD.md` 游戏节

**边界**：道具限家用常见物品；不推荐需专业设备项目；安全提示不可省略

---

## §8 kid-plan · 完整方案聚合与调整

**触发词**：今日方案 / 明天的计划 / 未来3天计划 / 生成本周方案 ｜ today's full plan / next 3 days plan

**输入**：`date(s)`（1-7 天）、可选调整指令（透传给各模块）

**工作流**：
1. 前置校验：vault 已初始化 + 档案完整（缺核心信息 → 引导补全）
2. 依序调用：kid-menu → kid-learning → kid-games（同一 `02_plans/<child-id>/YYYY-MM-DD.md`）
2.5. 汇总展示：三栏概览 + 营养重点 + 今日提醒
3. 批量模式：逐日生成（日期+1 时自动重算月龄、滚动周期均衡窗口）
4. 调整流程：接收调整指令 → 定位受影响模块 → 重生成 → 记录 `adjustments[]` + 调整原因沉淀

**输出**：`02_plans/<child-id>/YYYY-MM-DD.md`（完整三节）+ 概览简报

**边界**：批量 ≤7 天；调整不改档案事实字段（过敏等走 kid-profile）

---

## §9 kid-review · 周期复盘与进阶优化

**触发词**：周总结 / 月度报告 / 成长复盘 / 查看发育里程碑 / 下一阶段重点 ｜ weekly review / monthly report / growth review / milestones

**输入**：`period`（weekly/monthly/custom）、`date_range`（默认最近一周期）

**工作流**：
1. 拉取周期内全部日志 + 方案 + tags 变更历史
2. 数据统计：饮食多样性/接受度分布、运动总时长、学习完成率、睡眠趋势、情绪分布
3. 里程碑对照：读 `milestones.json`，按当前月龄标注已达成/观察中/待达成 + 红旗预警项
4. 异常预警：连续 3 天异常模式检测（DESIGN §6.6）→ 预警 + 护理建议 + 就医指征
5. 优化建议：3-5 条可执行建议，每条标注「可转化为规则」标记
6. 一键转规则：家长确认后，调用 kid-rules 注入

**输出**：`04_reviews/<child-id>/weekly/YYYY-Www.md`（或 monthly/）+ `04_reviews/<child-id>/milestones.md` 更新

**边界**：里程碑滞后不做诊断性结论，建议儿保科评估；复盘不评判家长
