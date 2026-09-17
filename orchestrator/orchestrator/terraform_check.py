"""Pre-deployment validation: detect destructive changes in a terraform plan."""
import json
import subprocess
from dataclasses import dataclass, field


@dataclass
class PlanCheckResult:
    is_destructive: bool
    destructive_resources: list = field(default_factory=list)
    resources_to_add: int = 0
    resources_to_change: int = 0
    resources_to_destroy: int = 0
    raw_actions: dict = field(default_factory=dict)


# Terraform action sets that indicate a resource will be destroyed/replaced
DESTRUCTIVE_ACTIONS = {
    frozenset(["delete"]),
    frozenset(["delete", "create"]),
    frozenset(["create", "delete"]),
}


def run_terraform_plan(working_dir: str, var_file: str, plan_out: str = "plan.tfplan") -> str:
    """Run `terraform plan -out=<plan_out>` in working_dir. Returns path to the plan file."""
    subprocess.run(
        ["terraform", "init", "-input=false"],
        cwd=working_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["terraform", "plan", f"-var-file={var_file}", f"-out={plan_out}", "-input=false"],
        cwd=working_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    return plan_out


def get_plan_json(working_dir: str, plan_file: str) -> dict:
    """Run `terraform show -json <plan_file>` and parse the result."""
    result = subprocess.run(
        ["terraform", "show", "-json", plan_file],
        cwd=working_dir,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def check_plan_for_destructive_changes(plan_json: dict) -> PlanCheckResult:
    """
    Inspect a parsed terraform plan (from `terraform show -json`) for destructive
    changes (deletes or replace-via-delete-create), most importantly on stateful
    resources like RDS.
    """
    resource_changes = plan_json.get("resource_changes", [])

    destructive_resources = []
    to_add = 0
    to_change = 0
    to_destroy = 0

    for rc in resource_changes:
        actions = rc.get("change", {}).get("actions", [])
        action_set = frozenset(actions)
        address = rc.get("address", "unknown")
        rtype = rc.get("type", "unknown")

        if "create" in actions and "delete" not in actions:
            to_add += 1
        if actions == ["update"]:
            to_change += 1
        if "delete" in actions and "create" not in actions:
            to_destroy += 1

        if action_set in DESTRUCTIVE_ACTIONS:
            destructive_resources.append({"address": address, "type": rtype, "actions": actions})

    return PlanCheckResult(
        is_destructive=len(destructive_resources) > 0,
        destructive_resources=destructive_resources,
        resources_to_add=to_add,
        resources_to_change=to_change,
        resources_to_destroy=to_destroy,
        raw_actions={"total_resource_changes": len(resource_changes)},
    )
