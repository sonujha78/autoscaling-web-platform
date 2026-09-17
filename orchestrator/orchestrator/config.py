"""Central configuration for the deployment orchestrator."""
import os

AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")
ENVIRONMENT = os.environ.get("DEPLOY_ENV", "dev")

# Terraform-managed resource identifiers (populated after terraform apply)
ASG_NAME = os.environ.get("ASG_NAME", "autoscaling-platform-dev-asg")
ALB_LISTENER_ARN = os.environ.get("ALB_LISTENER_ARN", "")
BLUE_TARGET_GROUP_ARN = os.environ.get("BLUE_TG_ARN", "")
GREEN_TARGET_GROUP_ARN = os.environ.get("GREEN_TG_ARN", "")
ALB_ARN = os.environ.get("ALB_ARN", "")

# Health check settings
HEALTH_CHECK_PATH = "/health"
HEALTH_CHECK_PORT = 8080
HEALTH_CHECK_TIMEOUT_SECONDS = 5
HEALTH_CHECK_RETRIES = 5
HEALTH_CHECK_RETRY_DELAY_SECONDS = 10

# Bake time / rollback settings
BAKE_TIME_SECONDS = int(os.environ.get("BAKE_TIME_SECONDS", "120"))
ROLLBACK_5XX_THRESHOLD = int(os.environ.get("ROLLBACK_5XX_THRESHOLD", "5"))
ROLLBACK_CHECK_INTERVAL_SECONDS = 15

# Audit log
AUDIT_LOG_DIR = os.environ.get("AUDIT_LOG_DIR", "./audit_logs")
AUDIT_LOG_S3_BUCKET = os.environ.get("AUDIT_LOG_S3_BUCKET", "")
