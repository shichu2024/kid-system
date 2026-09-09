---
name: kid-games
description: |
  每日亲子游戏推荐：按场景（室内/户外/车程/排队/做饭时/睡前）× 能力目标（大运动/精细动作/
  语言/认知/社交情绪）× 时长（5/15/30分钟）多维筛选，结合兴趣点与能力短板个性化匹配，
  全部游戏过安全滤网、道具限家用常见物品。
  触发词（中文）：今日游戏推荐 / 增加户外游戏 / 室内玩什么 / 车上玩什么 / 5分钟游戏 / 做饭时孩子缠人怎么办 / 救场游戏 / 游戏推荐
  Triggers (EN): today's games / outdoor games / indoor play / travel games / quick games
version: v1.0.0
phase: v0.5
applies_to: 02_plans/<child-id>/YYYY-MM-DD.md（游戏节）
source_of_truth:
  - docs/DESIGN.md §6.1（指令优先级）· §6.3（安全滤网）
  - docs/SKILLS_SPEC.md §7
  - references/games-library.json · references/safety-rules.json
  - knowledge/quick-rescue-games.md（狼狈场景 5 分钟救场游戏）
  - templates/{zh,en}/game.md
  - 上述 templates/references/knowledge 为本技能目录捆绑副本（路径相对本技能目录解析；仓库根为唯一编辑源，scripts/sync-skill-assets.mjs 同步）
---


# kid-games

> 亲子游戏推荐引擎。**寓教于乐的前提是安全：道具家用、滤网强制、短板优先补。**

## ⚠ 执行硬约束

1. **只从 `games-library.json` 选游戏**（id 引用），不凭空编造游戏；库内游戏可按家庭情况微调道具，但安全等级不得降低。**例外**：救场场景类请求（做饭时/车程/排队等）可从 `knowledge/quick-rescue-games.md` 取材，标注「救场游戏」与来源章节
2. **安全滤网强制**：<3 岁排除含细小零件/小颗粒道具的游戏（对照 `safety-rules.json → choking_hazards`）；护理模式（ill/recovering）排除剧烈运动类（gross_motor 高强度）
3. **道具约束**：优先匹配档案 `pantry_scope` 与家用常见物品；推荐的游戏若道具家庭大概率没有，标注「无道具替代玩法」
4. **筛选四维对齐**：月龄 ∧ 场景 ∧ 时长 ∧ 能力目标必须同时满足用户显式要求；未指定的维度按个性化匹配评分选择
5. **兴趣注入**：每次推荐 ≥1 个游戏结合 `tags.md` 兴趣点（如工程车兴趣 → G028 纸箱挖掘机），并在输出中说明联动关系
6. **完整输出**：每个游戏按 game 模板输出全部字段（目标/道具/时长/安全提示/步骤/进阶拓展/能力培养点），safety 字段不可省略

## 1. 何时调用

- 「今日游戏推荐」「室内玩什么」「车上玩什么」「5分钟游戏」→ 推荐
- 「增加户外游戏」→ 调整（追加场景游戏）
- kid-plan 聚合时被调用（游戏节）；kid-menu quick 模式联动「做饭时」场景

## 2. 输入

| 参数 | 必填 | 默认 | 说明 |
|------|------|------|------|
| `scene` | 否 | any | indoor / outdoor / travel / waiting / kitchen_time / bedtime / any |
| `domain` | 否 | 短板优先 | gross_motor / fine_motor / language / cognition / social_emotional |
| `duration` | 否 | 不限 | 5 / 15 / 30（分钟档位） |
| `count` | 否 | 3 | 推荐数量 1-5 |
| `date` | 否 | 今天 | — |
| `child_id` | 否 | active_child | — |

## 3. 工作流

### 步骤 1 · 上下文加载

1. 档案：月龄、`interests[]`、`activity_spaces[]`（场地约束：无户外条件时不推 outdoor）
2. 规则库：routine / general 类 active 条目（如「睡前不玩兴奋游戏」）
3. `tags.md`：兴趣点（联动）+ 能力观察（短板加权）
4. 健康模式：ill/recovering → 剧烈运动排除
5. 近 7 天方案游戏记录（避免高频重复，同一游戏 3 天内不重复推荐）

### 步骤 2 · 筛选与评分

```
候选 = games-library 中满足 (age_range ∋ 月龄) ∧ (scene 匹配) ∧ (duration 匹配) ∧ (domain 匹配)
     → 安全滤网（硬约束 2）
     → 评分：兴趣联动 +3 ｜ 能力短板域 +2 ｜ 近 3 天未出现 +1 ｜ 道具与家庭匹配 +1
     → 取 top N（count）
```

能力短板判定：`tags.md` 能力观察中的短板域，或里程碑对照中的 lagging 域（无数据时按大运动/精细动作轮换均衡）。

### 步骤 3 · 组装输出（模板：game.md × N）

每游戏完整字段 + 一行推荐理由（「为什么是它」：兴趣联动/补短板/场景适配）。
输出末尾附：**今日游戏组合说明**（覆盖了哪些能力域、总时长建议）。

### 步骤 4 · 调整流程

「增加户外游戏」「换成安静的」→ 按新约束重筛追加/替换，记录到方案 `adjustments[]`。

## 4. 输出契约

| 项 | 值 |
|----|----|
| 路径 | `02_plans/<child-id>/YYYY-MM-DD.md` 游戏节 |
| 来源 | 每游戏标注 games-library id |
| 推荐理由 | 每游戏 1 行 |
| 组合说明 | 能力域覆盖 + 总时长 |

## 5. 边界

- 不推荐户外独行/水域/交通场景无监护游戏（安全字段必须有成人陪同提示）
- 不推荐电子屏幕游戏
- 库内游戏不满足需求（如家长要求「专业感统器材」）→ 说明边界，给家用替代

## 6. 降级路径

| 场景 | 行为 |
|------|------|
| 筛选后候选为空 | 逐级放宽：duration → domain（保持场景与月龄不放宽），说明放宽项 |
| 场地约束与场景冲突（要 outdoor 但无户外条件） | 提示冲突，给 indoor 替代 + 说明 |
| tags.md 无能力数据 | 按五域轮换均衡推荐，输出注明 |
| 护理模式 | 只推 language/cognition/fine_motor 低强度 + bedtime 温和游戏 |

## 7. 幂等保证

同日同参数重推：结果一致（近 7 天记录不因本次推荐而变）；调整类追加不删除既有推荐（替换类除外）。

## 8. 自检清单

- [ ] 每游戏来自 games-library 且 id 已标注
- [ ] <3 岁无细小零件；护理模式无剧烈运动
- [ ] 月龄/场景/时长/能力四维与请求一致
- [ ] ≥1 个游戏联动兴趣点并说明
- [ ] 每游戏 safety 字段完整输出
- [ ] 同一游戏 3 天内未重复
- [ ] 附能力域组合说明
