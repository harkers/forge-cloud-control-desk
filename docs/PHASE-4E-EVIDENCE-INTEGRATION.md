# Phase 4E — Evidence Integration

**Document:** GCCD-PH4E-001  
**Created:** 2026-04-02  
**Status:** In Progress  
**Parent:** EMAIL-SERVER-EXTENSION.md  
**Depends:** Phase 4D (Event Webhook operational)  

---

## Overview

Phase 4E integrates mail event evidence into the GCCD governance framework:
- Correlate mail events with GCCD operations
- Build delivery dashboard
- Add cost tracking per email sent
- Create operational reports

This completes the email extension's evidence trail.

---

## Deliverables

### 1. Mail Event Dashboard
Real-time view of email delivery telemetry.

**File:** `src/mail/dashboard.py`
- Displays recent mail events
- Shows delivery success/failure rates
- Alerts on bounces and failures

### 2. Cost Tracking
Track email volume and estimate costs.

**Integration:**
- Count events per day
- Estimate SendGrid usage
- Include in governance reports

### 3. Evidence Integration
Link mail events to GCCD operations.

**Approach:**
- Parse `custom_args` from events
- Store correlation in Sheets register
- Include in evidence packs

### 4. Operational Reports
Weekly/monthly mail delivery reports.

**Output:**
- Markdown evidence files
- Dashboard visualization
- Spreadsheet summaries

---

## Implementation

### Mail Dashboard

```python
"""GCCD Mail Extension — Delivery Dashboard."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

from flask import Flask, render_template, jsonify

app = Flask(__name__)

EVIDENCE_DIR = Path(__file__).parent.parent.parent / "data" / "evidence" / "mail-events"


def load_recent_events(hours=24):
    """Load mail events from last N hours."""
    events = []
    cutoff = datetime.now() - timedelta(hours=hours)
    
    if not EVIDENCE_DIR.exists():
        return events
    
    for filepath in EVIDENCE_DIR.glob("*.json"):
        try:
            with open(filepath) as f:
                data = json.load(f)
                received_at = datetime.fromisoformat(data.get("received_at", ""))
                if received_at > cutoff:
                    events.extend(data.get("events", []))
        except Exception:
            continue
    
    return events


def get_delivery_stats(events):
    """Calculate delivery statistics."""
    if not events:
        return {
            "total": 0,
            "delivered": 0,
            "bounced": 0,
            "opened": 0,
            "clicked": 0,
            "success_rate": 0.0
        }
    
    counts = Counter(e.get("event") for e in events)
    
    total = len(events)
    delivered = counts.get("delivered", 0)
    bounced = counts.get("bounce", 0) + counts.get("dropped", 0)
    
    return {
        "total": total,
        "delivered": delivered,
        "bounced": bounced,
        "opened": counts.get("open", 0),
        "clicked": counts.get("click", 0),
        "success_rate": round(delivered / total * 100, 1) if total > 0 else 0
    }


@app.route("/")
def dashboard():
    """Mail delivery dashboard."""
    events = load_recent_events(hours=24)
    stats = get_delivery_stats(events)
    
    return render_template("mail_dashboard.html",
                          stats=stats,
                          events=events[:50],
                          now=datetime.now())


@app.route("/api/stats")
def api_stats():
    """API endpoint for mail stats."""
    events = load_recent_events(hours=24)
    stats = get_delivery_stats(events)
    return jsonify(stats)


if __name__ == "__main__":
    print("🚀 GCCD Mail Delivery Dashboard")
    print("   Access: http://localhost:5003")
    app.run(host="0.0.0.0", port=5003, debug=True)
```

---

### Event Correlation

Link mail events to GCCD operations via `custom_args`:

```python
def correlate_with_operations(event):
    """Link mail event to GCCD operation if possible."""
    custom_args = event.get("custom_args", {})
    
    operation_id = custom_args.get("gccd_operation_id")
    vm_name = custom_args.get("vm_name")
    action = custom_args.get("action")
    
    if operation_id:
        return {
            "operation_id": operation_id,
            "vm_name": vm_name,
            "action": action,
            "linked": True
        }
    
    return {"linked": False}
```

---

### Cost Tracking

Estimate SendGrid costs from event volume:

```python
SENDGRID_COST_PER_1K = 0.0  # Free tier: 100/day, then $0.001/email

def estimate_costs(events):
    """Estimate email sending costs."""
    processed = sum(1 for e in events if e.get("event") == "processed")
    
    # Free tier: 100 emails/day
    free_tier = 100
    billable = max(0, processed - free_tier)
    
    return {
        "emails_sent": processed,
        "free_tier_used": min(processed, free_tier),
        "billable_emails": billable,
        "estimated_cost_usd": round(billable * 0.001, 2)
    }
```

---

## Success Criteria

- [ ] Mail dashboard accessible at `http://localhost:5003`
- [ ] Recent events displayed with delivery stats
- [ ] Bounce/failure alerts visible
- [ ] Cost estimation working
- [ ] Event correlation with GCCD operations
- [ ] Evidence files generated

---

## Integration with Main GCCD

Add mail stats to daily digest:

```python
# In daily_digest.py
def include_mail_stats():
    events = load_recent_events(hours=24)
    stats = get_delivery_stats(events)
    costs = estimate_costs(events)
    
    return f"""
## Mail Extension (24h)
- Emails sent: {stats['total']}
- Delivered: {stats['delivered']} ({stats['success_rate']}%)
- Bounced: {stats['bounced']}
- Estimated cost: ${costs['estimated_cost_usd']}
"""
```

---

## Next Steps

After Phase 4E:
1. Document extension retirement plan
2. Complete GCCD Phase 4
3. Update ROADMAP with Phase 4 completion

---

*Document created as part of GCCD-001 Phase 4E implementation — 2026-04-02*
