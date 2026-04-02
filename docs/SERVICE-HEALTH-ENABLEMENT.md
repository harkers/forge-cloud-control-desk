# Service Health API Enablement Guide

**Document:** GCCD-OPS-002  
**Created:** 2026-04-02  
**Status:** Instructions for GCP Console  

---

## Overview

The Service Health integration (Phase 3) requires the **Cloud Resource Manager API** to be enabled in the GCP project. This guide walks through the enablement process.

---

## Prerequisites

- Access to GCP project: `orderededge-groupware` (301823798218)
- Owner or Editor role on the project
- Service account file: `/home/stu/.config/gcp/forge-ccd-service-account.json`

---

## Step 1: Enable Cloud Resource Manager API

### Option A: Via GCP Console (Recommended)

1. Open browser to: https://console.cloud.google.com/apis/api/cloudresourcemanager.googleapis.com

2. Select project: **orderededge-groupware** (301823798218)

3. Click **"ENABLE"** button

4. Wait for confirmation (usually takes 10-30 seconds)

5. Verify status shows "API enabled"

### Option B: Via gcloud CLI

If gcloud is installed and authenticated:

```bash
gcloud services enable cloudresourcemanager.googleapis.com --project=301823798218
```

Expected output:
```
Operation "operations/..." finished successfully.
```

---

## Step 2: Update Service Account Scopes

The Service Health API requires the `cloud-platform.read-only` scope.

### Check Current Scopes

```bash
# If using gcloud
gcloud iam service-accounts describe \
  forge-ccd@orderededge-groupware.iam.gserviceaccount.com \
  --project=orderededge-groupware
```

### Add Scope (if needed)

Service account scopes are set at VM creation time, not on the service account itself. The Python code requests the scope during OAuth, which should work automatically.

**If you encounter scope errors:**

1. Go to IAM & Admin → Service Accounts
2. Select `forge-ccd@orderededge-groupware.iam.gserviceaccount.com`
3. Click "Edit"
4. Ensure it has these roles:
   - **Viewer** (roles/viewer)
   - **Compute Viewer** (roles/compute.viewer)
5. Save changes

---

## Step 3: Test the Integration

After enabling the API:

```bash
cd /home/stu/.openclaw/workspace/projects/forge-cloud-control-desk
export $(grep -v '^#' .env | xargs)
python3 -m src.main health
```

### Expected Output (API Enabled)

```
Service Health Check: OPERATIONAL
Region: europe-west2
Active Incidents: 0
Evidence: /path/to/health_check_TIMESTAMP.md
```

### Check Evidence File

```bash
cat data/evidence/service_health/health_check_*.md
```

Should show real event data if any incidents exist.

---

## Step 4: Verify Service Health Dashboard

Visit the Service Health dashboard to see current status:

https://console.cloud.google.com/monitoring/dashboards/service-health

Check for:
- Any active incidents affecting Compute Engine
- Historical events in europe-west2
- Service status indicators

---

## Troubleshooting

### Error: "SERVICE_DISABLED"

**Cause:** API not enabled

**Fix:** Complete Step 1 above

---

### Error: "PERMISSION_DENIED"

**Cause:** Service account lacks required permissions

**Fix:** 
1. Verify service account has Viewer role
2. Check API is enabled for the project
3. Wait 2-5 minutes for permissions to propagate

---

### Error: "SCOPE_NOT_AUTHORIZED"

**Cause:** OAuth request missing required scope

**Fix:** The code already requests `cloud-platform.read-only` scope. If this error persists, check:
1. Service account JSON file is valid
2. Service account hasn't been deleted
3. API is enabled

---

### No Events Returned (Empty List)

**This is normal if:**
- No incidents have occurred recently
- No maintenance events are scheduled
- Service is fully operational

The integration is working correctly if it returns:
```json
{
  "status": "OPERATIONAL",
  "active_incidents": 0,
  "total_events": 0
}
```

---

## Monitoring & Alerts

Once enabled, consider:

1. **Daily Health Checks** — Add to cron for automated daily checks
2. **Alert on Active Incidents** — Integrate with notification system
3. **Weekly Summary** — Include in weekly governance report

Example cron entry (daily at 08:00):
```bash
0 8 * * * cd /home/stu/.openclaw/workspace/projects/forge-cloud-control-desk && export $(grep -v '^#' .env | xargs) && python3 -m src.main health
```

---

## Next Steps

After enablement:

1. ✅ Run initial health check
2. ✅ Verify evidence generation
3. ⏳ Build HTML dashboard to display status
4. ⏳ Integrate with daily digest
5. ⏳ Add incident alerting

---

*Document created as part of GCCD-001 Phase 3 implementation — 2026-04-02*
