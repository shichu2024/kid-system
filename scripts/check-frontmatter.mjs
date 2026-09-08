#!/usr/bin/env node
/**
 * check-frontmatter.mjs — 校验 kid-system 数据文件的 frontmatter 合规性
 *
 * 用法：node scripts/check-frontmatter.mjs <dir> [dir...]
 *
 * 规则（依据 references/journal-schema.json 与 profile-schema.json）：
 * 1. 所有 .md 数据文件必须有 YAML frontmatter（--- 包裹）
 * 2. 按文件位置推断类型并校验 required 字段：
 *    - 00_profiles/ 下任意子目录的 profile.md  → child_id, nickname, birthdate, gender, allergies, created, updated
 *    - 01_journal/ 下所有 .md       → date, child_id, health_status
 *    - 02_plans/*.md              → date, child_id, plan_type
 *    - 04_reviews/**（weekly|monthly）→ period, child_id
 *    - 03_rules/rules.md          → 仅要求 frontmatter 存在（条目在正文中管理）
 *    - 04_reviews/milestones.md   → 仅要求 frontmatter 存在
 * 3. 枚举校验：health_status ∈ {healthy, ill, recovering}；plan_type ∈ {daily, weekly_batch}
 *    period ∈ {weekly, monthly, custom}
 * 4. date 类字段必须为 ISO YYYY-MM-DD
 *
 * 跳过：隐藏目录、node_modules、templates/、99_system/、README.md
 */

import { readdirSync, readFileSync, statSync, existsSync } from 'node:fs'
import { join, relative } from 'node:path'

const ENUMS = {
  health_status: ['healthy', 'ill', 'recovering'],
  plan_type: ['daily', 'weekly_batch'],
  period: ['weekly', 'monthly', 'custom'],
  health_mode: ['normal', 'care'],
}

const REQUIRED = {
  profile: ['child_id', 'nickname', 'birthdate', 'gender', 'allergies', 'created', 'updated'],
  journal: ['date', 'child_id', 'health_status'],
  plan: ['date', 'child_id', 'plan_type'],
  review: ['period', 'child_id'],
  minimal: [],
}

const DATE_FIELDS = ['date', 'birthdate', 'created', 'updated']

/** 极简 frontmatter 解析：仅顶层 key: value（数组值取整行，不做嵌套解析） */
function parseFrontmatter(text) {
  const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---/)
  if (!m) return null
  const fm = {}
  for (const line of m[1].split(/\r?\n/)) {
    const kv = line.match(/^([A-Za-z_][\w]*):\s*(.*)$/)
    if (kv) fm[kv[1]] = kv[2].replace(/^['"]|['"]$/g, '').trim()
  }
  return fm
}

function classify(relPath) {
  const p = relPath.replace(/\\/g, '/')
  // v1.3 多儿童布局：<child-id> 目录层（单双儿童一致）
  if (/^00_profiles\/[^/]+\/profile\.md$/.test(p)) return 'profile'
  if (/^01_journal\/[^/]+\/\d{4}-\d{2}\/[^/]+\.md$/.test(p)) return 'journal'
  if (/^02_plans\/[^/]+\/\d{4}-\d{2}-\d{2}\.md$/.test(p)) return 'plan'
  if (/^04_reviews\/[^/]+\/(weekly|monthly)\/[^/]+\.md$/.test(p)) return 'review'
  if (/^04_reviews\/[^/]+\/milestones\.md$/.test(p) || /^03_rules\//.test(p)) return 'minimal'
  return null
}

function walk(dir, acc = []) {
  for (const name of readdirSync(dir)) {
    if (name.startsWith('.') || name === 'node_modules' || name === 'templates' || name === '99_system') continue
    if (name === 'README.md') continue
    const full = join(dir, name)
    const st = statSync(full)
    if (st.isDirectory()) walk(full, acc)
    else if (name.endsWith('.md')) acc.push(full)
  }
  return acc
}

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/
let errors = 0
let checked = 0

function fail(file, msg) {
  errors++
  console.error(`  ✘ ${file}: ${msg}`)
}

for (const root of process.argv.slice(2)) {
  if (!existsSync(root)) {
    console.error(`目录不存在: ${root}`)
    process.exit(1)
  }
  for (const file of walk(root)) {
    const rel = relative(root, file)
    const type = classify(rel)
    if (!type) continue
    checked++
    const fm = parseFrontmatter(readFileSync(file, 'utf8'))
    if (!fm) {
      fail(rel, '缺少 frontmatter（--- 包裹的 YAML）')
      continue
    }
    for (const field of REQUIRED[type]) {
      if (!(field in fm) || fm[field] === '') fail(rel, `缺少必填字段: ${field}`)
    }
    for (const [field, allowed] of Object.entries(ENUMS)) {
      if (field in fm && fm[field] !== '' && !allowed.includes(fm[field])) {
        fail(rel, `字段 ${field}="${fm[field]}" 不在枚举 [${allowed.join(', ')}]`)
      }
    }
    for (const field of DATE_FIELDS) {
      if (field in fm && fm[field] !== '' && !ISO_DATE.test(fm[field]) && !/^\d{4}-\d{2}-\d{2}\s*$/.test(fm[field])) {
        // date_range 等复合字段跳过；birthdate/date/created/updated 必须 ISO
        if (field === 'date' || field === 'birthdate') fail(rel, `字段 ${field}="${fm[field]}" 非 ISO 日期`)
      }
    }
  }
}

console.log(`\n检查完成: ${checked} 个数据文件, ${errors} 个错误`)
process.exit(errors ? 1 : 0)
