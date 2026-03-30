# API Enablement Commands for orderededge-groupware

## Enable Required APIs

Run these commands in your terminal:

```bash
# Set project
gcloud config set project orderededge-groupware

# Enable Compute Engine API
gcloud services enable compute.googleapis.com

# Enable Drive API
gcloud services enable drive.googleapis.com

# Enable Sheets API
gcloud services enable sheets.googleapis.com

# Enable Gmail API
gcloud services enable gmail.googleapis.com
```

## Or use Google Cloud Console

Go to [APIs & Services](https://console.cloud.google.com/apis/dashboard) and enable:
- Compute Engine API
- Drive API
- Sheets API
- Gmail API

## After enabling APIs

The service account `orge-ccd-sa@orderededge-groupware.iam.gserviceaccount.com` needs these roles:

- `roles/compute.instanceAdmin.v1` (Compute Engine)
- `roles/drive.file` (Drive)
- `roles/sheets.serviceUser` (Sheets)
- `roles/gmail.send` (Gmail)

## Validation

After enabling APIs, run:
```bash
gcloud compute instances list --project=orderededge-groupware
```
