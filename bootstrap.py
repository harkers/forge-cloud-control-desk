#!/usr/bin/env python3
"""
Forge Compute Control Desk — Project Bootstrap Script

This script sets up the initial project structure and validates environment readiness.
It can be run multiple times safely (idempotent).
"""

import os
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
WORKSPACE_ROOT = PROJECT_ROOT.parent

# Google Cloud baseline (from COMPUTE-BASELINE-EMAIL.md)
GC_BASELINE = {
    "region": "europe-west2",
    "zone": "europe-west2-b",
    "machine_type": "e2-medium",
    "disk_type": "pd-balanced",
    "disk_size_gb": 20,
    "os_image_project": "debian-cloud",
    "os_image_family": "debian-12-bookworm",
}

# Data model — Sheets register schema
SHEETS_REGISTER_SCHEMA = {
    "tab_name": "VM Register",
    "columns": [
        {"name": "instance_name", "type": "text", "required": True, "description": "VM instance name"},
        {"name": "project", "type": "text", "required": True, "description": "GCP project ID"},
        {"name": "zone", "type": "text", "required": True, "description": "Compute zone"},
        {"name": "machine_type", "type": "text", "required": True, "description": "e.g., e2-medium"},
        {"name": "owner", "type": "text", "required": False, "description": "Operator/owner"},
        {"name": "purpose", "type": "text", "required": False, "description": "Business purpose"},
        {"name": "environment", "type": "text", "required": True, "description": "dev/prod/staging"},
        {"name": "status", "type": "text", "required": False, "description": "running/stopped/failed/pending"},
        {"name": "last_action", "type": "text", "required": False, "description": "create/start/stop/restart"},
        {"name": "last_action_result", "type": "text", "required": False, "description": "success/pending/failed"},
        {"name": "change_reference", "type": "text", "required": False, "description": "Operation ID or timestamp"},
        {"name": "evidence_link", "type": "text", "required": False, "description": "Drive evidence folder URL"},
        {"name": "notes", "type": "text", "required": False, "description": "Free-text notes"},
    ],
}

# Evidence structure (Drive)
EVIDENCE_STRUCTURE = {
    "base_folder": "vm-evidence",
    "naming_convention": "YYYY-MM",
    "file_naming_pattern": "{instance_name}/{YYYYMMDD-HHMMSS}-{action}.md",
    "required_fields": [
        "timestamp",
        "requested_action",
        "target_vm.instance_name",
        "target_vm.project",
        "target_vm.zone",
        "parameters.reason",
        "api_response_summary",
        "final_operation_result",
        "register_row_link",
        "operator_identity",
        "notes",
    ],
}

# Action catalogue
ACTION_CATALOGUE = {
    "read": {
        "name": "inspect",
        "risk_level": "low",
        "needs_confirmation": False,
        "needs_drive_evidence": False,
    },
    "read": {
        "name": "list_instances",
        "risk_level": "low",
        "needs_confirmation": False,
        "needs_drive_evidence": False,
    },
    "write": {
        "name": "start",
        "risk_level": "medium",
        "needs_confirmation": "onscreen",
        "needs_drive_evidence": True,
    },
    "write": {
        "name": "stop",
        "risk_level": "medium",
        "needs_confirmation": "onscreen",
        "needs_drive_evidence": True,
    },
    "write": {
        "name": "restart",
        "risk_level": "medium",
        "needs_confirmation": "onscreen",
        "needs_drive_evidence": True,
    },
    "write": {
        "name": "create",
        "risk_level": "high",
        "needs_confirmation": "onscreen+gmail",
        "needs_drive_evidence": True,
        "needs_register_entry": True,
    },
    "write": {
        "name": "resize",
        "risk_level": "high",
        "needs_confirmation": "onscreen+gmail",
        "needs_drive_evidence": True,
    },
}

# Confirmation thresholds
CONFIRMATION_MODEL = {
    "low_risk": {
        "description": "Read-only actions, non-disruptive",
        "confirmation_level": "none",
        "actions": ["inspect", "list_instances"],
    },
    "medium_risk": {
        "description": "State changes with potential brief interruption",
        "confirmation_level": "onscreen",
        "actions": ["start", "stop", "restart"],
    },
    "high_risk": {
        "description": "Destructive or costly operations",
        "confirmation_level": "onscreen+gmail_receipt",
        "actions": ["create", "resize"],
    },
}

