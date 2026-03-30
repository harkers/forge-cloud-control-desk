#!/usr/bin/env python3
"""
Forge Compute Control Desk — Main Entry Point

Usage:
    python -m main start <instance_name> [reason]
    python -m main validate
"""

import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.core.start_instance import start_instance_workflow


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Forge Compute Control Desk")
        print("Usage: python -m main <command> [args]")
        print("")
        print("Commands:")
        print("  start <instance_name> [reason] - Start a VM instance")
        print("  validate                       - Validate environment setup")
        sys.exit(1)

    command = sys.argv[1]

    if command == "start":
        if len(sys.argv) < 3:
            print("Error: instance name required")
            print("Usage: python -m main start <instance_name> [reason]")
            sys.exit(1)

        instance_name = sys.argv[2]
        reason = sys.argv[3] if len(sys.argv) > 3 else "Started via forge-ccd"
        start_instance_workflow(instance_name, reason)

    elif command == "validate":
        print("Validating environment...")
        required_vars = [
            "GCP_PROJECT_ID",
            "GCP_REGION",
            "GCP_ZONE",
            "GCP_SERVICE_ACCOUNT_JSON",
            "SHEETS_SPREADSHEET_ID",
            "DRIVE_EVIDENCE_FOLDER_ID",
            "GMAIL_SENDER_EMAIL",
            "GMAIL_CLIENT_SECRETS",
        ]

        all_ok = True
        for var in required_vars:
            value = os.environ.get(var)
            if not value:
                print(f"❌ {var} not set")
                all_ok = False
            else:
                print(f"✅ {var} set")

        if all_ok:
            print("✅ Environment validated successfully!")
        else:
            print("❌ Environment validation failed")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        print("Use 'python -m main' to see available commands")
        sys.exit(1)


if __name__ == "__main__":
    main()
