# Phase 4A — Provision Forge Mail Server VM

**Document:** GCCD-PH4A-001  
**Created:** 2026-04-02  
**Status:** In Progress  
**Parent:** EMAIL-SERVER-EXTENSION.md  

---

## Overview

Phase 4A provisions the `forge-mail-server` VM through GCCD itself, using the established governance patterns from Phases 1-3.

This proves the extension governance model: **extensions are provisioned through the platform they extend**.

---

## Target Configuration

| Attribute | Value |
|-----------|-------|
| **Name** | `forge-mail-server` |
| **Project** | `301823798218` (orderededge-groupware) |
| **Region** | `europe-west2` |
| **Zone** | `europe-west2-b` |
| **Machine Type** | `e2-small` (2 vCPU, 2 GB) — scalable to `e2-medium` if needed |
| **OS** | Debian 12 (bookworm) |
| **Boot Disk** | 20 GB SSD persistent |
| **Network** | Default VPC, external IP (for SendGrid outbound) |
| **Tags** | `forge-mail`, `smtp-relay` |
| **Service Account** | `forge-ccd@orderededge-groupware.iam.gserviceaccount.com` |

---

## Pre-Provisioning Checklist

- [ ] Service Health check passes (no GCP incidents)
- [ ] VM name `forge-mail-server` not already in use
- [ ] Quota available for `e2-small` in `europe-west2`
- [ ] Sheets register ready for new VM entry
- [ ] Evidence folder path prepared

---

## Provisioning Command

```bash
cd /home/stu/.openclaw/workspace/projects/forge-cloud-control-desk
export $(grep -v '^#' .env | xargs)
python3 -m src.main create forge-mail-server \
  --machine-type=e2-small \
  --image-project=debian-cloud \
  --image-family=debian-12 \
  --boot-disk-size=20GB \
  --tags=forge-mail,smtp-relay \
  --reason="Phase 4A: Provision email relay VM for managed outbound relay extension"
```

---

## Post-Provisioning Verification

1. **VM Status**: `python3 -m src.main inspect forge-mail-server`
2. **SSH Access**: `gcloud compute ssh forge-mail-server --zone=europe-west2-b`
3. **Network**: Verify external IP assigned and reachable
4. **Sheets**: Confirm register entry created
5. **Evidence**: Verify evidence file generated in Drive

---

## Success Criteria

- [ ] VM `forge-mail-server` created via GCCD
- [ ] VM shows as `RUNNING` in GCP Console
- [ ] SSH access functional
- [ ] Sheets register updated with new VM entry
- [ ] Evidence file stored in Drive
- [ ] No quota or permission errors

---

## Rollback Plan

If provisioning fails or VM is not needed:

```bash
python3 -m src.main delete forge-mail-server \
  --reason="Phase 4A rollback: VM provisioning failed / not needed"
```

---

## Next Steps (Phase 4B)

After successful provisioning:
1. SSH into VM
2. Install Postfix baseline
3. Configure relay-only mode
4. Test local mail submission

See PHASE-4B-POSTFIX-BASELINE.md for detailed steps.

---

*Document created as part of GCCD-001 Phase 4A implementation — 2026-04-02*
