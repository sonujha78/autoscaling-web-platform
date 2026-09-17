"""Structured JSON audit logging for every orchestrator run."""
import json
import os
import getpass
from datetime import datetime

import boto3

from orchestrator import config


class AuditLog:
    """Accumulates structured events for one deployment run and writes them out."""

    def __init__(self, action: str):
        self.action = action
        self.run_id = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        self.started_by = getpass.getuser()
        self.start_time = datetime.utcnow().isoformat() + "Z"
        self.end_time = None
        self.stages = []
        self.final_status = "in_progress"

    def log_stage(self, name: str, status: str, details: dict = None):
        """Record one stage of the deployment (e.g. 'validate', 'health_check', 'traffic_shift')."""
        self.stages.append({
            "stage": name,
            "status": status,  # "pass" | "fail" | "skipped"
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "details": details or {},
        })

    def finalize(self, status: str):
        """status: 'success' | 'failed' | 'rolled_back'"""
        self.final_status = status
        self.end_time = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "action": self.action,
            "started_by": self.started_by,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "final_status": self.final_status,
            "stages": self.stages,
        }

    def write_local(self, directory: str = None) -> str:
        directory = directory or config.AUDIT_LOG_DIR
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, f"deploy-{self.run_id}.json")
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        return path

    def write_s3(self, bucket: str = None, region: str = None) -> str:
        bucket = bucket or config.AUDIT_LOG_S3_BUCKET
        if not bucket:
            return None
        region = region or config.AWS_REGION
        s3 = boto3.client("s3", region_name=region)
        key = f"audit_logs/deploy-{self.run_id}.json"
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(self.to_dict(), indent=2).encode("utf-8"),
            ContentType="application/json",
        )
        return f"s3://{bucket}/{key}"
