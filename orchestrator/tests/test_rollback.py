"""Unit tests for rollback decision logic. No CloudWatch calls - pure logic only."""
from orchestrator.rollback import evaluate_rollback_decision


def test_zero_errors_no_rollback():
    decision = evaluate_rollback_decision(error_count=0, threshold=5)
    assert decision.should_rollback is False
    assert decision.total_5xx_count == 0


def test_errors_below_threshold_no_rollback():
    decision = evaluate_rollback_decision(error_count=4, threshold=5)
    assert decision.should_rollback is False


def test_errors_at_threshold_triggers_rollback():
    decision = evaluate_rollback_decision(error_count=5, threshold=5)
    assert decision.should_rollback is True


def test_errors_above_threshold_triggers_rollback():
    decision = evaluate_rollback_decision(error_count=20, threshold=5)
    assert decision.should_rollback is True
    assert decision.total_5xx_count == 20


def test_decision_reason_is_populated():
    decision = evaluate_rollback_decision(error_count=10, threshold=5)
    assert "10" in decision.reason
    assert "5" in decision.reason


def test_default_threshold_from_config_is_used():
    from orchestrator import config
    decision = evaluate_rollback_decision(error_count=config.ROLLBACK_5XX_THRESHOLD)
    assert decision.should_rollback is True
