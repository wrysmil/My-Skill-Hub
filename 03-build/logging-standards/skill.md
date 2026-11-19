---
name: logging-standards
description: 日志规范技能，用于审查和编写符合规范的日志代码。涵盖格式标准化（JSON结构化）、级别规范（DEBUG/INFO/WARN/ERROR）、敏感信息过滤（密码/token脱敏）、性能日志（耗时记录与慢查询告警）。当用户编写日志、审查日志代码、设计日志系统或重构日志时触发。
---

# 日志规范技能 (Logging Standards)

## 技能概述

本技能提供一套完整的日志规范指南，涵盖格式标准化、级别规范、敏感信息过滤和性能日志规范。适用于任何编程语言和框架的项目。

## 触发条件

当用户执行以下操作时触发本技能：

- 编写或审查日志代码（`log.info`、`logger.debug`、`console.log` 等）
- 添加新的日志输出语句
- 设计或重构日志系统
- 进行代码审查时检查日志规范
- 用户明确要求检查日志规范

## 核心规范

### 1. 日志格式标准化

#### 1.1 统一使用结构化JSON格式

**必须**：所有日志输出使用JSON格式，禁止使用非结构化的字符串拼接。

**正确示例**：
```json
{
  "timestamp": "2026-05-11T10:30:45.123Z",
  "level": "INFO",
  "service": "user-service",
  "trace_id": "abc123",
  "message": "用户登录成功",
  "context": {
    "user_id": "u_12345",
    "ip": "192.168.1.100"
  }
}
```

**错误示例**：
```python
# 禁止：非结构化字符串
print(f"用户 {user_id} 在 {datetime.now()} 登录成功")
logger.info("用户登录成功，user_id=" + user_id)
```

#### 1.2 必须包含的标准字段

每条日志**必须**包含以下字段：

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `timestamp` | string | ISO 8601格式，含时区 | `"2026-05-11T10:30:45.123Z"` |
| `level` | string | 日志级别（大写） | `"INFO"` |
| `service` | string | 服务/模块名称 | `"user-service"` |
| `message` | string | 简洁的人类可读描述 | `"用户登录成功"` |

#### 1.3 推荐包含的可选字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `trace_id` | string | 请求追踪ID，用于链路追踪 |
| `span_id` | string | 当前操作的span ID |
| `user_id` | string | 用户标识（如涉及用户操作） |
| `request_id` | string | 请求ID |
| `duration_ms` | number | 操作耗时（毫秒） |
| `error` | object | 错误信息（仅ERROR级别） |
| `context` | object | 业务上下文数据 |

#### 1.4 字段命名规范

- 使用 **snake_case** 命名法（下划线分隔）
- 字段名使用 **小写字母**
- 避免缩写，保持可读性
- 跨服务保持一致的字段名

**正确**：`user_id`, `request_id`, `created_at`
**错误**：`userId`, `requestID`, `createdAt`, `uid`, `reqId`

---

### 2. 日志级别规范

#### 2.1 级别定义与使用场景

| 级别 | 用途 | 使用场景 | 示例 |
|------|------|----------|------|
| **DEBUG** | 开发调试 | 详细的调试信息，生产环境默认关闭 | 变量值、函数入参、循环中间状态 |
| **INFO** | 业务流程 | 关键业务流程节点、正常操作记录 | 用户登录、订单创建、支付完成 |
| **WARN** | 潜在问题 | 不影响功能但需关注的异常情况 | 接口超时但重试成功、配置项缺失使用默认值 |
| **ERROR** | 错误异常 | 影响功能的错误，需要人工介入 | 数据库连接失败、第三方接口异常、未捕获异常 |

#### 2.2 级别使用原则

**原则1：生产环境默认INFO级别**
- 生产环境日志级别设置为 `INFO`
- 开发/测试环境可设置为 `DEBUG`
- 线上排查问题时临时开启 `DEBUG` 需有超时自动恢复

