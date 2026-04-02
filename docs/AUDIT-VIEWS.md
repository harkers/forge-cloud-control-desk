# GCCD Audit Views

**Document:** GCCD-OPS-005  
**Created:** 2026-04-02  
**Status:** Operational  

---

## Overview

Enhanced audit views provide visibility into GCCD operations:
- Searchable operation log
- Cost analysis by VM
- Failed operation tracking
- SLA compliance metrics

---

## Commands

### Recent Operations

```bash
cd /home/stu/.openclaw/workspace/projects/forge-cloud-control-desk
python3 -m src.core.audit_view recent [days]
```

**Example:**
```
Recent Operations (last 7 days)
================================================================================

⏳ 2026-04-02 22:19 | delete     | forge-rt-225036      | completed 
⏳ 2026-04-02 22:19 | delete     | forge-rt-225452      | completed 
⏳ 2026-04-02 20:48 | health_check | unknown              | completed 

Total: 9 operations
```

---

### Cost Analysis

```bash
python3 -m src.core.audit_view costs
```

**Shows:**
- Creates/starts/stops per VM
- VM status (Active/Deleted)
- Activity summary

---

### Failed Operations

```bash
python3 -m src.core.audit_view failed [days]
```

**Output:**
```
Failed Operations (last 7 days)
================================================================================
No failed operations in the specified period ✅
```

---

### SLA Metrics

```bash
python3 -m src.core.audit_view sla [days]
```

**Output:**
```json
{
  "period_days": 30,
  "total_operations": 9,
  "successful": 0,
  "failed": 0,
  "success_rate": 0.0,
  "operations_by_type": {
    "delete": 5,
    "health_check": 4
  }
}
```

---

### Search Operations

```bash
python3 -m src.core.audit_view search <query>
```

**Example:**
```bash
python3 -m src.core.audit_view search forge-mail
```

---

## Python API

```python
from src.core.audit_view import AuditView

audit = AuditView()

# Load operations
operations = audit.load_operations(days=30)

# Search
results = audit.search_operations("forge-mail", days=30)

# SLA metrics
metrics = audit.get_sla_metrics(days=30)
print(f"Success rate: {metrics['success_rate']}%")

# Cost analysis
print(audit.show_cost_analysis())
```

---

## Integration Points

### Daily Digest

Add to `daily_digest.py`:
```python
from src.core.audit_view import AuditView

audit = AuditView()
metrics = audit.get_sla_metrics(days=1)

return f"""
## Operations (24h)
- Total: {metrics['total_operations']}
- Success rate: {metrics['success_rate']}%
- By type: {metrics['operations_by_type']}
"""
```

### Dashboard

Add to main dashboard:
- Recent operations table
- SLA gauge
- Failed operations alert

---

## Data Sources

Audit view scans:
- `data/evidence/vm_operations/*.md`
- `data/evidence/inspections/*.md`
- `data/evidence/service_health/*.md`

Parses timestamps, VM names, operation types from evidence files.

---

*Document created as part of GCCD-001 Phase 5 — 2026-04-02*
