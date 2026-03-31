# Forge Compute Control Desk — Operating Model

**Record:** GCCD-STR-001  
**Date:** 2026-03-31  
**Status:** ACTIVE — reflects Decisions 1, 4, 5, 6  

## Core Design

GCCD is a **team-operated governance platform**. Extensions are operated by named teams with on-call ownership. Solo operator mode is not the default assumption.

**Platform rule:** GCCD is a platform. Extensions are team-operated. Solo operator mode is not the default assumption.

## Team Governance Rules

1. **No destructive action without confirmation**
2. **No create action without register entry**
3. **No "success" state until operation resource confirms completion**
4. **No important action without evidence written to Drive**
5. **No silent failures; every failure generates a visible alert**
6. **Extensions require named on-call owner, handover procedure, and documented retirement path**

## Extension Acceptance Gate

Before any extension is accepted into GCCD, the following must be defined:

- Named on-call owner (team)
- Handover procedure
- Runbook ownership
- Retirement / shutdown path (mandatory — Decision 6)

## Notification Model

Gmail notifications are **not available in MVP baseline** (OAuth delegation unresolved).

Local notification files are written as the default mechanism. Gmail is Phase N+1.

## Product Scope (MVP)

| Feature | Status |
|---------|--------|
| VM register (Sheets) | ✅ In |
| VM actions (create/start/stop/restart/inspect) | ✅ In |
| Action logging | ✅ In |
| Evidence records (Drive) | ✅ In |
| Local confirmations/notifications | ✅ In |
| Service Health context | 🚫 Phase 3 |

## MVP Control Flow

```
User Action → Confirmation → Execute VM → Poll Operation → Update Sheets → Write Drive Evidence → Send Local Notification
```

## Workstreams

### Workstream 1: Google Foundation
- Project and API inventory
- Enabled APIs
- Auth model (separate identities per integration area recommended)
- Environment naming convention
- Region/zone strategy

### Workstream 2: Data Model & Register
**Sheets schema:**
- instance name, project, zone, machine type
- owner, purpose, environment
- status, last action, last action result
- change reference, evidence link, notes

**Design decision:** Single spreadsheet, multiple tabs

### Workstream 3: Compute Orchestration
**MVP actions:**
- create instance
- start instance
- stop instance
- restart instance
- inspect instance
- list instances

**Key constraint:** Compute Engine uses async operations — must poll completion

### Workstream 4: Notification & Confirmation
**Local notification use cases:**
- Action confirmation (high-risk changes)
- Success/failure notifications
- Daily digest of VM actions
- Weekly governance summary

**Notification classes:**
- Low risk: no confirmation
- Medium risk: on-screen confirmation only
- High risk: on-screen + local notification receipt

### Workstream 5: Evidence & Reporting
**Evidence pack for important changes:**
- timestamp
- requested action
- target VM
- parameters
- API response summary
- final operation result
- link to register row
- operator identity
- notes

**Design decision:** Monthly folders with consistent naming

### Workstream 6: Service Health
- Show project-relevant Google Cloud disruption events
- **Decision:** Phase 3 unless already essential

## Phase Plan

### Phase 1: Design & Foundation
**Goal:** Freeze MVP, enable APIs, define auth model, define register schema, define evidence structure

**Outputs:**
- Architecture note
- Data model
- Action catalogue
- Confirmation model
- API enablement checklist
- Team ops model

**Go/No-Go:** Know exactly which actions are in scope and where outputs will be stored

### Phase 2: Thin End-to-End Flow
**Goal:** Deliver one complete workflow: request → confirm → execute VM → poll operation → update Sheets → write Drive evidence → local notification

**Go/No-Go:** One action works end to end reliably

### Phase 3: Operations Visibility
**Goal:** Add Service Health integration, dashboard, and reporting

**Outputs:**
- Service Health context
- Status dashboard
- Scheduled reporting (monthly governance packs)
- Team ops runbook

**Go/No-Go:** Tool is useful enough to replace manual repetitive admin work

### Phase 4: Extension — Managed Outbound Relay (email)
**Begins only after Phase 3 proves cross-product governance.**

See EMAIL-SERVER-EXTENSION.md.

### Phase 5: Governance Hardening
**Goal:** Add resilience and hygiene

**Outputs:**
- Retry and backoff logic
- Quota-aware scheduling
- Better failure messages
- Weekly governance report
- Extension retirement runbooks
- Cleanup and retention rules

**Go/No-Go:** Trust it enough to use regularly without clutching your keyboard

## Acceptance Criteria (MVP Done)

- [ ] Execute at least one Compute Engine action from the tool and track to completion
- [ ] Result written to Sheets successfully
- [ ] Evidence record stored in Drive successfully
- [ ] Local notification written successfully
- [ ] Action log distinguishes requested/in-progress/succeeded/failed states
- [ ] Quota/concurrent-operation failures handled cleanly

## Recommended MVP Backlog (Build Order)

1. API foundation and auth
2. Sheets register structure
3. Drive evidence structure
4. One safe VM action (start or inspect)
5. Operation tracking
6. Local success/failure notification
7. Stop and restart
8. Create instance
9. Daily digest
10. Service Health integration (Phase 3)

## Architecture

| Layer | Responsibility |
|-------|----------------|
| Presentation | Dashboard for requests, approvals, inventory, status |
| Control | Workflow engine, orchestration, approvals, exports |
| Integration | Compute Engine, Drive, Sheets, Service Health (narrow scopes) |

## Team Control Model

| Action Type | Confirmation | Logging |
|-------------|--------------|---------|
| Read/inspect | None | Internal only |
| Start/stop/restart | On-screen | Sheets + Drive |
| Create | On-screen + local notification | Sheets + Drive + notification receipt |

## Recommendation

GCCD is built as a team-operated governance platform:

- **Compute Engine** as the execution layer
- **Sheets** as the live register
- **Drive** as the evidence store
- **Local notifications** as the baseline confirmation mechanism
- **Service Health** as Phase 3 context

Extensions are welcome but must meet the team ops gate: named owner, handover procedure, retirement path.
