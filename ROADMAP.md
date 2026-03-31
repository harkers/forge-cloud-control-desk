# Forge Cloud Control Desk — Roadmap

## Project Status
- **Forge Pipeline**: `project-20260330044222184857` — `in-progress`
- **GitHub**: https://github.com/harkers/forge-cloud-control-desk
- **Decisions**: GCCD-STR-001 (approved 2026-03-31)

## Vision
Governance platform for Google Compute Engine VM lifecycle, with structured approvals, audit trails, evidence tracking, and team-based extension support.

## Decisions (GCCD-STR-001)
- GCCD identity: **Platform** (team-operated extensions welcome)
- Notifications: **Local-first** (Gmail → Phase N+1)
- Email extension: **Phase 4** (after Service Health proves governance model)
- Titan submission: **Option A only** (local submission; Option B/C are future products)
- Extension operator: **Shared/team** (on-call ownership required)
- Extension retirement: **Required before acceptance** (shutdown path mandatory)

## Architecture
| Layer | Service | Purpose |
|-------|---------|---------|
| Execution | Compute Engine API | VM create/start/stop/resize/tag |
| Workflow | Local notifications | Approval confirmations, digests, alerts |
| Evidence | Drive API | Design docs, runbooks, change records |
| Register | Sheets API | VM inventory, cost tracker, change log |
| Awareness | Service Health API | Google Cloud service events |
| Extension | Postfix + SendGrid | managed outbound email relay (Phase 4) |

## MVP Scope
1. VM request & approval (local notification → Compute Engine)
2. VM provisioning & lifecycle control
3. Sheets asset register updates
4. Drive evidence/report output
5. Local incident/maintenance notifications
6. Team ops model for extensions

## Extension Scope — Forge Email Server
**Phase 4 only** — see EMAIL-SERVER-EXTENSION.md for current status.

1. Provision relay VM through GCCD (Phase 4A)
2. Install Postfix relay-only baseline (Phase 4B)
3. Authenticate sending subdomain in SendGrid (Phase 4C)
4. Capture delivery telemetry through Event Webhook (Phase 4D)
5. Record mail-domain evidence and status in GCCD (Phase 4E)

**Note:** Titan submission = Option A only (local submission from relay VM, or direct SendGrid). Options B and C are future products requiring new approval.

## Key Constraints
- Compute Engine rate/quota awareness (batched, backoff retry)
- Narrow API scopes (least privilege)
- Control workflows over free-for-all automation
- Email extension avoids dependency on outbound port 25 from GCP
- Extension retirement plan required before any extension is accepted

## Phases

### Phase 0 — Discovery & Design
- Finalise MVP workflows and approval paths
- Define naming/environment model
- Design Sheets data model (VM register + change log)
- Define Drive folder structure and evidence rules
- Document local notification templates
- Establish team ops model for extensions

### Phase 1 — Google Foundation
- Enable APIs, establish OAuth scopes
- Design rate/quota guardrails
- Implement orchestration service skeleton
- Wire Compute Engine + local notification loop
- Wire Sheets write-back from approved actions
- Wire Drive evidence store on completion

### Phase 2 — Thin End-to-End Flow
- Prove one safe VM action end to end (start/stop/restart) ✅
- Create instance workflow with full evidence trail ✅
- Delete instance workflow for cost-safe cleanup ✅
- Confirm evidence creation and register updates ✅
- Validate local notification delivery ✅
- Round-trip test path: create → inspect → delete ✅
- Daily digest workflow (evidence-scanning governance summary) ✅
- Document team ops runbook

### Phase 3 — Operations Visibility
- Service Health integration
- Status dashboard
- Scheduled reporting (monthly governance packs)
- Relay health / delivery event reporting (if Phase 4A is active)

### Phase 4 — Extension: Managed Outbound Relay (email)
**Begins only after Phase 3 proves cross-product governance.**

- Phase 4A — Provision `forge-mail-server` through GCCD
- Phase 4B — Apply Postfix relay-only baseline
- Phase 4C — Authenticate sending subdomain in SendGrid
- Phase 4D — Capture delivery telemetry through Event Webhook
- Phase 4E — Record mail-domain evidence and status in GCCD

### Phase 5 — Governance Hardening
- Exception handling, approval overrides
- Retention rules for exported reports
- Stronger audit views
- Extension retirement runbooks
- Hardening for relay-runbook operations

## Phase N+1 — Gmail Integration
- Gmail approval loop (when OAuth delegation is validated)
- Alternative email provider evaluation if OAuth remains blocked

## Deliverables (MVP)
- solution architecture
- API/security model
- data model for VM register and change log
- workflow catalogue
- MVP backlog
- test scenarios
- rollout plan
- runbook for operations and failure handling
- team ops model for extensions

## Deliverables (extension — Phase 4)
- relay VM spec
- mail-domain register model
- event webhook evidence model
- Postfix relay baseline runbook
- SendGrid authentication checklist
- extension retirement plan (mandatory)

## Extension Acceptance Gate
Before any extension is accepted into GCCD, the following must be defined:
- Named on-call owner (team)
- Handover procedure
- Runbook ownership
- Retirement / shutdown path (mandatory)

## Done Checklist
- [ ] Provision and manage Compute Engine VMs
- [ ] Send and track local approval/notification messages
- [ ] Maintain a live asset and change register
- [ ] Store evidence packs and reports
- [ ] Surface Google Cloud service disruptions
- [ ] Team ops model operational for extensions
- [ ] Extension retirement plans documented before acceptance
- [ ] (Phase 4) Provision managed outbound relay VM through GCCD
- [ ] (Phase 4) Capture relay-specific evidence and test results
