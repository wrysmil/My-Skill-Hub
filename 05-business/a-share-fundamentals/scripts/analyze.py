"""
A股基本面分析统一入口脚本
用法: python scripts/analyze.py 300624
输出: JSON 格式的完整分析结果（stdout）
"""
import json
import sys
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


def ensure_akshare():
    """确保 akshare 已安装"""
    try:
        import akshare
        return akshare
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "akshare", "-q"])
        import akshare
        return akshare


def parse_number(text):
    """解析中文财务数字：'1.04亿' → 104000000, '-160.21万' → -1602100"""
    if text is None or text is False or text == "":
        return None
    if isinstance(text, (int, float)):
        return float(text)
    text = str(text).strip().replace(",", "")
    m = re.match(r'^(-?[\d.]+)(万亿|亿|万)?$', text)
    if not m:
        try:
            return float(text)
        except (ValueError, TypeError):
            return None
    val = float(m.group(1))
    unit = m.group(2)
    if unit == "万亿":
        val *= 1e12
    elif unit == "亿":
        val *= 1e8
    elif unit == "万":
        val *= 1e4
    return val


def parse_percent(text):
    """解析百分比：'95.07%' → 95.07"""
    if text is None or text is False:
        return None
    text = str(text).strip().replace("%", "")
    try:
        return float(text)
    except (ValueError, TypeError):
        return None


def fetch_company_info(ak, code):
    """获取公司概况（带重试）"""
    import time
    for attempt in range(3):
        try:
            df = ak.stock_individual_info_em(symbol=code)
            info = {}
            for _, row in df.iterrows():
                info[str(row.iloc[0])] = row.iloc[1]
            return info
        except Exception:
            if attempt < 2:
                time.sleep(2)
    return {}


def fetch_key_indicators(ak, code):
    """获取关键财务指标（同花顺）"""
    df = ak.stock_financial_abstract_ths(symbol=code, indicator="按报告期")
    if df is None or df.empty:
        return []
    return df.to_dict("records")


def fetch_income_statement(ak, code):
    """获取利润表"""
    df = ak.stock_financial_report_sina(stock=code, symbol="利润表")
    if df is None or df.empty:
        return []
    return df.to_dict("records")


def fetch_balance_sheet(ak, code):
    """获取资产负债表"""
    df = ak.stock_financial_report_sina(stock=code, symbol="资产负债表")
    if df is None or df.empty:
        return []
    return df.to_dict("records")


def fetch_cashflow_statement(ak, code):
    """获取现金流量表"""
    df = ak.stock_financial_report_sina(stock=code, symbol="现金流量表")
    if df is None or df.empty:
        return []
    return df.to_dict("records")


def build_annual_data(key_indicators):
    """从关键指标中提取年报数据，构建多年财务数据"""
    annual = {}
    for row in key_indicators:
        period = str(row.get("报告期", ""))
        if not period.endswith("12-31"):
            continue
        year = period[:4]
        if int(year) < 2018:
            continue
        data = {
            "revenue": parse_number(row.get("营业总收入")),
            "net_profit": parse_number(row.get("净利润")),
            "deducted_net_profit": parse_number(row.get("扣非净利润")),
            "eps": parse_number(row.get("基本每股收益")),
            "bps": parse_number(row.get("每股净资产")),
            "ocf_per_share": parse_number(row.get("每股经营现金流")),
            "gross_margin": parse_percent(row.get("销售毛利率")),
            "net_margin": parse_percent(row.get("销售净利率")),
            "roe": parse_percent(row.get("净资产收益率")),
            "roe_diluted": parse_percent(row.get("净资产收益率-摊薄")),
            "current_ratio": parse_number(row.get("流动比率")),
            "quick_ratio": parse_number(row.get("速动比率")),
            "debt_ratio": parse_percent(row.get("资产负债率")),
            "equity_ratio": parse_number(row.get("产权比率")),
            "ar_turnover_days": parse_number(row.get("应收账款周转天数")),
            "inv_turnover": parse_number(row.get("存货周转率")),
            "inv_turnover_days": parse_number(row.get("存货周转天数")),
            "operating_cycle": parse_number(row.get("营业周期")),
        }
        annual[year] = data

    # 计算增长率
    years = sorted(annual.keys())
    for i, year in enumerate(years):
        if i == 0:
            continue
        prev = annual[years[i - 1]]
        curr = annual[year]
        if prev["revenue"] and prev["revenue"] != 0 and curr["revenue"]:
            curr["revenue_growth"] = round((curr["revenue"] - prev["revenue"]) / abs(prev["revenue"]) * 100, 2)
        if prev["net_profit"] and prev["net_profit"] != 0 and curr["net_profit"]:
            curr["profit_growth"] = round((curr["net_profit"] - prev["net_profit"]) / abs(prev["net_profit"]) * 100, 2)

    return annual


