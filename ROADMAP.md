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

## MVP Scope
1. VM request & approval (Gmail → Compute Engine)
2. VM provisioning & lifecycle control
3. Sheets asset register updates
4. Drive evidence/report output
5. Email incident/maintenance notifications

## Key Constraints
- Compute Engine rate/quota awareness (batched, backoff retry)
- Narrow API scopes (least privilege)
- Control workflows over free-for-all automation

## Phases

### Phase 0 — Discovery & Design (this week)
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

### Phase 2 — Operations Visibility
- Service Health integration
- Status dashboard
- Scheduled reporting (monthly governance packs)

### Phase 3 — Governance Hardening
- Exception handling, approval overrides
- Retention rules for exported reports
- Stronger audit views

## Deliverables (MVP)
- Solution architecture
- API/security model
- Data model for VM register and change log
- Workflow catalogue
- MVP backlog
- Test scenarios
- Rollout plan
- Runbook for operations and failure handling

## Done Checklist
- [ ] Provision and manage Compute Engine VMs
- [ ] Send and track approval/notification emails
- [ ] Maintain a live asset and change register
- [ ] Store evidence packs and reports
- [ ] Surface Google Cloud service disruptions
