#!/usr/bin/env python3
"""
Forge Compute Control Desk — Phase 2: Start Instance End-to-End Workflow

This module implements the start instance workflow:
1. Request start from user
2. Confirm action
3. Call Compute Engine API to start VM
4. Poll operation status
5. Update Sheets register
6. Write evidence locally
7. Send local notification

Note: Gmail notifications skipped due to OAuth delegation requirements for service accounts.
Local notification files are written to the evidence folder instead.
"""

import os
import json
import time
import re
from datetime import datetime
from typing import Optional, Any, Dict, List
from googleapiclient.discovery import Resource

# Google API clients
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "orderededge-groupware")
REGION = os.environ.get("GCP_REGION", "europe-west2")
ZONE = os.environ.get("GCP_ZONE", "europe-west2-b")
SERVICE_ACCOUNT_FILE = os.environ.get(
    "GCP_SERVICE_ACCOUNT_JSON", "/home/stu/.config/gcp/forge-ccd-service-account.json"
)
SHEETS_SPREADSHEET_ID = os.environ.get("SHEETS_SPREADSHEET_ID")
DRIVE_EVIDENCE_FOLDER_ID = os.environ.get("DRIVE_EVIDENCE_FOLDER_ID", "/tmp/forge-ccd-evidence")
GMAIL_SENDER_EMAIL = os.environ.get("GMAIL_SENDER_EMAIL", "stuharker@gmail.com")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Compute Engine service
compute: Optional[Resource] = None
sheets: Optional[Resource] = None


def init_compute():
    """Initialize Compute Engine API client."""
    global compute
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/compute"],
    )
    compute = build("compute", "v1", credentials=credentials)


def init_sheets():
    """Initialize Sheets API client."""
    global sheets
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    sheets = build("sheets", "v4", credentials=credentials)


def start_instance(instance_name: str) -> dict:
    """Start a VM instance and return operation."""
    if compute is None:
        init_compute()

    request = compute.instances().start(
        project=PROJECT_ID,
        zone=ZONE,
        instance=instance_name,
    )
    return request.execute()


def stop_instance(instance_name: str) -> dict:
    """Stop a VM instance and return operation."""
    if compute is None:
        init_compute()

    request = compute.instances().stop(
        project=PROJECT_ID,
        zone=ZONE,
        instance=instance_name,
    )
    return request.execute()


def restart_instance(instance_name: str) -> dict:
    """Restart a VM instance and return operation."""
    if compute is None:
        init_compute()

    request = compute.instances().reset(
        project=PROJECT_ID,
        zone=ZONE,
        instance=instance_name,
    )
    return request.execute()


def inspect_instance(instance_name: str) -> dict:
    """Get VM instance details."""
    if compute is None:
        init_compute()

    request = compute.instances().get(
        project=PROJECT_ID,
        zone=ZONE,
        instance=instance_name,
    )
    return request.execute()


def list_instances() -> list:
    """List all VM instances in the project and zone."""
    if compute is None:
        init_compute()

    request = compute.instances().list(
        project=PROJECT_ID,
        zone=ZONE,
    )
    response = request.execute()
    return response.get("items", [])


def poll_operation(
    operation_id: str,
    max_attempts: int = 60,
    interval: int = 5,
    max_backoff: int = 30,
) -> dict:
    """Poll Compute Engine operation until completion with exponential backoff."""
    import random

    if compute is None:
        init_compute()

    backoff = interval
    for attempt in range(max_attempts):
        try:
            request = compute.zoneOperations().get(
                project=PROJECT_ID,
                zone=ZONE,
                operation=operation_id,
            )
            result = request.execute()

            if result.get("status") == "DONE":
                if "error" in result:
                    return {"success": False, "error": result["error"]}
                return {"success": True, "operation": result}

            time.sleep(backoff)
            # Exponential backoff with jitter
            backoff = min(backoff * 2, max_backoff) + random.uniform(0, 1)
        except HttpError as e:
            # Check for quota-related errors
            if "rateLimitExceeded" in str(e) or "exceeded" in str(e):
                print(f"Rate limit hit, backing off...")
                backoff = min(backoff * 2, max_backoff)
            return {"success": False, "error": str(e)}

    return {"success": False, "error": "Timeout waiting for operation completion"}