**原则2：一条日志一个级别**
- 禁止在一条日志中混合多个级别的信息
- 禁止用 `ERROR` 级别记录非错误信息

**原则3：ERROR级别必须包含错误详情**
```json
{
  "level": "ERROR",
  "message": "数据库查询失败",
  "error": {
    "type": "DatabaseConnectionError",
    "message": "Connection refused",
    "stack_trace": "..."
  }
}
```

**原则4：WARN级别需说明影响**
```json
{
  "level": "WARN",
  "message": "Redis连接超时，已降级使用本地缓存",
  "context": {
    "fallback": "local_cache",
    "impact": "缓存一致性降低"
  }
}
```

#### 2.3 禁止使用的日志方式

| 禁止项 | 原因 | 替代方案 |
|--------|------|----------|
| `console.log()` | 无级别、无结构、无法控制 | 使用标准日志库 |
| `print()` | 同上 | 使用标准日志库 |
| `System.out.println()` | 同上 | 使用SLF4J/Logback |
| `alert()` | 浏览器弹窗，非日志 | 使用console API |

---

### 3. 敏感信息过滤

#### 3.1 绝对禁止记录的敏感信息

以下信息**严禁**出现在任何日志中：

| 类别 | 示例 |
|------|------|
| 密码 | 用户密码、数据库密码、API密钥 |
| 令牌 | JWT token、access_token、refresh_token |
| 密钥 | API key、secret key、private key |
| 身份证号 | 身份证、护照号、社保号 |
| 银行卡号 | 信用卡号、借记卡号 |
| 手机号 | 完整手机号（可记录脱敏后版本） |
| 邮箱 | 完整邮箱（可记录脱敏后版本） |

#### 3.2 敏感信息脱敏规则

**手机号**：保留前3位和后4位，中间用 `****` 替换
```
138****1234
```

**邮箱**：用户名保留首尾字符，域名保留
```
z***g@example.com
```

**身份证号**：保留前4位和后4位
```
1101****1234
```

**银行卡号**：仅保留后4位
```
****1234
```

#### 3.3 日志审查检查清单

在代码审查时，检查以下模式：

```regex
# 可能包含密码的模式
password\s*[:=]\s*['"][^'"]+['"]
pwd\s*[:=]\s*['"][^'"]+['"]
secret\s*[:=]\s*['"][^'"]+['"]

# 可能包含token的模式
token\s*[:=]\s*['"][^'"]+['"]
authorization:\s*Bearer\s+[^\s]+

# 可能包含密钥的模式
api[_-]?key\s*[:=]\s*['"][^'"]+['"]
private[_-]?key\s*[:=]\s*['"][^'"]+['"]
```

#### 3.4 实现建议

**方式1：日志库过滤器**
```python
# Python示例 - 使用日志过滤器
class SensitiveDataFilter(logging.Filter):
    SENSITIVE_PATTERNS = [
        (r'password["\s]*[:=]["\s]*([^"]+)', 'password=****'),
        (r'token["\s]*[:=]["\s]*([^"]+)', 'token=****'),
    ]

    def filter(self, record):
        msg = record.getMessage()
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            msg = re.sub(pattern, replacement, msg, flags=re.IGNORECASE)
        record.msg = msg
        return True
```

**方式2：中间件统一处理**
```javascript
// Node.js示例 - 中间件脱敏
const sensitiveKeys = ['password', 'token', 'secret', 'apiKey'];

function sanitize(obj) {
  return JSON.parse(JSON.stringify(obj, (key, value) => {
    if (sensitiveKeys.includes(key.toLowerCase())) {
      return '****';
    }
    return value;
  }));
}
```

---

### 4. 性能日志规范

#### 4.1 必须记录性能日志的场景

