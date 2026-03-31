#!/usr/bin/env python3
"""
Forge Compute Control Desk — Main Entry Point

Usage:
    python -m main <command> <instance_name> [reason]
    python -m main validate
"""

import sys
import os

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
    generate_weekly_governance_report,
)

COMMANDS = {
    "create": ("create_instance_workflow", True),
    "delete": ("delete_instance_workflow", True),
    "start": ("start_instance_workflow", True),
    "stop": ("stop_instance_workflow", True),
    "restart": ("restart_instance_workflow", True),
    "inspect": ("inspect_instance_workflow", True),
    "list": ("list_instances_workflow", False),
    "report": ("generate_weekly_governance_report", False),
}


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Forge Compute Control Desk")
        print("Usage: python -m main <command> [instance_name] [reason]")
        print("")
        print("Commands:")
        for cmd, (_, needs_instance) in COMMANDS.items():
            suffix = " <instance_name> [reason]" if needs_instance else ""
            print(f"  {cmd}{suffix}")
        print("  validate")
        sys.exit(1)

    command = sys.argv[1]

    if command == "validate":
        print("Validating environment...")
        required_vars = [
            "GCP_PROJECT_ID",
            "GCP_REGION",
            "GCP_ZONE",
            "GCP_SERVICE_ACCOUNT_JSON",
            "SHEETS_SPREADSHEET_ID",
            "DRIVE_EVIDENCE_FOLDER_ID",
        ]

        all_ok = True
        for var in required_vars:
            value = os.environ.get(var)
            if not value:
                print(f"  {var} not set")
                all_ok = False
            else:
                print(f"  {var} set")

        if all_ok:
            print("Environment validated successfully!")
        else:
            print("Environment validation failed")
            sys.exit(1)
        return

    if command not in COMMANDS:
        print(f"Unknown command: {command}")
        print("Use 'python -m main' to see available commands")
        sys.exit(1)

    _, needs_instance = COMMANDS[command]

    if needs_instance:
        if len(sys.argv) < 3:
            print(f"Error: instance name required for '{command}'")
            sys.exit(1)
        instance_name = sys.argv[2]
        reason = sys.argv[3] if len(sys.argv) > 3 else f"{command.title()} via forge-ccd"

    if command == "create":
        create_instance_workflow(instance_name, reason)
    elif command == "delete":
        delete_instance_workflow(instance_name, reason)
    elif command == "start":
        start_instance_workflow(instance_name, reason)
    elif command == "stop":
        stop_instance_workflow(instance_name, reason)
    elif command == "restart":
        restart_instance_workflow(instance_name, reason)
    elif command == "inspect":
        inspect_instance_workflow(instance_name)
    elif command == "list":
        list_instances_workflow()
    elif command == "report":
        generate_weekly_governance_report()


if __name__ == "__main__":
    main()