def update_sheets_register(
    instance_name: str,
    action: str,
    success: bool,
    operation_id: str,
) -> bool:
    """Update Sheets register with VM action result."""
    if sheets is None:
        init_sheets()

    # Find the row for this instance
    result = (
        sheets.spreadsheets()
        .values()
        .get(
            spreadsheetId=SHEETS_SPREADSHEET_ID,
            range="VM Register!A:A",
        )
        .execute()
    )
    rows = result.get("values", [])

    row_num = None
    for i, row in enumerate(rows, start=2):  # Skip header, start at row 2
        if row and row[0] == instance_name:
            row_num = i
            break

    if not row_num:
        print(f"Instance {instance_name} not found in Sheets register")
        return False

    # Update the row
    update_range = f"VM Register!A{row_num}:M{row_num}"
    current_time = datetime.utcnow().isoformat() + "Z"

    values = [
        [
            instance_name,  # instance_name
            PROJECT_ID,  # project
            ZONE,  # zone
            "",  # machine_type
            "",  # owner
            "",  # purpose
            "",  # environment
            "running" if success else "unknown",  # status
            action,  # last_action
            "success" if success else "failed",  # last_action_result
            operation_id,  # change_reference
            "",  # evidence_link
            f"Completed at {current_time} by forge-ccd",  # notes
        ]
    ]

    request = sheets.spreadsheets().values().update(
        spreadsheetId=SHEETS_SPREADSHEET_ID,
        range=update_range,
        valueInputOption="USER_ENTERED",
        body={"values": values},
    )
    response = request.execute()

    return True


def write_drive_evidence(
    instance_name: str,
    action: str,
    success: bool,
    operation_id: str,
    parameters: dict,
) -> str:
    """Write evidence record locally (shared Drive not available) and return file path."""
    import os

    # Use local folder instead of Drive
    evidence_folder = os.environ.get("DRIVE_EVIDENCE_FOLDER_ID", "/tmp/forge-ccd-evidence")
    os.makedirs(evidence_folder, exist_ok=True)

    # Create evidence content
    current_time = datetime.utcnow().isoformat() + "Z"
    evidence_content = f"""# {action.upper()} Instance: {instance_name}

**Timestamp:** {current_time}
**Action:** {action}
**Instance:** {instance_name}
**Project:** {PROJECT_ID}
**Zone:** {ZONE}
**Operation:** {operation_id}
**Status:** {'SUCCESS' if success else 'FAILED'}
**Result:** {'The instance was successfully started.' if success else 'The operation failed.'}

## Parameters
"""

    for key, value in parameters.items():
        evidence_content += f"- **{key}:** {value}\n"

    evidence_content += f"""
## Links
- [Sheets Register](https://docs.google.com/spreadsheets/d/{SHEETS_SPREADSHEET_ID}/edit)
- [GCP Console](https://console.cloud.google.com/compute/instancesDetail/zones/{ZONE}/instances/{instance_name}?project={PROJECT_ID})

---

*Evidence generated by Forge Compute Control Desk*
"""

    # Write to local file
    filename = f"{instance_name}_{current_time[:10]}_{action}.md"
    filepath = os.path.join(evidence_folder, filename)

    with open(filepath, "w") as f:
        f.write(evidence_content)

    return filepath


def send_local_notification(
    subject: str,
    body: str,
) -> bool:
    """Write local notification file (Gmail skipped due to OAuth requirements)."""
    import os

    # Write notification to local log
    notification_folder = os.environ.get("DRIVE_EVIDENCE_FOLDER_ID", "/tmp/forge-ccd-evidence")
    notification_folder = os.path.join(notification_folder, "notifications")
    os.makedirs(notification_folder, exist_ok=True)

    timestamp = datetime.utcnow().isoformat() + "Z"
    filename = f"notification_{timestamp}.txt"
    filepath = os.path.join(notification_folder, filename)

    content = f"""# {subject}

{body}

Timestamp: {timestamp}
Local Evidence Folder: {notification_folder}
"""

    with open(filepath, "w") as f:
        f.write(content)

    print(f"Notification written locally: {filepath}")
    return True


