# kid-system · 育儿实践成长系统

> 面向 0-12 岁儿童家长的全链路科学育儿实践管理技能包（Claude Code Skill Pack）
>
> Full-stack scientific parenting skill pack for parents of children aged 0-12.

[![CI](https://github.com/shichu2024/kid-system/actions/workflows/ci.yml/badge.svg)](../../actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 一、这是什么 / What is this

kid-system 以**儿童个性化成长档案**为核心，构建完整的育儿实践闭环：

```
档案初始化 → 知识规则注入 → 每日成长记录 → 个性化方案生成 → 数据沉淀迭代
    │              │               │               │               │
 kid-init      kid-rules      kid-journal   kid-menu /        kid-review
 kid-profile                 (五维日志)     kid-learning /     (周月复盘)
                                           kid-games /        (里程碑追踪)
                                           kid-plan
```

**核心价值**：
- **个性化** — 基于儿童专属档案与历史行为数据，千人千面的方案匹配
- **闭环化** — 日志驱动优化，数据自动沉淀，持续迭代推荐精准度
- **标准化** — 内置《中国居民膳食指南（2022）》、儿童发育里程碑等权威分龄资源
- **安全优先** — 过敏/禁忌绝对过滤，3 岁以下窒息风险物品零出现，不做医疗诊断

## 二、技能清单 / Skills

| 技能 | 功能 | 触发示例 |
|------|------|---------|
| `kid-init` | 初始化 vault + 5 步分步引导建档 | 「初始化档案」「建立孩子资料」 |
| `kid-profile` | 查看/修改儿童档案 | 「查看孩子档案」「添加过敏」 |
| `kid-rules` | 育儿知识注入与规则管理（冲突校验） | 「注入规则」「设定喂养要求」 |
| `kid-journal` | 每日成长日志（五维度记录+自动沉淀） | 「记录今天」「写日志」 |
| `kid-menu` | 每日个性化菜单推荐 | 「今日菜单」「把午餐换成清淡的」 |
| `kid-learning` | 每日分龄学习计划 | 「今日学习计划」 |
| `kid-games` | 亲子游戏推荐（场景×能力×时长） | 「今日游戏推荐」「增加户外游戏」 |
| `kid-plan` | 今日完整方案 + 批量 3-7 天 | 「今日方案」「未来 3 天计划」 |
| `kid-review` | 周期复盘 + 里程碑追踪 + 异常预警 | 「周总结」「月度报告」「成长复盘」 |

## 三、快速开始 / Quick Start

### 安装

```bash
# 方式 1：Claude Code 插件市场
/plugin marketplace add shichu2024/kid-system

# 方式 2：npx skills
npx skills add shichu2024/kid-system

# 方式 3：手动安装（Claude Code）
git clone https://github.com/shichu2024/kid-system.git ~/.claude/skills/kid-system/
```

### 使用

1. 在一个空目录（建议专用的育儿数据目录）中启动 Claude Code
2. 输入「初始化档案」，系统将分 5 步引导你完成孩子档案搭建：
   - 核心基础信息（月龄/性别/昵称）
   - 关键健康信息（过敏史/禁忌/慢性疾病）
   - 性格与偏好（饮食喜好/兴趣倾向）
   - 家庭养育条件（亲子时长/常用食材/活动场地）
   - 确认档案，正式启用
3. 日常使用：每天「记录今天」写日志 → 「今日方案」获取次日菜单+学习+游戏推荐
4. 每周/每月：「周总结」「月度报告」查看成长复盘与优化建议

### Web 仪表盘

内置轻量可视化仪表盘（`web/dashboard.html`），读取 vault 数据展示档案、方案、日志、规则与复盘：

```bash
cd <你的vault目录>
python -m http.server 8080   # 或 npx serve
# 浏览器打开 kid-system/web/dashboard.html
```

## 四、数据安全与边界 / Safety & Boundaries

- **知识/数据分离**：内置知识库随技能包更新；你的孩子档案、日志、规则等用户数据存放在你自己的 vault 目录，技能升级**永不覆盖**
- **隐私保护**：不要求提供儿童姓名、照片、住址等敏感个人信息
- **医疗边界**：不提供医疗诊断与处方；孩子生病时仅提供通用家庭护理建议并提示就医指征
- **不评判**：不评价养育方式，只提供可选方案与优化建议

## 五、仓库结构 / Repository Structure

```
├── skills/          # 9 个技能（SKILL.md）
├── templates/       # 中英双语 8 类输出模板
├── references/      # 内置知识库（营养标准/辅食分龄/里程碑/睡眠/安全/游戏库）
├── docs/            # DESIGN.md（真相源）、SKILLS_SPEC.md、CHANGELOG.md
├── scripts/         # frontmatter / 死链校验脚本
├── web/             # 轻量仪表盘（单文件 HTML）
└── examples/        # demo-vault 完整示例
```

## 六、许可 / License

MIT © 2026 shichu2024

> **免责声明**：本技能包提供的育儿建议基于公开权威指南整理，仅供参考，不能替代专业医疗诊断与治疗。孩子出现健康异常时请及时就医。
