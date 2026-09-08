#!/usr/bin/env node
/**
 * check-links.mjs — 校验 kid-system 仓库内 Markdown 链接与 vault wikilink 无死链
 *
 * 用法：node scripts/check-links.mjs <root> [root...]
 *
 * 检查范围：
 * 1. 相对路径 Markdown 链接 [text](path.md) / [text](./dir/) — 目标须存在
 * 2. Wikilink [[target]] / [[target|alias]] — 按 basename 匹配（Obsidian 约定），
 *    target 存在于任一扫描根则通过
 * 3. 跳过：http(s) 外链、#anchor、{{...}} 占位符、images
 */

import { readdirSync, readFileSync, statSync, existsSync } from 'node:fs'
import { join, relative, dirname, resolve } from 'node:path'

function walk(dir, acc = []) {
  for (const name of readdirSync(dir)) {
    if (name.startsWith('.') || name === 'node_modules') continue
    const full = join(dir, name)
    const st = statSync(full)
    if (st.isDirectory()) walk(full, acc)
    else if (name.endsWith('.md')) acc.push(full)
  }
  return acc
}

const mdFiles = []
for (const root of process.argv.slice(2)) {
  mdFiles.push(...walk(root))
}

// basename 索引（wikilink 用）
const basenameIndex = new Set()
const relPaths = new Set()
for (const f of mdFiles) {
  basenameIndex.add(f.split(/[\\/]/).pop().replace(/\.md$/, ''))
}

let errors = 0
const MD_LINK = /\[([^\]]*)\]\(([^)\s]+)[^)]*\)/g
const WIKILINK = /\[\[([^\]|]+)(?:\|[^\]]+)?\]\]/g

for (const file of mdFiles) {
  const text = readFileSync(file, 'utf8')
  const rel = relative(process.cwd(), file)

  for (const m of text.matchAll(MD_LINK)) {
    const target = m[2]
    if (/^(https?:|mailto:|#|data:)/.test(target)) continue
    if (target.includes('{{')) continue
    const resolved = resolve(dirname(file), target.replace(/#.*$/, ''))
    if (!existsSync(resolved)) {
      errors++
      console.error(`  ✘ ${rel}: 死链 [${m[1]}](${target})`)
    }
  }

  for (const m of text.matchAll(WIKILINK)) {
    const target = m[1].trim().replace(/#.*$/, '')
    if (!target || target.includes('{{')) continue
    if (!basenameIndex.has(target)) {
      errors++
      console.error(`  ✘ ${rel}: 死 wikilink [[${target}]]`)
    }
  }
}

console.log(`\n链接检查完成: ${mdFiles.length} 个 md 文件, ${errors} 个死链`)
process.exit(errors ? 1 : 0)