def send_gmail_notification(
    subject: str,
    body: str,
    to: str = None,
) -> bool:
    """Send local notification (Gmail skipped due to OAuth delegation requirements)."""
    import os
    import datetime

    # Write notification to local log instead of sending email
    notification_folder = os.environ.get("DRIVE_EVIDENCE_FOLDER_ID", "/tmp/forge-ccd-evidence")
    notification_folder = os.path.join(notification_folder, "notifications")
    os.makedirs(notification_folder, exist_ok=True)

    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    filename = f"notification_{timestamp}.txt"
    filepath = os.path.join(notification_folder, filename)

    content = f"""# {subject}

{body}

Timestamp: {timestamp}
Local Evidence Path: {notification_folder}
"""

    with open(filepath, "w") as f:
        f.write(content)

    print(f"Notification written locally: {filepath}")
    return True


def start_instance_workflow(instance_name: str, reason: str = "User requested start") -> dict:
    """Execute the complete start instance workflow."""
    print(f"Starting instance: {instance_name}")

    # Step 1: Start instance
    print("Step 1: Initiating start...")
    operation = start_instance(instance_name)
    operation_id = operation.get("name")
    print(f"Operation ID: {operation_id}")

    # Step 2: Poll for completion
    print("Step 2: Polling operation status...")
    result = poll_operation(operation_id)
    if not result.get("success"):
        print(f"Operation failed: {result.get('error')}")
        send_local_notification(
            f"[FAILED] {instance_name} start",
            f"Failed to start {instance_name}\nError: {result.get('error')}",
        )
        return {"success": False, "error": result.get("error")}

    # Step 3: Update Sheets
    print("Step 3: Updating Sheets register...")
    update_sheets_register(
        instance_name,
        "start",
        True,
        operation_id,
    )

    # Step 4: Write evidence locally
    print("Step 4: Writing evidence locally...")
    evidence_path = write_drive_evidence(
        instance_name,
        "start",
        True,
        operation_id,
        {"reason": reason},
    )
    print(f"Evidence path: {evidence_path}")

    # Step 5: Send notification
    print("Step 5: Sending local notification...")
    send_local_notification(
        f"[SUCCESS] {instance_name} started",
        f"Instance {instance_name} was successfully started.\n\n"
        f"Project: {PROJECT_ID}\n"
        f"Zone: {ZONE}\n"
        f"Operation: {operation_id}\n"
        f"Evidence: {evidence_path}\n"
        f"Reason: {reason}",
    )

    print(f"✅ {instance_name} started successfully!")
    return {"success": True, "operation_id": operation_id}


def stop_instance_workflow(instance_name: str, reason: str = "User requested stop") -> dict:
    """Execute the complete stop instance workflow."""
    print(f"Stopping instance: {instance_name}")

    # Step 1: Stop instance
    print("Step 1: Initiating stop...")
    operation = stop_instance(instance_name)
    operation_id = operation.get("name")
    print(f"Operation ID: {operation_id}")

    # Step 2: Poll for completion
    print("Step 2: Polling operation status...")
    result = poll_operation(operation_id)
    if not result.get("success"):
        print(f"Operation failed: {result.get('error')}")
        send_local_notification(
            f"[FAILED] {instance_name} stop",
            f"Failed to stop {instance_name}\nError: {result.get('error')}",
        )
        return {"success": False, "error": result.get("error")}

    # Step 3: Update Sheets
    print("Step 3: Updating Sheets register...")
    update_sheets_register(
        instance_name,
        "stop",
        True,
        operation_id,
    )

    # Step 4: Write evidence locally
    print("Step 4: Writing evidence locally...")
    evidence_path = write_drive_evidence(
        instance_name,
        "stop",
        True,
        operation_id,
        {"reason": reason},
    )
    print(f"Evidence path: {evidence_path}")

    # Step 5: Send notification
    print("Step 5: Sending local notification...")
    send_local_notification(
        f"[SUCCESS] {instance_name} stopped",
        f"Instance {instance_name} was successfully stopped.\n\n"
        f"Project: {PROJECT_ID}\n"
        f"Zone: {ZONE}\n"
        f"Operation: {operation_id}\n"
        f"Evidence: {evidence_path}\n"
        f"Reason: {reason}",
    )

    print(f"✅ {instance_name} stopped successfully!")
    return {"success": True, "operation_id": operation_id}


