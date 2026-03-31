# Forge Cloud Control Desk — Team Operations Runbook

**Record:** GCCD-OPS-001  
**Date:** 2026-04-01  
**Status:** ACTIVE  
**Owner:** Platform team (rotating on-call)  

---

## 1. Team Structure

### Core Platform Team
| Role | Responsibility | Escalation Path |
|------|----------------|-----------------|
| Platform Owner | GCCD architecture, extension acceptance, strategic decisions | Direct to CTO |
| On-Call Engineer | Daily operations, incident response, routine maintenance | Platform Owner |
| Extension Owner (per extension) | Extension-specific operations, handover, retirement planning | Platform Owner |

### Extension: Forge Email Server (Phase 4)
| Role | Responsibility | Status |
|------|----------------|--------|
| Extension Owner | TBD — must be assigned before Phase 4A begins | **PENDING** |
| On-Call Rotation | TBD — handover procedure required | **PENDING** |

---

## 2. Operational Responsibilities

### Daily (Automated)
- Daily digest generation (00:00 UTC)
- Evidence store health check
- Register sync validation

### Weekly (Manual Review)
- Review weekly governance report
- Check for orphaned VMs (not in register)
- Verify evidence completeness
- Review any failed operations

### Monthly (Governance)
- Extension health review
- Runbook accuracy check
- Access audit (service account keys)
- Cost review against register

---

## 3. Extension Acceptance Gate

Before any extension is accepted into GCCD, the following **must** be documented and approved:

### Required Documentation
1. **Extension Design Brief** — purpose, scope, boundaries
2. **Architecture Decisions** — runtime, auth model, network design
3. **Named On-Call Owner** — individual or team roster
4. **Handover Procedure** — how knowledge transfers between owners
5. **Runbook Ownership** — who maintains operational docs
6. **Retirement Plan** — explicit shutdown path

### Approval Workflow
```
Extension Proposal → Architecture Review → Owner Assignment →
Retirement Plan Review → Platform Owner Sign-off → Merge to Roadmap
```

### Current Extension Status

| Extension | Phase | Owner | Handover Doc | Retirement Plan | Status |
|-----------|-------|-------|--------------|-----------------|--------|
| Forge Email Server | 4 (pending) | **UNASSIGNED** | — | — | **BLOCKED** |

---

## 4. Incident Escalation Matrix

| Severity | Definition | Response Time | Action | Escalation |
|----------|------------|---------------|--------|------------|
| P0 (Critical) | Production VM loss, data breach, unauthorized access | 15 min | Page on-call engineer → Platform Owner → CTO | Immediate |
| P1 (High) | Service degradation, failed operations affecting workloads | 1 hour | Ticket + Slack alert → On-call engineer | 4 hours to Platform Owner |
| P2 (Medium) | Evidence gaps, register inconsistencies, minor failures | 4 hours | Ticket queue → Next business day review | 24 hours |
| P3 (Low) | Documentation gaps, optimization opportunities | 1 week | Backlog | Monthly review |

### Incident Response Procedure
1. **Detect**: Automated alerts (daily digest anomalies) or manual report
2. **Triage**: On-call engineer classifies severity within 30 minutes
3. **Respond**: Execute relevant runbook section
4. **Document**: Evidence record in `data/evidence/incidents/`
5. **Review**: Post-incident review within 48 hours for P0/P1

---

## 5. Runbook Ownership Model

### Document Hierarchy
```
TEAM-OPS-RUNBOOK.md (this file) — platform-level operations
├── EXTENSION-{NAME}-RUNBOOK.md — extension-specific operations
│   └── Sub-procedures (restart, failover, retirement)
└── PLAYBOOK-{SCENARIO}.md — scenario-specific response guides
```

### Update Requirements
| Document Type | Review Frequency | Owner |
|---------------|------------------|-------|
| Team Ops Runbook | Monthly | Platform Owner |
| Extension Runbook | Per-extension | Extension Owner |
| Playbooks | After each use | On-call engineer |

### Change Control
- All runbook changes require PR review
- Emergency changes may be committed directly with post-hoc review
- Outdated sections marked with `[DEPRECATED: YYYY-MM-DD]`

---

## 6. Extension Retirement Procedure

### Mandatory Retirement Plan Components
Before accepting any extension, document:

1. **Trigger Conditions** — when retirement is initiated
2. **Data Migration** — what data moves, where, how
3. **Workload Shutdown** — ordered shutdown steps
4. **Credential Revocation** — API keys, service accounts, tokens
5. **Resource Cleanup** — VMs, disks, networks, DNS
6. **Verification** — how to confirm complete removal
7. **Communication** — who gets notified, how

### Forge Email Server Retirement Template
```markdown
## Forge Email Server Retirement Plan

### Trigger
- Extension no longer needed, or
- Migration to managed service, or
- Security incident requiring shutdown

### Data Migration
- [ ] Export mail logs from /var/log/mail.log
- [ ] Copy queue contents (if any) to archive
- [ ] Document final SendGrid domain status

### Workload Shutdown
- [ ] Stop Postfix: sudo systemctl stop postfix
- [ ] Disable auto-start: sudo systemctl disable postfix
- [ ] Flush mail queue: sudo postsuper -d ALL

### Credential Revocation
- [ ] Rotate SendGrid API key
- [ ] Remove GCP service account IAM bindings
- [ ] Delete stored credentials from VM

### Resource Cleanup
- [ ] Delete VM via GCCD delete workflow
- [ ] Verify deletion in GCP Console
- [ ] Remove DNS records (if any were created)
- [ ] Clean up firewall rules

### Verification
- [ ] Confirm VM absent from `gcloud compute instances list`
- [ ] Confirm no unexpected charges in GCP billing
- [ ] Verify SendGrid domain inactive

### Communication
- [ ] Notify Platform Owner
- [ ] Update extension status in ROADMAP.md
- [ ] Archive runbook with retirement date
```

---

## 7. Handover Procedure

### When Required
- Extension owner leaving/changing roles
- On-call rotation change
- Extended absence (>2 weeks)

### Handover Checklist
- [ ] Current status documented in evidence store
- [ ] Open incidents/issues transferred
- [ ] Access credentials reviewed (not shared, but confirmed working)
- [ ] Runbook walkthrough completed
- [ ] Emergency contacts confirmed
- [ ] Retirement plan reviewed
- [ ] Platform Owner notified

### Handover Document Template
```markdown
## Extension Handover: {Extension Name}

**From:** {Outgoing Owner}  
**To:** {Incoming Owner}  
**Date:** {YYYY-MM-DD}

### Current State
- Status: {active/paused/degraded}
- Last incident: {date or "none"}
- Known issues: {list or "none"}

### Access Verification
- [ ] Service account key functional
- [ ] GCP Console access confirmed
- [ ] SendGrid dashboard accessible (if applicable)

### Documentation Review
- [ ] Extension runbook reviewed
- [ ] Retirement plan reviewed
- [ ] Recent evidence inspected

### Sign-off
- Outgoing: _______________ Date: _______
- Incoming: _______________ Date: _______
- Platform Owner: _______________ Date: _______
```

---

## 8. Operational Commands Reference

### Evidence Store Inspection
```bash
# Check recent actions
cd /path/to/forge-cloud-control-desk
cat data/evidence/reports/daily_digest_$(date +%Y-%m-%d).md

# List all VM actions for a date
ls -la data/evidence/*_$(date +%Y-%m-%d)_*.md

# Check notification backlog
ls -la data/evidence/notifications/
```

### Register Validation
```bash
# Open Sheets register (manual)
https://docs.google.com/spreadsheets/d/${SHEETS_SPREADSHEET_ID}/edit

# Verify GCP project
gcloud config get-value project
gcloud compute instances list --filter="labels.forge-managed=true"
```

### Emergency Procedures
```bash
# Stop all forge-managed VMs (emergency)
gcloud compute instances stop $(gcloud compute instances list --filter="labels.forge-managed=true" --format="value(name)") --zone=$GCP_ZONE

# Generate emergency digest
python3 src/main.py digest $(date +%Y-%m-%d)
```

---

## 9. Key Contacts

| Role | Contact | Method |
|------|---------|--------|
| Platform Owner | TBD | Slack #gccd-platform |
| On-Call Engineer | TBD | PagerDuty / Slack |
| GCP Support | — | Cloud Console |
| SendGrid Support (Phase 4) | — | sendgrid.com |

---

## 10. Document History

| Date | Change | Author |
|------|--------|--------|
| 2026-04-01 | Initial runbook | GCCD platform team |

---

*This runbook is a living document. Updates require Platform Owner approval.*
