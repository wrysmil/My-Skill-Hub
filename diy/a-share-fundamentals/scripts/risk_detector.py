"""预警信号规则引擎"""
from typing import List, Dict


class RiskDetector:
    """8条预警信号检测"""

    def detect(self, f: dict) -> List[Dict]:
        """检测所有预警信号，返回触发的警告列表"""
        warnings = []
        rules = [
            self._check_profit_cash_mismatch,
            self._check_deposit_loan_both_high,
            self._check_receivable_fast_growth,
            self._check_q4_revenue_spike,
            self._check_gross_margin_anomaly,
            self._check_audit_change,
            self._check_frequent_cfo_change,
            self._check_related_party_transactions,
        ]
        for rule_fn in rules:
            result = rule_fn(f)
            if result:
                warnings.append(result)
        return warnings

    def rate_risk(self, warnings: list) -> str:
        """综合风险评级"""
        if not warnings:
            return "low"
        high_count = sum(1 for w in warnings if w["severity"] == "high")
        medium_count = sum(1 for w in warnings if w["severity"] == "medium")

        if high_count >= 2:
            return "high"
        if high_count >= 1 or medium_count >= 3:
            return "medium"
        return "low"

    def _check_profit_cash_mismatch(self, f: dict) -> dict:
        npg = f.get("net_profit_growth", 0)
        ocf = f.get("operating_cashflow", 0)
        np = f.get("net_profit", 1)
        ratio = ocf / np if np else 0
        if npg > 0 and ratio < 0.5:
            return {
                "rule": "profit_cash_mismatch",
                "severity": "high",
                "desc": "利润增长但经营现金流持续为负，利润可能只是账面游戏",
                "detail": f"净利润增长{npg}%，经营现金流/净利润={ratio:.1%}",
            }
        return None

    def _check_deposit_loan_both_high(self, f: dict) -> dict:
        cash = f.get("cash", 0)
        total_assets = f.get("total_assets", 1)
        debt = f.get("interest_bearing_debt", 0)
        if cash > total_assets * 0.2 and debt > total_assets * 0.3:
            return {
                "rule": "deposit_loan_both_high",
                "severity": "high",
                "desc": "存贷双高：账面大量现金却背负高额贷款",
                "detail": f"现金占总资产{cash/total_assets:.1%}，有息负债占总资产{debt/total_assets:.1%}",
            }
        return None

    def _check_receivable_fast_growth(self, f: dict) -> dict:
        ar_growth = f.get("accounts_receivable_growth", 0)
        rev_growth = f.get("revenue_growth", 1)
        ratio = ar_growth / rev_growth if rev_growth else 0
        if ratio > 1.5 and ar_growth > 10:
            return {
                "rule": "receivable_fast_growth",
                "severity": "medium",
                "desc": "应收账款增速远超营收增速，坏账风险增加",
                "detail": f"应收增长{ar_growth}% vs 营收增长{rev_growth}%，比值{ratio:.1f}",
            }
        return None

    def _check_q4_revenue_spike(self, f: dict) -> dict:
        q4_ratio = f.get("q4_revenue_ratio", 0)
        if q4_ratio > 0.4:
            return {
                "rule": "q4_revenue_spike",
                "severity": "medium",
                "desc": "Q4收入占比异常偏高，可能存在年底突击确认收入",
                "detail": f"Q4收入占全年{q4_ratio:.1%}",
            }
        return None

    def _check_gross_margin_anomaly(self, f: dict) -> dict:
        gm = f.get("gross_margin", 0)
        industry_gm = f.get("industry_avg_gm", 30)
        if gm > industry_gm * 1.5:
            return {
                "rule": "gross_margin_anomaly",
                "severity": "medium",
                "desc": "毛利率长期不合理高于同行，数据可能被粉饰",
                "detail": f"公司毛利率{gm}% vs 行业均值{industry_gm}%",
            }
        return None

    def _check_audit_change(self, f: dict) -> dict:
        if f.get("auditor_changed", False):
            return {
                "rule": "audit_change",
                "severity": "low",
                "desc": "近期更换审计机构",
                "detail": "当年审计机构与上年不同",
            }
        return None

    def _check_frequent_cfo_change(self, f: dict) -> dict:
        changes = f.get("cfo_changes_3y", 0)
        if changes >= 3:
            return {
                "rule": "frequent_cfo_change",
                "severity": "medium",
                "desc": "3年内财务负责人频繁变动",
                "detail": f"3年内更换{changes}次",
            }
        return None

    def _check_related_party_transactions(self, f: dict) -> dict:
        ratio = f.get("related_party_ratio", 0)
        if ratio > 0.3:
            return {
                "rule": "related_party_transactions",
                "severity": "high",
                "desc": "关联交易占比过高，可能虚增收入",
                "detail": f"关联交易占总收入{ratio:.1%}",
            }
        return None
