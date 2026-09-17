"""Full blue-green deployment orchestration: ties together terraform, ansible,
health checks, traffic shifting, and rollback into one workflow."""
import subprocess

from orchestrator import config
from orchestrator.audit_log import AuditLog
from orchestrator.health_check import wait_for_target_group_healthy
from orchestrator.traffic_shift import shift_to_green, shift_to_blue
from orchestrator.rollback import monitor_bake_period


class DeploymentFailed(Exception):
    pass


def run_ansible_configure(ansible_dir: str, private_key: str, ssh_user: str = "ec2-user") -> None:
    """Run the site.yml playbook against the (green) instances via dynamic inventory."""
    subprocess.run(
        [
            "ansible-playbook", "site.yml",
            "--private-key", private_key,
            "--user", ssh_user,
            "--limit", "app_dev_green",
        ],
        cwd=ansible_dir,
        check=True,
    )


def run_blue_green_deploy(
    listener_arn: str,
    blue_tg_arn: str,
    green_tg_arn: str,
    ansible_dir: str,
    private_key: str,
    alb_arn_suffix: str,
    audit: AuditLog,
    dry_run: bool = False,
    skip_ansible: bool = False,
) -> str:
    """
    Full blue-green flow. Returns final status: 'success', 'rolled_back', or 'failed'.
    """

    if skip_ansible:
        audit.log_stage("ansible_configure", "skipped", {"reason": "skip_ansible=True"})
    else:
        try:
            if not dry_run:
                run_ansible_configure(ansible_dir, private_key)
            audit.log_stage("ansible_configure", "pass")
        except subprocess.CalledProcessError as e:
            audit.log_stage("ansible_configure", "fail", {"error": str(e)})
            audit.finalize("failed")
            raise DeploymentFailed("Ansible configuration of green instances failed") from e

    health_summary = wait_for_target_group_healthy(green_tg_arn)
    if not health_summary.all_healthy:
        audit.log_stage(
            "green_health_check", "fail",
            {"results": [r.__dict__ for r in health_summary.results]},
        )
        audit.finalize("failed")
        raise DeploymentFailed("Green instances failed health checks; traffic not shifted")
    audit.log_stage(
        "green_health_check", "pass",
        {"results": [r.__dict__ for r in health_summary.results]},
    )

    if not dry_run:
        shift_to_green(listener_arn, blue_tg_arn, green_tg_arn)
    audit.log_stage("traffic_shift_to_green", "pass", {"green_weight": 100, "blue_weight": 0})

    decision = monitor_bake_period(alb_arn_suffix)
    audit.log_stage(
        "bake_monitor", "fail" if decision.should_rollback else "pass",
        {"reason": decision.reason, "total_5xx_count": decision.total_5xx_count},
    )

    if decision.should_rollback:
        if not dry_run:
            shift_to_blue(listener_arn, blue_tg_arn, green_tg_arn)
        audit.log_stage("rollback_to_blue", "pass", {"reason": decision.reason})
        audit.finalize("rolled_back")
        return "rolled_back"

    audit.log_stage("bake_complete", "pass")
    audit.finalize("success")
    return "success"
