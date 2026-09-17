"""Automatic rollback: monitor ALB 5xx error counts during bake time and decide."""
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import boto3

from orchestrator import config


@dataclass
class MetricWindow:
    """One window of ALB 5xx count data."""
    start_time: datetime
    end_time: datetime
    error_5xx_count: int


@dataclass
class RollbackDecision:
    should_rollback: bool
    reason: str
    total_5xx_count: int = 0


def get_alb_5xx_count(alb_arn_suffix: str, start_time: datetime, end_time: datetime,
                       region: str = None) -> int:
    """
    Query CloudWatch for ALB HTTPCode_Target_5XX_Count (or HTTPCode_ELB_5XX_Count)
    summed over the given window.
    """
    region = region or config.AWS_REGION
    cloudwatch = boto3.client("cloudwatch", region_name=region)

    response = cloudwatch.get_metric_statistics(
        Namespace="AWS/ApplicationELB",
        MetricName="HTTPCode_Target_5XX_Count",
        Dimensions=[{"Name": "LoadBalancer", "Value": alb_arn_suffix}],
        StartTime=start_time,
        EndTime=end_time,
        Period=60,
        Statistics=["Sum"],
    )

    datapoints = response.get("Datapoints", [])
    return int(sum(dp["Sum"] for dp in datapoints))


def evaluate_rollback_decision(error_count: int, threshold: int = None) -> RollbackDecision:
    """
    Pure decision function: given a 5xx error count observed during the bake
    window, decide whether to roll back.
    """
    threshold = threshold if threshold is not None else config.ROLLBACK_5XX_THRESHOLD

    if error_count >= threshold:
        return RollbackDecision(
            should_rollback=True,
            reason=f"5xx error count ({error_count}) reached/exceeded threshold ({threshold})",
            total_5xx_count=error_count,
        )
    return RollbackDecision(
        should_rollback=False,
        reason=f"5xx error count ({error_count}) within threshold ({threshold})",
        total_5xx_count=error_count,
    )


def monitor_bake_period(alb_arn_suffix: str, bake_seconds: int = None, threshold: int = None,
                         check_interval: int = None, region: str = None) -> RollbackDecision:
    """
    Poll CloudWatch every `check_interval` seconds for `bake_seconds` total,
    checking cumulative 5xx count against threshold. Returns as soon as a
    rollback condition is hit, or after the full bake period if healthy.
    """
    bake_seconds = bake_seconds or config.BAKE_TIME_SECONDS
    check_interval = check_interval or config.ROLLBACK_CHECK_INTERVAL_SECONDS
    deploy_start = datetime.utcnow()
    elapsed = 0

    while elapsed < bake_seconds:
        time.sleep(check_interval)
        elapsed += check_interval

        now = datetime.utcnow()
        error_count = get_alb_5xx_count(alb_arn_suffix, deploy_start, now, region=region)
        decision = evaluate_rollback_decision(error_count, threshold=threshold)

        if decision.should_rollback:
            return decision

    # Bake period completed with no rollback trigger
    final_count = get_alb_5xx_count(alb_arn_suffix, deploy_start, datetime.utcnow(), region=region)
    return evaluate_rollback_decision(final_count, threshold=threshold)