def build_latest_from_statements(income, balance, cashflow):
    """从三表中提取最新年报的详细数据"""
    result = {}

    # 利润表 - 找最新年报
    for row in income:
        date = str(row.get("报告日", ""))
        if date.endswith("1231"):
            result["revenue"] = row.get("营业收入") or row.get("营业总收入")
            result["cost_of_goods"] = row.get("营业成本")
            result["selling_expense"] = row.get("销售费用")
            result["admin_expense"] = row.get("管理费用")
            result["rd_expense"] = row.get("研发费用")
            result["finance_expense"] = row.get("财务费用")
            result["operating_profit"] = row.get("营业利润")
            result["net_profit"] = row.get("净利润")
            result["net_profit_parent"] = row.get("归属于母公司所有者的净利润")
            result["report_date"] = date
            break

    # 资产负债表 - 找最新年报
    for row in balance:
        date = str(row.get("报告日", ""))
        if date.endswith("1231"):
            result["cash"] = row.get("货币资金")
            result["accounts_receivable"] = row.get("应收账款")
            result["inventory"] = row.get("存货")
            result["current_assets"] = row.get("流动资产合计")
            result["total_assets"] = row.get("资产总计")
            result["current_liabilities"] = row.get("流动负债合计")
            result["total_liabilities"] = row.get("负债合计")
            result["total_equity"] = row.get("所有者权益(或股东权益)合计")
            result["parent_equity"] = row.get("归属于母公司股东权益合计")
            result["short_term_borrowing"] = row.get("短期借款")
            break

    # 现金流量表 - 找最新年报
    for row in cashflow:
        date = str(row.get("报告日", ""))
        if date.endswith("1231"):
            result["operating_cashflow"] = row.get("经营活动产生的现金流量净额")
            result["investing_cashflow"] = row.get("投资活动产生的现金流量净额")
            result["financing_cashflow"] = row.get("筹资活动产生的现金流量净额")
            result["capex"] = row.get("购建固定资产、无形资产和其他长期资产所支付的现金")
            break

    # 转换为浮点数
    for k in list(result.keys()):
        if k == "report_date":
            continue
        v = result[k]
        if v is not None:
            try:
                result[k] = float(v)
            except (ValueError, TypeError):
                result[k] = None

    return result


def calc_derived_metrics(latest):
    """计算衍生指标"""
    m = {}

    # 盈利指标
    revenue = latest.get("revenue") or 0
    cogs = latest.get("cost_of_goods") or 0
    net_profit = latest.get("net_profit") or 0
    total_assets = latest.get("total_assets") or 1
    total_equity = latest.get("total_equity") or 1
    current_assets = latest.get("current_assets") or 0
    current_liabilities = latest.get("current_liabilities") or 1
    total_liabilities = latest.get("total_liabilities") or 0
    cash = latest.get("cash") or 0
    ocf = latest.get("operating_cashflow") or 0
    capex = latest.get("capex") or 0
    ar = latest.get("accounts_receivable") or 0
    rd = latest.get("rd_expense") or 0

    m["gross_margin"] = round((revenue - cogs) / revenue * 100, 2) if revenue else 0
    m["net_margin"] = round(net_profit / revenue * 100, 2) if revenue else 0
    m["roe"] = round(net_profit / total_equity * 100, 2) if total_equity else 0
    m["roa"] = round(net_profit / total_assets * 100, 2) if total_assets else 0

    # 杜邦拆解
    net_profit_rate = net_profit / revenue if revenue else 0
    asset_turnover = revenue / total_assets if total_assets else 0
    equity_multiplier = total_assets / total_equity if total_equity else 0
    m["dupont"] = {
        "net_profit_margin": round(net_profit_rate * 100, 2),
        "asset_turnover": round(asset_turnover, 4),
        "equity_multiplier": round(equity_multiplier, 4),
        "roe_reconstructed": round(net_profit_rate * asset_turnover * equity_multiplier * 100, 2),
    }

    # 偿债指标
    m["current_ratio"] = round(current_assets / current_liabilities, 2) if current_liabilities else 0
    m["quick_ratio"] = round((current_assets - (latest.get("inventory") or 0)) / current_liabilities, 2) if current_liabilities else 0
    m["debt_ratio"] = round(total_liabilities / total_assets * 100, 2) if total_assets else 0
    m["cashflow_ratio"] = round(ocf / current_liabilities, 2) if current_liabilities else 0

    # 营运指标
    m["ar_turnover"] = round(revenue / ar, 2) if ar else 0
    m["at_turnover"] = round(revenue / total_assets, 4) if total_assets else 0
    m["free_cashflow"] = round(ocf - capex, 2)

    # 费用率
    m["selling_expense_ratio"] = round((latest.get("selling_expense") or 0) / revenue * 100, 2) if revenue else 0
    m["admin_expense_ratio"] = round((latest.get("admin_expense") or 0) / revenue * 100, 2) if revenue else 0
    m["rd_expense_ratio"] = round(rd / revenue * 100, 2) if revenue else 0
    m["finance_expense_ratio"] = round((latest.get("finance_expense") or 0) / revenue * 100, 2) if revenue else 0

    return m


