# Auto-Scaling Web Platform

## Architecture

Production-grade auto-scaling web platform with blue-green deployment:

- **Terraform** — provisions AWS infrastructure (VPC, EC2 Auto Scaling Groups, RDS, Load Balancer) using modular remote state (S3 + DynamoDB)
- **Ansible** — configures application instances dynamically using the `aws_ec2` inventory plugin, deploys the Flask app to blue/green target groups
- **Python Orchestrator** — drives blue-green deployment, runs health checks, and triggers automatic rollback based on CloudWatch 5xx error rates
Terraform (infra) → Ansible (config + deploy) → Orchestrator (health check + rollback)

## How to Run Locally

1. Clone the repository
2. Configure AWS credentials: `aws configure`
3. Provision infrastructure: `cd terraform && terraform init && terraform apply`
4. Run the orchestrator: `python orchestrator/cli.py deploy --green-limit app_dev_green`

## How to Deploy

Deployment is orchestrated through the Python CLI, which:

1. Runs Ansible against the green environment
2. Performs health checks against the new target group
3. Shifts traffic via the load balancer
4. Automatically rolls back on sustained 5xx errors from CloudWatch
python orchestrator/cli.py deploy --green-limit app_dev_green
