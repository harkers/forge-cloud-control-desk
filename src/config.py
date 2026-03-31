# Configuration module
import os
from pathlib import Path

# Load .env file from project root
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"
env_vars = {}
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key] = value

# Project configuration
GCP_PROJECT_ID = env_vars.get("GCP_PROJECT_ID")
GCP_PROJECT_NAME = env_vars.get("GCP_PROJECT_NAME", GCP_PROJECT_ID)
GCP_REGION = env_vars.get("GCP_REGION", "europe-west2")
GCP_ZONE = env_vars.get("GCP_ZONE", "europe-west2-b")
GCP_SERVICE_ACCOUNT_JSON = env_vars.get("GCP_SERVICE_ACCOUNT_JSON")
SHEETS_SPREADSHEET_ID = env_vars.get("SHEETS_SPREADSHEET_ID")
DRIVE_EVIDENCE_FOLDER_ID = env_vars.get("DRIVE_EVIDENCE_FOLDER_ID")
GMAIL_SENDER_EMAIL = env_vars.get("GMAIL_SENDER_EMAIL", "stuharker@gmail.com")
GMAIL_CLIENT_SECRETS = env_vars.get("GMAIL_CLIENT_SECRETS")
LOG_LEVEL = env_vars.get("LOG_LEVEL", "INFO")

# Validation
REQUIRED_VARS = [
    "GCP_PROJECT_ID",
    "GCP_REGION",
    "GCP_ZONE",
    "GCP_SERVICE_ACCOUNT_JSON",
    "SHEETS_SPREADSHEET_ID",
    "DRIVE_EVIDENCE_FOLDER_ID",
    "GMAIL_SENDER_EMAIL",
    "GMAIL_CLIENT_SECRETS",
]


def validate():
    """Validate that all required environment variables are set."""
    missing = [var for var in REQUIRED_VARS if not env_vars.get(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    return True


# Export configuration
__all__ = [
    "GCP_PROJECT_ID",
    "GCP_PROJECT_NAME",
    "GCP_REGION",
    "GCP_ZONE",
    "GCP_SERVICE_ACCOUNT_JSON",
    "SHEETS_SPREADSHEET_ID",
    "DRIVE_EVIDENCE_FOLDER_ID",
    "GMAIL_SENDER_EMAIL",
    "GMAIL_CLIENT_SECRETS",
    "LOG_LEVEL",
    "validate",
]
