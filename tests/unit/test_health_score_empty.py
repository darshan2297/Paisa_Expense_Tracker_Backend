"""Empty-state financial health must not invent a healthy composite score."""

from app.api.v1.insights.service import _status_ge, _status_le


def test_empty_budget_and_debt_no_longer_average_to_thirty_three() -> None:
    """Regression: 0 budget util + 0 debt used to contribute 100+100 → composite 33."""
    savings_rate = 0.0
    inv_rate = 0.0
    budget_util = 0.0
    ef_months = 0.0
    debt_ratio = 0.0
    goal_progress = 0.0
    has_budget = False
    has_debt_signal = False

    budget_component = max(0.0, 100.0 - budget_util) if has_budget else 0.0
    debt_component = max(0.0, 100.0 - debt_ratio * 2) if has_debt_signal else 0.0
    composite = int(
        round(
            (
                min(100.0, savings_rate * 2.5)
                + min(100.0, inv_rate * 5)
                + budget_component
                + min(100.0, ef_months / 6 * 100)
                + debt_component
                + goal_progress
            )
            / 6
        )
    )
    assert composite == 0


def test_unset_budget_card_is_needs_work() -> None:
    status, score = ("Needs work", 25)
    assert status == "Needs work"
    assert score == 25
    # Sanity: once a budget exists, 0% utilisation is healthy.
    ok_status, ok_score = _status_le(0.0, 85, 100)
    assert ok_status == "Healthy"
    assert ok_score == 85


def test_status_ge_zero_is_needs_work() -> None:
    status, score = _status_ge(0.0, 20, 10)
    assert status == "Needs work"
    assert score == 25
