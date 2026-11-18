#!/usr/bin/env node
// dsh-plugin-publish —— 把本地 DSH 插件发布到 GitHub 仓库 + 市场索引 index.json。
//
// 默认只做「体检」（dry-run），打印将要发生什么、以及本地与仓库的差异。
// 加 --write 才真正改文件；再加 --commit / --push / --purge 才继续往下走。
//
// 用法：
//   node publish.mjs                        # 体检：列出插件、版本、本地/仓库差异
//   node publish.mjs --write                # 升版本 + 同步源码 + 改写 index.json（不提交）
//   node publish.mjs --write --commit --push --purge
//   node publish.mjs --plugins dsh-global-cmd --minor --write --commit --push
//
// 为什么默认不写：这个脚本会覆盖发布仓库里的插件目录，先看一遍 diff 比事后回滚便宜。
// 为什么版本号在「本地」升：profile 里插件是 link 到本地目录的，本地 package.json 就是唯一真相，
// 升完再整体复制进仓库，两边不会打架。

import { readFileSync, writeFileSync, existsSync, cpSync, readdirSync } from 'node:fs'
import { join, relative } from 'node:path'
import { execFileSync } from 'node:child_process'

// ------------------------------------------------------------------ 参数

const argv = process.argv.slice(2)

function flag(name) {
  return argv.includes(name)
}

function option(name, fallback) {
  const index = argv.indexOf(name)
  const next = index >= 0 ? argv[index + 1] : undefined
  return next && !next.startsWith('--') ? next : fallback
}

const REPO = option('--repo', 'D:\\workspace\\dsh-personal-agent')
const SRC_ROOT = option('--src', 'D:\\workspace\\dsh-plugins')
const KIND = flag('--major') ? 'major' : flag('--minor') ? 'minor' : 'patch'
const ONLY = option('--plugins', '')
  .split(',')
  .map((item) => item.trim())
  .filter(Boolean)
const WRITE = flag('--write')
const COMMIT = flag('--commit')
const PUSH = flag('--push')
const PURGE = flag('--purge')
const NO_BUMP = flag('--no-bump')

// 复制时跳过的东西：仓库里不需要，而且会让 diff 一片红。
const SKIP = new Set(['.git', 'node_modules', '.DS_Store', '.idea', 'dist', '.cache'])

// ------------------------------------------------------------------ 小工具

const log = (...parts) => console.log(...parts)

function fail(message) {
  console.error(`\n✗ ${message}\n`)
  process.exit(1)
}

function git(args, { quiet = false } = {}) {
  const output = execFileSync('git', ['-C', REPO, ...args], {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
  })
  if (!quiet) log(`$ git ${args.join(' ')}`)
  return output.trim()
}

function readJson(path) {
  return JSON.parse(readFileSync(path, 'utf8'))
}

