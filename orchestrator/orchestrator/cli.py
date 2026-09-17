"""CLI entrypoint for the deployment orchestrator."""
import sys

import click

from orchestrator import config
from orchestrator.terraform_check import (
    run_terraform_plan,
    get_plan_json,
    check_plan_for_destructive_changes,
)


@click.group()
def cli():
    """Production deployment orchestrator: Terraform + Ansible + blue-green via boto3."""
    pass


@cli.command()
@click.option(
    "--terraform-dir",
    default="../terraform/environments/dev",
    help="Path to terraform environment directory",
)
@click.option(
    "--var-file",
    default="dev.tfvars",
    help="Terraform var file name (relative to terraform-dir)",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Proceed even if the plan shows destructive changes (manual override).",
)
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
            click.secho(
                "\nRefusing to proceed automatically. Review the plan manually, "
                "or re-run with --force to override.",
                fg="yellow",
            )
            sys.exit(1)
        else:
            click.secho("\n--force passed: proceeding despite destructive changes.", fg="yellow")
    else:
        click.secho("\nNo destructive changes detected. Safe to proceed.", fg="green")


@cli.command()
def deploy():
    """Run full blue-green deployment: provision green, configure, health-check, shift traffic."""
    click.echo("Deploy command - to be implemented")


@cli.command()
def rollback():
    """Manually trigger rollback to blue."""
    click.echo("Rollback command - to be implemented")


if __name__ == "__main__":
    cli()
