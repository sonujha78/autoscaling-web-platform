"""Unit tests for health check evaluation logic. Pure logic only."""
from orchestrator.health_check import InstanceHealthResult, evaluate_health_results


def test_all_healthy_returns_true():
    results = [
        InstanceHealthResult("i-1", "10.0.1.1", healthy=True, status_code=200),
        InstanceHealthResult("i-2", "10.0.1.2", healthy=True, status_code=200),
    ]
    summary = evaluate_health_results(results)
    assert summary.all_healthy is True


def test_one_unhealthy_fails_overall():
    results = [
        InstanceHealthResult("i-1", "10.0.1.1", healthy=True, status_code=200),
        InstanceHealthResult("i-2", "10.0.1.2", healthy=False, status_code=500),
    ]
    summary = evaluate_health_results(results)
    assert summary.all_healthy is False


def test_empty_results_is_not_healthy():
    summary = evaluate_health_results([])
    assert summary.all_healthy is False
