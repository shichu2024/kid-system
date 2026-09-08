---
name: kid-init
description: |
  初始化 kid-system 育儿数据 vault 并分 5 步引导建立儿童成长档案。在指定目录铺设目录骨架、
  模板与配置，通过聊天式分步采集完成基础身份/健康禁忌/性格偏好/家庭条件五维度建档。
  触发词（中文）：初始化档案 / 建立孩子资料 / 设置宝宝信息 / 建立孩子档案 / 初始化
  Triggers (EN): init child profile / setup kid vault / initialize kid-system
version: v1.0.0
phase: v0.3
applies_to: vault 根目录（全骨架） + 00_profiles/
source_of_truth:
  - docs/DESIGN.md §3（vault 结构）
  - docs/DESIGN.md §4.1（档案数据模型）
  - docs/SKILLS_SPEC.md §1
---

# kid-init

> 铺 vault 骨架 + 分 5 步引导建档。**已初始化的 vault 绝不覆盖任何文件。**

## ⚠ 执行硬约束（缺一不得输出 ✓ 完成报告）

1. **幂等守门**：vault 根已存在 `.kid-initialized` 或 `99_system/` 目录时，**禁止覆盖任何文件**，只能转入「添加新儿童」流程（跳过步骤 2，直接走步骤 3-5）或退出
2. **不采集敏感信息**：禁止询问/写入真实姓名、照片、住址、身份证号等；儿童标识只用**昵称**
3. **过敏必答**：步骤 ② 健康禁忌中「过敏史」必须得到明确回答（可以是「无」），不得留空或跳过
4. **档案写盘前确认**：`profile.md` 写入前必须向家长完整展示档案内容并获得确认
5. **模板铺设数量**：`99_system/templates/{zh,en}/` 各 **8 个**模板（dish/daily-menu/game/learning-plan/journal/weekly-review/monthly-report/milestone-timeline），写完 `ls` 实测清点
6. **frontmatter 合规**：`profile.md` 必须符合 `references/profile-schema.json`（required: child_id, nickname, birthdate, gender, allergies, created, updated）
7. **自检清单（§9）逐项核对后才输出完成报告**

## 1. 何时调用

- 用户在空目录（或指定目录）首次使用 kid-system
- 显式触发：「初始化档案」「建立孩子资料」「设置宝宝信息」
- 隐式触发：其他 kid-* 技能发现 vault 未初始化时，引导回本技能

## 2. 输入

| 参数 | 必填 | 默认 | 说明 |
|------|------|------|------|
| `vault_root` | 否 | 当前工作目录 | vault 根路径 |
| `language` | 否 | `zh` | 全 vault 语言（zh/en），决定模板与后续生成内容语言；用户消息中声明的语言优先 |
| 建档信息 | 交互采集 | — | 分 5 步聊天式采集（步骤 3） |

## 3. 工作流

### 步骤 1 · 幂等守门

1. 检查 `vault_root` 下是否存在 `.kid-initialized` 标记文件或 `99_system/` 目录
2. **已初始化** → 不覆盖任何文件，询问家长意图：
   - 「添加新儿童」→ 跳到步骤 3（走 ①-⑤ 建档，child_id 加入 `kid.config.yaml.children` 并切换 active_child）
   - 「重新查看引导」→ 输出快速上手说明后结束
3. **未初始化** → 继续

### 步骤 2 · 铺设 vault 骨架

按 DESIGN §3 创建：

```
00_profiles/          01_journal/        02_plans/
03_rules/             04_reviews/weekly/  04_reviews/monthly/
99_system/config/     99_system/templates/{zh,en}/
```

- 复制技能包 `templates/{zh,en}/*.md`（8 个/语言）到 `99_system/templates/{zh,en}/`
- 写 `99_system/kid.config.yaml`：

```yaml
language: zh
active_child: <child-id>
children: [<child-id>]
initialized_at: YYYY-MM-DD
skill_version: v1.0.0
```

- 写 `03_rules/rules.md` 空骨架（含说明头 + 空规则列表）
- 写 `.kid-initialized`：

```yaml
schema_version: 1
skill_version: v1.0.0
language: zh
initialized_at: YYYY-MM-DD
```

### 步骤 3 · 5 步分步引导建档（聊天式，非问卷式）

> 一次只问一小步，语气自然（如「顺便问一下，宝宝现在多大了？」）。家长说「跳过」可跳过非必填项；带 ★ 为必填。