| 场景 | 记录内容 | 阈值建议 |
|------|----------|----------|
| HTTP请求 | 方法、路径、状态码、耗时 | >1s 告警 |
| 数据库查询 | SQL摘要、行数、耗时 | >500ms 告警 |
| 外部API调用 | 服务名、端点、状态码、耗时 | >2s 告警 |
| 缓存操作 | 操作类型、命中率、耗时 | >100ms 告警 |
| 消息队列 | 队列名、消息大小、处理耗时 | >5s 告警 |

#### 4.2 性能日志格式

```json
{
  "timestamp": "2026-05-11T10:30:45.123Z",
  "level": "INFO",
  "service": "order-service",
  "message": "数据库查询完成",
  "performance": {
    "operation": "db_query",
    "table": "orders",
    "query_summary": "SELECT * FROM orders WHERE user_id = ?",
    "rows_affected": 15,
    "duration_ms": 45,
    "slow_query": false
  }
}
```

#### 4.3 慢查询日志

当操作超过阈值时，**必须**使用 `WARN` 级别记录：

```json
{
  "timestamp": "2026-05-11T10:30:45.123Z",
  "level": "WARN",
  "service": "order-service",
  "message": "慢查询告警",
  "performance": {
    "operation": "db_query",
    "table": "orders",
    "query_summary": "SELECT * FROM orders WHERE status = ?",
    "rows_affected": 15000,
    "duration_ms": 2340,
    "slow_query": true,
    "threshold_ms": 500
  }
}
```

#### 4.4 性能统计聚合

建议定期（每分钟/每小时）聚合性能指标：

```json
{
  "timestamp": "2026-05-11T11:00:00.000Z",
  "level": "INFO",
  "service": "order-service",
  "message": "性能统计报告",
  "metrics": {
    "period": "1h",
    "requests": {
      "total": 12500,
      "success": 12350,
      "failed": 150,
      "avg_duration_ms": 120,
      "p95_duration_ms": 450,
      "p99_duration_ms": 890
    }
  }
}
```

---

## 代码审查检查项

审查日志代码时，检查以下项目：

### 必须通过项（BLOCKER）

- [ ] 所有日志使用JSON结构化格式
- [ ] 包含必须字段：timestamp、level、service、message
- [ ] 未记录敏感信息（密码、token、密钥等）
- [ ] 使用标准日志库，非console.log/print

### 建议改进项（WARNING）

- [ ] 包含trace_id用于链路追踪
- [ ] 性能日志包含duration_ms
- [ ] ERROR级别包含error对象详情
- [ ] 慢操作有WARN级别告警
- [ ] 字段命名使用snake_case

---

## 各语言日志库推荐

| 语言 | 推荐日志库 | 配置要点 |
|------|-----------|----------|
| Python | `structlog` 或 `loguru` | 配置JSON renderer |
| Node.js | `pino` 或 `winston` | 使用JSON格式 |
| Java | SLF4J + Logback | 配置JSON encoder |
| Go | `zap` 或 `zerolog` | 使用JSON输出 |
| Rust | `tracing` + `tracing-subscriber` | 使用JSON formatter |

---

## 使用示例

### 审查现有代码

当用户要求审查日志时：

```
请帮我检查这段代码的日志是否符合规范
```

AI将检查：
1. 是否使用结构化格式
2. 是否包含敏感信息
3. 日志级别是否正确
4. 是否包含必要字段

### 编写新日志

当用户编写新代码时：

```
帮我为这个函数添加日志
```

AI将：
1. 在关键节点添加INFO日志
2. 在异常处理添加ERROR日志（含error详情）
3. 在耗时操作添加性能日志
4. 确保敏感信息已脱敏

### 重构日志系统

当用户要求改进日志时：

```
帮我重构这个项目的日志系统
```

AI将：
1. 替换console.log/print为标准日志库
2. 添加JSON格式化
3. 配置敏感信息过滤器
4. 添加性能日志中间件

---

## 版本信息

- **版本**：1.0.0
- **创建日期**：2026-05-11
- **适用范围**：通用/多语言
- **维护者**：Claude Code Skills
