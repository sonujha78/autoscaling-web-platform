"""CLI entrypoint for the deployment orchestrator."""
import sys

import click

from orchestrator import config
from orchestrator.terraform_check import (
    run_terraform_plan,
    get_plan_json,
    check_plan_for_destructive_changes,
)
from orchestrator.audit_log import AuditLog
from orchestrator.deploy import run_blue_green_deploy, DeploymentFailed
from orchestrator.traffic_shift import shift_to_blue


@click.group()
def cli():
    """Production deployment orchestrator: Terraform + Ansible + blue-green via boto3."""
    pass


@cli.command()
@click.option("--terraform-dir", default="../terraform/environments/dev")
@click.option("--var-file", default="dev.tfvars")
@click.option("--force", is_flag=True, default=False)
def validate(terraform_dir, var_file, force):
    """Run terraform plan and check for destructive changes before allowing deploy."""
    click.echo(f"Running terraform plan in {terraform_dir} ...")

    try:
        plan_file = run_terraform_plan(terraform_dir, var_file)
        plan_json = get_plan_json(terraform_dir, plan_file)
    except Exception as e:
        click.secho(f"Terraform plan failed: {e}", fg="red")
        sys.exit(1)

    result = check_plan_for_destructive_changes(plan_json)

    click.echo(f"Resources to add: {result.resources_to_add}")
    click.echo(f"Resources to change: {result.resources_to_change}")
    click.echo(f"Resources to destroy: {result.resources_to_destroy}")

    if result.is_destructive:
        click.secho("\n⚠ DESTRUCTIVE CHANGES DETECTED:", fg="red", bold=True)
        for r in result.destructive_resources:
            click.secho(f"  - {r['address']} ({r['type']}): {r['actions']}", fg="red")
        if not force:
            click.secho("\nRefusing to proceed automatically. Use --force to override.", fg="yellow")
            sys.exit(1)
        click.secho("\n--force passed: proceeding despite destructive changes.", fg="yellow")
    else:
        click.secho("\nNo destructive changes detected. Safe to proceed.", fg="green")


@cli.command()
@click.option("--listener-arn", default=lambda: config.ALB_LISTENER_ARN)
@click.option("--blue-tg-arn", default=lambda: config.BLUE_TARGET_GROUP_ARN)
@click.option("--green-tg-arn", default=lambda: config.GREEN_TARGET_GROUP_ARN)
@click.option("--alb-arn-suffix", required=True, help="ALB ARN suffix for CloudWatch dimension, e.g. app/name/id")
@click.option("--ansible-dir", default="../ansible")
@click.option("--private-key", required=True, help="Path to SSH private key for Ansible")
@click.option("--dry-run", is_flag=True, default=False, help="Run through stages without making real AWS/SSH calls")
@click.option("--skip-ansible", is_flag=True, default=False, help="Skip the ansible configure step (green already configured)")
def deploy(listener_arn, blue_tg_arn, green_tg_arn, alb_arn_suffix, ansible_dir, private_key, dry_run, skip_ansible):
    """Run full blue-green deployment: configure green, health-check, shift traffic, monitor, auto-rollback."""
    if not all([listener_arn, blue_tg_arn, green_tg_arn]):
        click.secho("Missing listener/target-group ARNs. Pass --listener-arn/--blue-tg-arn/--green-tg-arn "
                     "or set ALB_LISTENER_ARN/BLUE_TG_ARN/GREEN_TG_ARN env vars.", fg="red")
        sys.exit(1)

    audit = AuditLog(action="deploy")
    click.echo(f"Starting deployment run {audit.run_id} ...")

    try:
        status = run_blue_green_deploy(
            listener_arn=listener_arn,
            blue_tg_arn=blue_tg_arn,
            green_tg_arn=green_tg_arn,
            ansible_dir=ansible_dir,
            private_key=private_key,
            alb_arn_suffix=alb_arn_suffix,
            audit=audit,
            dry_run=dry_run,
            skip_ansible=skip_ansible,
        )
    except DeploymentFailed as e:
        click.secho(f"Deployment failed: {e}", fg="red")
        status = "failed"
    finally:
        log_path = audit.write_local()
        click.echo(f"Audit log written to {log_path}")

    if status == "success":
        click.secho("\nDeployment succeeded. Traffic fully on green.", fg="green", bold=True)
    elif status == "rolled_back":
        click.secho("\nDeployment rolled back to blue due to elevated error rate.", fg="yellow", bold=True)
        sys.exit(1)
    else:
        click.secho("\nDeployment failed.", fg="red", bold=True)
        sys.exit(1)


@cli.command()
@click.option("--listener-arn", default=lambda: config.ALB_LISTENER_ARN)
@click.option("--blue-tg-arn", default=lambda: config.BLUE_TARGET_GROUP_ARN)
@click.option("--green-tg-arn", default=lambda: config.GREEN_TARGET_GROUP_ARN)
def rollback(listener_arn, blue_tg_arn, green_tg_arn):
    """Manually shift traffic back to blue."""
    if not all([listener_arn, blue_tg_arn, green_tg_arn]):
        click.secho("Missing listener/target-group ARNs.", fg="red")
        sys.exit(1)

    click.echo("Shifting traffic back to blue ...")
    shift_to_blue(listener_arn, blue_tg_arn, green_tg_arn)
    click.secho("Traffic shifted to blue.", fg="green")


if __name__ == "__main__":
    cli()
