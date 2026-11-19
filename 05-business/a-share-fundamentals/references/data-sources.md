# 数据源清单与降级策略

## 数据源优先级

| 数据类型 | 首选(置信度high) | 备选(置信度medium) | 兜底(置信度low) |
|---------|-----------------|-------------------|----------------|
| 财务报表 | AKShare | 巨潮资讯网(Playwright) | 同花顺(Playwright) |
| 实时指标 | AKShare | 同花顺(Playwright) | 东方财富(WebFetch) |
| 公司概况 | AKShare | 东方财富(WebFetch) | — |
| 审计意见 | 巨潮资讯网(Playwright) | 交易所官网(Playwright) | — |
| 新闻舆情 | bocha-mcp | WebSearch | — |
| 工商信息 | 天眼查(Playwright) | 国家企业信用信息(Playwright) | — |
| 行业对比 | AKShare同行数据 | 同花顺行业(Playwright) | — |
| 机构研报 | WebSearch | 东方财富研报(Playwright) | — |

## 降级策略

### AKShare 不可用
1. 检查网络连接
2. 尝试 Playwright 从同花顺/东方财富爬取
3. 标记数据源为"网页采集"，置信度降为 medium

### 巨潮 PDF 解析失败
1. 用 AKShare 已获取的报表数据替代
2. 在报告中标注"审计意见未获取"

### 天眼查需登录/验证码
1. 跳过工商信息
2. 用 AKShare 公司概况替代基础信息
3. 在报告中标注"工商信息未获取"

### mcp-server-chart 不可用
1. 降级为纯文字表格
2. 用 Markdown 表格展示数据

### bocha 搜索无结果
1. 改用 WebSearch 重试
2. 仍无结果则标注"舆情信息未获取"

## 数据来源标注格式

每条数据必须附带：
```json
{
    "value": 59.45,
    "unit": "%",
    "metric": "毛利率",
    "period": "2025Q3",
    "source": "AKShare",
    "confidence": "high",
    "fetch_time": "2026-05-15T10:30:00"
}
```

置信度等级：
- high：官方数据源（巨潮/交易所/AKShare结构化数据）
- medium：第三方整理（同花顺/东方财富网页数据）
- low：新闻报道/非官方渠道

## 交叉验证规则

同一指标多源获取到不同数值时：
1. 优先采信置信度最高的来源
2. 差异 >5%：标注"数据存在分歧"，列出所有来源
3. 差异 ≤5%：采信高置信度来源，不额外标注
