---
name: project-planner
description: >
  将想法、问题与功能诉求分流为合适形态：提案文档、功能工单或缺陷报告。
  具备仓库感知能力——从当前仓库发现模板与文档结构。适用于：（1）用户描述想跟踪的想法、功能或问题；
  （2）用户说「提个 bug」「我有个想法」「规划一下这个功能」等；（3）用户想把大功能拆成阶段并用
  GitHub issue 跟踪。不适用于：实际写代码实现（用 coding-agent）、评审 PR、或泛泛的代码库问答。
---

# 项目规划器（Project Planner）

## 前置条件

- git  
- gh（GitHub CLI，通过 `gh auth login` 完成认证）  

将用户输入分流为合适的项目产物：**提案**（含阶段的大想法）、**功能工单**（小改进）、或**缺陷报告**（东西坏了或行为不对）。

## 仓库发现

动手之前，先摸清当前仓库的配置：

1. 运行 `git rev-parse --show-toplevel` 找到仓库根目录  
2. 检查根目录是否有 `.project-planner.yml` —— 若有则阅读，并以其为准配置路径、标签与约定  
3. 若无配置文件，则回退到自动发现：  
   - 提案模板：查找 `docs/proposals/TEMPLATE.md`  
   - Issue 模板：查找 `.github/ISSUE_TEMPLATE/`  
   - 文档目录：查找 `docs/`、`mkdocs.yml`  
   - 若都找不到，使用技能内置的兜底格式  
4. 若仓库有 `CLAUDE.md` 或 `CONTRIBUTING.md`，阅读以遵循约定  
5. 运行 `gh repo view --json name,owner` 确认创建 issue 时对应的仓库  

### 配置文件：`.project-planner.yml`

可选，放在仓库根。所有字段均为可选 —— 未填部分由自动发现补全。  
可复制技能目录中的 `project-planner.yml` 作为起步模板。

```yaml
project: MyProject                    # 项目名称（用于 issue 标题）
repo: owner/repo                      # GitHub 仓库（通常可自动检测）

proposals:
  dir: docs/proposals                 # 提案文档所在目录
  template: docs/proposals/TEMPLATE.md # 要遵循的提案模板
  index: docs/proposals/index.md      # 新建提案时要更新的索引文件
  mkdocs_nav: true                    # 创建提案时是否更新 mkdocs.yml 导航

issues:
  labels:
    feature: enhancement              # 功能类 issue 的标签
    bug: bug                          # 缺陷类 issue 的标签
  # branch_prefix: feature/           # 分支命名前缀

# conventions:
#   docs: docs                        # 项目文档根目录
```

## 分流规则

先问：**这件事是否需要设计工作或多个阶段？**

- 需要设计决策、多个阶段或架构层面的思考 → **提案**  
- 单一、明确的改动 —— 不需要设计 → **功能工单**  
- 功能损坏或行为错误 → **缺陷报告**  

若不清楚，问用户：「这是个小修还是需要设计文档？」

## 工作流：提案

适用于需要分阶段与设计的大想法。

1. 发现提案模板（见上文「仓库发现」）  
2. 检索代码库及 `docs/` 等目录获取相关背景  
3. 想清楚设计 —— 动机、方案、取舍  
4. 拆成可交付的阶段（每阶段对用户有价值）  
5. 在总体与各阶段两个层级写验收标准  
6. 在 `docs/proposals/<name>.md` 创建提案文档  
7. 若存在 `mkdocs.yml`，在导航的 Proposals 下加入该提案  
8. 若存在 `docs/proposals/index.md`，将其加入「进行中提案」列表  
9. 用 `gh issue create` 为每个阶段创建 GitHub issue：  
   - 标题：`<提案名>: 第 N 阶段 — <阶段名>`  
   - 正文：阶段目标、验收标准、任务清单、链接到提案  
   - 标签：`enhancement`  
10. 在提案文档中回填各阶段对应的 issue 链接  
11. 在新分支上提交并推送  

### 提案质量自检

提交前确认：

- [ ] 摘要是一段清晰的话  
- [ ] 动机说明「为什么是现在」  
- [ ] 设计同时覆盖用户体验与技术方案  
- [ ] 每个阶段都可独立交付  
- [ ] 验收标准可测试（不模糊）  
- [ ] 有「未决问题」小节（可为空）  
- [ ] 「相关」小节链到相关文档、issue 或设计稿  
- [ ] 状态设为「就绪」（若已建 issue）或「草稿」（若尚未）  

## 工作流：功能工单

适用于小而自洽的增强。

1. 发现功能模板（见「仓库发现」）  
2. 用 `gh issue create` 创建 GitHub issue：  
   - 标题：清晰、可执行导向  
   - 正文：摘要、验收标准清单、如有则引用文档  
   - 若仓库有模板格式则遵循  
   - 标签：`enhancement`  
3. 向用户回报 issue 编号与 URL  

## 工作流：缺陷报告

适用于故障与错误行为。

1. 发现缺陷模板（见「仓库发现」）  
2. 尽量通过检索代码库定位相关代码  
3. 用 `gh issue create` 创建 GitHub issue：  
   - 标题：`Bug: <简明描述>`  
   - 正文：描述、复现步骤（若已知）、期望 vs 实际、相关代码文件/行、相关文档  
   - 若仓库有模板格式则遵循  
   - 标签：`bug`  
4. 向用户回报 issue 编号与 URL  

## 重要规则

- **始终使用 `gh issue create`** —— 具备仓库感知且处理认证  
- **始终互相链接** —— issue 引用提案，提案引用 issue  
- **提案长期保留** —— 只改状态，文档不随意移动或删除  
- **一个功能一份提案** —— 不要把多个想法塞进同一文档  
- **阶段必须可交付** —— 每阶段对用户有价值，而不只是「后端干完」  
- **在分支上提交** —— 不要直接推 main  
- **尊重仓库约定** —— 若有 CLAUDE.md 或 CONTRIBUTING.md，按其分支命名、提交信息与 MR/PR 规范执行  
