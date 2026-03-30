# Phase 2 — Thin End-to-End Flow

## Goal

Deliver one complete workflow: request → confirm → execute VM → poll operation → update Sheets → write Drive evidence → send Gmail result.

## MVP Action Selection

**Start with a safe action:** `start` or `inspect` (non-destructive)

### Selected: Start Instance

**Why:**
- Non-destructive
- Clear success/failure states
- Demonstrates async operation polling
- Useful for maintenance workflows

## End-to-End Flow (Start Instance)

```
1. User selects VM → clicks "Start"
2. System shows confirmation (instance, zone, reason field)
3. User confirms → API call sent to Compute Engine
4. Operation resource returned → polling loop started
5. Poll every 5s until DONE or FAILED
6. On success:
   - Update Sheets register row (status=running, last_action=start, last_action_result=success)
   - Write evidence pack to Drive
   - Send Gmail success notification
7. On failure:
   - Update Sheets register row (status=unknown, last_action_result=failed)
   - Write evidence pack to Drive with failure details
   - Send Gmail failure notification
```

## Technical Requirements

### Compute Engine API

```bash
POST https://compute.googleapis.com/compute/v1/projects/{project}/zones/{zone}/instances/{instance}/start
```

**Response:**
```json
{
  "name": "operation-123",
  "zone": "zones/us-central1-a",
  "operationType": "start",
  "status": "RUNNING"
}
```

### Operation Polling

**Endpoint:**
```bash
GET https://compute.googleapis.com/compute/v1/projects/{project}/zones/{zone}/operations/{operationId}
```

**Poll criteria:**
- `status == "DONE"` → success or failure
- Poll interval: 5s
- Max poll attempts: 60 (5 min timeout)

### Sheets Update

Update row where `instance_name = {instance}`:

| Column | New Value |
|--------|-----------|
| status | running |
| last_action | start |
| last_action_result | success |
| change_reference | operation-123 |

### Evidence Pack (Drive)

**File:** `{instance_name}/20260330-050000-start.md`

**Content:**
```markdown
# Start Instance: {instance_name}
Timestamp: 2026-03-30T05:00:00Z
Action: start
Instance: {instance_name}
Project: {project}
Zone: {zone}
Operation: operation-123
Status: DONE
Reason: {user-provided reason}
Result: success
Link to register row: [Sheets](https://docs.google.com/spreadsheets/d/...)
```

### Gmail Notification

**Recipient:** operator (self)

**Template:**
```
VM {instance_name} started successfully

Project: {project}
Zone: {zone}
Operation: operation-123
Duration: 12s

View register: [Link]
View evidence: [Link]
```

## Acceptance Criteria

- [ ] One VM starts from the tool
- [ ] Operation polled to completion
- [ ] Sheets register updated
- [ ] Evidence pack written to Drive
- [ ] Gmail notification sent

## Next Step

Proceed to Phase 3 — broaden the action set once the thin flow is reliable.
