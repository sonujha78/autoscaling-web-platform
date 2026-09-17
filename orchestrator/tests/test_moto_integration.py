"""Integration-style test using moto to mock AWS - no real AWS calls."""
import boto3
from moto import mock_aws

from orchestrator.traffic_shift import get_current_weights, shift_traffic


@mock_aws
def test_get_and_shift_weights_with_mocked_elbv2():
    region = "ap-south-1"
    ec2 = boto3.client("ec2", region_name=region)
    elbv2 = boto3.client("elbv2", region_name=region)

    vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")["Vpc"]["VpcId"]
    subnet1 = ec2.create_subnet(VpcId=vpc, CidrBlock="10.0.1.0/24", AvailabilityZone=f"{region}a")["Subnet"]["SubnetId"]
    subnet2 = ec2.create_subnet(VpcId=vpc, CidrBlock="10.0.2.0/24", AvailabilityZone=f"{region}b")["Subnet"]["SubnetId"]

    lb = elbv2.create_load_balancer(Name="test-alb", Subnets=[subnet1, subnet2])["LoadBalancers"][0]
    lb_arn = lb["LoadBalancerArn"]

    blue_tg = elbv2.create_target_group(Name="tg-blue", Protocol="HTTP", Port=8080, VpcId=vpc)["TargetGroups"][0]["TargetGroupArn"]
    green_tg = elbv2.create_target_group(Name="tg-green", Protocol="HTTP", Port=8080, VpcId=vpc)["TargetGroups"][0]["TargetGroupArn"]

    listener = elbv2.create_listener(
        LoadBalancerArn=lb_arn,
        Protocol="HTTP",
        Port=80,
        DefaultActions=[{
            "Type": "forward",
            "ForwardConfig": {
                "TargetGroups": [
                    {"TargetGroupArn": blue_tg, "Weight": 100},
                    {"TargetGroupArn": green_tg, "Weight": 0},
                ]
            },
        }],
    )["Listeners"][0]
    listener_arn = listener["ListenerArn"]

    # Verify initial weights
    weights = get_current_weights(listener_arn, region=region)
    assert weights[blue_tg] == 100
    assert weights[green_tg] == 0

    # Shift traffic fully to green
    shift_traffic(listener_arn, blue_tg, green_tg, blue_weight=0, green_weight=100, region=region)

    weights_after = get_current_weights(listener_arn, region=region)
    assert weights_after[blue_tg] == 0
    assert weights_after[green_tg] == 100
