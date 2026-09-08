---
name: kid-plan
description: |
  今日完整方案聚合器：一次调用生成「菜单 + 学习计划 + 游戏推荐」完整每日方案；
  支持批量生成未来 3-7 天（滚动周期均衡），支持自然语言方案调整
  （「今天不吃海鲜」「增加户外游戏」「换成快手菜」）并沉淀调整原因。
  触发词（中文）：今日方案 / 明天的计划 / 未来3天计划 / 生成本周方案 / 调整方案 / 换个计划
  Triggers (EN): today's full plan / next 3 days plan / weekly plan / adjust plan
version: v1.0.0
phase: v0.5
applies_to: 02_plans/<child-id>/YYYY-MM-DD.md（聚合三节）
source_of_truth:
  - docs/DESIGN.md §6.1（指令优先级）· §6.2（闭环数据流）
  - docs/SKILLS_SPEC.md §8
  - skills/kid-menu · kid-learning · kid-games（被聚合模块）
---

# kid-plan

> 完整方案的编排入口。**本技能只做编排与聚合，推荐逻辑一律委托给 kid-menu / kid-learning / kid-games。**

## ⚠ 执行硬约束

1. **前置校验强制**：vault 未初始化 → 引导 kid-init；档案缺出生日期或过敏信息 → 停止生成并引导补全（kid-profile），**不得用默认值臆测月龄/过敏**
2. **不重复实现推荐逻辑**：菜单/学习/游戏分别按对应技能的硬约束与工作流生成；本技能不得绕过其安全滤网
3. **批量上限 7 天**：days ≤ 7；逐日生成时日期 +1 并重算月龄（跨月龄段时提示标准切换）
4. **调整不改档案**：调整指令只影响当次方案并记录 `adjustments[]`；涉及过敏/禁忌的永久变更必须引导 kid-profile
5. **单文件完整**：每日方案聚合在同一个 `02_plans/<child-id>/YYYY-MM-DD.md`，frontmatter 按 journal-schema plan 定义（date/child_id/age_months_at_plan/plan_type/health_mode/adjustments）
6. **聚合简报必附**：三栏概览 + 营养重点 + 今日提醒（健康/里程碑/规则变更提示）

## 1. 何时调用

- 「今日方案」「明天的计划」→ 单日聚合
- 「未来 3 天计划」「生成本周方案」→ 批量
- 「把午餐换成清淡的」「增加户外游戏」→ 方案调整
- 「今天不吃海鲜」→ 当日约束调整（区别于永久过敏登记）

## 2. 输入

| 参数 | 必填 | 默认 | 说明 |
|------|------|------|------|
| `dates` / `days` | 否 | 1（今天） | 单日 date 或批量 days（1-7） |
| `adjust` | 否 | — | 自然语言调整指令（透传给对应模块） |
| `child_id` | 否 | active_child | — |

## 3. 工作流

### 步骤 1 · 前置校验

1. `.kid-initialized` 存在 + active_child 档案完整（birthdate、allergies 非空——「无」也算显式）
2. 档案 `00_profiles/<child-id>/profile.md` 存在且 schema 合规
3. 不满足 → 输出缺失项 + 引导（kid-init / kid-profile）

### 步骤 2 · 健康模式判定

读最近日志 `health_status`：ill/recovering → `health_mode: care`（各模块自动适配）。

### 步骤 3 · 依序聚合（对每个目标日期）

1. **kid-menu**：生成菜单节（mode 默认 normal；care → light）
2. **kid-learning**：生成学习计划节（双版本；care → 减半温和版）
3. **kid-games**：生成游戏节（默认 3 个；care → 低强度组合）
4. 写入 `02_plans/<child-id>/YYYY-MM-DD.md`：frontmatter（含 age_months_at_plan 重算）+ 三节
5. 批量模式：下一日期时各模块的周期均衡窗口滚动 +1 天

### 步骤 4 · 聚合简报

```
【XX的每日方案 · X岁X月 · YYYY-MM-DD】（护理模式 时标注）
▌菜单：三餐两点一览（1 行摘要）+ 今日营养重点
▌学习：核心环节 + 难度档（+ 调整依据）
▌游戏：N 个游戏名 + 能力域覆盖
▌今日提醒：健康提示 / 里程碑临近项 / 规则变更影响
```

批量模式额外输出：日期 × 模块矩阵概览 + 周食材多样性统计（来自 kid-menu）。

### 步骤 5 · 方案调整流程

1. 解析调整指令 → 分类路由：

| 指令类型 | 路由 | 示例 |
|---------|------|------|
| 餐饮调整 | kid-menu 调整流程 | 「午餐换清淡」「不吃海鲜（今天）」 |
| 学习调整 | kid-learning | 「今天只做绘本」 |
| 游戏调整 | kid-games | 「增加户外游戏」「换成安静的」 |
| 永久健康变更 | kid-profile（引导） | 「确认对芒果过敏」 |

2. 重生成受影响节，其余保留
3. `adjustments[]` 追加：`{instruction, reason, date}`
4. 偏好相关原因（「孩子不爱吃」）提醒家长当日记录日志以便 tags 沉淀

## 4. 输出契约

| 项 | 值 |
|----|----|
| 路径 | `02_plans/<child-id>/YYYY-MM-DD.md` × N 天 |
| frontmatter | date / child_id / age_months_at_plan / plan_type（daily｜weekly_batch）/ health_mode / adjustments[] |
| 简报 | 单日：三栏概览；批量：矩阵 + 多样性统计 |

## 5. 边界

- 不生成 >7 天的批量
- 不在档案信息缺失时「先出一个通用版」（宁可停下来补全）
- 调整指令与安全滤网冲突 → 拒绝该调整并解释（各模块边界继承）

## 6. 降级路径

| 场景 | 行为 |
|------|------|
| 某一模块生成失败/数据不足 | 输出其余两节 + 明确标注缺失节的原因与补救建议 |
| 跨月龄段的批量（如生成日跨 24m） | 在对应日期标注「月龄段切换：新阶段标准生效」 |
| 目标日期已有方案 | 询问覆盖/合并/查看 |
| 调整指令无法解析 | 列出可调整项清单（餐次/模式/游戏场景/学习版本）请家长明确 |

## 7. 幂等保证

- 同参数重生成：完整替换对应日期方案（adjustments 历史保留）
- 调整幂等：同指令重复执行结果一致

## 8. 自检清单

- [ ] 前置校验执行（未用默认值臆测）
- [ ] 三节齐全且各自通过模块自检（菜单安全滤网/难度依据/游戏 id 来源）
- [ ] frontmatter 完整（age_months_at_plan 为当日重算值）
- [ ] 批量 ≤7 天且滚动窗口生效
- [ ] 聚合简报含营养重点与今日提醒
- [ ] adjustments[] 记录完整（调整类调用）；同日重生成后 **adjustments[] 历史条目仍然保留**（未被覆盖丢失）
- [ ] 永久健康变更已引导 kid-profile（未擅改档案）
