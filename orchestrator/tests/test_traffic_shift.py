"""Unit tests for traffic weight computation. Pure logic only."""
from orchestrator.traffic_shift import compute_next_weight_step


def test_first_step_from_zero():
    assert compute_next_weight_step(0, step=25) == 25


def test_middle_step():
    assert compute_next_weight_step(50, step=25) == 75


def test_step_caps_at_max_weight():
    assert compute_next_weight_step(90, step=25, max_weight=100) == 100


def test_already_at_max_stays_at_max():
    assert compute_next_weight_step(100, step=25, max_weight=100) == 100
