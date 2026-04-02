# Exception Handling Runbook

**Document:** GCCD-OPS-004  
**Created:** 2026-04-02  
**Status:** Operational  

---

## Overview

This runbook describes GCCD's exception handling framework:
- Retry logic with exponential backoff
- Circuit breaker pattern
- Error classification
- Manual override system

---

## Error Categories

| Category | Description | Action |
|----------|-------------|--------|
| **TRANSIENT** | Network timeout, connection error | Retry with backoff |
| **PERMANENT** | Invalid credentials, permission denied | Fail immediately |
| **RATE_LIMIT** | Too many requests, throttling | Extended backoff |
| **QUOTA_EXCEEDED** | Resource limits hit | Wait or escalate |
| **UNKNOWN** | Uncategorized | Treat as transient |

---

## Retry Behavior

### Default Settings
- **Max retries:** 3
- **Base delay:** 1 second
- **Max delay:** 60 seconds
- **Backoff:** Exponential (1, 2, 4, 8... seconds)

### Retry Outcomes

**Success on retry:**
```
Attempt 1/4 failed: Connection timeout
Retrying in 1s...
Attempt 2/4 failed: Connection timeout
Retrying in 2s...
Attempt 3/4 succeeded!
```

**Permanent error (no retry):**
```
Permanent error on create_instance: Permission denied
GCCDException: Permanent error in create_instance
```

**All retries exhausted:**
```
Attempt 1/4 failed: Connection timeout
Retrying in 1s...
Attempt 2/4 failed: Connection timeout
Retrying in 2s...
Attempt 3/4 failed: Connection timeout
Retrying in 4s...
Attempt 4/4 failed: Connection timeout
GCCDException: All 4 attempts failed for create_instance
```

---

## Circuit Breaker

### States

**CLOSED:** Normal operation, requests pass through
**OPEN:** Too many failures, requests blocked
**HALF_OPEN:** Testing recovery after timeout

### Configuration

```python
from src.core.exception_handler import CircuitBreaker

cb = CircuitBreaker(
    failure_threshold=5,      # Open after 5 failures
    recovery_timeout=300      # Try recovery after 5 minutes
)
```

### Usage

```python
from src.core.exception_handler import with_retry, default_circuit_breaker

@with_retry(max_retries=3, circuit_breaker=default_circuit_breaker)
def create_instance(name: str):
    # GCP API call
    pass
```

### When Circuit Opens

```
Circuit breaker: OPEN after 5 failures
GCCDException: Circuit breaker OPEN for create_instance — too many failures
```

**Action:** Wait 5 minutes, then system will try HALF_OPEN state

---

## Manual Override

### When to Use

- Operation stuck for >30 minutes
- Emergency action needed
- Retry logic not appropriate

### Requesting Override

```python
from src.core.exception_handler import manual_override

# Request override
manual_override.request_override(
    operation_id="create-forge-test-20260402",
    reason="Emergency VM needed for incident response"
)
# Output: Override requested: data/overrides/override_create-forge...
#         Operation will proceed when approved
```

### Approving Override

```bash
# As GCCD operator
cd /home/stu/.openclaw/workspace/projects/forge-cloud-control-desk

# View pending overrides
ls -la data/overrides/

# Approve (edit file or use script)
python3 -c "
from src.core.exception_handler import manual_override
manual_override.approve_override(
    operation_id='create-forge-test-20260402',
    approver='operator-name'
)
"
```

### In Workflow Code

```python
def create_instance_workflow(name: str, reason: str):
    operation_id = f"create-{name}-{datetime.now():%Y%m%d%H%M%S}"
    
    # Check for approved override
    if manual_override.check_override(operation_id):
        print(f"Override approved for {operation_id}, proceeding")
        return execute_without_retry(name)
    
    # Normal retry logic
    return with_retry(max_retries=3)(create_instance)(name)
```

---

## Error Logging

All errors are logged to `data/evidence/errors/`:

```python
from src.core.exception_handler import log_error

try:
    risky_operation()
except Exception as e:
    error_file = log_error(e, "risky_operation")
    # Output: Error logged: data/evidence/errors/error_risky_operation_2026-04-02T22-30-00.json
```

### Error File Format

```json
{
  "timestamp": "2026-04-02T22:30:00",
  "operation": "risky_operation",
  "error_type": "ConnectionError",
  "error_message": "Connection timeout",
  "category": "transient",
  "traceback": "..."
}
```

---

## Troubleshooting

### Operation Keeps Failing

1. **Check error category:**
   ```bash
   cat data/evidence/errors/error_*.json | jq '.category'
   ```

2. **If PERMANENT:** Fix root cause (credentials, permissions)

3. **If TRANSIENT:** May resolve on its own, or check GCP status

4. **If RATE_LIMIT:** Reduce operation frequency

### Circuit Breaker Stuck Open

1. **Check last failure time:**
   ```python
   from src.core.exception_handler import default_circuit_breaker
   print(f"Last failure: {default_circuit_breaker.last_failure_time}")
   print(f"Failures: {default_circuit_breaker.failures}")
   ```

2. **Manual reset:**
   ```python
   default_circuit_breaker.state = "CLOSED"
   default_circuit_breaker.failures = 0
   ```

3. **Or wait for automatic recovery** (5 minutes default)

### Override Not Working

1. **Check file exists:**
   ```bash
   ls -la data/overrides/override_*
   ```

2. **Verify status is "approved":**
   ```bash
   cat data/overrides/override_* | jq '.status'
   ```

3. **Check operation_id matches exactly**

---

## Best Practices

1. **Use @with_retry for all external API calls**
2. **Log errors immediately** for troubleshooting
3. **Don't override unless necessary** — defeats governance
4. **Monitor circuit breaker state** — indicates systemic issues
5. **Classify errors properly** — helps with alerting

---

## Integration Points

### Daily Digest

Include error summary:
```
## Errors (24h)
- Total: 12
- Transient: 10 (resolved via retry)
- Permanent: 2 (requires attention)
- Circuit breaker: CLOSED
```

### Dashboard

Add error panel to main dashboard:
- Error rate graph
- Circuit breaker status
- Recent failures table

---

*Document created as part of GCCD-001 Phase 5 — 2026-04-02*
