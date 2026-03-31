# Phase 1 — Design & Foundation

## Goal

Freeze the MVP, enable APIs, define the auth model, define the register schema, and define the evidence structure.

## Deliverables

- [ ] architecture note
- [ ] data model
- [ ] action catalogue
- [ ] confirmation model
- [ ] API enablement checklist
- [ ] extension-boundary note for governed product add-ons

## Architecture Note

### Target Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | Simple internal dashboard | Requests, inventory, status |
| Control Layer | Python service | Workflow engine, orchestration |
| Integration Layer | Google Cloud APIs | Compute Engine, Gmail, Drive, Sheets, Service Health |
| Extension integration | product-specific adapters | bind selected workloads into the same register/evidence model |

### Auth Model

Separate service identities per integration area is still the preferred direction. For solo MVP, simplified credentials are acceptable if scopes stay narrow and documented.

### Environment Model

| Environment | Naming Convention | Zone Strategy |
|-------------|-------------------|---------------|
| dev | `{env}-{service}-{id}` | single region/zone for MVP |
| prod | `{env}-{service}-{id}` | multi-zone awareness later |

### API Enablement Checklist

| API | Status | Notes |
|-----|--------|-------|
| Compute Engine API | baseline in use | VM lifecycle actions |
| Gmail API | partial / constrained | service-account limitations require fallback handling |
| Drive API | partial / constrained | local fallback documented where needed |
| Sheets API | baseline in use | live operational register |
| Service Health API | later phase | upstream context |

## Register Schema (Sheets)

### Tab: VM Register

| Column | Type | Description |
|--------|------|-------------|
| instance_name | text | VM instance name |
| project | text | GCP project ID |
| zone | text | Compute zone |
| machine_type | text | instance type |
| owner | text | operator / owner |
| purpose | text | business purpose |
| environment | text | dev/prod/staging |
| status | text | running/stopped/failed |
| last_action | text | create/start/stop/restart |
| last_action_result | text | success/pending/failed |
| change_reference | text | action ID or timestamp |
| evidence_link | text | evidence folder URL or path |
| notes | text | free-text notes |

### Extension tab: Mail Domains

This tab is for the Forge Email Server extension only.

| Column | Type | Description |
|--------|------|-------------|
| domain | text | sending domain / subdomain |
| relay_vm | text | relay VM name |
| relay_provider | text | SendGrid |
| relay_port_primary | number | 587 |
| relay_port_fallbacks | text | `465,2525` |
| authenticated_domain_status | text | pending / verified / failed |
| dmarc_policy | text | none / quarantine / reject |
| event_webhook_status | text | disabled / enabled / verified |
| evidence_link | text | evidence URL/path |
| notes | text | operational notes |

## Evidence Structure

### Core evidence

```text
/vm-evidence/
  YYYY-MM/
    {instance_name}/
      YYYYMMDD-HHMMSS-{action}.md
```

### Extension evidence (mail relay)

```text
/mail-evidence/
  {domain-or-subdomain}/
    relay-config/
    sendgrid-auth/
    webhook/
    validation/
```

## Evidence Pack Template

```yaml
timestamp: 2026-03-31T00:00:00Z
requested_action: create
target_vm:
  instance_name: forge-mail-server
  project: 301823798218
  zone: europe-west2-b
parameters:
  - key: purpose
    value: outbound relay
api_response_summary: operation started
final_operation_result: DONE
register_row_link: https://docs.google.com/...
operator_identity: stuart.harker@orderededge.co.uk
notes: relay extension provisioned via GCCD
```

## Confirmation Model

| Action | Confirmation Required |
|--------|----------------------|
| Read/inspect | none |
| Start/stop/restart | on-screen |
| Create VM | on-screen + evidence |
| Provision relay extension | on-screen + evidence |
| Destructive extension changes | explicit confirmation |

## Extension boundary rule

A governed extension must state:
- what the product actually is
- what is explicitly out of scope
- what evidence it adds to GCCD
- whether it changes the register schema

The Forge Email Server extension passes this rule only as an **outbound relay** product.

## Go/No-Go Checkpoint

You know exactly:
- which actions are in scope
- where every output will be stored
- how confirmation works
- what the register schema looks like
- how extension evidence will be separated from core VM evidence

## Next Step

Proceed when the thin end-to-end flow is stable and the extension workload can inherit the same evidence discipline without redefining the core platform.
