---
name: a-share-fundamentals
description: A股上市公司基本面分析。通过 AKShare 采集财务数据，四维度（盈利/偿债/营运/发展）量化评估，检测预警信号，生成带可视化图表的 MD 分析报告。当用户提到"基本面分析"、"财报分析"、"ROE"、"毛利率"、"看看XX公司"、"分析XX"、"财务排雷"时触发。
---

# A股基本面分析 Skill

对 A 股上市公司进行系统化基本面分析，输出带图表的 MD 报告。

## 触发条件

- 基本面分析、财报分析、财务指标、ROE、毛利率
- 公司分析 + 股票代码/公司名称
- "看看XX公司"、"分析一下XX"、"XX基本面怎么样"
- 预警信号、风险排查、财务排雷

## 流程总览（3 步）

```
步骤1: python scripts/analyze.py {code}  →  获取 JSON 数据
步骤2: 基于 JSON 数据分析 + 计算评分 + 撰写文字
步骤3: 调用 MCP 生成图表  →  组装 MD 报告  →  写入文件
```

---

## 步骤 1：数据采集

### 1.1 识别公司

从用户输入提取股票代码（6位数字）或公司名称。如果是名称，搜索确认代码。

### 1.2 运行采集脚本

```bash
cd {SKILL目录}
python scripts/analyze.py {股票代码}
```

脚本自动完成：
- **并发**获取利润表/资产负债表/现金流量表/公司概况/关键指标
- 提取近5年年报数据并计算增长率
- 计算衍生指标（毛利率/净利率/ROE/流动比率/费用率等）
- 检测预警信号
- 输出完整 JSON 到 stdout

### 1.3 降级处理

如果脚本报错（akshare 接口不可用），使用 WebSearch 搜索：
- "{公司名称} 最新财报 财务指标"
- "{公司名称} ROE 毛利率 净利润"

从搜索结果中提取关键数据，标注来源为"WebSearch"。

---

## 步骤 2：分析与评分

基于步骤 1 的 JSON 数据，完成以下分析。

### 2.1 四维度评分

参考 `scripts/indicator_calculator.py` 中的评分规则：

| 维度 | 指标 | 权重 | 绿灯(≥80) | 黄灯(≥60) | 红灯(<60) |
|------|------|------|-----------|-----------|-----------|
| **盈利** | ROE | 40% | ≥15% | ≥8% | <8% |
| | 毛利率 | 30% | 行业1.2倍+ | 行业0.9倍+ | <0.9倍 |
| | 净利率 | 30% | ≥15% | ≥5% | <5% |
| **偿债** | 资产负债率 | 40% | ≤50% | ≤70% | >70% |
| | 流动比率 | 30% | ≥2.0 | ≥1.0 | <1.0 |
| | 现金流动负债比 | 30% | >0.3 | >0 | ≤0 |
| **营运** | 经营现金流 | 40% | 正数 | 0 | 负数 |
| | 应收周转率 | 30% | 行业1.2倍+ | 行业0.9倍+ | <0.9倍 |
| | 自由现金流 | 30% | 正数 | 0 | 负数 |
| **发展** | 营收增长率 | 40% | ≥15% | ≥0% | <0% |
| | 净利润增长率 | 40% | ≥15% | ≥0% | <0% |
| | 研发投入占比 | 20% | 行业1.2倍+ | 行业0.9倍+ | <0.9倍 |

综合评分 = 盈利×30% + 偿债×25% + 营运×20% + 发展×25%

评分→灯色：≥80 绿灯(优秀)、≥60 黄灯(一般)、<60 红灯(警惕)

### 2.2 预警信号

JSON 中的 `warnings` 字段已包含自动检测的预警信号。补充检查：
- 费用率是否超过100%
- 是否连续亏损
- 流动比率是否跌破安全线

### 2.3 撰写文字分析

为每个维度撰写2-3句分析文字，指出：
- 关键指标数值及趋势
- 与行业基准的对比
- 核心矛盾和风险点