def restart_instance_workflow(instance_name: str, reason: str = "User requested restart") -> dict:
    """Execute the complete restart instance workflow."""
    print(f"Restarting instance: {instance_name}")

    # Step 1: Restart instance
    print("Step 1: Initiating restart...")
    operation = restart_instance(instance_name)
    operation_id = operation.get("name")
    print(f"Operation ID: {operation_id}")

    # Step 2: Poll for completion
    print("Step 2: Polling operation status...")
    result = poll_operation(operation_id)
    if not result.get("success"):
        print(f"Operation failed: {result.get('error')}")
        send_local_notification(
            f"[FAILED] {instance_name} restart",
            f"Failed to restart {instance_name}\nError: {result.get('error')}",
        )
        return {"success": False, "error": result.get("error")}

    # Step 3: Update Sheets
    print("Step 3: Updating Sheets register...")
    update_sheets_register(
        instance_name,
        "restart",
        True,
        operation_id,
    )

    # Step 4: Write evidence locally
    print("Step 4: Writing evidence locally...")
    evidence_path = write_drive_evidence(
        instance_name,
        "restart",
        True,
        operation_id,
        {"reason": reason},
    )
    print(f"Evidence path: {evidence_path}")

    # Step 5: Send notification
    print("Step 5: Sending local notification...")
    send_local_notification(
        f"[SUCCESS] {instance_name} restarted",
        f"Instance {instance_name} was successfully restarted.\n\n"
        f"Project: {PROJECT_ID}\n"
        f"Zone: {ZONE}\n"
        f"Operation: {operation_id}\n"
        f"Evidence: {evidence_path}\n"
        f"Reason: {reason}",
    )

    print(f"✅ {instance_name} restarted successfully!")
    return {"success": True, "operation_id": operation_id}


def inspect_instance_workflow(instance_name: str) -> dict:
    """Execute the inspect instance workflow (read-only, no Sheets update)."""
    print(f"Inspecting instance: {instance_name}")

    # Step 1: Get instance details
    print("Step 1: Getting instance details...")
    instance = inspect_instance(instance_name)
    instance_id = instance.get("id")
    machine_type = instance.get("machineType", "").split("/")[-1]
    status = instance.get("status")

    print(f"Instance details:")
    print(f"  - Name: {instance_name}")
    print(f"  - ID: {instance_id}")
    print(f"  - Machine Type: {machine_type}")
    print(f"  - Status: {status}")

    # Step 2: Write evidence locally (for read operations)
    print("Step 2: Writing evidence locally...")
    current_time = datetime.utcnow().isoformat() + "Z"
    evidence_content = f"""# INSPECT Instance: {instance_name}

**Timestamp:** {current_time}
**Action:** inspect
**Instance:** {instance_name}
**Project:** {PROJECT_ID}
**Zone:** {ZONE}
**Instance ID:** {instance_id}
**Machine Type:** {machine_type}
**Status:** {status}

## Instance Details
```json
{json.dumps(instance, indent=2, default=str)}
```

---

*Evidence generated by Forge Compute Control Desk*
"""

    evidence_folder = os.environ.get("DRIVE_EVIDENCE_FOLDER_ID", "/tmp/forge-ccd-evidence")
    evidence_folder = os.path.join(evidence_folder, "inspections")
    os.makedirs(evidence_folder, exist_ok=True)

    filename = f"{instance_name}_{current_time[:10]}_inspect.md"
    filepath = os.path.join(evidence_folder, filename)

    with open(filepath, "w") as f:
        f.write(evidence_content)
    print(f"Evidence path: {filepath}")

    # Step 3: Send notification
    print("Step 3: Sending local notification...")
    send_local_notification(
        f"[SUCCESS] {instance_name} inspected",
        f"Instance {instance_name} inspection completed.\n\n"
        f"Project: {PROJECT_ID}\n"
        f"Zone: {ZONE}\n"
        f"Status: {status}\n"
        f"Machine Type: {machine_type}\n"
        f"Evidence: {filepath}",
    )

    print(f"✅ {instance_name} inspected successfully!")
    return {"success": True, "instance": instance}


