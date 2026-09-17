"""Unit tests for destructive-change detection. No AWS/terraform calls - pure logic only."""
from orchestrator.terraform_check import check_plan_for_destructive_changes


def make_resource_change(address, rtype, actions):
    return {"address": address, "type": rtype, "change": {"actions": actions}}


def test_no_changes_is_not_destructive():
    plan_json = {"resource_changes": []}
    result = check_plan_for_destructive_changes(plan_json)
    assert result.is_destructive is False
    assert result.destructive_resources == []


def test_pure_create_is_not_destructive():
    plan_json = {"resource_changes": [
        make_resource_change("aws_instance.app", "aws_instance", ["create"]),
    ]}
    result = check_plan_for_destructive_changes(plan_json)
    assert result.is_destructive is False
    assert result.resources_to_add == 1


def test_pure_update_is_not_destructive():
    plan_json = {"resource_changes": [
        make_resource_change("aws_launch_template.app", "aws_launch_template", ["update"]),
    ]}
    result = check_plan_for_destructive_changes(plan_json)
    assert result.is_destructive is False
    assert result.resources_to_change == 1


def test_pure_delete_is_destructive():
    plan_json = {"resource_changes": [
        make_resource_change("aws_db_instance.main", "aws_db_instance", ["delete"]),
    ]}
    result = check_plan_for_destructive_changes(plan_json)
    assert result.is_destructive is True
    assert result.resources_to_destroy == 1
    assert result.destructive_resources[0]["address"] == "aws_db_instance.main"


def test_replace_create_then_delete_is_destructive():
    """This is the critical RDS-replacement case from the task spec."""
    plan_json = {"resource_changes": [
        make_resource_change("aws_db_instance.main", "aws_db_instance", ["create", "delete"]),
    ]}
    result = check_plan_for_destructive_changes(plan_json)
    assert result.is_destructive is True
    assert result.destructive_resources[0]["type"] == "aws_db_instance"


def test_replace_delete_then_create_is_destructive():
    plan_json = {"resource_changes": [
        make_resource_change("aws_db_instance.main", "aws_db_instance", ["delete", "create"]),
    ]}
    result = check_plan_for_destructive_changes(plan_json)
    assert result.is_destructive is True


def test_mixed_safe_and_destructive_changes():
    plan_json = {"resource_changes": [
        make_resource_change("aws_instance.app", "aws_instance", ["create"]),
        make_resource_change("aws_security_group.app", "aws_security_group", ["update"]),
        make_resource_change("aws_db_instance.main", "aws_db_instance", ["delete", "create"]),
    ]}
    result = check_plan_for_destructive_changes(plan_json)
    assert result.is_destructive is True
    assert result.resources_to_add == 1
    assert result.resources_to_change == 1
    assert len(result.destructive_resources) == 1
