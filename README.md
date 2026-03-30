# Forge Compute Control Desk

A lightweight operations and governance platform for Google Cloud virtual machines, using the Compute Engine API as the action layer and Google Workspace / Enterprise APIs as the workflow, evidence, and reporting layer.

## Overview

Forge Compute Control Desk gives you one place to request, approve, provision, update, monitor, and report on Compute Engine workloads with clear approvals, recorded evidence, operational visibility, and lightweight reporting.

## Why This Fits Compute Engine

Compute Engine is API-driven but has per-project rate quotas and concurrent-operation limits. That makes a governed workflow platform a better fit than ad hoc scripts scattered across machines and inboxes.

## MVP Scope (v1)

1. **VM request & approval** — Gmail-based approval workflow
2. **VM lifecycle actions** — create, start, stop, resize, inspect
3. **Live asset register** — Sheets-based inventory and change log
4. **Evidence storage** — Drive-based implementation packs and runbooks
5. **Notifications** — Gmail for status updates and summaries

## Architecture

| Layer | Service | Purpose |
|-------|---------|---------|
| Execution | Compute Engine API | VM create/start/stop/resize/tag |
| Workflow | Gmail API | Approvals, notifications, digests |
| Evidence | Drive API | Design docs, runbooks, change records |
| Register | Sheets API | VM inventory, cost tracker, change log |
| Awareness | Service Health API | Google Cloud service events |

## Key Constraints

- Compute Engine rate/quota awareness (batched, backoff retry)
- Narrow API scopes (least privilege)
- Control workflows over free-for-all automation

## Project Status

- **Forge Pipeline**: `project-20260330044222184857`
- **GitHub**: https://github.com/harkers/forge-cloud-control-desk

## Next Steps

See `ROADMAP.md` for the 30/60/90 plan and detailed phase breakdown.
