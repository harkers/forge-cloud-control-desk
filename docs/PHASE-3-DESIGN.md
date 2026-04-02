# Phase 3 — Operations Visibility Design

**Document:** GCCD-PH3-DES-001  
**Created:** 2026-04-02  
**Status:** Draft  

---

## Overview

Phase 3 adds operational awareness and visibility to the Forge Cloud Control Desk. After Phase 2 proved safe VM lifecycle operations with evidence tracking, Phase 3 focuses on:

1. **Service Health Integration** — Know when Google Cloud services are degraded
2. **Status Dashboard** — Real-time view of VM states and platform health
3. **Scheduled Reporting** — Monthly governance packs for stakeholders
4. **Extension Health Monitoring** — Prepare for Phase 4 relay monitoring

---

## 1. Service Health Integration

### Goal
Detect Google Cloud service disruptions that may affect Compute Engine operations before users report issues.

### Approach
Use the **Google Cloud Service Health API** to:
- Subscribe to events affecting `compute.googleapis.com` in `europe-west2`
- Store event history in Sheets or local evidence
- Alert on active incidents affecting VM operations

### Data Model
```json
{
  "event_id": "evt_20260402_compute_europe-west2",
  "service": "Compute Engine API",
  "impact": "DEGRAVED_PERFORMANCE",
  "affected_regions": ["europe-west2"],
  "start_time": "2026-04-02T10:00:00Z",
  "update_time": "2026-04-02T10:15:00Z",
  "status": "ACTIVE",
  "description": "Increased latency for VM start/stop operations"
}
```

### Implementation Options

**Option A: Service Health API (Preferred)**
- Pros: Official Google API, structured data, programmatic access
- Cons: Requires additional OAuth scope, may have quota limits
- Effort: Medium

**Option B: RSS Feed Parsing**
- Pros: No auth required, simple implementation
- Cons: Unstructured, harder to filter by region/service
- Effort: Low

**Option C: Manual Status Page Checks**
- Pros: No implementation needed
- Cons: Not automated, easy to miss updates
- Effort: None (but defeats purpose)

**Decision:** Option A — Service Health API integration

### Required OAuth Scopes
```
https://www.googleapis.com/auth/cloud-platform.read-only
```

### Integration Points
- Daily health check during digest generation
- Pre-operation check (warn if service degraded before starting VM)
- Incident logging in evidence folder

---

## 2. Status Dashboard

### Goal
Provide real-time visibility into VM states, recent operations, and platform health.

### Format Options

**Option A: Web Dashboard (Flask/FastAPI)**
- Pros: Interactive, real-time, can add auth later
- Cons: Requires hosting, port management, web server maintenance
- Effort: High

**Option B: Static HTML Generator**
- Pros: Simple, no server needed, can host anywhere
- Cons: Requires regeneration for updates, no real-time data
- Effort: Medium

**Option C: Terminal Dashboard (Rich/TUI)**
- Pros: Lightweight, runs anywhere Python runs, no hosting
- Cons: Not shareable, requires CLI access
- Effort: Low-Medium

**Option D: Sheets-Based Dashboard**
- Pros: Already using Sheets for register, shareable, familiar UI
- Cons: Limited visualization, Google-dependent
- Effort: Low

**Decision:** Option B + D — Static HTML for visual dashboard, Sheets for operational status

### Dashboard Content

**VM Status Panel:**
- Instance name, status, machine type
- External IP (if assigned)
- Last action timestamp
- Tags

**Recent Operations:**
- Last 10 actions with status
- Operation IDs for troubleshooting
- Duration metrics

**Platform Health:**
- Service Health status (green/yellow/red)
- Active incidents
- Last health check timestamp

**Cost Indicators:**
- Running instance count
- Estimated daily cost (based on machine types)
- Instances running >7 days (review candidates)

### Refresh Strategy
- Static HTML: Regenerate on each action + hourly cron
- Sheets: Update on each action (already implemented)

---

## 3. Scheduled Reporting (Monthly Governance Packs)

### Goal
Produce comprehensive monthly reports for stakeholders showing:
- VM inventory changes
- Operational activity summary
- Cost trends
- Incidents and their impact
- Compliance evidence

### Report Structure

**1. Executive Summary**
- Total VMs managed
- Actions performed (create/delete/start/stop counts)
- Uptime percentage
- Notable incidents

**2. Inventory Changes**
- New VMs provisioned
- VMs decommissioned
- Machine type changes
- Tag updates

**3. Operational Activity**
- Action timeline (chart)
- Success/failure rates
- Average operation durations
- Peak usage periods

**4. Cost Analysis**
- Estimated monthly spend by VM
- Cost trends vs previous month
- Idle resource identification
- Optimization recommendations

**5. Incident Log**
- Service Health events
- Failed operations and root causes
- Mitigation actions taken

**6. Compliance Evidence**
- All approvals recorded
- Evidence pack index
- Audit trail completeness

### Generation Schedule
- **Monthly:** Full governance pack (PDF + Markdown)
- **Weekly:** Summary report (current implementation)
- **Daily:** Digest (current implementation)

### Output Formats
- Markdown (for version control)
- PDF (for stakeholder distribution)
- Sheets (for data analysis)

---

## 4. Extension Health Monitoring (Phase 4 Prep)

### Goal
Prepare monitoring framework for email relay extension (Phase 4).

### Metrics to Track

**Relay VM Health:**
- Postfix service status
- Queue depth (pending emails)
- Connection success rate to SendGrid

**Delivery Telemetry:**
- Emails sent per day
- Delivery success rate
- Bounce/complaint rates
- SendGrid event webhook processing

**Integration Points:**
- Event Webhook receiver (FastAPI endpoint)
- Event storage (local JSON or SQLite)
- Alerting on delivery failures

### Implementation Timeline
This work begins **only after Phase 4A** (relay VM provisioning) is complete.

---

## Phase 3 Deliverables

| Item | Format | Priority |
|------|--------|----------|
| Service Health API integration | Python module | High |
| Health check in daily digest | Feature addition | High |
| Static HTML dashboard | HTML generator | Medium |
| Monthly report template | Quarto/Markdown | Medium |
| Cost estimation logic | Python module | Low |
| Extension monitoring prep | Design doc only | Low |

---

## Technical Decisions Required

1. **Dashboard Hosting** — Where does static HTML live? (GitHub Pages, internal webserver, GCS bucket?)
2. **Report Distribution** — How do stakeholders receive monthly packs? (Email, Drive, download link?)
3. **Cost Data Source** — Use Billing API estimates or manual calculation from machine types?
4. **Alerting Channel** — Local files only, or integrate with Slack/Email/SMS?

---

## Next Steps

1. ✅ Complete this design document
2. ⏳ Enable Service Health API in GCP project
3. ⏳ Create service account with read-only scope
4. ⏳ Implement health check module
5. ⏳ Build static HTML dashboard generator
6. ⏳ Design monthly report template
7. ⏳ Test with forge-test-vm data

---

## Success Criteria

Phase 3 is complete when:
- [ ] Service Health checks run daily without errors
- [ ] Dashboard shows accurate VM states
- [ ] Monthly report generates with all sections populated
- [ ] Stakeholders can access reports without CLI access
- [ ] Extension monitoring design is documented (implementation deferred to Phase 4)

---

*Document created as part of GCCD-001 Phase 3 planning — 2026-04-02*
