"""EMI must use outstanding + remaining term after rate changes."""

from datetime import date
from decimal import Decimal

from app.api.v1.loans.schemas import LoanResponse, compute_emi


def test_compute_emi_original_principal_tenure_is_wrong_after_rate_change():
    # Old (incorrect) formula matched the reported ₹5,786 bug.
    assert compute_emi(Decimal("480000"), Decimal("7.85"), 120) == Decimal("5785.75")


def test_compute_emi_outstanding_remaining_matches_bank():
    # Bank EMI for ₹4,32,906 @ 7.85% over 97 remaining months ≈ ₹6,042.
    assert compute_emi(Decimal("432906"), Decimal("7.85"), 97) == Decimal("6041.77")


def test_loan_response_emi_uses_outstanding_and_remaining():
    loan = LoanResponse(
        id="00000000-0000-4000-8000-000000000001",
        name="Home Loan",
        kind="HL",
        principal=Decimal("480000"),
        rate_pct=Decimal("7.85"),
        tenure_months=114,  # paid ~17 + remaining 97
        start_date=date(2025, 3, 15),
        outstanding=Decimal("432906"),
    )
    # paid_months depends on "today"; force remaining via tenure - paid.
    # With remaining_months > 0, EMI must track outstanding, not principal.
    assert loan.remaining_months >= 1
    assert loan.emi == compute_emi(
        Decimal("432906"), Decimal("7.85"), loan.remaining_months
    )
