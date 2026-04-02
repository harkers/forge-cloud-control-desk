# Phase 5 — Governance Hardening

**Document:** GCCD-PH5-001  
**Created:** 2026-04-02  
**Status:** In Progress  
**Parent:** ROADMAP.md  
**Depends:** Phase 4 Complete (Email Extension operational)  

---

## Overview

Phase 5 hardens GCCD's governance capabilities:
- Exception handling and approval overrides
- Retention rules for exported reports
- Stronger audit views
- Extension retirement runbooks
- Relay-runbook operations hardening

This phase ensures GCCD can operate safely at scale with team-based ownership.

---

## Deliverables

### 1. Exception Handling Framework
Handle edge cases and failures gracefully.

**Components:**
- Retry logic with exponential backoff
- Circuit breaker for failed operations
- Manual override for stuck operations
- Error classification and alerting

### 2. Approval Override System
Allow emergency actions with post-hoc approval.

**Use cases:**
- Critical VM restart during incident
- Emergency delete of compromised VM
- Bulk operations for cost optimization

### 3. Retention Rules
Automated cleanup of old evidence and reports.

**Policy:**
- Evidence files: 90 days local, archive to Drive
- Daily digests: 30 days
- Weekly reports: 1 year
- VM change log: indefinite (Sheets)

### 4. Enhanced Audit Views
Better visibility into operations history.

**Features:**
- Searchable operation log
- Cost analysis by VM
- Failed operation tracking
- SLA compliance metrics

### 5. Extension Retirement Runbooks
Operational guides for extension lifecycle.

**Documents:**
- Phase 4 retirement plan ✅ (already created)
- Phase N+1 deprecation procedures
- Emergency shutdown playbooks

---

## Implementation Priority

| Feature | Priority | Effort | Impact |
|---------|----------|--------|--------|
| Retention automation | High | Medium | Cost + compliance |
| Exception handling | High | Medium | Reliability |
| Enhanced audit views | Medium | High | Operations |
| Approval overrides | Medium | Medium | Flexibility |
| Retention rules | Low | Low | Maintenance |

---

## Next Steps

1. **Start with retention automation** — Clean up old evidence files
2. **Add exception handling** — Retry logic for GCP API failures
3. **Build audit view** — Operation history dashboard

Which would you like to tackle first?

---

*Document created as Phase 5 kickoff — 2026-04-02*
