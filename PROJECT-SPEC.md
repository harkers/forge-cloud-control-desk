# Forge Compute Control Desk — Project Spec

## Project Charter

### Purpose

Create a single internal platform to govern Compute Engine virtual machine operations with clear approvals, recorded evidence, operational visibility, and lightweight reporting.

### Objectives

The platform should:

- Provision and manage Compute Engine VMs through API calls
- Send approval and completion emails
- Maintain a spreadsheet-based inventory and change log
- Store evidence and exported reports in Drive
- Show relevant Google Cloud service health events

## In Scope

- Compute Engine API integration
- Gmail API integration for notifications and approvals
- Drive API integration for evidence and exports
- Sheets API integration for inventory and status tracking
- Service Health API integration for external incident visibility
- Dashboard, workflow engine, and audit trail

## Out of Scope

- Full cloud cost management platform
- Enterprise CMDB replacement
- Bulk support for every Google Cloud product
- Full ticketing-system replacement
- Broad document-management suite
- Generalised workflow automation for the whole business

## Success Criteria (MVP)

The MVP is successful when:

- [ ] A VM request can move from request to approval to execution without manual copy-paste
- [ ] Compute Engine changes are reflected in a live register
- [ ] Every completed action produces an evidence record
- [ ] Email approvals and status updates work reliably
- [ ] External Google Cloud service incidents can be shown in context
- [ ] The system respects API scopes and quota constraints

## Product Modules

### 1. Compute Orchestration

Performs VM lifecycle actions against Compute Engine and tracks asynchronous operations to completion. Includes retry, backoff, and operation-state tracking.

### 2. Approval and Notification

Sends approval requests, execution outcomes, failure notices, and periodic summaries using Gmail. Supports both direct send and draft-based send patterns.

### 3. Evidence Store

Writes change packs, exports, runbooks, and supporting evidence into Drive. Uses Drive API v3.

### 4. Register and Reporting

Uses Sheets as the live operational register for instances, owners, environments, approvals, change dates, and status. Supports value reads/writes and formatting.

### 5. Service Health Context

Pulls relevant Google Cloud service-health events to distinguish provider-side disruption from local failures.

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
- Narrowly scoped service credentials
- Clear separation of duties

## Key Workflows

### Workflow A: New VM Request
1. Request submitted
2. Approval requested by email
3. Approved action creates VM
4. Result logged in Sheets
5. Evidence pack stored in Drive

### Workflow B: Start/Stop and Maintenance
1. Operator triggers action (manual or scheduled)
2. Compute Engine executes action
3. Operation tracked to completion
4. Register updated
5. Summary emailed

### Workflow C: Exception Visibility
1. Service Health API reports event
2. Platform flags incident
3. Links event context to affected environment
4. Operator sees upstream vs local issue

### Workflow D: Monthly Governance Pack
1. Export VM inventory, changes, and events
2. Store in Drive
3. Email monthly summary to stakeholders

## 30/60/90 Roadmap

### First 30 Days
- Define operating model, data model, MVP workflows
- Enable required APIs
- Agree auth model and scopes
- Define Sheets register structure
- Define Drive evidence structure
- Deliver thin prototype: request → approval → VM action → register update
- Include quota awareness and error-handling patterns

### By Day 60
- Deliver working MVP
- Add Gmail notifications
- Add Drive evidence generation
- Add Sheets-based reporting
- Add operation history
- Add role-based approvals
- Include async Compute Engine handling
- Include failure states and retries
- Add basic dashboard (active requests, recent changes, VM inventory)

### By Day 90
- Add Service Health API context
- Add scheduled reports
- Add exception dashboards
- Add audit views
- Tighten scopes
- Add quota monitoring
- Decide on event-driven enhancements (Gmail push notifications, Workspace events)

## Risks and Controls

### Risk 1: Over-building
Sheets is excellent as a pragmatic register, but should stay a register — not become your accidental transactional database with Stockholm syndrome.

**Control**: Strict MVP scope, phase gates, clear out-of-scope boundaries.

### Risk 2: API Sprawl
Use minimum needed access per integration — no broad “god mode” credentials.

**Control**: Narrow-scoped credentials, separation of duties, explicit scope documentation.

### Risk 3: Orchestration Noise
Compute Engine rate quotas and concurrent operation limits mean the platform must queue, batch, and retry sensibly.

**Control**: Backoff strategy, operation queuing, rate-aware scheduling.

### Risk 4: Document Clutter
Drive is a good evidence store only if naming, foldering, retention, and ownership are defined early.

**Control**: Early folder structure, naming conventions, retention rules, ownership tags.

## Deliverables

- Solution architecture
- Security and authorisation model
- Data model for VM register and change log
- Workflow catalogue
- MVP backlog
- Test scenarios
- 30/60/90 roadmap
- Operations runbook
- Reporting and evidence model

## Recommendation

Build this as a VM governance and operations desk with a very disciplined MVP. Compute Engine should be the execution layer. Gmail should handle approvals and notifications. Drive should hold evidence. Sheets should be the live register. Service Health should provide upstream context. That is a coherent product, not just a shopping basket of APIs.