# Gmail notification classes
GMAIL_NOTIFICATIONS = {
    "low_risk": {
        "description": "Read-only action completed",
        "send_email": False,
        "send_digest": True,
    },
    "medium_risk": {
        "description": "State change completed",
        "send_email": True,
        "send_digest": True,
        "email_template": "success_failure_notification",
    },
    "high_risk": {
        "description": "Destructive action with confirmation",
        "send_email": True,
        "send_digest": True,
        "email_template": "success_failure_notification",
        "pre_action_confirmation_email": True,
    },
    "daily_digest": {
        "description": "Summary of all VM actions",
        "send_email": True,
        "recipients": ["self"],
        "time": "20:00",
    },
    "weekly_governance": {
        "description": "Weekly governance summary",
        "send_email": True,
        "recipients": ["stakeholders"],
        "time": "Monday 09:00",
    },
}

# Quota awareness guidelines
QUOTA_GUIDANCE = {
    "compute_engine": {
        "rate_quota": "per-minute limits per project",
        "concurrent_operation_quota": "maximum in-flight operations",
        "best_practices": [
            "Queue actions rather than firing burst requests",
            "Use exponential backoff for retries",
            "Poll operation status every 5s, max 60 attempts",
            "Track operation state in local state file",
        ],
    },
}

# Phase 1 checklist
PHASE_1_CHECKLIST = {
    "api_enablement": [
        {"api": "compute.googleapis.com", "enabled": False},
        {"api": "gmail.googleapis.com", "enabled": False},
        {"api": "drive.googleapis.com", "enabled": False},
        {"api": "sheets.googleapis.com", "enabled": False},
        {"api": "servicehealth.googleapis.com", "enabled": False},
    ],
    "auth_setup": {
        "service_account_name": "forge-ccd-sa",
        "scopes": [
            "https://www.googleapis.com/auth/compute",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/cloud-platform.read-only",
        ],
    },
    "register_setup": {
        "spreadsheet_name": "VM Register",
        "tab_names": ["VM Register", "Change Log", "Evidence Index"],
    },
    "evidence_setup": {
        "folder_name": "VM Evidence",
        "subfolders": ["2026-03", "2026-04"],
    },
}

# Phase 2 MVP flow validation
PHASE_2_MVP_FLOW = {
    "workflow": "start instance",
    "steps": [
        "User selects VM → clicks 'Start'",
        "System shows confirmation (instance, zone, reason field)",
        "User confirms → API call sent to Compute Engine",
        "Operation resource returned → polling loop started",
        "Poll every 5s until DONE or FAILED",
        "On success: Update Sheets, Write Drive evidence, Send Gmail",
        "On failure: Update Sheets, Write Drive evidence, Send Gmail failure",
    ],
    "success_criteria": [
        "One VM starts from the tool",
        "Operation polled to completion",
        "Sheets register updated",
        "Evidence pack written to Drive",
        "Gmail notification sent",
    ],
}


