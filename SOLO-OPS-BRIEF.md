# Forge Compute Control Desk — Solo Operating Model

## Core Design

This is **one operator's cloud control desk** — not a shared CAB or enterprise CMDB.

## Solo Governance Rules

1. **No destructive action without confirmation**
2. **No create action without register entry**
3. **No "success" state until operation resource confirms completion**
4. **No important action without evidence written to Drive**
5. **No silent failures; every failure generates a visible alert**

## Product Scope (MVP)

| Feature | Status |
|---------|--------|
| VM register (Sheets) | ✅ In |
| VM actions (create/start/stop/restart/inspect) | ✅ In |
| Action logging | ✅ In |
| Evidence records (Drive) | ✅ In |
| Gmail confirmations/notifications | ✅ In |
| Service Health context | 🚫 Phase 2 |

## MVP Control Flow

```
User Action → Confirmation → Execute VM → Poll Operation → Update Sheets → Write Drive Evidence → Send Gmail Result
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
**Gmail use cases:**
- Action confirmation (high-risk changes)
- Success/failure notifications
- Daily digest of VM actions
- Weekly governance summary

**Notification classes:**
- Low risk: no confirmation
- Medium risk: on-screen confirmation only
- High risk: on-screen + Gmail confirmation receipt

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
- **Decision:** Phase 2 unless already essential

## Phase Plan

### Phase 1: Design & Foundation
**Goal:** Freeze MVP, enable APIs, define auth model, define register schema, define evidence structure

**Outputs:**
- Architecture note
- Data model
- Action catalogue
- Confirmation model
- API enablement checklist

**Go/No-Go:** Know exactly which actions are in scope and where outputs will be stored

### Phase 2: Thin End-to-End Flow
**Goal:** Deliver one complete workflow: request → confirm → execute VM → poll operation → update Sheets → write Drive evidence → send Gmail result

**Go/No-Go:** One action works end to end reliably

### Phase 3: Broaden Action Set
**Goal:** Add remaining VM lifecycle actions and build operator dashboard

**Outputs:**
- Core action library
- Register views
- Action history view
- Failure handling
- Digest emails

**Go/No-Go:** Tool is useful enough to replace manual repetitive admin work

### Phase 4: Operational Hardening
**Goal:** Add resilience and hygiene

**Outputs:**
- Retry and backoff logic
- Quota-aware scheduling
- Better failure messages
- Weekly governance report
- Cleanup and retention rules
- Optional Service Health integration

**Go/No-Go:** Trust it enough to use regularly without clutching your keyboard

## Acceptance Criteria (MVP Done)

- [ ] Execute at least one Compute Engine action from the tool and track to completion
- [ ] Result written to Sheets successfully
- [ ] Evidence record stored in Drive successfully
- [ ] Gmail notification sent successfully
- [ ] Action log distinguishes requested/in-progress/succeeded/failed states
- [ ] Quota/concurrent-operation failures handled cleanly

## Recommended MVP Backlog (Build Order)

1. API foundation and auth
2. Sheets register structure
3. Drive evidence structure
4. One safe VM action (start or inspect)
5. Operation tracking
6. Gmail success/failure notification
7. Stop and restart
8. Create instance
9. Daily digest
10. Service Health integration

## Architecture

| Layer | Responsibility |
|-------|----------------|
| Presentation | Dashboard for requests, approvals, inventory, status |
| Control | Workflow engine, orchestration, approvals, exports |
| Integration | Compute Engine, Gmail, Drive, Sheets, Service Health (narrow scopes) |

## Solo Control Model

| Action Type | Confirmation | Logging |
|-------------|--------------|---------|
| Read/inspect | None | Internal only |
| Start/stop/restart | On-screen | Sheets + Drive |
| Create | On-screen + Gmail | Sheets + Drive + Gmail receipt |

## Recommendation

Build this as a solo operator's cloud control desk:

- **Compute Engine** as the execution layer
- **Sheets** as the live register
- **Drive** as the evidence store
- **Gmail** as the confirmation and notification layer
- **Service Health** as optional phase-two context

That gives you a practical, low-friction platform with real auditability, without pretending you are running an enterprise change board from your kitchen table.
