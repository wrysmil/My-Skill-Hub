import pytest
from scripts.indicator_calculator import IndicatorCalculator


@pytest.fixture
def calc():
    return IndicatorCalculator()


@pytest.fixture
def sample_financials():
    """模拟财务数据"""
    return {
        "revenue": 100_000_000,
        "cost_of_goods": 40_000_000,
        "net_profit": 15_000_000,
        "total_assets": 200_000_000,
        "total_equity": 120_000_000,
        "current_assets": 80_000_000,
        "current_liabilities": 50_000_000,
        "inventory": 10_000_000,
        "total_liabilities": 80_000_000,
        "operating_cashflow": 18_000_000,
        "capex": 5_000_000,
        "accounts_receivable": 15_000_000,
        "interest_bearing_debt": 30_000_000,
        "cash": 25_000_000,
        "rd_expense": 8_000_000,
    }


def test_gross_margin(calc, sample_financials):
    result = calc.calc_profitability(sample_financials)
    assert abs(result["gross_margin"] - 60.0) < 0.01


def test_net_margin(calc, sample_financials):
    result = calc.calc_profitability(sample_financials)
    assert abs(result["net_margin"] - 15.0) < 0.01


def test_roe(calc, sample_financials):
    result = calc.calc_profitability(sample_financials)
    assert abs(result["roe"] - 12.5) < 0.01


def test_dupont(calc, sample_financials):
    result = calc.calc_profitability(sample_financials)
    dupont = result["dupont"]
    assert abs(dupont["roe_reconstructed"] - 12.5) < 0.5


def test_current_ratio(calc, sample_financials):
    result = calc.calc_solvency(sample_financials)
    assert abs(result["current_ratio"] - 1.6) < 0.01


def test_debt_ratio(calc, sample_financials):
    result = calc.calc_solvency(sample_financials)
    assert abs(result["debt_ratio"] - 40.0) < 0.01


def test_free_cashflow(calc, sample_financials):
    result = calc.calc_operating(sample_financials)
    assert result["free_cashflow"] == 13_000_000


def test_score_green(calc):
    score = calc._score_indicator("roe", 20.0, None)
    assert score >= 80


def test_score_red(calc):
    score = calc._score_indicator("roe", 3.0, None)
    assert score < 60


def test_dimension_score(calc, sample_financials):
    result = calc.calc_profitability(sample_financials)
    assert 0 <= result["score"] <= 100
    assert result["light"] in ("green", "yellow", "red")
