"""四维度财务指标计算 + 评分"""
from typing import Optional


class IndicatorCalculator:
    """四维度财务指标计算引擎"""

    PROFIT_WEIGHTS = {"roe": 0.4, "gross_margin": 0.3, "net_margin": 0.3}
    SOLVENCY_WEIGHTS = {"debt_ratio": 0.4, "current_ratio": 0.3, "cashflow_ratio": 0.3}
    OPERATING_WEIGHTS = {"ocf": 0.4, "ar_turnover": 0.3, "free_cashflow": 0.3}
    GROWTH_WEIGHTS = {"revenue_growth": 0.4, "profit_growth": 0.4, "rd_ratio": 0.2}

    SCORE_THRESHOLDS = {
        "roe": {"green": 15, "yellow": 8},
        "net_margin": {"green": 15, "yellow": 5},
        "debt_ratio": {"green": 50, "yellow": 70, "invert": True},
        "current_ratio": {"green": 2.0, "yellow": 1.0},
        "revenue_growth": {"green": 15, "yellow": 0},
        "profit_growth": {"green": 15, "yellow": 0},
    }

    def calc_profitability(self, f: dict, industry_avg: dict = None) -> dict:
        """盈利能力计算"""
        revenue = f.get("revenue", 0)
        cost = f.get("cost_of_goods", 0)
        net_profit = f.get("net_profit", 0)
        total_assets = f.get("total_assets", 0)
        total_equity = f.get("total_equity", 0)

        gross_margin = ((revenue - cost) / revenue * 100) if revenue else 0
        net_margin = (net_profit / revenue * 100) if revenue else 0
        roe = (net_profit / total_equity * 100) if total_equity else 0
        roa = (net_profit / total_assets * 100) if total_assets else 0

        net_profit_rate = net_margin / 100 if net_margin else 0
        asset_turnover = revenue / total_assets if total_assets else 0
        equity_multiplier = total_assets / total_equity if total_equity else 0
        roe_reconstructed = net_profit_rate * asset_turnover * equity_multiplier * 100

        dupont = {
            "net_profit_margin": round(net_margin, 2),
            "asset_turnover": round(asset_turnover, 4),
            "equity_multiplier": round(equity_multiplier, 4),
            "roe_reconstructed": round(roe_reconstructed, 2),
        }

        gm_score = self._score_indicator("gross_margin", gross_margin, industry_avg)
        nm_score = self._score_indicator("net_margin", net_margin, industry_avg)
        roe_score = self._score_indicator("roe", roe, industry_avg)
        weighted_score = (
            roe_score * self.PROFIT_WEIGHTS["roe"]
            + gm_score * self.PROFIT_WEIGHTS["gross_margin"]
            + nm_score * self.PROFIT_WEIGHTS["net_margin"]
        )

        return {
            "gross_margin": round(gross_margin, 2),
            "net_margin": round(net_margin, 2),
            "roe": round(roe, 2),
            "roa": round(roa, 2),
            "dupont": dupont,
            "score": round(weighted_score),
            "light": self._score_to_light(weighted_score),
        }

    def calc_solvency(self, f: dict, industry_avg: dict = None) -> dict:
        """偿债能力计算"""
        current_assets = f.get("current_assets", 0)
        current_liabilities = f.get("current_liabilities", 0)
        inventory = f.get("inventory", 0)
        total_assets = f.get("total_assets", 0)
        total_liabilities = f.get("total_liabilities", 0)
        ocf = f.get("operating_cashflow", 0)
        cash = f.get("cash", 0)
        interest_debt = f.get("interest_bearing_debt", 0)

        current_ratio = current_assets / current_liabilities if current_liabilities else 0
        quick_ratio = (current_assets - inventory) / current_liabilities if current_liabilities else 0
        debt_ratio = total_liabilities / total_assets * 100 if total_assets else 0
        cashflow_ratio = ocf / current_liabilities if current_liabilities else 0

        deposit_loan_flag = (
            cash > total_assets * 0.2 and interest_debt > total_assets * 0.3
        )

        cr_score = self._score_indicator("current_ratio", current_ratio, industry_avg)
        dr_score = self._score_indicator("debt_ratio", debt_ratio, industry_avg)
        cfr_score = 80 if cashflow_ratio > 0.3 else (60 if cashflow_ratio > 0 else 30)
        weighted_score = (
            dr_score * self.SOLVENCY_WEIGHTS["debt_ratio"]
            + cr_score * self.SOLVENCY_WEIGHTS["current_ratio"]
            + cfr_score * self.SOLVENCY_WEIGHTS["cashflow_ratio"]
        )

        return {
            "current_ratio": round(current_ratio, 2),
            "quick_ratio": round(quick_ratio, 2),
            "debt_ratio": round(debt_ratio, 2),
            "cashflow_ratio": round(cashflow_ratio, 2),
            "deposit_loan_flag": deposit_loan_flag,
            "score": round(weighted_score),
            "light": self._score_to_light(weighted_score),
        }

    def calc_operating(self, f: dict, industry_avg: dict = None) -> dict:
        """营运能力计算"""
        revenue = f.get("revenue", 0)
        cogs = f.get("cost_of_goods", 0)
        ocf = f.get("operating_cashflow", 0)
        capex = f.get("capex", 0)
        ar = f.get("accounts_receivable", 0)
        inventory = f.get("inventory", 0)
        total_assets = f.get("total_assets", 0)

        ar_turnover = revenue / ar if ar else 0
        inv_turnover = cogs / inventory if inventory else 0
        at_turnover = revenue / total_assets if total_assets else 0
        free_cashflow = ocf - capex

        ocf_score = 80 if ocf > 0 else (50 if ocf == 0 else 20)
        ar_score = self._score_indicator("ar_turnover", ar_turnover, industry_avg)
        fcf_score = 80 if free_cashflow > 0 else (50 if free_cashflow == 0 else 20)
        weighted_score = (
            ocf_score * self.OPERATING_WEIGHTS["ocf"]
            + ar_score * self.OPERATING_WEIGHTS["ar_turnover"]
            + fcf_score * self.OPERATING_WEIGHTS["free_cashflow"]
        )

        return {
            "ar_turnover": round(ar_turnover, 2),
            "inv_turnover": round(inv_turnover, 2),
            "at_turnover": round(at_turnover, 4),
            "free_cashflow": free_cashflow,
            "operating_cashflow": ocf,
            "score": round(weighted_score),
            "light": self._score_to_light(weighted_score),
        }

    def calc_growth(self, f: dict, industry_avg: dict = None) -> dict:
        """发展能力计算"""
        revenue_growth = f.get("revenue_growth", 0)
        profit_growth = f.get("profit_growth", 0)
        rd_ratio = f.get("rd_ratio", 0)

        rg_score = self._score_indicator("revenue_growth", revenue_growth, industry_avg)
        pg_score = self._score_indicator("profit_growth", profit_growth, industry_avg)
        rd_score = self._score_indicator("rd_ratio", rd_ratio, industry_avg)
        weighted_score = (
            rg_score * self.GROWTH_WEIGHTS["revenue_growth"]
            + pg_score * self.GROWTH_WEIGHTS["profit_growth"]
            + rd_score * self.GROWTH_WEIGHTS["rd_ratio"]
        )

        return {
            "revenue_growth": round(revenue_growth, 2),
            "profit_growth": round(profit_growth, 2),
            "rd_ratio": round(rd_ratio, 2),
            "score": round(weighted_score),
            "light": self._score_to_light(weighted_score),
        }

    def calc_total_score(self, profit: dict, solvency: dict, operating: dict, growth: dict) -> dict:
        """综合评分"""
        total = (
            profit["score"] * 0.3
            + solvency["score"] * 0.25
            + operating["score"] * 0.2
            + growth["score"] * 0.25
        )
        return {
            "total_score": round(total),
            "light": self._score_to_light(total),
            "profit": profit,
            "solvency": solvency,
            "operating": operating,
            "growth": growth,
        }

    def _score_indicator(self, metric: str, value: float, industry_avg: dict = None) -> float:
        """单项指标评分(0-100)"""
        thresholds = self.SCORE_THRESHOLDS.get(metric)
        if not thresholds:
            if industry_avg and metric in industry_avg:
                avg = industry_avg[metric]
                if avg > 0:
                    ratio = value / avg
                    if ratio >= 1.2:
                        return 90
                    elif ratio >= 0.9:
                        return 70
                    elif ratio >= 0.5:
                        return 40
                    else:
                        return 20
            return 60

        green = thresholds["green"]
        yellow = thresholds["yellow"]
        invert = thresholds.get("invert", False)

        if invert:
            if value <= green:
                return 90
            elif value <= yellow:
                return 70
            else:
                return 30
        else:
            if value >= green:
                return 90
            elif value >= yellow:
                return 70
            else:
                return 30

    @staticmethod
    def _score_to_light(score: float) -> str:
        if score >= 80:
            return "green"
        elif score >= 60:
            return "yellow"
        return "red"
