# Extension Retirement Plan — Forge Email Server

**Document:** GCCD-EXT-RET-001  
**Created:** 2026-04-02  
**Status:** Approved  
**Applies to:** Phase 4 — Forge Email Server Extension  

---

## Overview

This document defines the mandatory retirement/shutdown path for the Forge Email Server extension. **No extension may be accepted into GCCD without a documented retirement plan.**

The email extension can be retired gracefully without impacting core GCCD VM operations.

---

## Retirement Triggers

### Planned Retirement
- Email volume drops below threshold (e.g., <10 emails/month)
- Alternative email solution adopted (e.g., managed SaaS)
- Extension no longer provides value
- Cost exceeds benefit

### Emergency Retirement
- Security compromise of relay VM
- SendGrid account breach
- Persistent delivery failures
- Compliance requirement to cease operations

---

## Retirement Procedure

### Phase 1: Disable New Email Flow (Day 0)

1. **Update firewall rules** to block outbound port 587
   ```bash
   gcloud compute firewall-rules delete allow-smtp-outbound --quiet
   ```

2. **Stop Postfix** to prevent queuing
   ```bash
   gcloud compute ssh forge-mail-server --zone=europe-west2-b \
     --command="sudo systemctl stop postfix"
   ```

3. **Notify stakeholders** via GCCD notification channel

### Phase 2: Drain Queue (Day 0-1)

1. **Check queue status**
   ```bash
   gcloud compute ssh forge-mail-server --zone=europe-west2-b \
     --command="sudo postqueue -p"
   ```

2. **If queue empty:** Proceed to Phase 3
   
3. **If messages pending:**
   - Option A: Wait 24h for natural drain (messages will defer/fail)
   - Option B: Force flush: `sudo postsuper -d ALL`

### Phase 3: Disable Event Webhook (Day 1)

1. **Stop webhook receiver**
   ```bash
   sudo systemctl stop gccd-mail-webhook
   sudo systemctl disable gccd-mail-webhook
   ```

2. **Remove firewall rule** for port 5002
   ```bash
   gcloud compute firewall-rules delete allow-webhook-inbound --quiet
   ```

3. **Disable SendGrid webhook** in dashboard

### Phase 4: Archive Evidence (Day 1-2)

1. **Copy mail events to long-term storage**
   ```bash
   tar -czf mail-events-archive-$(date +%Y%m%d).tar.gz \
     data/evidence/mail-events/
   ```

2. **Upload to Drive** evidence folder

3. **Update Sheets register** with retirement timestamp

### Phase 5: Decommission VM (Day 2-3)

1. **Final backup** of Postfix config
   ```bash
   gcloud compute ssh forge-mail-server --zone=europe-west2-b \
     --command="sudo tar -czf /tmp/postfix-config-$(date +%Y%m%d).tar.gz /etc/postfix/"
   ```

2. **Delete VM via GCCD**
   ```bash
   cd /home/stu/.openclaw/workspace/projects/forge-cloud-control-desk
   export $(grep -v '^#' .env | xargs)
   python3 -m src.main delete forge-mail-server \
     --reason="Extension retirement: Phase 4 email server decommissioned per retirement plan"
   ```

3. **Verify deletion** in Sheets register

### Phase 6: Cleanup (Day 3-7)

1. **Remove DNS records** (if authenticated domain was used)

2. **Delete SendGrid subuser** (if dedicated subuser created)

3. **Archive documentation**
   - Move extension docs to `docs/archive/phase4-email/`

4. **Update ROADMAP** — Mark Phase 4 as retired

5. **Final evidence** — Create retirement completion report

---

## Rollback Capability

If retirement was initiated in error, recovery is possible **before VM deletion**:

```bash
# Re-enable Postfix
gcloud compute ssh forge-mail-server --zone=europe-west2-b \
  --command="sudo systemctl start postfix"

# Re-enable webhook
sudo systemctl start gccd-mail-webhook

# Restore firewall
gcloud compute firewall-rules create allow-smtp-outbound \
  --direction=EGRESS --action=ALLOW --rules=tcp:587
```

**After VM deletion:** Full rebuild required (Phase 4A-E)

---

## Ownership

| Role | Owner | Responsibility |
|------|-------|----------------|
| Decision | GCCD Platform Team | Approve retirement |
| Execution | GCCD Operator | Perform retirement steps |
| Verification | GCCD Platform Team | Confirm clean shutdown |
| Archive | GCCD Operator | Evidence preservation |

---

## Evidence Requirements

Retirement must produce:
- [ ] Retirement decision record (approval documentation)
- [ ] Queue drain confirmation (screenshot/logs)
- [ ] Final mail event archive (tar.gz in Drive)
- [ ] VM deletion evidence (GCCD delete workflow output)
- [ ] Retirement completion report (Markdown)

---

## Cost Impact

**Pre-retirement monthly:**
- VM (e2-medium): ~$25/month
- SendGrid: Free tier (100/day) or paid

**Post-retirement:** $0 (VM deleted, SendGrid account suspended)

---

## Timeline Summary

| Phase | Duration | Critical Action |
|-------|----------|-----------------|
| 1 | Day 0 | Stop new email flow |
| 2 | Day 0-1 | Drain queue |
| 3 | Day 1 | Disable webhook |
| 4 | Day 1-2 | Archive evidence |
| 5 | Day 2-3 | Delete VM |
| 6 | Day 3-7 | Final cleanup |

**Total:** 3-7 days for complete retirement

---

## Emergency Shutdown (Sub-1 Hour)

If immediate shutdown required:

```bash
# Stop all email flow NOW
gcloud compute firewall-rules delete allow-smtp-outbound --quiet
gcloud compute ssh forge-mail-server --zone=europe-west2-b \
  --command="sudo systemctl stop postfix && sudo postsuper -d ALL"

# Disable webhook
sudo systemctl stop gccd-mail-webhook

# Log emergency action
echo "Emergency shutdown: $(date)" >> data/evidence/emergency-shutdown.log
```

Then proceed with Phases 4-6 when safe.

---

## Acceptance Criteria

This retirement plan is accepted when:
- [x] All phases documented with commands
- [x] Timeline defined (3-7 days)
- [x] Rollback procedure documented
- [x] Evidence requirements specified
- [x] Ownership assigned
- [x] Cost impact calculated
- [x] Emergency shutdown procedure included

**Status:** ✅ **APPROVED FOR PHASE 4 ACCEPTANCE**

---

*Document created as mandatory extension retirement plan — 2026-04-02*