function writeJson(path, value) {
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`, 'utf8')
}

function bump(version, kind) {
  const parts = String(version).split('.').map((part) => Number.parseInt(part, 10) || 0)
  while (parts.length < 3) parts.push(0)
  if (kind === 'major') return `${parts[0] + 1}.0.0`
  if (kind === 'minor') return `${parts[0]}.${parts[1] + 1}.0`
  return `${parts[0]}.${parts[1]}.${parts[2] + 1}`
}

// index.json 是「手工维护 + 定点替换」的文件：不能 JSON.stringify 整份重排，
// 否则内联的 { "en": ..., "zh": ... } 会展开成多行，一个版本号改动变成上百行 diff。
function findObjectRange(text, anchor) {
  const stack = []
  for (let i = 0; i < anchor; i += 1) {
    const char = text[i]
    if (char === '{' || char === '[') stack.push({ char, index: i })
    else if (char === '}' || char === ']') stack.pop()
  }
  let start = -1
  for (let i = stack.length - 1; i >= 0; i -= 1) {
    if (stack[i].char === '{') {
      start = stack[i].index
      break
    }
  }
  if (start < 0) throw new Error('index.json 结构异常：找不到插件对象起点')
  let depth = 0
  for (let i = start; i < text.length; i += 1) {
    if (text[i] === '{') depth += 1
    else if (text[i] === '}') {
      depth -= 1
      if (depth === 0) return { start, end: i + 1 }
    }
  }
  throw new Error('index.json 结构异常：插件对象没有闭合')
}

function replaceFirst(block, field, literal) {
  const pattern = new RegExp(`("${field}"\\s*:\\s*)([^,\\n]+)`)
  if (!pattern.test(block)) throw new Error(`index.json 里找不到字段 ${field}`)
  return block.replace(pattern, (_, head) => `${head}${literal}`)
}

// ------------------------------------------------------------------ 体检

if (!existsSync(join(REPO, 'index.json'))) {
  fail(`发布仓库不像是对的位置：${REPO}\n  （没找到 index.json。用 --repo 指定克隆目录，或先 git clone）`)
}
if (!existsSync(SRC_ROOT)) fail(`本地插件目录不存在：${SRC_ROOT}`)

const indexPath = join(REPO, 'index.json')
const rawIndex = readFileSync(indexPath, 'utf8')
const eol = rawIndex.includes('\r\n') ? '\r\n' : '\n'
let indexText = rawIndex.replace(/\r\n/g, '\n')
const indexJson = JSON.parse(indexText)

const entries = indexJson.plugins ?? []
const targets = []
for (const entry of entries) {
  const short = String(entry.name).replace(/^@[^/]+\//, '')
  const dirName = entry.repository?.directory || entry.versions?.[0]?.source?.path || short
  const srcDir = join(SRC_ROOT, dirName)
  if (ONLY.length && !ONLY.includes(short) && !ONLY.includes(entry.name)) continue
  if (!existsSync(join(srcDir, 'package.json'))) {
    // 第三方插件（npm 源）在本地没有源码目录，跳过很正常。
    if (!entry.versions?.some((version) => version.source?.type === 'git')) continue
    log(`! ${short}：索引里是 git 源，但本地没找到 ${srcDir}（跳过）`)
    continue
  }
  targets.push({ entry, short, dirName, srcDir, repoDir: join(REPO, dirName) })
}

if (!targets.length) fail('没有可发布的插件。用 --plugins <名字> 指定，或检查 --src 路径。')

const plan = targets.map((target) => {
  const localPkg = readJson(join(target.srcDir, 'package.json'))
  const repoPkgPath = join(target.repoDir, 'package.json')
  const repoPkg = existsSync(repoPkgPath) ? readJson(repoPkgPath) : { version: '(仓库里没有)' }
  const next = NO_BUMP ? localPkg.version : bump(localPkg.version, KIND)
  return {
    ...target,
    localPkg,
    repoVersion: repoPkg.version,
    currentVersion: localPkg.version,
    nextVersion: next,
    sourceChanged: diffDirs(target.srcDir, target.repoDir),
  }
})

function diffDirs(from, to) {
  // 只做粗粒度的「有没有不同」判断，给体检输出用；细看还是看 git diff。
  if (!existsSync(to)) return '新增'
  const stack = ['']
  while (stack.length) {
    const rel = stack.pop()
    const fromDir = join(from, rel)
    const toDir = join(to, rel)
    for (const name of readdirSync(fromDir, { withFileTypes: true })) {
      if (SKIP.has(name.name)) continue
      const relPath = rel ? `${rel}/${name.name}` : name.name
      if (name.isDirectory()) {
        if (!existsSync(join(to, relPath))) return `仓库缺 ${relPath}`
        stack.push(relPath)
        continue
      }
      const toFile = join(to, relPath)
      if (!existsSync(toFile)) return `仓库缺 ${relPath}`
      if (!readFileSync(join(from, relPath)).equals(readFileSync(toFile))) return `有改动 ${relPath}`
    }
  }
  return '一致'
}

log(`\n仓库：${REPO}`)
log(`源码：${SRC_ROOT}`)
log(`模式：${WRITE ? '写入' : '体检（dry-run，加 --write 才动文件）'}  升版本：${NO_BUMP ? '否' : KIND}\n`)
log('插件\t\t仓库版本\t→\t新版本\t源码差异')
for (const item of plan) {
  log(`${item.short}\t${item.repoVersion}\t→\t${item.nextVersion}\t${item.sourceChanged}`)
}

if (ONLY.length) log(`\n仅处理：${ONLY.join(', ')}`)

if (!WRITE) {
  log('\n体检结束。确认无误后加 --write（可再叠加 --commit --push --purge）。')
  process.exit(0)
}

// ------------------------------------------------------------------ 写文件

for (const item of plan) {
  const localPkgPath = join(item.srcDir, 'package.json')
  if (!NO_BUMP) {
    const nextPkg = { ...item.localPkg, version: item.nextVersion }
    writeJson(localPkgPath, nextPkg)
    log(`· 本地版本 → ${item.nextVersion}  ${relative(SRC_ROOT, localPkgPath)}`)
  }
  cpSync(item.srcDir, item.repoDir, {
    recursive: true,
    force: true,
    filter: (source) => {
      const name = source.split(/[\\/]/).pop()
      return !SKIP.has(name)
    },
  })
  log(`· 同步源码 → ${relative(REPO, item.repoDir)}`)
}

// ------------------------------------------------------------------ 提交代码

let codeCommit = null
if (COMMIT) {
  const paths = plan.map((item) => item.dirName)
  git(['add', '--', ...paths])
  const summary = plan.map((item) => `${item.short}@${item.nextVersion}`).join(', ')
  const staged = git(['diff', '--cached', '--name-only'], { quiet: true })
  if (!staged) {
    log('· 源码没有实际改动，跳过代码提交')
  } else {
    const first = plan[0]
    const message =
      plan.length === 1
        ? `feat(${first.short}): release ${first.nextVersion}`
        : `chore: sync plugin sources (${summary})`
    git(['commit', '-q', '-m', message])
    log(`· 代码提交：${git(['rev-parse', '--short', 'HEAD'], { quiet: true })}  ${message}`)
  }
  codeCommit = git(['rev-parse', 'HEAD'], { quiet: true })
} else {
  codeCommit = git(['rev-parse', 'HEAD'], { quiet: true })
  log('· 未加 --commit：index.json 将指向当前 HEAD（先确认它包含本次代码）')
}

// ------------------------------------------------------------------ 改写 index.json

const timestamp = Math.floor(Date.now() / 1000)
for (const item of plan) {
  const anchor = indexText.indexOf(`"name": "${item.entry.name}"`)
  if (anchor < 0) throw new Error(`index.json 里找不到插件 ${item.entry.name}`)
  const { start, end } = findObjectRange(indexText, anchor)
  let block = indexText.slice(start, end)
  block = replaceFirst(block, 'version', JSON.stringify(item.nextVersion))
  block = replaceFirst(block, 'commit', JSON.stringify(codeCommit))
  block = replaceFirst(block, 'publishTimestamp', String(timestamp))
  indexText = indexText.slice(0, start) + block + indexText.slice(end)
  log(`· 索引：${item.short} → ${item.nextVersion} @ ${codeCommit.slice(0, 7)}`)
}

const verify = JSON.parse(indexText) // 写回前先确认还是合法 JSON
writeFileSync(indexPath, indexText.replace(/\n/g, eol), 'utf8')
log(`· 已写回 index.json（${eol === '\r\n' ? 'CRLF' : 'LF'}，${verify.plugins.length} 个插件）`)

if (COMMIT) {
  git(['add', '--', 'index.json'])
  const summary = plan.map((item) => `${item.short} ${item.nextVersion}`).join(', ')
  git(['commit', '-q', '-m', `chore(index): publish ${summary}`])
  log('· 索引提交完成')
}

// ------------------------------------------------------------------ 推送与刷新

if (PUSH) {
  log(git(['push', 'origin', 'HEAD']))
  const remote = git(['ls-remote', 'origin', 'refs/heads/main'], { quiet: true })
  log(`· 远端 main：${remote.split(/\s+/)[0]}`)
} else {
  log('· 未推送（加 --push）。别忘了：市场按 commit 拉代码，没推上去就装不到。')
}

if (PURGE) {
  const repoSlug = git(['remote', 'get-url', 'origin'], { quiet: true })
    .replace(/^.*github\.com[:/]/, '')
    .replace(/\.git$/, '')
  const url = `https://purge.jsdelivr.net/gh/${repoSlug}@main/index.json`
  const purged = await fetch(url).then((response) => response.json())
  log(`· jsdelivr 刷新：${purged.status}`)
  const served = await fetch(
    `https://cdn.jsdelivr.net/gh/${repoSlug}@main/index.json?t=${Date.now()}`,
  ).then((response) => response.json())
  for (const item of plan) {
    const hit = served.plugins.find((plugin) => plugin.name === item.entry.name)
    const version = hit?.versions?.at(-1)
    log(`  CDN 现在：${item.short} ${version?.version} @ ${String(version?.source?.commit).slice(0, 7)}`)
  }
}

log('\n完成。DSH 的插件市场缓存了索引，要重启 DSH 才能在界面里看到新版本。')