def detect_warnings(annual, latest, metrics):
    """检测预警信号"""
    warnings = []

    # 1. 毛利率异常（与软件行业基准对比）
    gm = metrics.get("gross_margin", 0)
    if gm > 90:
        warnings.append({
            "rule": "gross_margin_anomaly",
            "severity": "medium",
            "desc": f"毛利率异常偏高（{gm}%），远超软件行业均值",
            "detail": "消费类软件天然高毛利，但需关注营业成本占比变化趋势",
        })

    # 2. 费用率超100%
    total_expense_ratio = (
        metrics.get("selling_expense_ratio", 0)
        + metrics.get("admin_expense_ratio", 0)
        + metrics.get("rd_expense_ratio", 0)
        + metrics.get("finance_expense_ratio", 0)
    )
    cost_ratio = 100 - gm
    if total_expense_ratio + cost_ratio > 100:
        warnings.append({
            "rule": "expense_exceeds_revenue",
            "severity": "high",
            "desc": f"费用率合计{total_expense_ratio + cost_ratio:.1f}%，超过100%",
            "detail": f"销售{metrics.get('selling_expense_ratio',0)}% + 研发{metrics.get('rd_expense_ratio',0)}% + 管理{metrics.get('admin_expense_ratio',0)}% + 成本{cost_ratio:.1f}%",
        })

    # 3. 经营现金流恶化
    ocf = latest.get("operating_cashflow") or 0
    net_profit = latest.get("net_profit") or 0
    if net_profit < 0 and ocf > 0 and ocf < abs(net_profit) * 0.5:
        warnings.append({
            "rule": "profit_cash_mismatch",
            "severity": "medium",
            "desc": "经营现金流与净利润不匹配",
            "detail": f"净利润{net_profit/1e8:.2f}亿，经营现金流仅{ocf/1e8:.2f}亿",
        })

    # 4. 自由现金流为负
    fcf = metrics.get("free_cashflow", 0)
    if fcf < 0:
        warnings.append({
            "rule": "negative_free_cashflow",
            "severity": "medium",
            "desc": f"自由现金流为负（{fcf/1e8:.2f}亿）",
            "detail": "公司处于'烧钱'阶段，需关注融资能力",
        })

    # 5. 流动比率低于健康线
    cr = metrics.get("current_ratio", 0)
    if cr < 2.0:
        warnings.append({
            "rule": "low_current_ratio",
            "severity": "low" if cr > 1.0 else "medium",
            "desc": f"流动比率{cr}低于2.0健康线",
            "detail": "短期偿债能力承压",
        })

    # 6. 连续亏损
    years = sorted(annual.keys())
    recent_losses = 0
    for y in years[-3:]:
        np = annual[y].get("net_profit")
        if np is not None and np < 0:
            recent_losses += 1
    if recent_losses >= 2:
        warnings.append({
            "rule": "consecutive_losses",
            "severity": "high",
            "desc": f"近3年中有{recent_losses}年亏损",
            "detail": "持续亏损可能触发退市风险警示",
        })

    return warnings


