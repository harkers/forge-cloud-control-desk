# Service Account Setup for Forge Compute Control Desk

## Step 1: Create Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Select your project: `orderededge-groupware` (ID: 301823798218)
3. Click **+ CREATE SERVICE ACCOUNT**
4. Fill in:
   - **Service account name**: `forge-ccd-sa`
   - **Service account description**: `Forge Compute Control Desk service account`
5. Click **CREATE AND CONTINUE**

## Step 2: Grant Roles

Select the following roles (minimum required):

| Role | Purpose |
|------|---------|
| `Compute Instance Admin (v1)` | Create, start, stop, restart, inspect VMs |
| `Service Usage Admin` | Enable APIs on project |
| `Cloud Resource Manager Viewer` | View project resources |
| `Storage Object Creator` | Write to Drive (evidence) |
| `Sheets API User` | Access Sheets spreadsheets |
| `Gmail send message` | Send notifications |

**Or use these predefined roles:**
- `roles/compute.instanceAdmin.v1`
- `roles/serviceusage.serviceUsageAdmin`
- `roles/resourcemanager.projectViewer`
- `roles/storage.objectCreator`
- `roles/sheets.serviceUser`
- `roles/gmail.send`

Click **CONTINUE** → **DONE**

## Step 3: Create Key

1. Find your new service account `forge-ccd-sa@orderededge-groupware.iam.gserviceaccount.com`
2. Click the three dots → **MANAGE KEYS**
3. Click **ADD KEY** → **Create new key**
4. Select **JSON** format
5. Click **CREATE**
6. Download the JSON file — save it as:
   ```
   ~/.config/gcp/forge-ccd-service-account.json
   ```

## Step 4: Enable Required APIs

Run these commands (or enable via Cloud Console):

```bash
gcloud services enable compute.googleapis.com \
  --project=orderededge-groupware

gcloud services enable drive.googleapis.com \
  --project=orderededge-groupware

gcloud services enable sheets.googleapis.com \
  --project=orderededge-groupware

gcloud services enable gmail.googleapis.com \
  --project=orderededge-groupware
```

## Step 5: Configure Gmail OAuth2 (for email notifications)

1. Go to [Google Cloud Console - APIs & Services](https://console.cloud.google.com/apis/credentials)
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. Application type: **Desktop app**
4. Name: `forge-ccd-gmail-client`
5. Click **CREATE**
6. Download the JSON — save as:
   ```
   ~/.config/gmail/client_secrets.json
   ```

7. Authorize scopes (in code, we'll request):
   - `https://www.googleapis.com/auth/gmail.modify`
   - `https://www.googleapis.com/auth/gmail.send`

## Step 6: Test Service Account

```bash
# Install gcloud if not already installed
# Set project
gcloud config set project orderededge-groupware

# Authenticate with service account
gcloud auth activate-service-account \
  --key-file=~/.config/gcp/forge-ccd-service-account.json

# Test Compute Engine API
gcloud compute instances list \
  --project=orderededge-groupware
```

## Step 7: Update .env with Actual Values

```bash
# Get the service account JSON path (should match where you saved it)
GCP_SERVICE_ACCOUNT_JSON=/home/stu/.config/gcp/forge-ccd-service-account.json

# After creating Sheets spreadsheet, copy its ID from URL:
# https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit
SHEETS_SPREADSHEET_ID=

# After creating Drive folder, copy folder ID from URL:
# https://drive.google.com/drive/folders/[FOLDER_ID]
DRIVE_EVIDENCE_FOLDER_ID=

# Gmail OAuth client secrets
GMAIL_CLIENT_SECRETS=/home/stu/.config/gmail/client_secrets.json
```

## Summary of Files to Create

| File | Location | Purpose |
|------|----------|---------|
| Service Account Key | `~/.config/gcp/forge-ccd-service-account.json` | GCP API authentication |
| Gmail Client Secrets | `~/.config/gmail/client_secrets.json` | Gmail OAuth authentication |

## Important Notes

1. **Keep keys secure**: Never commit `.env` or JSON keys to Git
2. **Rotate keys**: Regenerate service account keys periodically
3. **Least privilege**: Only grant the minimum required roles
4. **Audit**: Review service account activity in Cloud Audit Logs