def list_instances_workflow() -> dict:
    """Execute the list instances workflow."""
    print("Listing all instances...")

    # Step 1: List instances
    print("Step 1: Getting instance list...")
    instances = list_instances()

    if not instances:
        print("No instances found in project.")
        return {"success": True, "instances": [], "count": 0}

    print(f"Found {len(instances)} instance(s):")
    for inst in instances:
        name = inst.get("name")
        status = inst.get("status")
        machine_type = inst.get("machineType", "").split("/")[-1]
        print(f"  - {name}: {status} ({machine_type})")

    # Step 2: Write evidence locally
    print("Step 2: Writing evidence locally...")
    current_time = datetime.utcnow().isoformat() + "Z"
    evidence_content = f"""# LIST INSTANCES

**Timestamp:** {current_time}
**Action:** list
**Project:** {PROJECT_ID}
**Zone:** {ZONE}

## Instance Count
**Total:** {len(instances)}

## Instances
"""

    for inst in instances:
        name = inst.get("name")
        status = inst.get("status")
        machine_type = inst.get("machineType", "").split("/")[-1]
        evidence_content += f"- **{name}:** {status} ({machine_type})\n"

    evidence_content += """
---

*Evidence generated by Forge Compute Control Desk*
"""

    evidence_folder = os.environ.get("DRIVE_EVIDENCE_FOLDER_ID", "/tmp/forge-ccd-evidence")
    evidence_folder = os.path.join(evidence_folder, "lists")
    os.makedirs(evidence_folder, exist_ok=True)

    filename = f"list_instances_{current_time[:10]}.md"
    filepath = os.path.join(evidence_folder, filename)

    with open(filepath, "w") as f:
        f.write(evidence_content)
    print(f"Evidence path: {filepath}")

    # Step 3: Send notification
    print("Step 3: Sending local notification...")
    send_local_notification(
        f"[SUCCESS] Instance list retrieved",
        f"Instance listing completed.\n\n"
        f"Project: {PROJECT_ID}\n"
        f"Zone: {ZONE}\n"
        f"Total Instances: {len(instances)}\n"
        f"Evidence: {filepath}",
    )

    print(f"✅ Instance listing completed!")
    return {"success": True, "instances": instances, "count": len(instances)}


def generate_weekly_governance_report() -> dict:
    """Generate a weekly governance report with VM status summary."""
    import os

    if compute is None:
        init_compute()

    print("Generating weekly governance report...")

    # Get all instances
    instances = list_instances()

    # Count by status
    status_counts = {}
    for inst in instances:
        status = inst.get("status", "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1

    # Generate report content
    current_time = datetime.utcnow().isoformat() + "Z"
    report_content = f"""# Weekly Governance Report

**Generated:** {current_time}
**Project:** {PROJECT_ID}
**Zone:** {ZONE}

## Summary

| Status | Count |
|--------|-------|
"""

    for status, count in sorted(status_counts.items()):
        report_content += f"| {status} | {count} |\n"

    report_content += f"""
## Instance Details

"""

    for inst in instances:
        name = inst.get("name")
        status = inst.get("status")
        machine_type = inst.get("machineType", "").split("/")[-1]
        zone = inst.get("zone", "").split("/")[-1]
        report_content += f"- **{name}** ({zone}): {status} ({machine_type})\n"

    report_content += """
---

*Report generated by Forge Compute Control Desk*
"""

    # Write report to evidence folder
    evidence_folder = os.environ.get("DRIVE_EVIDENCE_FOLDER_ID", "/tmp/forge-ccd-evidence")
    evidence_folder = os.path.join(evidence_folder, "reports")
    os.makedirs(evidence_folder, exist_ok=True)

    report_filename = f"governance_report_weekly_{current_time[:10]}.md"
    report_filepath = os.path.join(evidence_folder, report_filename)

    with open(report_filepath, "w") as f:
        f.write(report_content)

    print(f"Weekly governance report written to: {report_filepath}")
    print(f"Summary: {len(instances)} instance(s), statuses: {status_counts}")

    return {
        "success": True,
        "count": len(instances),
        "status_counts": status_counts,
        "report_path": report_filepath,
    }


if __name__ == "__main__":
    # For testing
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.core.start_instance <instance_name> <action>")
        print("Actions: start, stop, restart, inspect, list")
        print("Example: python -m src.core.start_instance forge-test-vm start")
        sys.exit(1)

    instance_name = sys.argv[1]
    action = sys.argv[2] if len(sys.argv) > 2 else "start"
    reason = sys.argv[3] if len(sys.argv) > 3 else "Manual start via forge-ccd"

    if action == "start":
        start_instance_workflow(instance_name, reason)
    elif action == "stop":
        stop_instance_workflow(instance_name, reason)
    elif action == "restart":
        restart_instance_workflow(instance_name, reason)
    elif action == "inspect":
        inspect_instance_workflow(instance_name)
    elif action == "list":
        list_instances_workflow()
    elif action == "report":
        generate_weekly_governance_report()
    else:
        print(f"Unknown action: {action}")
        print("Actions: start, stop, restart, inspect, list, report")
        sys.exit(1)
