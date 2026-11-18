# Qi-Skill-Hub

高质量 AI 辅助技能（Skill）集合仓库，面向代码助手、智能体（Agent）等 AI 工具。每个技能以 `SKILL.md` 为入口，提供领域知识、工作流引导与最佳实践。

## 仓库结构

```
Qi-Skill-Hub/
├── development/      # 开发类技能（23 个）
├── diy/              # 自研技能（2 个）
├── other/            # 办公文档类技能（4 个）
└── README.md
```

## 已收录技能一览

下表仅列出**当前目录中实际存在**的技能包（入口一般为 `<技能名>/SKILL.md`，例外见表内说明）。若需更多社区技能，可使用 `find-skills` 或官方 Skills 生态工具检索与安装。

### 自研类（`diy/`）

本仓库原创/自用的技能，随使用场景持续迭代。

| 分类           | 技能目录                | 核心用途                                                                                     |
| -------------- | ----------------------- | -------------------------------------------------------------------------------------------- |
| 工具链与发布   | `dsh-plugin-publish`    | DSH 插件发布：同步源码、升版本、改写 index.json 的 `version` 与 `source.commit`、刷 jsdelivr CDN |
| 金融分析       | `a-share-fundamentals`  | A股基本面分析：AKShare 取数、四维度量化评估、预警信号检测与图表报告                            |

### 开发类（`development/`）

| 分类         | 技能目录                     | 核心用途                                                     |
| ------------ | ---------------------------- | ------------------------------------------------------------ |
| 社区与发现   | `find-skills`                | 在社区生态中搜索、发现与安装技能                               |
| 前端         | `frontend-design`            | 高质量网页、落地页、仪表盘等界面设计与实现                     |
| 前端         | `web-artifacts-builder`      | 复杂前端产物（如多组件、状态与路由）的构建指引                 |
| 前端         | `web-design-guidelines`      | 网页可访问性、设计规范与体验审查                               |
| 前端         | `ui-ux-pro-max`              | UI/UX 设计情报与可检索的设计参考数据                           |
| 架构与规划   | `planning-with-files`        | 复杂任务拆解、文件化计划与进度追踪                             |
| 架构与规划   | `project-planner`            | 需求/想法归类为提案、Issue 或缺陷报告等                        |
| 架构与规划   | `architecture-patterns`      | 整洁/六边形/DDD 等后端架构模式与分层实践                       |
| 架构与规划   | `architecture-doc-writer`    | 按模板产出系统架构/技术设计类 Markdown 与 Mermaid 图示         |
| 架构与规划   | `writing-plans`              | 在动手写代码前，将规格拆解为实施计划                           |
| 架构与规划   | `executing-plans`            | 按计划分阶段执行并设检查点                                     |
| 质量与测试   | `test-driven-development`    | 测试驱动开发流程引导                                           |
| 质量与测试   | `requesting-code-review`     | 合并前代码审查与质量核对                                       |
| 质量与测试   | `systematic-debugging`       | 结构化排查缺陷、定位根因                                       |
| 质量与测试   | `auto-testcase-generator`    | 从需求/API/项目文档生成结构化 Excel 测试用例（含图片与路径分析） |
| 质量与测试   | `logging-standards`          | 日志编写与审查：级别、结构化、脱敏与性能记录（入口为 `skill.md`） |
| 记忆与上下文 | `memory-bank`                | 分层记忆、会话续接与上下文压缩                                 |
| 协作与版本控制 | `git`                      | 组织级 Git 分支模型、提交规范与合并请求流程（安装标识：`git-xywh`） |
| 开发提效     | `brainstorming`              | 实现前的需求澄清与方案发散                                     |
| 开发提效     | `skill-creator`              | 自定义技能的创建与迭代                                         |
| 专项         | `prompt-engineering-expert`  | 面向智能体的提示词与指令设计优化                               |
| 文档与办公   | `technical-writer`           | 技术文档、指南、知识库类写作                                   |

### 办公文档类（`other/`）

| 分类       | 技能目录 | 核心用途                               |
| ---------- | -------- | -------------------------------------- |
| 文档与办公 | `docx`   | Word 文档创建、编辑与格式相关流程       |
| 文档与办公 | `pdf`    | PDF 处理（合并、拆分、表单等）          |
| 文档与办公 | `pptx`   | 演示文稿生成与编辑                     |
| 文档与办公 | `xlsx`   | 表格数据处理、公式与图表等             |

## 技能目录结构

每个技能目录遵循统一规范：

```
<技能名>/
├── SKILL.md          # 技能入口（必填），含 YAML frontmatter 元数据
├── _meta.json        # （选填）注册/发布元数据（ownerId、slug、version、publishedAt）
├── LICENSE.txt       # （选填）许可证
├── references/       # （选填）深度参考文档
├── scripts/          # （选填）辅助工具脚本
├── examples/         # （选填）示例文件
├── templates/        # （选填）模板文件
└── *.yml             # （选填）配置文件（如 Issue 模板、项目配置等）
```

**SKILL.md 格式示例：**

```markdown
---
name: <技能名>
description: <触发条件与功能描述>
slug: <唯一标识>
---

# <技能标题>

<触发条件、工作流、规则、示例等正文>
```

## 使用方式

1. 根据任务需求，在上方表格中查找对应分类的技能。
2. 打开对应路径的技能入口文件：
   - 自研类：`diy/<技能目录>/SKILL.md`
   - 开发类：`development/<技能目录>/SKILL.md`
   - 办公文档类：`other/<技能目录>/SKILL.md`
3. 遵循 `SKILL.md` 中定义的触发条件、执行步骤与约束规则。
4. 部分技能附带 `references/`、`scripts/`、`templates/` 等子资源，以各技能 `SKILL.md` 中的引用为准。

## 命名约定

- 技能入口统一命名为 `SKILL.md`（唯一例外：`logging-standards` 使用小写 `skill.md`）
- 技能目录名使用 kebab-case 命名
- `_meta.json` 中的 `slug` 字段为技能的唯一安装标识（如 `git` 的安装标识为 `git-xywh`）
