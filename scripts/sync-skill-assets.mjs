#!/usr/bin/env node
/**
 * sync-skill-assets.mjs — 把仓库根的共享资产同步进各技能目录（自包含安装）
 *
 * 背景：per-skill 安装器（如 `npx skills add shichu2024/kid-system`）只拷贝
 * `skills/<name>/` 目录。仓库根的 templates/ references/ knowledge/ 是唯一
 * 编辑源（authoring source），本脚本按各 SKILL.md 声明的依赖映射复制副本进
 * `skills/<name>/`，使每个技能目录自包含。
 *
 * 用法：
 *   node scripts/sync-skill-assets.mjs          # 同步（幂等）
 *   node scripts/sync-skill-assets.mjs --check  # 只校验，不同步；有漂移 exit 1
 *
 * 规则：
 * - 复制目标存在即覆盖为根目录内容（根 = 单一真相源）
 * - en 变体自动镜像：zh 条目存在对应 en 文件（templates/en/、references/en/、
 *   knowledge/en/）时一并同步
 * - 目标目录中不在映射内的多余文件会被报告（--check 模式下报错），防止残留
 */

import { copyFileSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync } from 'node:fs'
import { dirname, join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'

const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')

/**
 * 技能 → 依赖资产映射（依据各 SKILL.md「依赖」声明，勿随意增删）
 * templates: templates/{zh,en}/ 下的文件名（不含语言目录）
 * references: references/ 下的文件名
 * knowledge: knowledge/ 下的文件名
 */
const ASSET_MAP = {
  'kid-init': {
    templates: ['dish.md', 'daily-menu.md', 'game.md', 'learning-plan.md', 'journal.md', 'weekly-review.md', 'monthly-report.md', 'milestone-timeline.md'],
    references: ['profile-schema.json'],
    knowledge: [],
  },
  'kid-profile': {
    templates: [],
    references: ['profile-schema.json'],
    knowledge: [],
  },
  'kid-rules': {
    templates: [],
    references: ['journal-schema.json'],
    knowledge: [],
  },
  'kid-journal': {
    templates: ['journal.md'],
    references: ['journal-schema.json', 'safety-rules.json'],
    knowledge: ['problem-navigation.md'],
  },
  'kid-menu': {
    templates: ['dish.md', 'daily-menu.md'],
    references: ['nutrition-standards.md', 'feeding-stages.json', 'safety-rules.json'],
    knowledge: [],
  },
  'kid-learning': {
    templates: ['learning-plan.md'],
    references: ['milestones.json', 'safety-rules.json'],
    knowledge: ['picture-books.md'],
  },
  'kid-games': {
    templates: ['game.md'],
    references: ['games-library.json', 'safety-rules.json'],
    knowledge: ['quick-rescue-games.md'],
  },
  'kid-plan': { templates: [], references: [], knowledge: [] },
  'kid-review': {
    templates: ['weekly-review.md', 'monthly-report.md', 'milestone-timeline.md'],
    references: ['milestones.json', 'safety-rules.json', 'sleep-guide.json'],
    knowledge: [],
  },
}

const LANG_DIRS = { templates: ['zh', 'en'], references: ['.', 'en'], knowledge: ['.', 'en'] }

function listDir(dir) {
  if (!existsSync(dir)) return []
  return readdirSync(dir).filter((f) => !f.startsWith('.'))
}

function syncFile(src, dest, checkMode, issues) {
  const label = relative(REPO_ROOT, dest)
  if (!existsSync(src)) {
    issues.push(`缺失源文件: ${relative(REPO_ROOT, src)}（映射声明了但仓库根不存在）`)
    return
  }
  if (existsSync(dest) && readFileSync(dest, 'utf8') === readFileSync(src, 'utf8')) return
  if (checkMode) {
    issues.push(`未同步/内容不一致: ${label}`)
  } else {
    mkdirSync(dirname(dest), { recursive: true })
    copyFileSync(src, dest)
    console.log(`synced: ${label}`)
  }
}

function cleanExtraFiles(skillDir, expected, checkMode, issues) {
  for (const assetKind of ['templates', 'references', 'knowledge']) {
    const kindDir = join(skillDir, assetKind)
    if (!existsSync(kindDir)) continue
    const walk = (dir) => {
      for (const entry of listDir(dir)) {
        const full = join(dir, entry)
        if (statSync(full).isDirectory()) {
          walk(full)
        } else {
          const relInSkill = relative(skillDir, full).split('\\').join('/')
          if (!expected.has(relInSkill)) {
            if (checkMode) {
              issues.push(`映射外多余文件: ${relative(REPO_ROOT, full)}`)
            } else {
              rmSync(full)
              console.log(`removed extra: ${relative(REPO_ROOT, full)}`)
            }
          }
        }
      }
    }
    walk(kindDir)
  }
}

const checkMode = process.argv.includes('--check')
const issues = []
let synced = 0

for (const [skill, map] of Object.entries(ASSET_MAP)) {
  const skillDir = join(REPO_ROOT, 'skills', skill)
  const expected = new Set()

  for (const tpl of map.templates) {
    for (const lang of LANG_DIRS.templates) {
      const src = join(REPO_ROOT, 'templates', lang, tpl)
      if (!existsSync(src) && lang === 'zh') {
        issues.push(`缺失源文件: templates/${lang}/${tpl}`)
        continue
      }
      if (!existsSync(src)) continue
      expected.add(`templates/${lang}/${tpl}`)
      syncFile(src, join(skillDir, 'templates', lang, tpl), checkMode, issues)
    }
  }

  for (const kind of ['references', 'knowledge']) {
    for (const name of map[kind]) {
      for (const langDir of LANG_DIRS[kind]) {
        const sub = langDir === '.' ? [] : [langDir]
        const src = join(REPO_ROOT, kind, ...sub, name)
        if (!existsSync(src)) {
          if (langDir === '.') issues.push(`缺失源文件: ${kind}/${name}`)
          continue
        }
        const destRel = [kind, ...sub, name].join('/')
        expected.add(destRel)
        syncFile(src, join(skillDir, ...sub.length ? [kind, ...sub, name] : [kind, name]), checkMode, issues)
      }
    }
  }

  cleanExtraFiles(skillDir, expected, checkMode, issues)
  synced += expected.size
}

if (issues.length) {
  console.error(`\n[skill-assets] ${checkMode ? '校验失败' : '警告'}:`)
  for (const i of issues) console.error(`  - ${i}`)
  if (checkMode) {
    console.error('\n请运行 `node scripts/sync-skill-assets.mjs` 后提交（根目录资产是唯一编辑源）。')
    process.exit(1)
  }
}

console.log(`\n[skill-assets] ${checkMode ? 'OK：技能目录资产与根目录一致' : `同步完成：${synced} 个捆绑文件`}`)