def build_sources(info, key_indicators, income, balance, cashflow):
    """构建数据来源列表"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    sources = []
    if info:
        sources.append({"metric": "公司概况", "source": "AKShare (stock_individual_info_em)", "confidence": "high", "fetch_time": now})
    if key_indicators:
        sources.append({"metric": "关键财务指标", "source": "AKShare (stock_financial_abstract_ths)", "confidence": "high", "fetch_time": now})
    if income:
        sources.append({"metric": "利润表", "source": "AKShare (stock_financial_report_sina)", "confidence": "high", "fetch_time": now})
    if balance:
        sources.append({"metric": "资产负债表", "source": "AKShare (stock_financial_report_sina)", "confidence": "high", "fetch_time": now})
    if cashflow:
        sources.append({"metric": "现金流量表", "source": "AKShare (stock_financial_report_sina)", "confidence": "high", "fetch_time": now})
    return sources


def analyze(code):
    """主分析流程"""
    print(f"[1/4] 初始化 akshare...", file=sys.stderr)
    ak = ensure_akshare()
    errors = []

    # 并发获取数据
    info, key_indicators, income, balance, cashflow = {}, [], [], [], []

    print(f"[2/4] 并发获取 {code} 财务数据...", file=sys.stderr)
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(fetch_company_info, ak, code): "company_info",
            executor.submit(fetch_key_indicators, ak, code): "key_indicators",
            executor.submit(fetch_income_statement, ak, code): "income",
            executor.submit(fetch_balance_sheet, ak, code): "balance",
            executor.submit(fetch_cashflow_statement, ak, code): "cashflow",
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
                if name == "company_info":
                    info = result
                elif name == "key_indicators":
                    key_indicators = result
                elif name == "income":
                    income = result
                elif name == "balance":
                    balance = result
                elif name == "cashflow":
                    cashflow = result
            except Exception as e:
                errors.append({"source": name, "error": str(e)})

    print(f"[3/4] 数据采集完成，开始分析...", file=sys.stderr)
    print(f"  公司概况: {'OK' if info else 'FAIL'}", file=sys.stderr)
    print(f"  关键指标: {len(key_indicators)}条", file=sys.stderr)
    print(f"  利润表: {len(income)}条", file=sys.stderr)
    print(f"  资产负债表: {len(balance)}条", file=sys.stderr)
    print(f"  现金流量表: {len(cashflow)}条", file=sys.stderr)
    if errors:
        print(f"  错误: {errors}", file=sys.stderr)

    # 构建公司信息
    company_info = {
        "name": info.get("股票简称", "未知"),
        "code": code,
        "industry": info.get("行业", "未知"),
        "ipo_date": str(info.get("上市时间", "")),
        "total_market_cap": info.get("总市值"),
        "float_market_cap": info.get("流通市值"),
        "total_shares": info.get("总股本"),
        "float_shares": info.get("流通股"),
        "latest_price": info.get("最新"),
    }

    # 构建多年数据
    annual = build_annual_data(key_indicators)

    # 构建最新详细数据
    latest = build_latest_from_statements(income, balance, cashflow)

    # 计算衍生指标
    metrics = calc_derived_metrics(latest)

    # 检测预警信号
    warnings = detect_warnings(annual, latest, metrics)

    # 构建数据来源
    sources = build_sources(info, key_indicators, income, balance, cashflow)

    # 合并 latest 和 metrics 到 latest
    latest.update(metrics)

    print(f"[4/4] 分析完成，输出结果", file=sys.stderr)

    return {
        "company_info": company_info,
        "financials": annual,
        "latest": latest,
        "warnings": warnings,
        "sources": sources,
        "errors": errors,
    }


def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/analyze.py <股票代码>", file=sys.stderr)
        print("示例: python scripts/analyze.py 300624", file=sys.stderr)
        sys.exit(1)

    code = sys.argv[1].strip()
    if not code.isdigit() or len(code) != 6:
        print(f"错误: 股票代码必须为6位数字，收到: {code}", file=sys.stderr)
        sys.exit(1)

    result = analyze(code)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2, default=str)
    print()  # 末尾换行


if __name__ == "__main__":
    main()
