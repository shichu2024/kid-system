---
name: kid-profile
description: |
  查看与修改儿童成长档案（五维度：基础身份/健康禁忌/发展状态/偏好习惯/家庭条件）。
  修改过敏、禁忌等关键字段时二次确认，并提示对后续菜单/学习/游戏方案的影响范围。
  触发词（中文）：查看孩子档案 / 宝宝信息 / 修改年龄 / 添加过敏 / 更新偏好 / 切换孩子
  Triggers (EN): view child profile / update profile / add allergy / switch child
version: v1.0.0
phase: v0.3
applies_to: 00_profiles/<child-id>/profile.md · 99_system/kid.config.yaml
source_of_truth:
  - docs/DESIGN.md §4.1（档案数据模型）
  - docs/SKILLS_SPEC.md §2
---

# kid-profile

> 档案的读取与维护入口。**健康禁忌字段的修改必须二次确认，且必须说明影响范围。**

## ⚠ 执行硬约束

1. **前置守门**：vault 未初始化（无 `.kid-initialized`）→ 不自行建档，引导先执行 kid-init
2. **必填字段不可清空**：nickname / birthdate 不允许删除，只能修改
3. **健康字段二次确认**：allergies / diet_restrictions / chronic_conditions / medical_notes 的任何变更（增/删/改），必须向家长展示变更前后对比并获确认——尤其是**删除**（误删过敏项有安全风险）
4. **age_months 重算**：每次读取或修改档案时，用当前日期重算 `age_months` 并回写
5. **写盘合规**：修改后 frontmatter 仍须符合 `references/profile-schema.json`

## 1. 何时调用

- 「查看孩子档案」「宝宝信息」→ 展示
- 「修改年龄」「添加过敏」「更新偏好」「改成每天1小时亲子时间」等字段修改 → 维护
- 多孩家庭「切换孩子」→ 改 `kid.config.yaml.active_child`
- 其他技能缺档案信息时引导至此

## 2. 输入

| 参数 | 必填 | 说明 |
|------|------|------|
| `child_id` | 否 | 默认 `kid.config.yaml.active_child` |
| 操作 | 是 | `view` / `update <字段> <新值>` / `switch <child_id>` |
| `dimension` | 否 | 查看/修改限定某维度（basic/health/development/preference/family） |

## 3. 工作流

### 步骤 1 · 定位档案

1. 读 `kid.config.yaml` → active_child → `00_profiles/<child-id>/profile.md`
2. 文件不存在 → 检查 `children[]` 是否有其他儿童并提示选择；vault 未初始化 → 引导 kid-init

### 步骤 2A · 查看（view）

1. 按五维度分组展示：
   - **基础身份**：昵称、月龄（重算后）、性别、性格
   - **健康与禁忌** 🔴：过敏、饮食禁忌、慢性疾病、医疗注意（红色/加粗高亮）
   - **发展状态**：运动/语言/认知水平、作息
   - **偏好与习惯**：喜好/厌恶、兴趣、已会技能、习惯目标
   - **家庭条件**：亲子时长、饮食风格、场地、食材范围
2. 附 tags.md 摘要（近期自动沉淀的偏好/能力标签）
3. 空维度标注「暂未填写，可现在补充」

### 步骤 2B · 修改（update）

1. 解析目标字段与新值（自然语言 → schema 字段映射，如「对鸡蛋过敏」→ `allergies: +鸡蛋`）
2. **非健康字段**：直接更新 + `updated: <today>` + 重算 age_months
3. **健康字段**：展示前后对比 → 二次确认 → 更新
4. **影响提示**（每次修改后输出）：

| 变更涉及 | 影响模块 | 提示文案要点 |
|---------|---------|-------------|
| allergies / diet_restrictions | menu | 新过敏原将从下一次菜单生成起绝对排除 |
| interests / food_likes | menu, games, learning | 推荐将优先匹配新偏好 |
| birthdate / age_months | 全部 | 分龄标准整体切换到新月龄段 |
| parent_time_daily_min | learning, games | 方案时长上限随之调整 |
| habits_target | learning | 习惯培养环节选题更新 |

### 步骤 2C · 切换儿童（switch）

改 `kid.config.yaml.active_child` → 简报展示新活跃儿童摘要。

## 4. 输出契约

- 查看：五维度展示 + tags 摘要（纯展示，无写盘，除 age_months 重算回写）
- 修改：更新后的字段 diff 摘要（旧值 → 新值）+ 影响说明
- frontmatter 始终符合 `references/profile-schema.json`

## 5. 边界

- 不删除必填字段；不直接编造家长未提供的值（缺失即标注）
- tags.md 由 kid-journal 维护，本技能只读不写（家长口述偏好写入 profile 偏好维度，不写 tags）
- 不做发展水平「诊断」，development 维度只记录家长自评与里程碑对照结果

## 6. 降级路径

| 场景 | 行为 |
|------|------|
| 档案存在但 required 字段缺失 | 触发补全引导（逐项询问缺失字段，走 update 流程） |
| 修改指令含糊（「改一下吃的偏好」） | 反问澄清具体增/删项，一次确认 |
| 家长拒绝二次确认 | 不写入，保留原值并说明 |
| 多孩 child_id 不存在 | 列出 children[] 供选择 |

## 7. 幂等保证

- 相同 update 重复执行：结果一致（列表字段按「已存在则跳过」处理）
- age_months 重算天然幂等

## 8. 自检清单

- [ ] 定位档案路径正确（active_child 解析无误）
- [ ] age_months 已按当前日期重算
- [ ] 健康字段变更执行了二次确认（含删除场景）
- [ ] 修改后 frontmatter 仍符合 profile-schema
- [ ] 输出了影响提示（哪些后续模块受影响）
- [ ] 未触碰 tags.md
