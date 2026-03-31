# Forge Compute Control Desk

A lightweight operations and governance platform for Google Cloud virtual machines, using the Compute Engine API as the action layer and Google Workspace / Enterprise APIs as the workflow, evidence, and reporting layer.

## Overview

Forge Compute Control Desk gives you one place to request, approve, provision, update, monitor, and report on Compute Engine workloads with clear approvals, recorded evidence, operational visibility, and lightweight reporting.

It also now carries a **product extension for managed outbound email relay infrastructure** on GCP.

## Why This Fits Compute Engine

Compute Engine is API-driven but has per-project rate quotas and concurrent-operation limits. That makes a governed workflow platform a better fit than ad hoc scripts scattered across machines and inboxes.

## MVP Scope (core product)

1. **VM request & approval** — local notification-based approval workflow (Gmail deferred to Phase N+1)
2. **VM lifecycle actions** — create, delete, start, stop, restart, inspect, list
3. **Live asset register** — Sheets-based inventory and change log
4. **Evidence storage** — local evidence packs (Drive integration future)
5. **Notifications** — local-first notification files (see STRATEGIC-DECISIONS.md)

## Extension scope: Forge Email Server

The Forge Email Server is now documented as a GCCD extension.
Its validated shape is:

```text
application or internal system → Postfix relay on GCP VM → SendGrid on 587
```

### Extension boundaries
- outbound relay only
- no inbound MX hosting in the baseline
- no mailbox hosting / IMAP / webmail baseline
- Cloudflare Access only for human-facing HTTP applications related to the workflow

## Architecture

| Layer | Service | Purpose |
|-------|---------|---------|
| Execution | Compute Engine API | VM create/start/stop/resize/tag |
| Workflow | Local notifications | Approvals, notifications, digests (Gmail deferred to Phase N+1) |
| Evidence | Local evidence packs / Drive-ready structure | Design docs, runbooks, change records |
| Register | Sheets API | VM inventory, cost tracker, change log |
| Awareness | Service Health API | Google Cloud service events |
| Extension | Postfix + SendGrid | outbound relay for operational/application mail |

## Key Constraints

- Compute Engine rate/quota awareness (batched, backoff retry)
- Narrow API scopes (least privilege)
- Control workflows over free-for-all automation
- For the email extension: no normal design dependence on outbound port 25 from GCP

## Project Status

- **Forge Pipeline**: `project-20260330044222184857`
- **GitHub**: https://github.com/harkers/forge-cloud-control-desk
- **Extension doc**: `EMAIL-SERVER-EXTENSION.md`

## Next Steps

See `ROADMAP.md` for the core plan and the email extension milestones.
