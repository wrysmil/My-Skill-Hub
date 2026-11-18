# dsh-plugin-publish

把自研的 [DeepSeek Harness (DSH)](https://github.com/deepseek-ai) 插件发布成「插件市场里能装到的新版本」的技能包。含一份操作手册和一个能一条命令跑完发布流程的脚本。

## 它解决什么问题

DSH 插件市场不是「推个 npm 包就完事」：市场数据来自一个**你自己维护的 GitHub 仓库**，仓库根目录有 `index.json` 记录每个插件的版本与 `source.commit`，市场安装时按这个 commit 拉代码。于是发布要同时动两个地方（源码 + 索引），漏一步的典型后果是：市场显示新版本、装下来却是旧代码。

这个技能把这些步骤、顺序和踩过的坑固化下来，并提供脚本自动完成机械部分。

## 安装

放到 DSH 的技能目录即可（个人级）：

```powershell
# Windows
Copy-Item . "$env:USERPROFILE\.dsh\skills\dsh-plugin-publish" -Recurse -Force
```

DSH 下次启动/刷新会话时会在技能目录里发现它（名称 `dsh-plugin-publish`）。Claude Code / Codex 等支持 Agent Skills 的工具，也可以直接把这个目录放进各自的 skills 路径。

## 快速开始

```powershell
cd "$env:USERPROFILE\.dsh\skills\dsh-plugin-publish"

# 体检：只读，告诉你哪个插件有改动、版本会升到多少
node scripts/publish.mjs --repo D:\workspace\<你的发布仓库> --src D:\workspace\dsh-plugins

# 发布：升版本 + 同步源码 + 改索引 + 提交 + 推送 + 刷 CDN
node scripts/publish.mjs --repo D:\workspace\<你的发布仓库> --src D:\workspace\dsh-plugins --write --commit --push --purge
```

默认仓库/源码路径写在脚本顶部常量里（`D:\workspace\dsh-personal-agent`、`D:\workspace\dsh-plugins`），换成自己的，或用 `--repo` / `--src` 覆盖。

## 目录结构

```
dsh-plugin-publish/
├── SKILL.md                  # 技能入口：心智模型、流程、坑清单
├── references/
│   └── market-index.md       # index.json 字段语义、安装报错怎么读
└── scripts/
    └── publish.mjs           # 发布脚本（默认 dry-run）
```

## 脚本做了什么

1. 读发布仓库的 `index.json`，找出「本地有源码」的插件；
2. 升本地 `package.json` 的版本（patch / `--minor` / `--major`）；
3. 把插件目录复制进仓库（跳过 `.git`、`node_modules`、`dist`，以及 `.tmp-*`、`*.tmp`、`*.bak` 这类临时产物）；
4. 提交源码，拿到**代码提交的 sha**；
5. 把 sha 与新版本写进 `index.json`（定点字符串替换，保留原行尾）；
6. 提交索引 → 推送 → 刷新 jsdelivr → 回读 CDN 校验。

不做：跑测试、改文案、判断该升哪个版本位、处理 npm 源插件。发布前请自己跑一遍插件的 `node --check` 与测试。

## 已验证

- 在临时克隆的仓库副本上跑通 `--write --commit --minor`：两个插件版本正确升级、源码同步无残留、只产生两次提交；
- `index.json` 改动仅 6 行（version / publishTimestamp / commit 各两处），内联双语字段没有被拆行；
- CRLF 行尾保留，`JSON.parse` 校验通过；
- 写入的 `source.commit` 等于代码提交的 sha，而非索引提交的 sha；
- 真实仓库在 dry-run 后保持干净（脚本默认不写盘）。

## 适用范围

- ✅ DSH 插件（bundle 形式：`package.json` + `cordis.patch.yml` + `index.js` / `client.js`）的版本发布
- ✅ 任何「GitHub 仓库 + 根目录 index.json 清单」式的市场结构（如 DSH 插件市场索引）
- ❌ npm 源第三方插件的发布（不在本技能范围）
- ❌ 插件代码本身的构建与打包（假定源码已可运行）

## 许可

MIT。脚本按「现状」提供，会修改发布仓库文件，请先跑 dry-run 确认。
