---
name: kid-review
description: |
  周期成长复盘：自动生成周/月度成长报告（饮食/运动/学习/睡眠/情绪多维统计），
  对照发育里程碑时间轴追踪达成情况，连续 3 天异常自动预警，
  优化建议支持一键转化为育儿规则注入规则库。
  触发词（中文）：周总结 / 月度报告 / 成长复盘 / 查看发育里程碑 / 下一阶段重点 / 本周情况
  Triggers (EN): weekly review / monthly report / growth review / milestones / next stage focus
version: v1.0.0
phase: v0.6
applies_to: 04_reviews/<child-id>/weekly/YYYY-Www.md · 04_reviews/<child-id>/monthly/YYYY-MM.md · 04_reviews/<child-id>/milestones.md
source_of_truth:
  - docs/DESIGN.md §4.6（复盘模型）· §6.6（异常预警）
  - docs/SKILLS_SPEC.md §9
  - references/milestones.json · references/safety-rules.json · references/sleep-guide.json
  - templates/{zh,en}/weekly-review.md · monthly-report.md · milestone-timeline.md
---

# kid-review

> 闭环的收口：数据 → 洞察 → 建议 → 规则。**里程碑滞后不做诊断性结论，复盘不评判家长。**

## ⚠ 执行硬约束

1. **数据优先**：统计数字只能来自周期内实际日志/方案文件，逐项可溯源（报告标注数据来源日期范围与天数）；**无数据的天数显式说明，不得按有数据天数外推总量**
2. **异常预警机械判定（v1.3 升格）**：连续异常天数 ≥ `kid.config.yaml → review.warning_days`（缺省 **3**）即**必须**触发预警——这是机械判定，禁止以「看起来还好」「刚生病完正常」等语义理由跳过。触发后：预警条目置顶 + 护理调整建议 + 就医指征提示
3. **红旗处理**：日志或对照中出现 `milestones.json` 的 red_flags（含 universal_red_flags「技能倒退」）→ 显著提示「请及时儿保科评估」+ 免责声明，**不做诊断**
4. **里程碑对照必做 + 滞后窗口量化（v1.3）**：周/月复盘必须包含四域里程碑对照（读 `milestones.json` 当前与下一月龄段），更新 `04_reviews/<child-id>/milestones.md` 时间轴。滞后项分级机械判定：**超出预期窗口 ≥1 个月 = 「观察说明」**（附日常练习建议）；**≥2 个月 = 「建议儿保科评估」**（非诊断措辞）
5. **覆盖率阈值配置化（v1.3）**：数据覆盖率 < `review.min_coverage`（缺省 **0.5**）→ 报告降级为「初步观察版」，所有结论标注局限；**禁止在低覆盖率下输出确定性结论**
6. **建议可执行可转化**：优化建议 3-5 条，每条含具体动作 + 依据数据 + 「☐ 转化为规则」标记；家长确认后调用 kid-rules 注入（source 标注复盘来源）
7. **不评判措辞**：报告用语中立（「本周蔬菜摄入种类 4 种，低于建议的 5 种」✔；「你们对孩子饮食不够上心」✘）

## 1. 何时调用

- 「周总结」「复盘本周」→ weekly
- 「月度报告」「成长复盘」→ monthly
- 「查看发育里程碑」「下一阶段重点」→ 里程碑时间轴
- 连续异常时其他技能提示「建议做一次复盘」

## 2. 输入

| 参数 | 必填 | 默认 | 说明 |
|------|------|------|------|
| `period` | 否 | weekly | weekly / monthly / custom |
| `date_range` | 否 | 最近完整周期 | custom 时必填（start/end） |
| `child_id` | 否 | active_child | — |

## 3. 工作流

### 步骤 1 · 数据拉取与阈值读取

1. 读 `99_system/kid.config.yaml → review`（v1.3）：`min_coverage`（缺省 0.5）、`warning_days`（缺省 3）；报告开头声明本次生效阈值
2. 周期内全部 `01_journal/<child-id>/` 日志 + `02_plans/<child-id>/` 方案
3. `tags.md` 当前状态；rules.md 变更（如有）
4. 上期复盘（环比趋势用）
5. 统计数据覆盖率：有日志天数 / 周期总天数（< min_coverage → 按「初步观察版」降级，硬约束 5）

### 步骤 2 · 多维统计