---

## 步骤 3：图表生成与报告组装

### 3.0 MCP 图表服务配置

mcp-server-chart 已在项目 `.mcp.json` 中配置。调用方式：通过 Bash 发送 HTTP 请求到 MCP 服务端点（JSON-RPC 协议）。

**MCP 调用模板**（Python）：

```python
import json, urllib.request

def call_mcp_chart(tool_name, arguments, session_id=None):
    url = "https://mcp.api-inference.modelscope.net/0bd0a201c3ef4b/mcp"
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if session_id:
        headers["Mcp-Session-Id"] = session_id

    # Initialize
    req = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
           "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                      "clientInfo": {"name": "chart", "version": "1.0"}}}
    data = json.dumps(req).encode()
    r = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(r, timeout=15) as resp:
        sid = resp.headers.get("Mcp-Session-Id")
        resp.read()

    # Notification
    notif = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
    data = json.dumps(notif).encode()
    headers["Mcp-Session-Id"] = sid
    r = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(r, timeout=15) as resp:
        resp.read()

    # Call tool
    call = {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments}}
    data = json.dumps(call).encode()
    r = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(r, timeout=30) as resp:
        result = json.loads(resp.read().decode())

    return result["result"]["content"][0]["text"]  # 返回图片 URL
```

### 3.1 雷达图（必选）

工具名：`generate_radar_chart`

```json
{
  "data": [
    {"name": "盈利能力", "value": 39, "group": "万兴科技"},
    {"name": "偿债能力", "value": 72, "group": "万兴科技"},
    {"name": "营运能力", "value": 54, "group": "万兴科技"},
    {"name": "发展能力", "value": 44, "group": "万兴科技"}
  ],
  "title": "万兴科技(300624) 四维度评分"
}
```

### 3.2 折线图（数据≥3年时生成）

工具名：`generate_line_chart`

```json
{
  "data": [
    {"time": "2020", "value": 9.76, "group": "营收(亿)"},
    {"time": "2021", "value": 10.29, "group": "营收(亿)"},
    {"time": "2022", "value": 11.80, "group": "营收(亿)"},
    {"time": "2023", "value": 14.81, "group": "营收(亿)"},
    {"time": "2024", "value": 14.40, "group": "营收(亿)"},
    {"time": "2025", "value": 15.33, "group": "营收(亿)"},
    {"time": "2020", "value": 1.25, "group": "净利润(亿)"},
    {"time": "2021", "value": -0.34, "group": "净利润(亿)"},
    {"time": "2022", "value": 0.40, "group": "净利润(亿)"},
    {"time": "2023", "value": 0.86, "group": "净利润(亿)"},
    {"time": "2024", "value": -1.63, "group": "净利润(亿)"},
    {"time": "2025", "value": -0.91, "group": "净利润(亿)"}
  ],
  "title": "营收与净利润趋势(2020-2025)",
  "axisXTitle": "年份",
  "axisYTitle": "金额(亿元)"
}
```

### 3.3 饼图（分类≥3项时生成）

工具名：`generate_pie_chart`

```json
{
  "data": [
    {"category": "销售费用", "value": 8.75},
    {"category": "研发费用", "value": 4.32},
    {"category": "管理费用", "value": 2.24},
    {"category": "营业成本", "value": 1.41}
  ],
  "title": "2025年费用结构(亿元)",
  "innerRadius": 0.5
}
```

### 3.4 柱状图（对比维度≥3时生成）

工具名：`generate_column_chart`

```json
{
  "data": [
    {"category": "销售费用率", "value": 57.07, "group": "2025"},
    {"category": "研发费用率", "value": 28.18, "group": "2025"},
    {"category": "毛利率", "value": 90.77, "group": "2025"},
    {"category": "销售费用率", "value": 45.14, "group": "2020"},
    {"category": "研发费用率", "value": 22.39, "group": "2020"},
    {"category": "毛利率", "value": 94.86, "group": "2020"}
  ],
  "title": "费用率对比: 2020 vs 2025(%)",
  "group": true
}
```