def ensure_dir(path: Path) -> Path:
    """Create directory if it doesn't exist, return path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, data: dict, indent: int = 2) -> None:
    """Write JSON file with consistent formatting."""
    with open(path, "w") as f:
        json.dump(data, f, indent=indent)
        f.write("\n")


def bootstrap():
    """Run the bootstrap process."""
    print("Forge Compute Control Desk — Project Bootstrap")
    print("=" * 50)

    # 1. Ensure workspace structure
    print("\n[1] Ensuring workspace structure...")
    ensure_dir(PROJECT_ROOT / "config")
    ensure_dir(PROJECT_ROOT / "data")
    ensure_dir(PROJECT_ROOT / "docs")
    ensure_dir(PROJECT_ROOT / "src")
    ensure_dir(PROJECT_ROOT / "src" / "core")
    ensure_dir(PROJECT_ROOT / "src" / "integrations")
    ensure_dir(PROJECT_ROOT / "src" / "ui")
    ensure_dir(PROJECT_ROOT / "tests")

    # 2. Write configuration files
    print("\n[2] Writing configuration files...")

    write_json(
        PROJECT_ROOT / "config" / "google-cloud-baseline.json",
        GC_BASELINE,
    )
    write_json(
        PROJECT_ROOT / "config" / "sheets-register-schema.json",
        SHEETS_REGISTER_SCHEMA,
    )
    write_json(
        PROJECT_ROOT / "config" / "evidence-structure.json",
        EVIDENCE_STRUCTURE,
    )
    write_json(
        PROJECT_ROOT / "config" / "action-catalogue.json",
        ACTION_CATALOGUE,
    )
    write_json(
        PROJECT_ROOT / "config" / "confirmation-model.json",
        CONFIRMATION_MODEL,
    )
    write_json(
        PROJECT_ROOT / "config" / "gmail-notifications.json",
        GMAIL_NOTIFICATIONS,
    )
    write_json(
        PROJECT_ROOT / "config" / "quota-guidance.json",
        QUOTA_GUIDANCE,
    )
    write_json(
        PROJECT_ROOT / "config" / "phase-1-checklist.json",
        PHASE_1_CHECKLIST,
    )
    write_json(
        PROJECT_ROOT / "config" / "phase-2-mvp-flow.json",
        PHASE_2_MVP_FLOW,
    )

    # 3. Write environment template
    print("\n[3] Writing environment template...")
    env_template = """# Google Cloud
GCP_PROJECT_ID=your-gcp-project-id
GCP_REGION=europe-west2
GCP_ZONE=europe-west2-b

# Service Account (for Compute Engine, Drive, Sheets, Gmail)
GCP_SERVICE_ACCOUNT_JSON=/path/to/service-account.json

# Sheets (VM Register)
SHEETS_SPREADSHEET_ID=your-sheets-spreadsheet-id

# Drive (Evidence)
DRIVE_EVIDENCE_FOLDER_ID=your-drive-folder-id

# Gmail (Notifications)
GMAIL_SENDER_EMAIL=your-email@gmail.com
GMAIL_CLIENT_SECRETS=/path/to/client_secrets.json

# Logging
LOG_LEVEL=INFO
"""
    with open(PROJECT_ROOT / ".env.template", "w") as f:
        f.write(env_template)

    # 4. Write bootstrap README
    print("\n[4] Writing bootstrap README...")
    bootstrap_readme = """# Forge Compute Control Desk

## Project Status

**Bootstrap completed:** 2026-03-30

## Quick Start

1. Copy `.env.template` to `.env` and fill in values
2. Enable required APIs in Google Cloud Console
3. Create service account with appropriate scopes
4. Create Sheets spreadsheet and note its ID
5. Create Drive folder for evidence and note its ID
6. Run `python -m src.core.bootstrap` to validate

## Project Structure

```
forge-cloud-control-desk/
├── config/          # Configuration files (schemas, models)
├── data/            # Local state, logs,缓存
├── docs/            # Documentation (architecture, runbooks)
├── src/             # Source code
│   ├── core/        # Core business logic
│   ├── integrations/ # Google API integrations
│   └── ui/          # Dashboard UI code
├── tests/           # Test suite
├── .env             # Environment variables (gitignored)
└── .env.template    # Environment template
```

## Phase Plan

- **Phase 1**: Design & foundation (done)
- **Phase 2**: Thin end-to-end flow (next)
- **Phase 3**: Broaden action set
- **Phase 4**: Operational hardening

## Solo Governance Rules

1. No destructive action without confirmation
2. No create action without register entry
3. No "success" state until operation resource confirms
4. No important action without Drive evidence
5. No silent failures

## Next Steps

Run `make validate` to verify environment setup.
Run `make start` to launch the development server.

---

*Project bootstrap complete.*
"""
    with open(PROJECT_ROOT / "BOOTSTRAP-README.md", "w") as f:
        f.write(bootstrap_readme)

    print("\n[✓] Bootstrap complete!")
    print("\nNext steps:")
    print("1. Copy .env.template to .env and fill in values")
    print("2. Run 'make validate' to verify setup")
    print("3. Proceed to Phase 2 implementation")


if __name__ == "__main__":
    bootstrap()
