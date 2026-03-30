#!/usr/bin/env python3
"""
Forge Compute Control Desk — Phase 2: Start Instance End-to-End Workflow

This module implements the start instance workflow:
1. Request start from user
2. Confirm action
3. Call Compute Engine API to start VM
4. Poll operation status
5. Update Sheets register
6. Write evidence to Drive
7. Send Gmail notification
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
DRIVE_EVIDENCE_FOLDER_ID = os.environ.get("DRIVE_EVIDENCE_FOLDER_ID")
GMAIL_SENDER_EMAIL = os.environ.get("GMAIL_SENDER_EMAIL", "stuharker@gmail.com")
GMAIL_CLIENT_SECRETS = os.environ.get(
    "GMAIL_CLIENT_SECRETS", "/home/stu/.config/gmail/client_secrets.json"
)

# Compute Engine service
compute: Optional[Resource] = None
sheets: Optional[Resource] = None
drive: Optional[Resource] = None
gmail: Optional[Resource] = None


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


def init_drive():
    """Initialize Drive API client."""
    global drive
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/drive.file"],
    )
    drive = build("drive", "v3", credentials=credentials)


def init_gmail():
    """Initialize Gmail API client."""
    global gmail
    # For now, use service account for Gmail
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/gmail.modify"],
    )
    gmail = build("gmail", "v1", credentials=credentials)


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


def poll_operation(operation_id: str, max_attempts: int = 60, interval: int = 5) -> dict:
    """Poll Compute Engine operation until completion."""
    if compute is None:
        init_compute()

    for attempt in range(max_attempts):
        try:
            request = compute.operations().get(
                project=PROJECT_ID,
                zone=ZONE,
                operation=operation_id,
            )
            result = request.execute()

            if result.get("status") == "DONE":
                if "error" in result:
                    return {"success": False, "error": result["error"]}
                return {"success": True, "operation": result}

            time.sleep(interval)
        except HttpError as e:
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
    """Write evidence record to Drive and return file URL."""
    if drive is None:
        init_drive()

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

    # Create file in Drive
    file_metadata = {
        "name": f"{instance_name}_{current_time[:10]}_{action}.md",
        "parents": [DRIVE_EVIDENCE_FOLDER_ID],
        "mimeType": "text/markdown",
    }

    media = {"data": evidence_content.encode("utf-8"), "mimeType": "text/markdown"}

    file = (
        drive.files()
        .create(body=file_metadata, media_body=media, fields="id, webContentLink")
        .execute()
    )

    return file.get("webContentLink", f"https://drive.google.com/file/d/{file.get('id')}/view")


def send_gmail_notification(
    subject: str,
    body: str,
    to: str = None,
) -> bool:
    """Send Gmail notification."""
    if gmail is None:
        init_gmail()

    recipient = to or GMAIL_SENDER_EMAIL

    # Create email message
    message = f"From: {GMAIL_SENDER_EMAIL}\nTo: {recipient}\nSubject: {subject}\n\n{body}"

    # Encode for MIME
    import base64
    encoded_message = base64.urlsafe_b64encode(message.encode("utf-8")).decode("utf-8")

    create_message = {"raw": encoded_message}

    try:
        message = (
            gmail.users().messages().send(userId="me", body=create_message).execute()
        )
        print(f"Message sent: {message['id']}")
        return True
    except HttpError as error:
        print(f"An error occurred: {error}")
        return False


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
        send_gmail_notification(
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

    # Step 4: Write Drive evidence
    print("Step 4: Writing evidence to Drive...")
    evidence_link = write_drive_evidence(
        instance_name,
        "start",
        True,
        operation_id,
        {"reason": reason},
    )
    print(f"Evidence link: {evidence_link}")

    # Step 5: Send notification
    print("Step 5: Sending notification...")
    send_gmail_notification(
        f"[SUCCESS] {instance_name} started",
        f"Instance {instance_name} was successfully started.\n\n"
        f"Project: {PROJECT_ID}\n"
        f"Zone: {ZONE}\n"
        f"Operation: {operation_id}\n"
        f"Evidence: {evidence_link}\n"
        f"Reason: {reason}",
    )

    print(f"✅ {instance_name} started successfully!")
    return {"success": True, "operation_id": operation_id}


if __name__ == "__main__":
    # For testing
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.core.start_instance <instance_name>")
        sys.exit(1)

    instance_name = sys.argv[1]
    reason = sys.argv[2] if len(sys.argv) > 2 else "Manual start via forge-ccd"

    start_instance_workflow(instance_name, reason)
