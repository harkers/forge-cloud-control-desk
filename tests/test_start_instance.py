"""
Forge Compute Control Desk — Phase 2 Test Runner

Test the start instance workflow with a VM that's already been created.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from src.core.start_instance import start_instance_workflow


def main():
    """Run the start instance workflow."""
    if len(sys.argv) < 2:
        print("Usage: python test_start_instance.py <instance_name> [reason]")
        print("Example: python test_start_instance.py my-vm User testing workflow")
        sys.exit(1)

    instance_name = sys.argv[1]
    reason = sys.argv[2] if len(sys.argv) > 2 else "Test workflow execution"

    print(f"Testing start instance workflow for: {instance_name}")
    print(f"Reason: {reason}")
    print("-" * 50)

    result = start_instance_workflow(instance_name, reason)

    if result.get("success"):
        print(f"\n✅ SUCCESS: {instance_name} started")
        print(f"Operation ID: {result.get('operation_id')}")
    else:
        print(f"\n❌ FAILED: {instance_name}")
        print(f"Error: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