| 维度 | 指标 |
|------|------|
| 饮食 | 食材多样性（谷物/蔬菜/蛋白源种类数）、接受度分布（喜欢/一般/拒绝占比）、拒绝 Top3 食物 |
| 运动 | 总时长、户外占比、类型分布 |
| 学习 | 完成率（对照方案勾选/日志记录）、接受度趋势、难度调整轨迹 |
| 睡眠 | 夜间时长均值与波动、午睡规律度、对照 `sleep-guide.json` 参考区间 |
| 情绪 | happy/calm/fussy/crying 分布、异常日列表 |

### 步骤 3 · 里程碑对照

1. 当前月龄 → `milestones.json` 四域当前段 items：逐项标 已达成（附日志证据日期）/ 观察中 / 待达成
2. red_flags 逐项排查（硬约束 3）
3. **滞后分级（v1.3 机械判定）**：待达成项按「当前月龄 − 预期窗口月龄」分级——超出 ≥1 个月 = 观察说明（附日常练习建议）；超出 ≥2 个月 = 建议儿保科评估（非诊断措辞）；两类均在时间轴标注超出月数
4. 下一月龄段重点预览（「未来 3 个月发展重点」）
5. 更新 `04_reviews/<child-id>/milestones.md` 时间轴（增量，保留历史判断与变更记录）

### 步骤 4 · 异常预警（机械判定，N = warning_days，缺省 3）

```
扫描周期内日志序列：
  饮食量=偏少 连续≥N天 → 预警
  睡眠质量=差 连续≥N天 → 预警
  情绪∈{fussy,crying} 连续≥N天 → 预警
  同一 illness_notes 持续≥N天 → 预警
连续天数 = N-1 → 输出「持续观察」条目（提示已达预警前一日）
```

预警条目：现象（日期范围）→ 可能相关因素（对照同期数据）→ 护理调整建议 → 就医指征（引 safety-rules 红线）。

### 步骤 5 · 报告生成（模板：weekly-review / monthly-report）

月度报告额外含：里程碑达成汇总表 + 下月发展重点 + 环比上月趋势。

### 步骤 6 · 建议与转化

1. 3-5 条优化建议（每条：动作 + 数据依据 + ☐ 转化为规则）
2. 家长勾选确认 → 逐条调用 kid-rules 注入（走其完整校验流程）
3. 未确认的建议保留在报告中，下期复盘复查执行情况

## 4. 输出契约

| 项 | 值 |
|----|----|
| 周报 | `04_reviews/<child-id>/weekly/YYYY-Www.md` |
| 月报 | `04_reviews/<child-id>/monthly/YYYY-MM.md` |
| 时间轴 | `04_reviews/<child-id>/milestones.md`（增量更新） |
| frontmatter | period / date_range / child_id / summary_tags[]（符合 review schema） |
| 数据覆盖 | 报告开头标注（X/Y 天有记录） |

## 5. 边界

- 不做发育诊断/智力评价；红旗只提示评估
- 不在数据覆盖率 < min_coverage（缺省 0.5）时输出确定性结论
- 建议不涉及药物治疗；健康类建议附就医提示

## 6. 降级路径

| 场景 | 行为 |
|------|------|
| 周期内无任何日志 | 说明无法复盘 + 引导从「记录今天」开始；可给纯里程碑对照（无数据部分标待观察） |
| 数据不足（< min_coverage） | 生成「初步观察版」，标注局限，建议补记 |
| 首次复盘（无上期） | 环比部分省略，说明「下期起提供趋势」 |
| 月龄跨段 | 分段对照并说明切换点 |

## 7. 幂等保证

- 同周期重新生成：完整替换对应报告文件（milestones.md 仍增量保留历史）
- 里程碑判断升级（观察中→已达成）需日志证据，不因重复执行而漂移

## 8. 自检清单

- [ ] 数据来源与覆盖率已标注，无外推编造
- [ ] 异常预警机械判定执行（warning_days，缺省 3），预警置顶且含就医指征；N-1 天已输出「持续观察」
- [ ] 报告开头声明本次生效阈值（min_coverage / warning_days，含缺省来源）
- [ ] 里程碑滞后项已按 ≥1m 观察 / ≥2m 建议评估分级并标注超出月数
- [ ] red_flags 逐项排查，命中处已提示儿保评估 + 免责声明
- [ ] 里程碑时间轴增量更新（含证据日期与变更记录）
- [ ] 建议 3-5 条、每条可执行、带「☐ 转化为规则」标记
- [ ] 措辞中立零评判
- [ ] frontmatter 符合 review schema
