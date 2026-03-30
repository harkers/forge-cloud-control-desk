# Phase 1 — Design & Foundation

## Goal

Freeze the MVP, enable APIs, define the auth model, define the register schema, define the evidence structure.

## Deliverables

- [ ] Architecture note
- [ ] Data model
- [ ] Action catalogue
- [ ] Confirmation model
- [ ] API enablement checklist

## Architecture Note

### Target Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | Simple internal dashboard | Requests, inventory, status |
| Control Layer | Python/Node.js service | Workflow engine, orchestration |
| Integration Layer | Google Cloud APIs | Compute Engine, Gmail, Drive, Sheets, Service Health |

### Auth Model

**Recommendation:** Separate service identities per integration area (eventually), but for solo MVP a simpler model is acceptable if scopes stay narrow.

### Environment Model

| Environment | Naming Convention | Zone Strategy |
|-------------|-------------------|---------------|
| dev | `{env}-{service}-{id}` | Single region/zone for MVP |
| prod | `{env}-{service}-{id}` | Multi-zone awareness later |

### API Enablement Checklist

| API | Status | Scopes Required |
|-----|--------|-----------------|
| Compute Engine API | `pending` | `compute.roles.viewer`, `compute.instances.create`, `compute.instances.update` |
| Gmail API | `pending` | `gmail.send`, `gmail.compose` |
| Drive API | `pending` | `drive.file`, `drive.create` |
| Sheets API | `pending` | `spreadsheets`, `drive.file` |
| Service Health API | `pending` | `cloud-platform` |

### Register Schema (Sheets)

**Tab: VM Register**

| Column | Type | Description |
|--------|------|-------------|
| instance_name | text | VM instance name |
| project | text | GCP project ID |
| zone | text | Compute zone |
| machine_type | text | e.g., `e2-medium` |
| owner | text | Operator/owner |
| purpose | text | Business purpose |
| environment | text | dev/prod/staging |
| status | text | running/stopped/failed |
| last_action | text | create/start/stop/restart |
| last_action_result | text | success/pending/failed |
| change_reference | text | Action ID or timestamp |
| evidence_link | text | Drive evidence folder URL |
| notes | text | Free-text notes |

### Evidence Structure (Drive)

**Folder: `/vm-evidence/`**

| Subfolder | Contents |
|-----------|----------|
| `YYYY-MM/` | Monthly evidence packs |
| `{instance_name}/` | Per-VM evidence subfolder |
| `YYYYMMDD-HHMMSS-{action}.md` | Individual evidence records |

### Evidence Pack Template

```yaml
timestamp: 2026-03-30T05:00:00Z
requested_action: start
target_vm:
  instance_name: my-vm
  project: my-project
  zone: us-central1-a
parameters:
  - key: reason
    value: "scheduled maintenance"
api_response_summary: "Operation started"
final_operation_result: "DONE"
register_row_link: "https://docs.google.com/spreadsheets/d/..."
operator_identity: "stuharker@gmail.com"
notes: "Scheduled weekly restart"
```

### Confirmation Model

| Action | Confirmation Required |
|--------|----------------------|
| Read/inspect | None |
| Start/stop/restart | On-screen |
| Create | On-screen + Gmail receipt |

## Go/No-Go Checkpoint

You know exactly:
- Which actions are in scope
- Where every output will be stored (Sheets, Drive, Gmail)
- How confirmation works
- What the register schema looks like

## Next Step

Proceed to Phase 2 when this is signed off — build the thin end-to-end flow for one safe VM action (start or inspect).
