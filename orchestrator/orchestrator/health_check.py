"""Direct health checks against target group instances, bypassing the ALB."""
import time
from dataclasses import dataclass, field

import boto3
import requests

from orchestrator import config


@dataclass
class InstanceHealthResult:
    instance_id: str
    ip_address: str
    healthy: bool
    status_code: int = None
    error: str = None


@dataclass
class HealthCheckSummary:
    all_healthy: bool
    results: list = field(default_factory=list)


def get_target_group_instance_ips(target_group_arn: str, region: str = None) -> dict:
    """
    Return {instance_id: private_ip} for all instances currently registered
    in the given target group (regardless of current health state).
    """
    region = region or config.AWS_REGION
    elbv2 = boto3.client("elbv2", region_name=region)
    ec2 = boto3.client("ec2", region_name=region)

    targets = elbv2.describe_target_health(TargetGroupArn=target_group_arn)
    instance_ids = [t["Target"]["Id"] for t in targets["TargetHealthDescriptions"]]

    if not instance_ids:
        return {}

    reservations = ec2.describe_instances(InstanceIds=instance_ids)["Reservations"]
    ip_map = {}
    for r in reservations:
        for inst in r["Instances"]:
            ip_map[inst["InstanceId"]] = inst.get("PublicIpAddress") or inst.get("PrivateIpAddress")
    return ip_map


def check_instance_health(instance_id: str, ip_address: str, path: str = None, port: int = None,
                           timeout: int = None) -> InstanceHealthResult:
    """Hit http://<ip>:<port>/<path> directly on one instance."""
    path = path or config.HEALTH_CHECK_PATH
    port = port or config.HEALTH_CHECK_PORT
    timeout = timeout or config.HEALTH_CHECK_TIMEOUT_SECONDS

    url = f"http://{ip_address}:{port}{path}"
    try:
        resp = requests.get(url, timeout=timeout)
        return InstanceHealthResult(
            instance_id=instance_id,
            ip_address=ip_address,
            healthy=(resp.status_code == 200),
            status_code=resp.status_code,
        )
    except requests.RequestException as e:
        return InstanceHealthResult(
            instance_id=instance_id,
            ip_address=ip_address,
            healthy=False,
            error=str(e),
        )


def evaluate_health_results(results: list) -> HealthCheckSummary:
    """Pure decision function: given a list of InstanceHealthResult, decide overall health."""
    all_healthy = len(results) > 0 and all(r.healthy for r in results)
    return HealthCheckSummary(all_healthy=all_healthy, results=results)


def wait_for_target_group_healthy(target_group_arn: str, retries: int = None,
                                   delay: int = None, region: str = None) -> HealthCheckSummary:
    """
    Poll all instances in a target group directly (bypassing ALB) until healthy
    or retries exhausted.
    """
    retries = retries or config.HEALTH_CHECK_RETRIES
    delay = delay or config.HEALTH_CHECK_RETRY_DELAY_SECONDS

    last_summary = HealthCheckSummary(all_healthy=False, results=[])

    for attempt in range(1, retries + 1):
        ip_map = get_target_group_instance_ips(target_group_arn, region=region)
        results = [
            check_instance_health(instance_id, ip)
            for instance_id, ip in ip_map.items()
        ]
        last_summary = evaluate_health_results(results)

        if last_summary.all_healthy:
            return last_summary

        time.sleep(delay)

    return last_summary
