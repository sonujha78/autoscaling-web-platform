# Auto-Scaling Web Platform (Terraform + Ansible + Python)

Production-style 3-tier AWS platform, free-tier-safe.

- **Terraform** — VPC, public subnets, ALB, ASG, RDS (Single-AZ), S3+DynamoDB remote state
- **Ansible** — dynamic inventory (aws_ec2), app config, Vault-encrypted secrets
- **Python orchestrator** — blue-green deployment, pre-deploy validation, health checks, auto-rollback via CloudWatch

Status: 🚧 in progress

## Structure
- `terraform/bootstrap/` — one-time S3 backend + DynamoDB lock table setup
- `terraform/modules/` — networking, compute, database, loadbalancer
- `terraform/environments/` — dev, prod (separate tfvars)
- `ansible/` — roles, playbooks, dynamic inventory
- `orchestrator/` — Python CLI (click + boto3 + subprocess)
- `docs/` — architecture diagram, cost trade-off write-up, deployment logs

## Cost note
No NAT Gateway, RDS Single-AZ — free-tier-safe by design (see docs/cost-tradeoffs.md).
