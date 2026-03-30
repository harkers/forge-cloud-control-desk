#!/usr/bin/env python3
"""
Forge Compute Control Desk — Setup and Validation Script

Run this script to validate environment setup before implementing Phase 2.
"""

import os
import sys
import json


def validate():
    """Validate environment configuration."""
    print("Forge Compute Control Desk — Environment Validation")
    print("=" * 60)

    # Load .env - look in parent directory (project root)
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if not os.path.exists(env_path):
        print("❌ .env file not found")
        return False

    env_vars = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key] = value

    # Required variables
    required = [
        "GCP_PROJECT_ID",
        "GCP_REGION",
        "GCP_ZONE",
        "GCP_SERVICE_ACCOUNT_JSON",
        "SHEETS_SPREADSHEET_ID",
        "DRIVE_EVIDENCE_FOLDER_ID",
        "GMAIL_SENDER_EMAIL",
        "GMAIL_CLIENT_SECRETS",
    ]

    print("\nEnvironment Variables:")
    all_ok = True
    for var in required:
        value = env_vars.get(var, "")
        if not value or value.startswith("your-"):
            print(f"  ❌ {var} not configured")
            all_ok = False
        else:
            print(f"  ✅ {var} = {value[:30]}{'...' if len(value) > 30 else ''}")

    # Check service account JSON
    sa_path = env_vars.get("GCP_SERVICE_ACCOUNT_JSON", "")
    if os.path.exists(sa_path):
        print(f"\n✅ Service account JSON found at: {sa_path}")
        with open(sa_path) as f:
            sa_data = json.load(f)
        print(f"   Project: {sa_data.get('project_id')}")
        print(f"   Email: {sa_data.get('client_email')}")
    else:
        print(f"\n❌ Service account JSON not found: {sa_path}")
        all_ok = False

    # Check Gmail client secrets
    gmail_path = env_vars.get("GMAIL_CLIENT_SECRETS", "")
    if os.path.exists(gmail_path):
        print(f"\n✅ Gmail client secrets found at: {gmail_path}")
        with open(gmail_path) as f:
            gmail_data = json.load(f)
        client_id = gmail_data.get("installed", {}).get("client_id", "unknown")
        print(f"   Client ID: {client_id[:20]}...")
    else:
        print(f"\n❌ Gmail client secrets not found: {gmail_path}")
        all_ok = False

    print("\n" + "=" * 60)
    if all_ok:
        print("✅ Environment validation PASSED")
        print("\nReady to implement Phase 2!")
        return True
    else:
        print("❌ Environment validation FAILED")
        print("\nPlease configure missing values in .env")
        return False


if __name__ == "__main__":
    success = validate()
    sys.exit(0 if success else 1)
