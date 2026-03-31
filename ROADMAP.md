# Forge Cloud Control Desk — Roadmap

## Project Status
- **Forge Pipeline**: `project-20260330044222184857` — `in-progress`
- **GitHub**: https://github.com/harkers/forge-cloud-control-desk

## Vision
Internal governance-and-operations platform for Google Compute Engine VM lifecycle, with structured approvals, audit trails, and Google Workspace integration.

## Architecture
| Layer | Service | Purpose |
|-------|---------|---------|
| Execution | Compute Engine API | VM create/start/stop/resize/tag |
| Workflow | Gmail API | Approvals, notifications, digests |
| Evidence | Drive API | Design docs, runbooks, change records |
| Register | Sheets API | VM inventory, cost tracker, change log |
| Awareness | Service Health API | Google Cloud service events |
| Extension | Postfix + SendGrid | managed outbound email relay |

## MVP Scope
1. VM request & approval (Gmail → Compute Engine)
2. VM provisioning & lifecycle control
3. Sheets asset register updates
4. Drive evidence/report output
5. Email incident/maintenance notifications

## Extension Scope — Forge Email Server
1. Provision relay VM through GCCD
2. Install Postfix relay-only baseline
3. Authenticate sending subdomain in SendGrid
4. Capture delivery telemetry through Event Webhook
5. Record mail-domain evidence and status in GCCD

## Key Constraints
- Compute Engine rate/quota awareness (batched, backoff retry)
- Narrow API scopes (least privilege)
- Control workflows over free-for-all automation
- Email extension avoids normal dependency on outbound port 25 from GCP

## Phases

### Phase 0 — Discovery & Design
- Finalise MVP workflows and approval paths
- Define naming/environment model
- Design Sheets data model (VM register + change log)
- Define Drive folder structure and evidence rules
- Document exact Gmail message templates

### Phase 1 — Google Foundation
- Enable APIs, establish OAuth scopes
- Design rate/quota guardrails
- Implement orchestration service skeleton
- Wire Compute Engine + Gmail approval loop
- Wire Sheets write-back from approved actions
- Wire Drive evidence store on completion

### Phase 2 — Thin End-to-End Flow
- Prove one safe VM action end to end
- Confirm evidence creation and register updates
- Maintain local notification fallback where OAuth delegation is unavailable

### Phase 3 — Extension: Managed outbound relay
- Provision `forge-mail-server`
- Apply Postfix relay-only baseline
- Configure SendGrid on 587 with documented fallbacks 465 / 2525
- Add mail-domain and relay evidence handling
- Validate delivery telemetry path

### Phase 4 — Operations Visibility
- Service Health integration
- Status dashboard
- Scheduled reporting (monthly governance packs)
- Relay health / delivery event reporting where justified

### Phase 5 — Governance Hardening
- Exception handling, approval overrides
- Retention rules for exported reports
- Stronger audit views
- Hardening for relay-runbook operations

## Deliverables (MVP)
- solution architecture
- API/security model
- data model for VM register and change log
- workflow catalogue
- MVP backlog
- test scenarios
- rollout plan
- runbook for operations and failure handling

## Deliverables (extension)
- relay VM spec
- mail-domain register model
- event webhook evidence model
- Postfix relay baseline runbook
- SendGrid authentication checklist

## Done Checklist
- [ ] Provision and manage Compute Engine VMs
- [ ] Send and track approval/notification emails
- [ ] Maintain a live asset and change register
- [ ] Store evidence packs and reports
- [ ] Surface Google Cloud service disruptions
- [ ] Provision managed outbound relay VM through GCCD
- [ ] Capture relay-specific evidence and test results
