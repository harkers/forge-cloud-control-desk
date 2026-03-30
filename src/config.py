# Configuration module
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Project configuration
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
GCP_PROJECT_NAME = os.environ.get("GCP_PROJECT_NAME", GCP_PROJECT_ID)
GCP_REGION = os.environ.get("GCP_REGION", "europe-west2")
GCP_ZONE = os.environ.get("GCP_ZONE", "europe-west2-b")
GCP_SERVICE_ACCOUNT_JSON = os.environ.get("GCP_SERVICE_ACCOUNT_JSON")
SHEETS_SPREADSHEET_ID = os.environ.get("SHEETS_SPREADSHEET_ID")
DRIVE_EVIDENCE_FOLDER_ID = os.environ.get("DRIVE_EVIDENCE_FOLDER_ID")
GMAIL_SENDER_EMAIL = os.environ.get("GMAIL_SENDER_EMAIL", "stuharker@gmail.com")
GMAIL_CLIENT_SECRETS = os.environ.get("GMAIL_CLIENT_SECRETS")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

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
    missing = [var for var in REQUIRED_VARS if not os.environ.get(var)]
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
