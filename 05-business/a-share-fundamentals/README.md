# A股基本面分析 Skill

对 A 股上市公司进行系统化基本面分析，基于 AKShare 采集财务数据，从盈利、偿债、营运、发展四个维度进行量化评分，自动检测预警信号，最终生成带有 ECharts 可视化图表的 Markdown 分析报告。

## 前置条件

### 1. Python 环境

本 Skill 依赖 Python 脚本采集 A 股财务数据，需要确保 Python 3.8+ 环境可用。

核心依赖会在脚本首次运行时自动安装：
- `akshare` — A 股数据接口
- `pandas` / `numpy` — 数据处理

### 2. 可视化图表 MCP Server（重要）

本 Skill 依赖 **mcp-server-chart**（基于 AntV 的图表生成服务）来生成雷达图、折线图、柱状图、饼图等可视化图表。该服务需要在 ModelScope（魔搭社区）上部署一个免费实例。

#### 为什么需要部署？

MCP 图表服务需要通过 HTTP（Streamable HTTP 协议）提供图表生成接口。Skill 中的图表生成步骤会向该服务发送 JSON-RPC 请求，获取生成的图表图片 URL，然后嵌入到分析报告中。ModelScope 提供免费的 GPU/CPU 资源来托管这类 MCP 服务。

#### 部署步骤

**第一步：登录 ModelScope MCP 广场**

访问 [ModelScope MCP 广场](https://modelscope.cn/mcp)，登录你的 ModelScope 账号（没有账号的话先注册）。

**第二步：创建 MCP 服务**

1. 在 MCP 广场页面，点击「创建 MCP」或「自定义创建」按钮
2. 选择「可视化图表-MCP-Server」模板

**第三步：配置并部署**

1. 选择免费的资源配置（ModelScope 提供免费额度用于 MCP 托管）
2. 确认部署，等待服务启动

**第四步：获取 MCP 服务 URL**

部署成功后，你会获得一个类似以下格式的 MCP 服务端点 URL：

```
https://mcp.api-inference.modelscope.net/{你的服务ID}/mcp
```

**第五步：更新 Skill 中的 MCP 地址**

将你的 MCP 服务 URL 更新到以下两个位置：

1. **`references/mcp-config.json`** — 修改 `mcpServers.mcp-server-chart.url` 字段
2. **`SKILL.md`** 步骤 3.0 中的 `call_mcp_chart` 函数的 `url` 变量

> **提示**：如果你不想部署，也可以直接在本地通过 npx 运行 mcp-server-chart：
>
> ```bash
> npx -y @antv/mcp-server-chart
> ```
>
> 但本地运行需要 Node.js 18+ 环境，且图表生成时依赖本机渲染服务。

### 3. 前置条件检查清单

| 检查项 | 说明 |
|--------|------|
| Python 3.8+ | 运行 `python --version` 确认 |
| AKShare 可用 | 脚本首次运行会自动安装 |
| MCP 图表服务已部署 | 确认 MCP URL 可访问 |
| 网络连通 | 能访问 ModelScope API 和 AKShare 数据源 |

## 快速开始

### 标准分析流程

```bash
# 1. 运行数据采集脚本
cd a-share-fundamentals
python scripts/analyze.py 300624

# 2. 脚本输出 JSON 数据到 stdout，包含财务指标、评分、预警信号
# 3. Skill 自动根据 JSON 调用 MCP 图表服务生成可视化图表
# 4. 组装并输出 Markdown 报告
```

### 触发方式

在 AI 对话中直接使用以下表述即可激活本 Skill：

- "分析一下万兴科技 300624 的基本面"
- "看看茅台的财务状况"
- "帮我做一下比亚迪的财务排雷"
- "深入分析宁德时代的盈利能力"

## 报告内容

每份分析报告包含八个章节：

1. **执行摘要** — 3-5 句话核心结论
2. **仪表盘** — 四维度评分 + 雷达图
3. **盈利能力分析** — ROE/毛利率/净利率 + 杜邦拆解 + 费用结构图
4. **偿债能力分析** — 资产负债率/流动比率/现金流动负债比
5. **营运能力分析** — 经营现金流/应收周转率/自由现金流
6. **发展能力分析** — 营收增长率/净利润增长率 + 趋势折线图
7. **护城河与竞争优势** — 行业地位与竞争壁垒
8. **预警信号** — 高危/中危/低危分类
9. **综合结论** — 评分总结 + 核心矛盾 + 风险提示

## 目录结构

```
a-share-fundamentals/
├── SKILL.md                          # Skill 定义文件
├── README.md                         # 本文件
├── references/
│   ├── analysis-framework.md         # 分析框架参考
│   ├── data-sources.md               # 数据源清单
│   ├── industry-benchmarks.md        # 行业基准值
│   ├── warning-signals.md            # 预警信号规则
│   └── mcp-config.json               # MCP 图表服务配置
├── scripts/
│   ├── analyze.py                    # 统一入口，数据采集+计算+检测
│   ├── indicator_calculator.py       # 评分规则参考
│   ├── risk_detector.py              # 预警规则参考
│   └── report_generator.py           # 报告结构参考
└── tests/
    ├── test_indicator_calculator.py
    ├── test_report_generator.py
    └── test_risk_detector.py
```

## 常见问题

### Q: MCP 图表调用失败怎么办？

Skill 内置降级机制：如果图表生成失败，会自动降级为纯文字表格展示，不会阻塞报告生成。

### Q: AKShare 接口超时怎么办？

Skill 会自动降级到 WebSearch 搜索公开财务数据，确保分析流程不中断。

### Q: 股票代码找不到？

Skill 会提示用户确认，并列出名称相似的公司供选择。
