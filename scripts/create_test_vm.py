#!/usr/bin/env python3
"""
Create a test VM for Phase 2 workflow testing - with polling to completion.
"""

import os
import sys
import time

from google.oauth2 import service_account
from googleapiclient.discovery import build

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "orderededge-groupware")
ZONE = os.environ.get("GCP_ZONE", "europe-west2-b")
SA_FILE = "/home/stu/.config/gcp/forge-ccd-service-account.json"

credentials = service_account.Credentials.from_service_account_file(
    SA_FILE,
    scopes=["https://www.googleapis.com/auth/compute"],
)

compute = build("compute", "v1", credentials=credentials)

# Create a test VM
instance = {
    "name": "forge-test-vm",
    "machineType": f"projects/{PROJECT_ID}/zones/{ZONE}/machineTypes/e2-medium",
    "disks": [
        {
            "autoDelete": True,
            "boot": True,
            "deviceName": "forge-test-vm",
            "initializeParams": {
                "diskSizeGb": "20",
                "diskType": f"projects/{PROJECT_ID}/zones/{ZONE}/diskTypes/pd-balanced",
                "sourceImage": "projects/debian-cloud/global/images/debian-12-bookworm-v20260310",
            },
            "type": "PERSISTENT",
        }
    ],
    "networkInterfaces": [
        {
            "network": f"projects/{PROJECT_ID}/global/networks/default",
            "accessConfigs": [
                {"name": "External NAT", "type": "ONE_TO_ONE_NAT"}
            ],
        }
    ],
    "metadata": {
        "items": [
            {"key": "startup-script", "value": "#!/bin/bash\necho 'Hello from forge-test-vm'"},
        ]
    },
    "tags": {"items": ["forge-test"]},
}

request = compute.instances().insert(
    project=PROJECT_ID,
    zone=ZONE,
    body=instance,
)

response = request.execute()
operation_id = response.get("name")
print(f"Creating VM: forge-test-vm")
print(f"Operation: {operation_id}")

# Poll for completion
print("\nPolling for VM creation completion...")
max_attempts = 60
interval = 5

for attempt in range(max_attempts):
    try:
        op_request = compute.zoneOperations().get(
            project=PROJECT_ID,
            zone=ZONE,
            operation=operation_id,
        )
        op_result = op_request.execute()
        status = op_result.get("status", "PENDING")
        print(f"Attempt {attempt+1}: Status = {status}")

        if status == "DONE":
            if "error" in op_result:
                print(f"❌ Creation failed: {op_result['error']}")
                sys.exit(1)
            print(f"✅ VM forge-test-vm created successfully!")
            print(f"\nReady to test start workflow...")
            sys.exit(0)

        time.sleep(interval)
    except Exception as e:
        print(f"Error polling: {e}")
        time.sleep(interval)

print(f"❌ Timeout waiting for VM creation")
sys.exit(1)
