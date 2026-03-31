"""
Forge Compute Control Desk — Workflow Test Runner

Test VM lifecycle workflows. Supports individual actions and a full
create-validate-delete round-trip that leaves no chargeable resource behind.

Usage:
    python tests/test_start_instance.py <action> <instance_name> [reason]

Actions:
    start / stop / restart / inspect / list   — existing lifecycle
    create / delete                           — provision / teardown
    roundtrip                                 — create → inspect → delete (cost-safe)
"""

import sys
import os
import time

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.core.start_instance import (
    create_instance_workflow,
    delete_instance_workflow,
    start_instance_workflow,
    stop_instance_workflow,
    restart_instance_workflow,
    inspect_instance_workflow,
    list_instances_workflow,
)


def run_roundtrip(instance_name: str, reason: str) -> bool:
    """Create a VM, inspect it, then delete it immediately. Returns True on full success."""
    print("=" * 60)
    print(f"ROUND-TRIP TEST: {instance_name}")
    print("=" * 60)

    # Phase 1 — Create
    print("\n--- Phase 1: CREATE ---")
    create_result = create_instance_workflow(instance_name, reason)
    if not create_result.get("success"):
        print(f"CREATE FAILED: {create_result.get('error')}")
        print("No cleanup needed — VM was not created.")
        return False

    # Phase 2 — Inspect (verify it exists)
    print("\n--- Phase 2: INSPECT ---")
    inspect_result = inspect_instance_workflow(instance_name)
    if not inspect_result.get("success"):
        print(f"INSPECT FAILED: {inspect_result.get('error')}")
        print("Proceeding to delete anyway...")

    # Phase 3 — Delete (always attempted if create succeeded)
    print("\n--- Phase 3: DELETE ---")
    delete_result = delete_instance_workflow(instance_name, "Roundtrip test cleanup")
    if not delete_result.get("success"):
        print(f"DELETE FAILED: {delete_result.get('error')}")
        print(f"WARNING: {instance_name} may still be running — manual cleanup required!")
        return False

    print("\n" + "=" * 60)
    print(f"ROUND-TRIP COMPLETE: {instance_name} created and deleted successfully")
    print("=" * 60)
    return True


def main():
    """Run a workflow test."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1]
    instance_name = sys.argv[2] if len(sys.argv) > 2 else "forge-test-vm"
    reason = sys.argv[3] if len(sys.argv) > 3 else "Test workflow execution"

    print(f"Action: {action}")
    print(f"Instance: {instance_name}")
    print(f"Reason: {reason}")
    print("-" * 50)

    if action == "roundtrip":
        ok = run_roundtrip(instance_name, reason)
        sys.exit(0 if ok else 1)

    dispatch = {
        "create": lambda: create_instance_workflow(instance_name, reason),
        "delete": lambda: delete_instance_workflow(instance_name, reason),
        "start": lambda: start_instance_workflow(instance_name, reason),
        "stop": lambda: stop_instance_workflow(instance_name, reason),
        "restart": lambda: restart_instance_workflow(instance_name, reason),
        "inspect": lambda: inspect_instance_workflow(instance_name),
        "list": lambda: list_instances_workflow(),
    }

    if action not in dispatch:
        print(f"Unknown action: {action}")
        print("Actions: create, delete, start, stop, restart, inspect, list, roundtrip")
        sys.exit(1)

    result = dispatch[action]()

    if result.get("success"):
        print(f"\nSUCCESS: {action} {instance_name}")
        if "operation_id" in result:
            print(f"Operation ID: {result['operation_id']}")
    else:
        print(f"\nFAILED: {action} {instance_name}")
        print(f"Error: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
