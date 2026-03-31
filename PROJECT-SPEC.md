# Forge Compute Control Desk — Project Spec

## Project Charter

### Purpose

Create a single internal platform to govern Compute Engine virtual machine operations with clear approvals, recorded evidence, operational visibility, and lightweight reporting.

### Extension purpose

Support selected infrastructure products that are best represented as governed GCP workloads. The current extension is **Forge Email Server**, documented as a **managed outbound relay** product rather than a mailbox platform.

### Objectives

The platform should:

- Provision and manage Compute Engine VMs through API calls
- Send approval and completion emails or local notification fallbacks
- Maintain a spreadsheet-based inventory and change log
- Store evidence and exported reports in Drive or documented local fallback
- Show relevant Google Cloud service health events
- Support extension workloads that need the same governance/evidence model

## In Scope

- Compute Engine API integration
- Gmail API integration for notifications and approvals (local fallback)
- Drive API integration for evidence and exports (local fallback)
- Sheets API integration for inventory and status tracking
- Service Health API integration for external incident visibility
- Dashboard, workflow engine, and audit trail
- Retry/backoff logic for transient failures
- Weekly governance reports
- Extension support for GCP-hosted outbound relay infrastructure

## Out of Scope

- Full cloud cost management platform
- Enterprise CMDB replacement
- Bulk support for every Google Cloud product
- Full ticketing-system replacement
- Broad document-management suite
- Generalised workflow automation for the whole business
- Gmail email notifications via service account (requires OAuth delegation)
- Shared Drive creation (requires enterprise Google Workspace admin privileges)
- Extension assumption of inbound mail hosting, mailbox storage, or public MX by default

## Success Criteria (MVP)

The MVP is successful when:

- [x] A VM request can move from request to approval to execution without manual copy-paste
- [x] Compute Engine changes are reflected in a live register
- [x] Every completed action produces an evidence record (local storage)
- [x] Local notifications are written reliably
- [x] External Google Cloud service incidents can be shown in context
- [x] The system respects API scopes and quota constraints
- [x] Dashboard UI provides VM management interface
- [x] Weekly governance reports generated automatically
- [x] MCP server exposes VM management capabilities

**Note:** Email notifications via Gmail API are not available for service accounts without OAuth delegation. Local notification files are written instead.

## Success Criteria (email extension)

The email extension is successful when:
- [ ] a relay VM can be provisioned through GCCD
- [ ] relay evidence is written alongside VM evidence
- [ ] the Postfix relay profile is documented and reproducible
- [ ] SendGrid-authenticated sending is validated
- [ ] delivery telemetry can be tied back to GCCD evidence or linked records

## Next Steps

- scheduled weekly reports via cron
- email notifications via external SMTP or OAuth delegation
- Service Health API integration
- advanced filtering/search in dashboard
- MCP server integration with OpenClaw
- webhook notifications for external systems
- relay extension implementation after VM-provisioning workflow alignment

## Product Modules

### 1. Compute Orchestration

Performs VM lifecycle actions against Compute Engine and tracks asynchronous operations to completion. Includes retry, backoff, and operation-state tracking.

### 2. Approval and Notification

Sends approval requests, execution outcomes, failure notices, and periodic summaries using Gmail where possible. Falls back to local notification files when service-account limitations apply.

### 3. Evidence Store

Writes change packs, exports, runbooks, and supporting evidence into Drive or a documented local evidence folder.

### 4. Register and Reporting

Uses Sheets as the live operational register for instances, owners, environments, approvals, change dates, and status.

### 5. Service Health Context

Pulls relevant Google Cloud service-health events to distinguish provider-side disruption from local failures.

### 6. Weekly Governance Report

Generates periodic summary output for operator review.

### 7. Extension Workload Model

Supports governed product-specific workloads that sit on top of the same VM/evidence/register foundation.

Current documented extension:
- **Forge Email Server** — GCP-hosted Postfix outbound relay using SendGrid

## Extension boundaries for Forge Email Server

### In scope
- outbound relay VM
- Postfix relay-only profile
- SendGrid SMTP auth and authenticated domain
- delivery telemetry and evidence linkage

### Out of scope
- inbound MX cutover
- mailbox hosting
- IMAP / POP / webmail baseline
- Cloudflare Access in the SMTP path

## Recommended Architecture

### Presentation Layer
- Simple internal dashboard for requests, approvals, inventory, and status

### Control Layer
- Workflow engine
- Orchestration logic
- Approvals logic
- Export/reporting services

### Integration Layer
- Compute Engine, Gmail, Drive, Sheets, Service Health
- SendGrid for relay-backed extension workflows where appropriate
- narrowly scoped credentials
- clear separation of duties

## Key Workflows

### Workflow A: New VM Request
1. request submitted
2. approval requested
3. approved action creates VM
4. result logged in register
5. evidence written

### Workflow B: Start/Stop and Maintenance
1. operator triggers action
2. Compute Engine executes action
3. operation tracked to completion
4. register updated
5. summary recorded / sent

### Workflow C: Exception Visibility
1. Service Health API reports event
2. platform flags incident
3. links event context to affected environment
4. operator sees upstream vs local issue

### Workflow D: Extension Relay Provisioning
1. relay VM requested
2. provisioning action executed via GCCD
3. evidence captured
4. mail-domain status recorded
5. relay config and test evidence linked

## Risks and Controls

### Risk 1: Over-building
Keep Sheets as a register, not a hidden database.

### Risk 2: API Sprawl
Use minimum needed access per integration.

### Risk 3: Orchestration Noise
Handle quotas and async operations sensibly.

### Risk 4: Extension Drift
Do not let product extensions silently redefine the core platform.

**Control:** document extension boundaries explicitly.

### Risk 5: Inaccurate mail assumptions
The relay extension is not an inbox-hosting product.

**Control:** keep outbound relay scope explicit in docs and acceptance criteria.

## Deliverables

- solution architecture
- security and authorisation model
- data model for VM register and change log
- workflow catalogue
- MVP backlog
- test scenarios
- roadmap
- operations runbook
- reporting and evidence model
- extension-specific runbook where applicable

## Recommendation

Build GCCD as the governed control plane for GCP workloads first, then let adjacent infrastructure products plug into that model only when their boundaries are explicit. For the current email extension, that means a **small outbound relay product**, not a sprawling self-hosted mail suite.