| 步骤 | 采集内容 | 必填 | 提示要点 |
|------|---------|------|---------|
| ① 核心基础 | 昵称★、出生日期或月龄★、性别★、性格特质 | 昵称/出生日期 | 月龄会随时间自动重算；出生日期不确定时可用近似月龄反推并标注 |
| ② 健康禁忌 | **过敏史★（可答「无」）**、饮食禁忌、慢性疾病史、医疗注意事项 | 过敏史 | 说明用途：所有菜单/游戏推荐的绝对过滤项 |
| ③ 性格与偏好 | 饮食喜好/厌恶清单、兴趣倾向、已掌握技能、待培养习惯 | 无 | 「大概说说就行，后续日志会自动补充」 |
| ④ 家庭条件 | 每日可支配亲子时长、家庭饮食风格、活动场地（居家/户外）、常用食材范围 | 无 | 用于方案可落地性（快手菜 vs 精细制作、室内 vs 户外） |
| ⑤ 确认启用 | 汇总展示全部采集结果 → 家长确认/修正 | 确认动作 | 确认后才写盘 |

**child_id 生成**：昵称拼音 kebab-case（如「糖糖」→ `tangtang`）；冲突时追加 `-2`。

### 步骤 4 · 写入档案

- `00_profiles/<child-id>/profile.md`：frontmatter 按 `references/profile-schema.json` 五维度字段；正文按五维度分节呈现（含空维度占位说明）
- `00_profiles/<child-id>/tags.md`：动态标签空骨架（饮食偏好/能力观察/兴趣点三节，各附「由 kid-journal 自动维护」说明）
- 计算 `age_months`（当前日期 − birthdate）写入 frontmatter

### 步骤 5 · 完成简报

输出：
1. ✅ vault 结构清单（ls 实测）
2. ✅ 档案摘要卡片（昵称/月龄/过敏重点）
3. 下一步引导：「今日方案」生成首日方案 / 「注入规则」添加家庭规则

## 4. 输出契约

| 项 | 值 |
|----|----|
| 档案路径 | `00_profiles/<child-id>/profile.md` |
| 标签路径 | `00_profiles/<child-id>/tags.md` |
| 模板数量 | `99_system/templates/{zh,en}/` 各 8 个（实测清点） |
| 配置 | `99_system/kid.config.yaml`（language/active_child/children 齐全） |
| 标记 | `.kid-initialized`（YAML 格式，见步骤 2） |

## 5. 边界

- 不覆盖已初始化 vault 的任何文件
- 不采集真实姓名/照片/住址/证件号
- 不在无确认的情况下写 profile.md
- 多儿童数量无上限，但每次会话只建一个档案

## 6. 降级路径

| 场景 | 行为 |
|------|------|
| 目录非空但无初始化标记 | 列出将创建的子目录，征得同意后继续（只创建缺失目录，不动既有文件） |
| 家长中途停止 | 已完成步骤的骨架保留；下次继续时从步骤 3 恢复（骨架已在则跳过步骤 2） |
| 出生日期只知大概 | 用近似月龄反推 birthdate 并在 profile 正文标注「近似」 |
| language 参数缺失 | 默认 zh；用户消息为英文时可提示是否切换 en |

## 7. 幂等保证

- 重复调用且已初始化：不产生任何写操作（除非家长明确选择「添加新儿童」）
- 「添加新儿童」重复中断：不完整的 profile 目录下次继续，不重复创建

## 8. 与其他技能的衔接

| 后续技能 | 依赖本技能的产物 |
|---------|----------------|
| kid-profile | profile.md / kid.config.yaml |
| kid-journal | kid.config.yaml.active_child / journal 模板 |
| kid-menu / learning / games / plan | 档案五维度 + 模板 + tags.md |
| kid-rules | 03_rules/rules.md 骨架 |
| kid-review | 04_reviews/ 结构 |

## 9. 自检清单（完成报告前逐项核对）

- [ ] `.kid-initialized` 存在且为 YAML 格式（含 schema_version/skill_version/language/initialized_at）
- [ ] `99_system/kid.config.yaml` 四项齐全（language/active_child/children/initialized_at）
- [ ] `99_system/templates/{zh,en}/` 各实测 **8 个**模板（ls 清点 ≠ 8 → 阻断级告警）
- [ ] `00_profiles/<child-id>/profile.md` frontmatter 含全部 required 字段且 allergies 非空（「无」也显式写入 `allergies: []` 并在正文注明）
- [ ] `tags.md` 三节骨架存在
- [ ] 未覆盖任何既有文件（幂等守门执行）
- [ ] 未采集任何敏感个人信息
- [ ] 完成简报包含档案摘要 + 下一步引导
