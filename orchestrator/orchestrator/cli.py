"""CLI entrypoint for the deployment orchestrator."""
import click

from orchestrator import config


@click.group()
def cli():
    """Production deployment orchestrator: Terraform + Ansible + blue-green via boto3."""
    pass


@cli.command()
def validate():
    """Run pre-deployment validation (terraform plan check for destructive changes)."""
    click.echo("Validate command - to be implemented")


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