### 3.5 返回值处理

所有图表工具返回格式一致：
```json
{"result": {"content": [{"type": "text", "text": "https://mdn.alipayobjects.com/...图片URL"}]}}
```

提取方式：`result["result"]["content"][0]["text"]` 即为图片 URL。

嵌入 MD：`![图表标题](图片URL)`

### 3.6 组装报告

报告结构（八章节）：

```markdown
# {公司名称}({股票代码}) 基本面分析报告

> 分析日期 | 综合评分 | 数据来源

## 执行摘要
（3-5句话结论）

## 仪表盘
| 维度 | 评分 | 灯色 |
![雷达图](URL)

## 一、盈利能力分析
（文字 + 指标表格 + 杜邦拆解 + 费用结构饼图/柱状图）

## 二、偿债能力分析
（文字 + 指标表格）

## 三、营运能力分析
（文字 + 指标表格）

## 四、发展能力分析
（文字 + 趋势折线图）

## 五、护城河与竞争优势
（基于公司信息和行业特征分析）

## 六、预警信号
（列表展示，分高/中/低危）

## 七、机构观点
（如有研报数据则展示，否则标注"暂无"）

## 八、综合结论
（评分总结 + 核心矛盾 + 风险提示）

## 附录：数据来源明细
```

### 3.7 输出文件

将完整报告写入：`{SKILL目录}/{公司名称}_{股票代码}_基本面分析.md`

向用户展示报告摘要，告知文件路径。

---

## 深挖模式

当用户要求深入分析某个维度（如"深入分析盈利能力"）时：
- 只输出该维度的详细分析
- 增加多年趋势表格和图表
- 展开杜邦拆解或单指标趋势分析

## 速览模式

当用户说"看看XX"、"XX怎么样"时：
- 只输出仪表盘 + 3句话结论 + 预警信号摘要
- 不生成图表（或只生成雷达图）
- 不写入文件，直接在对话中展示

---

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| akshare 未安装 | 脚本自动 pip install |
| AKShare 接口超时/报错 | 降级到 WebSearch 搜索公开数据 |
| MCP 图表调用失败 | 降级为纯文字表格，不阻塞报告 |
| 股票代码不存在 | 提示用户确认，列出相似名称公司 |
| 数据不完整 | 基于可用数据分析，标注"数据缺失" |

## 参考文档

- **分析框架**：`references/analysis-framework.md`
- **数据源清单**：`references/data-sources.md`
- **行业基准值**：`references/industry-benchmarks.md`
- **预警信号规则**：`references/warning-signals.md`
- **MCP 配置**：`references/mcp-config.json`

## 脚本说明

- `scripts/analyze.py` — **统一入口**，并发采集 + 指标计算 + 风险检测，输出 JSON
- `scripts/indicator_calculator.py` — 评分规则参考（供 Claude 阅读，不直接运行）
- `scripts/risk_detector.py` — 预警规则参考（供 Claude 阅读，不直接运行）
- `scripts/report_generator.py` — 报告结构参考（供 Claude 阅读，不直接运行）

## 使用示例

### 标准分析
**用户**：分析一下万兴科技 300624 的基本面
**流程**：
1. `python scripts/analyze.py 300624` → 获取 JSON
2. 分析数据、计算评分、撰写文字
3. 生成雷达图+折线图+饼图 → 组装报告 → 写入文件

### 速览
**用户**：看看茅台基本面
**流程**：
1. `python scripts/analyze.py 600519` → 获取 JSON
2. 生成仪表盘 + 3句话 → 直接输出

### 深挖
**用户**：深入分析茅台的盈利能力
**流程**：
1. `python scripts/analyze.py 600519` → 获取 JSON
2. 详细分析盈利能力 + 杜邦拆解 + 多年趋势图
