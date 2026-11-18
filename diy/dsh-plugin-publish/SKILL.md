---
name: dsh-plugin-publish
description: 把自研 DSH（DeepSeek Harness）插件的改动发布成「插件市场里能装到的新版本」——同步源码到 GitHub 发布仓库、升 package.json 版本、改写仓库根目录 index.json 的 versions[].version 与 source.commit、推送、刷新 jsdelivr CDN，并说明为什么 DSH 界面里还显示旧版本。Use when 用户说推送/发布插件、更新插件市场、市场里还是旧版本、要改 index.json 的 version 或 commit、问「是不是改 cordis.patch.yml 第 N 行」、或需要搞清插件市场索引配在哪里。
---

# DSH 插件发布

## 心智模型（先记住这一条）

插件市场只有一处真相：**发布仓库根目录的 `index.json`**。它给每个插件记一条 `versions[]`，里面的 `source.commit` 指向仓库里某个具体提交 —— 市场「安装」时按这个 commit 从 GitHub 拉代码，而不是拉分支最新。

所以顺序永远是：**先推代码 → 再让 index.json 指向那个提交 → 再推 index.json**。反了就会出现「市场里显示新版本，装下来还是旧代码」。

## 三个位置

| 角色 | 典型路径 | 说明 |
|---|---|---|
| 本地插件源码 | `D:\workspace\dsh-plugins\<插件>` | profile 用 `link:` 链到这里，跑的是这份；版本号以这里为准 |
| 发布仓库 | `D:\workspace\<你的发布仓库>` | 根目录 `index.json` + 每个插件一个目录 |
| 市场索引 URL | `https://cdn.jsdelivr.net/gh/<owner>/<repo>@main/index.json` | 一旦在 DSH 设置里配好就不用再改 |

路径只是本文档的示例值，脚本支持 `--src` / `--repo` 覆盖，先按用户实际目录替换。

## 别改错地方

- **`~/.dsh/profiles/<profile>/cordis.patch.yml` 不是市场索引。** 它决定「本机加载哪些 bundle 行」，索引决定「市场里能装什么、装哪个 commit」。有人会说「改第 202 行」，先读文件确认——那多半是桌宠的 `bottom: 222` 之类，跟发布完全无关。
- 市场索引的 URL 已经在 DSH 设置里配好，**不用改**。要改的一直是仓库里的文件。
- 插件市场的「已安装版本」读的是本机 `package.json`，所以本地升了版本、市场还没更新时，界面会显示 `different-version` 或旧版本号，这是数据不同步，不是安装坏了。

## 一条命令发布

脚本在 `scripts/publish.mjs`，默认只体检不写盘：

```powershell
# 0. 进入本技能目录（安装后通常是 ~/.dsh/skills/dsh-plugin-publish）
cd "$env:USERPROFILE\.dsh\skills\dsh-plugin-publish"

# 1. 先看会发生什么（只读）
node scripts/publish.mjs

# 2. 真正发布：升版本 + 同步源码 + 改索引 + 提交 + 推送 + 刷 CDN
node scripts/publish.mjs --write --commit --push --purge
```

常用参数：

| 参数 | 作用 |
|---|---|
| `--write` | 允许改文件（不加就是 dry-run） |
| `--commit` | 代码一个提交、index.json 一个提交 |
| `--push` | 推到 `origin` 并回读远端 sha 验证 |
| `--purge` | 刷新 jsdelivr 并回读 CDN 上的版本号 |
| `--minor` / `--major` | 升版本幅度（默认 patch） |
| `--no-bump` | 只同步文件、不动版本号 |
| `--plugins a,b` | 只处理指定插件 |
| `--repo <path>` / `--src <path>` | 换了仓库或源码目录时指定 |

脚本做的事：本地 `package.json` 升版本 → 复制插件目录进仓库（跳过 `.git`/`node_modules`/`dist`）→ 提交源码 → 把**那个提交的 sha** 写进 `index.json` 的 `version`、`commit`、`publishTimestamp` → 提交索引 → 推送 → 刷 CDN 并回读校验。

脚本不做的事：不跑测试、不改描述文案、不判定该升 patch 还是 minor、不处理 npm 源插件。这些要自己判断——发布前至少跑一遍插件自己的 `node --check` 和相关测试。

## 手工流程（脚本不可用时）

1. 同步源码进仓库对应目录（`dsh-global-cmd/`、`prompt-enhance/` …）。
2. 升 `package.json` 的 `version`（本地与仓库都升，避免两边打架）。
3. `git commit`，拿到 sha：`git rev-parse HEAD`。
4. 改根目录 `index.json`：该插件的 `versions[0].version` 设为新版本、`versions[0].source.commit` 设为上一步的 sha。**必须定点字符串替换**，见下面的坑。
5. 提交 index.json。
6. `git push origin HEAD`，再 `git ls-remote origin refs/heads/main` 确认远端 sha。
7. 刷新 CDN：请求 `https://purge.jsdelivr.net/gh/<owner>/<repo>@main/index.json`，然后直接 `Invoke-RestMethod` 那个索引 URL 看版本号是否已更新。
8. 告诉用户重启 DSH —— 它的插件市场在进程内缓存了索引。

## 验证清单

发布完至少确认三件事，缺一件就别汇报「已发布」：

```powershell
# 1) 远端 main 的 sha == 本地 HEAD
git -C <发布仓库> ls-remote origin refs/heads/main

# 2) CDN 上已是新版本，且 commit 与代码提交一致
(Invoke-RestMethod 'https://cdn.jsdelivr.net/gh/<owner>/<repo>@main/index.json').plugins |
  Where-Object { $_.author -eq '<你的 GitHub 用户名>' } |
  ForEach-Object { "{0} {1} {2}" -f $_.name, $_.versions[-1].version, $_.versions[-1].source.commit.Substring(0,7) }

# 3) index.json 里的 source.commit 等于代码提交的 sha（不是索引提交的 sha）
```

## 坑（都踩过）

| 坑 | 说明 |
|---|---|
| 用 `JSON.stringify` 重排 index.json | 内联的 `{ "en": ..., "zh": ... }` 会被展开成多行，一个版本号改动变成上百行 diff。用定点替换，diff 应只有 6 行左右 |
| 忘了保留 CRLF | 若仓库 `core.autocrlf=true` 且文件本来是非 CRLF 行尾，改写后按原 EOL 写回，否则整个文件都算改过 |
| 忘了 push | 市场按 commit 拉代码，本地提交没推上去 = 装不到 |
| 忘了升版本 | 市场仍按原版本号显示，且 `plugin_market` 会报 `different-version` |
| commit 指错 | `source.commit` 要指向含新代码的提交；若和索引写在同一个提交里，指向那个提交也没问题——但要确认它包含代码改动 |
| jsdelivr 缓存 | `@main` 有缓存，push 后立刻拉还是旧内容，必须 purge，再回读确认 |
| DSH 进程缓存索引 | 即使 CDN 已是新版本，`plugin_market` 仍可能返回旧的（`defaultVersion` 是旧版本号）。重启 DSH 才在界面生效 |
| 拿 `grep` 扫整个 `~/.dsh` | 里面大量 0 字节 junction，会报几百条「系统找不到指定的路径」。只按具体子目录搜 |
| 把 npm 源插件也塞进 git 发布 | 第三方插件在 `index.json` 里是 npm 源，没有本地源码目录，脚本会自动跳过 |

## 参考

- `references/market-index.md` —— index.json 的字段结构、`versions` 语义、`engines.dsh` 兼容区间、常见安装报错怎么读。
