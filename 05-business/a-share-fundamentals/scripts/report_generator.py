"""报告组装 + 数据来源标注"""
from typing import List, Dict


LIGHT_EMOJI = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
LIGHT_TEXT = {"green": "优秀", "yellow": "一般", "red": "警惕"}


class ReportGenerator:
    """根据分析结果组装报告"""

    def generate_quick_summary(self, analysis: dict) -> str:
        """速览模式：仪表盘 + 3句话"""
        c = analysis
        light = LIGHT_EMOJI.get(c["light"], "⚪")
        lines = [
            f"# {c['company_name']}({c['stock_code']}) 基本面速览",
            f"",
            f"> {c['date']} | 综合评分：{c['total_score']}/100 {light}",
            f"",
            self._three_sentence_conclusion(c),
            f"",
            f"**四维度**："
            f"盈利 {LIGHT_EMOJI[c['profit']['light']]}{c['profit']['score']} | "
            f"偿债 {LIGHT_EMOJI[c['solvency']['light']]}{c['solvency']['score']} | "
            f"营运 {LIGHT_EMOJI[c['operating']['light']]}{c['operating']['score']} | "
            f"发展 {LIGHT_EMOJI[c['growth']['light']]}{c['growth']['score']}",
            f"",
            f"**预警**：{self._warning_summary(c.get('warnings', []))}",
        ]
        return "\n".join(lines)

    def generate_dashboard(self, analysis: dict) -> str:
        """仪表盘输出"""
        c = analysis
        lines = [
            f"| 维度 | 评分 | 灯色 |",
            f"|------|------|------|",
            f"| 盈利能力 | {c['profit']['score']}/100 | {LIGHT_EMOJI[c['profit']['light']]} |",
            f"| 偿债能力 | {c['solvency']['score']}/100 | {LIGHT_EMOJI[c['solvency']['light']]} |",
            f"| 营运能力 | {c['operating']['score']}/100 | {LIGHT_EMOJI[c['operating']['light']]} |",
            f"| 发展能力 | {c['growth']['score']}/100 | {LIGHT_EMOJI[c['growth']['light']]} |",
            f"",
            f"**综合评分：{c['total_score']}/100 — {LIGHT_TEXT[c['light']]}**",
        ]
        return "\n".join(lines)

    def generate_full_report(self, analysis: dict, sources: list = None) -> str:
        """完整报告"""
        c = analysis
        sections = [
            self._header(c),
            self._executive_summary(c),
            "## 仪表盘\n",
            self.generate_dashboard(c),
            "",
            "## 一、盈利能力分析\n",
            self._profitability_section(c),
            "## 二、偿债能力分析\n",
            self._solvency_section(c),
            "## 三、营运能力分析\n",
            self._operating_section(c),
            "## 四、发展能力分析\n",
            self._growth_section(c),
            "## 五、护城河与竞争优势\n",
            c.get("moat_analysis", "待补充"),
            "## 六、预警信号\n",
            self._warning_section(c.get("warnings", [])),
            "## 七、机构观点\n",
            c.get("institution_opinions", "待补充"),
            "## 八、综合结论\n",
            self._final_conclusion(c),
        ]
        if sources:
            sections.append("## 附录：数据来源明细\n")
            sections.append(self.generate_source_table(sources))
        return "\n\n".join(sections)

    def generate_source_table(self, sources: list) -> str:
        """数据来源明细表"""
        lines = ["| 数据项 | 来源 | 置信度 | 获取时间 |", "|--------|------|--------|---------|"]
        for s in sources:
            lines.append(f"| {s['metric']} | {s['source']} | {s['confidence']} | {s.get('fetch_time', '-')} |")
        return "\n".join(lines)

    def _header(self, c: dict) -> str:
        return f"# {c['company_name']}({c['stock_code']}) 基本面分析报告\n\n> 分析日期：{c['date']}"

    def _executive_summary(self, c: dict) -> str:
        light = LIGHT_TEXT[c["light"]]
        return (
            f"## 执行摘要\n\n"
            f"{c['company_name']}基本面综合评分 **{c['total_score']}/100**，评级为**{light}**。"
            f"盈利能力{'优秀' if c['profit']['score'] >= 80 else '一般' if c['profit']['score'] >= 60 else '需关注'}，"
            f"偿债能力{'稳健' if c['solvency']['score'] >= 80 else '尚可' if c['solvency']['score'] >= 60 else '需关注'}，"
            f"营运效率{'良好' if c['operating']['score'] >= 80 else '一般' if c['operating']['score'] >= 60 else '需关注'}，"
            f"成长性{'强劲' if c['growth']['score'] >= 80 else '平稳' if c['growth']['score'] >= 60 else '放缓'}。"
        )

    def _three_sentence_conclusion(self, c: dict) -> str:
        light = LIGHT_TEXT[c["light"]]
        return (
            f"{c['company_name']}基本面综合评分{c['total_score']}/100，评级{light}。"
            f"盈利维度{c['profit']['score']}分，偿债维度{c['solvency']['score']}分，"
            f"营运维度{c['operating']['score']}分，发展维度{c['growth']['score']}分。"
            f"{self._warning_summary(c.get('warnings', []))}。"
        )

    def _warning_summary(self, warnings: list) -> str:
        if not warnings:
            return "无预警信号"
        high = sum(1 for w in warnings if w["severity"] == "high")
        med = sum(1 for w in warnings if w["severity"] == "medium")
        low = sum(1 for w in warnings if w["severity"] == "low")
        return f"{high}个高危 / {med}个中危 / {low}个低危预警"

    def _warning_section(self, warnings: list) -> str:
        if not warnings:
            return "🟢 未检测到预警信号\n"
        lines = []
        for w in warnings:
            icon = {"high": "🔴", "medium": "🟡", "low": "⚪"}[w["severity"]]
            lines.append(f"- {icon} **{w['desc']}** — {w['detail']}")
        return "\n".join(lines) + "\n"

    def _profitability_section(self, c: dict) -> str:
        p = c["profit"]
        d = p.get("dupont", {})
        return (
            f"| 指标 | 数值 |\n|------|------|\n"
            f"| 毛利率 | {p['gross_margin']}% |\n"
            f"| 净利率 | {p['net_margin']}% |\n"
            f"| ROE | {p['roe']}% |\n"
            f"| ROA | {p['roa']}% |\n\n"
            f"**杜邦拆解**：销售利润率 {d.get('net_profit_margin', '-')}% × "
            f"总资产周转率 {d.get('asset_turnover', '-')} × "
            f"权益乘数 {d.get('equity_multiplier', '-')} = ROE {d.get('roe_reconstructed', '-')}%\n"
        )

    def _solvency_section(self, c: dict) -> str:
        s = c["solvency"]
        return (
            f"| 指标 | 数值 | 健康值 |\n|------|------|--------|\n"
            f"| 流动比率 | {s['current_ratio']} | ≥2.0 |\n"
            f"| 速动比率 | {s['quick_ratio']} | ≥1.0 |\n"
            f"| 资产负债率 | {s['debt_ratio']}% | <60% |\n"
            f"| 现金流动负债比 | {s['cashflow_ratio']} | >0 |\n"
        )

    def _operating_section(self, c: dict) -> str:
        o = c["operating"]
        return (
            f"| 指标 | 数值 |\n|------|------|\n"
            f"| 应收账款周转率 | {o['ar_turnover']} |\n"
            f"| 存货周转率 | {o['inv_turnover']} |\n"
            f"| 总资产周转率 | {o['at_turnover']} |\n"
            f"| 自由现金流 | {o['free_cashflow']:,}元 |\n"
        )

    def _growth_section(self, c: dict) -> str:
        g = c["growth"]
        return (
            f"| 指标 | 数值 |\n|------|------|\n"
            f"| 营收增长率 | {g['revenue_growth']}% |\n"
            f"| 净利润增长率 | {g['profit_growth']}% |\n"
            f"| 研发投入占比 | {g['rd_ratio']}% |\n"
        )

    def _final_conclusion(self, c: dict) -> str:
        return f"综合评分 {c['total_score']}/100，基本面{LIGHT_TEXT[c['light']]}。{self._warning_summary(c.get('warnings', []))}。"
