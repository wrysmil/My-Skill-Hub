import pytest
from scripts.report_generator import ReportGenerator


@pytest.fixture
def generator():
    return ReportGenerator()


@pytest.fixture
def sample_analysis():
    return {
        "company_name": "贵州茅台",
        "stock_code": "600519",
        "date": "2026-05-15",
        "total_score": 88,
        "light": "green",
        "profit": {"score": 92, "light": "green", "gross_margin": 91.5, "net_margin": 33.0, "roe": 28.5, "roa": 15.2,
                   "dupont": {"net_profit_margin": 33.0, "asset_turnover": 0.46, "equity_multiplier": 1.87, "roe_reconstructed": 28.5}},
        "solvency": {"score": 85, "light": "green", "current_ratio": 3.5, "quick_ratio": 3.2, "debt_ratio": 25.0, "cashflow_ratio": 1.2, "deposit_loan_flag": False},
        "operating": {"score": 80, "light": "green", "ar_turnover": 50.0, "inv_turnover": 0.8, "at_turnover": 0.46, "free_cashflow": 50_000_000_000, "operating_cashflow": 60_000_000_000},
        "growth": {"score": 75, "light": "yellow", "revenue_growth": 12.0, "profit_growth": 15.0, "rd_ratio": 0.5},
        "warnings": [],
        "warning_rating": "low",
    }


def test_quick_summary(generator, sample_analysis):
    result = generator.generate_quick_summary(sample_analysis)
    assert "贵州茅台" in result
    assert "600519" in result
    assert "88" in result


def test_dashboard(generator, sample_analysis):
    result = generator.generate_dashboard(sample_analysis)
    assert "盈利能力" in result
    assert "偿债能力" in result
    assert "营运能力" in result
    assert "发展能力" in result
    assert "92" in result
    assert "85" in result


def test_data_source_attribution(generator, sample_analysis):
    sources = [{"metric": "毛利率", "source": "AKShare", "confidence": "high", "period": "2025", "fetch_time": "2026-05-15"}]
    result = generator.generate_source_table(sources)
    assert "AKShare" in result
    assert "high" in result
