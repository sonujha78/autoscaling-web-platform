"""Shift ALB traffic between blue and green target groups via weighted forwarding."""
import boto3

from orchestrator import config


def get_current_weights(listener_arn: str, region: str = None) -> dict:
    """Return {target_group_arn: weight} for the listener's current default action."""
    region = region or config.AWS_REGION
    elbv2 = boto3.client("elbv2", region_name=region)

    listener = elbv2.describe_listeners(ListenerArns=[listener_arn])["Listeners"][0]
    default_action = listener["DefaultActions"][0]
    forward_config = default_action.get("ForwardConfig", {})
    target_groups = forward_config.get("TargetGroups", [])

    return {tg["TargetGroupArn"]: tg["Weight"] for tg in target_groups}


def shift_traffic(listener_arn: str, blue_tg_arn: str, green_tg_arn: str,
                   blue_weight: int, green_weight: int, region: str = None) -> dict:
    """
    Update the ALB listener's default action to forward traffic with the given
    weights between blue and green target groups.
    """
    region = region or config.AWS_REGION
    elbv2 = boto3.client("elbv2", region_name=region)

    response = elbv2.modify_listener(
        ListenerArn=listener_arn,
        DefaultActions=[
            {
                "Type": "forward",
                "ForwardConfig": {
                    "TargetGroups": [
                        {"TargetGroupArn": blue_tg_arn, "Weight": blue_weight},
                        {"TargetGroupArn": green_tg_arn, "Weight": green_weight},
                    ]
                },
            }
        ],
    )
    return response


def shift_to_green(listener_arn: str, blue_tg_arn: str, green_tg_arn: str, region: str = None) -> dict:
    """Full cutover: 100% traffic to green, 0% to blue."""
    return shift_traffic(listener_arn, blue_tg_arn, green_tg_arn, blue_weight=0, green_weight=100, region=region)


def shift_to_blue(listener_arn: str, blue_tg_arn: str, green_tg_arn: str, region: str = None) -> dict:
    """Rollback: 100% traffic to blue, 0% to green."""
    return shift_traffic(listener_arn, blue_tg_arn, green_tg_arn, blue_weight=100, green_weight=0, region=region)


def compute_next_weight_step(current_green_weight: int, step: int = 25, max_weight: int = 100) -> int:
    """
    Pure function: given the current green weight, compute the next weight in a
    gradual traffic shift (e.g. canary-style ramp-up: 0 -> 25 -> 50 -> 75 -> 100).
    """
    return min(current_green_weight + step, max_weight)
