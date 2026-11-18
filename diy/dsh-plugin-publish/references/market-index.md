# index.json 结构参考

发布仓库根目录的 `index.json` 是 DSH 插件市场的**唯一数据源**。它是 `format: 1` 的清单，顶层四个键：

```json
{
  "format": 1,
  "title": { "en": "...", "zh": "..." },
  "description": { "en": "...", "zh": "..." },
  "metadata": { "categories": { "custom": { "title": { "en": "Custom", "zh": "定制" } } } },
  "plugins": [ /* … */ ]
}
```

`metadata.categories` 只是给界面分组用的标签表；插件用 `metadata.category` 引用其中一个键，写错不会报错，但会在界面上掉进「未分类」或不显示分组。

## 单个插件条目

```json
{
  "name": "dsh-global-cmd",
  "title": { "en": "Global CMD", "zh": "全局 CMD" },
  "description": { "en": "...", "zh": "..." },
  "author": "wrysmil",
  "homepage": "https://github.com/wrysmil/dsh-personal-agent/tree/main/dsh-global-cmd",
  "repository": {
    "url": "https://github.com/wrysmil/dsh-personal-agent.git",
    "directory": "dsh-global-cmd"
  },
  "metadata": { "category": "custom", "keywords": ["commands", "shell", "terminal"] },
  "versions": [
    {
      "version": "0.2.0",
      "publishTimestamp": 1794991134,
      "engines": { "dsh": ">=0.2.0-0 <0.3.0" },
      "source": {
        "type": "git",
        "url": "https://github.com/wrysmil/dsh-personal-agent.git",
        "commit": "4ffb6b152c5830edcdf9081d9e1c6ed260bede0a",
        "path": "dsh-global-cmd"
      }
    }
  ]
}
```

字段含义：

| 字段 | 说明 |
|---|---|
| `name` | 安装时用的包名。`@local/<x>` 风格只表示「本地开发包」，市场照样按 git 源安装 |
| `title` / `description` | 双语对象，界面按当前语言取；只写一种语言会回退到另一种 |
| `repository.directory` | 仓库里插件所在子目录。和 `source.path` 保持一致 |
| `versions[]` | 版本列表，界面取 `versions.at(-1)` 作为默认版本。只保留一个通常就够 |
| `versions[].version` | 必须与插件 `package.json` 的 `version` 一致，否则本机会报 `different-version` |
| `versions[].publishTimestamp` | Unix 秒。仅用于显示/排序，改成 `Math.floor(Date.now()/1000)` 即可 |
| `versions[].engines.dsh` | 可安装的 DSH 版本区间；不满足时市场会显示为不兼容，`compatibility.compatible: false` |
| `versions[].source.type` | `git` = 按 commit 从仓库拉；`npm` 类第三方插件则是 npm 包名，没有 `commit` |
| `versions[].source.commit` | **最关键**：安装时 checkout 的完整 40 位 sha。指向错误 = 装到旧代码或直接失败 |
| `versions[].source.path` | 仓库里该插件的相对目录，如 `prompt-enhance` |

## 为什么 commit 不能指向分支

市场生成的安装目标是：

```
git+https://github.com/<owner>/<repo>.git#<commit>&path:/<path>
```

带的是具体 sha，不是 `main`。这带来两个推论：

1. 只推 `index.json` 不推代码，安装会失败或拉到空的旧目录；
2. 反过来，先把代码推上去但忘了改 `source.commit`，市场会安静地装旧版本 —— 表面上「发布成功」，实际没生效。所以验证时一定要比对 `source.commit` 与代码提交的 sha。

## 常见安装报错怎么读

| 现象 | 原因 |
|---|---|
| `plugin_market` 里 `installation.status = "different-version"` | 本机已装版本 ≠ 索引默认版本。要么本地版本比市场新（正常，说明你还没发布），要么市场缓存还没刷新 |
| 市场里版本号是旧的，但 CDN 上已是新的 | DSH 进程内缓存了索引，重启 DSH |
| CDN 上是旧的，仓库里已是新的 | jsdelivr 还在缓存 `@main`，请求 purge 端点后重试 |
| 安装后功能没变 | `source.commit` 指向的提交里没有新代码 |
| 提示不兼容 | `engines.dsh` 区间与当前 DSH 版本不匹配 |
