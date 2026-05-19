import pytest
from scripts.risk_detector import RiskDetector


@pytest.fixture
def detector():
    return RiskDetector()


def test_no_warnings_healthy_company(detector):
    financials = {
        "net_profit_growth": 20,
        "operating_cashflow": 100_000_000,
        "net_profit": 80_000_000,
        "cash": 50_000_000,
        "total_assets": 1_000_000_000,
        "interest_bearing_debt": 100_000_000,
        "accounts_receivable_growth": 10,
        "revenue_growth": 15,
        "q4_revenue_ratio": 0.28,
        "gross_margin": 35,
        "industry_avg_gm": 30,
        "auditor_changed": False,
        "cfo_changes_3y": 1,
        "related_party_ratio": 0.05,
    }
    warnings = detector.detect(financials)
    assert len(warnings) == 0


def test_profit_cash_mismatch(detector):
    financials = {
        "net_profit_growth": 20,
        "operating_cashflow": -50_000_000,
        "net_profit": 100_000_000,
        "cash": 50_000_000,
        "total_assets": 1_000_000_000,
        "interest_bearing_debt": 100_000_000,
        "accounts_receivable_growth": 10,
        "revenue_growth": 15,
        "q4_revenue_ratio": 0.28,
        "gross_margin": 35,
        "industry_avg_gm": 30,
        "auditor_changed": False,
        "cfo_changes_3y": 1,
        "related_party_ratio": 0.05,
    }
    warnings = detector.detect(financials)
    assert any(w["rule"] == "profit_cash_mismatch" for w in warnings)


def test_deposit_loan_both_high(detector):
    financials = {
        "net_profit_growth": 10,
        "operating_cashflow": 50_000_000,
        "net_profit": 80_000_000,
        "cash": 300_000_000,
        "total_assets": 1_000_000_000,
        "interest_bearing_debt": 400_000_000,
        "accounts_receivable_growth": 10,
        "revenue_growth": 15,
        "q4_revenue_ratio": 0.28,
        "gross_margin": 35,
        "industry_avg_gm": 30,
        "auditor_changed": False,
        "cfo_changes_3y": 1,
        "related_party_ratio": 0.05,
    }
    warnings = detector.detect(financials)
    assert any(w["rule"] == "deposit_loan_both_high" for w in warnings)


def test_receivable_fast_growth(detector):
    financials = {
        "net_profit_growth": 10,
        "operating_cashflow": 50_000_000,
        "net_profit": 80_000_000,
        "cash": 50_000_000,
        "total_assets": 1_000_000_000,
        "interest_bearing_debt": 100_000_000,
        "accounts_receivable_growth": 50,
        "revenue_growth": 10,
        "q4_revenue_ratio": 0.28,
        "gross_margin": 35,
        "industry_avg_gm": 30,
        "auditor_changed": False,
        "cfo_changes_3y": 1,
        "related_party_ratio": 0.05,
    }
    warnings = detector.detect(financials)
    assert any(w["rule"] == "receivable_fast_growth" for w in warnings)


def test_multiple_high_warnings(detector):
    financials = {
        "net_profit_growth": 20,
        "operating_cashflow": -50_000_000,
        "net_profit": 100_000_000,
        "cash": 300_000_000,
        "total_assets": 1_000_000_000,
        "interest_bearing_debt": 400_000_000,
        "accounts_receivable_growth": 10,
        "revenue_growth": 15,
        "q4_revenue_ratio": 0.28,
        "gross_margin": 35,
        "industry_avg_gm": 30,
        "auditor_changed": False,
        "cfo_changes_3y": 1,
        "related_party_ratio": 0.05,
    }
    warnings = detector.detect(financials)
    high_count = sum(1 for w in warnings if w["severity"] == "high")
    assert high_count >= 2


def test_risk_rating(detector):
    assert detector.rate_risk([]) == "low"
    assert detector.rate_risk([{"severity": "low"}]) == "low"
    assert detector.rate_risk([{"severity": "medium"}, {"severity": "medium"}, {"severity": "medium"}]) == "medium"
    assert detector.rate_risk([{"severity": "high"}]) == "medium"
    assert detector.rate_risk([{"severity": "high"}, {"severity": "high"}]) == "high"
