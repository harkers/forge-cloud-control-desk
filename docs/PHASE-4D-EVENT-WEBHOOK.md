# Phase 4D — Event Webhook for Delivery Telemetry

**Document:** GCCD-PH4D-001  
**Created:** 2026-04-02  
**Status:** In Progress  
**Parent:** EMAIL-SERVER-EXTENSION.md  
**Depends:** Phase 4B (Postfix baseline operational)  
**Independent of:** Phase 4C (can capture events even without SendGrid auth)  

---

## Overview

Phase 4D creates an HTTP endpoint to receive SendGrid Event Webhook notifications. This captures delivery telemetry (sent, delivered, opened, clicked, bounced, etc.) for the GCCD email extension.

**Key Insight:** Event Webhook works independently of SMTP authentication. You can:
- Receive webhook events for any SendGrid account
- Store and analyze delivery telemetry
- Build alerting on bounces/failures

Then later (Phase 4C) connect the actual SMTP relay.

---

## Architecture

```
SendGrid ──Event Webhook──▶ FastAPI Endpoint ──▶ Local Storage
     │                            │
     │                            ▼
     │                    evidence/mail-events/
     │
     └── SMTP (Phase 4C) ──▶ Postfix Relay
```

---

## Implementation

### 1. Webhook Receiver (FastAPI)

**File:** `src/mail/webhook_receiver.py`

```python
"""SendGrid Event Webhook receiver for GCCD Email Extension."""

import json
import hashlib
import hmac
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuration
EVIDENCE_DIR = Path(__file__).parent.parent.parent / "data" / "evidence" / "mail-events"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# In production, load from environment
WEBHOOK_SECRET = "your-sendgrid-webhook-secret"  # Phase 4D Step 2


def verify_signature(payload: bytes, signature: str, timestamp: str) -> bool:
    """Verify SendGrid webhook signature."""
    if not WEBHOOK_SECRET or WEBHOOK_SECRET == "your-sendgrid-webhook-secret":
        # Skip verification if secret not configured
        return True
    
    # Construct signed payload
    signed_payload = timestamp.encode() + payload
    expected_sig = hmac.new(
        WEBHOOK_SECRET.encode(),
        signed_payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_sig, signature)


def store_events(events: List[Dict[str, Any]]):
    """Store events to local evidence directory."""
    timestamp = datetime.now().isoformat()
    filename = f"mail_events_{timestamp.replace(':', '-').replace('.', '_')}.json"
    filepath = EVIDENCE_DIR / filename
    
    evidence = {
        "received_at": timestamp,
        "event_count": len(events),
        "events": events
    }
    
    with open(filepath, "w") as f:
        json.dump(evidence, f, indent=2)
    
    return filepath


@app.route("/webhook/mail-events", methods=["POST"])
def receive_events():
    """Receive SendGrid Event Webhook."""
    payload = request.get_data()
    
    # Get SendGrid signature headers
    signature = request.headers.get("X-Twilio-Email-Event-Webhook-Signature", "")
    timestamp = request.headers.get("X-Twilio-Email-Event-Webhook-Timestamp", "")
    
    # Verify signature (optional in dev)
    if not verify_signature(payload, signature, timestamp):
        return jsonify({"error": "Invalid signature"}), 401
    
    # Parse events
    try:
        events = request.get_json()
        if not isinstance(events, list):
            events = [events]
    except Exception as e:
        return jsonify({"error": f"Invalid JSON: {e}"}), 400
    
    # Store events
    filepath = store_events(events)
    
    # Log summary
    event_types = {}
    for event in events:
        event_type = event.get("event", "unknown")
        event_types[event_type] = event_types.get(event_type, 0) + 1
    
    print(f"📧 Received {len(events)} mail events: {event_types}")
    print(f"💾 Stored to: {filepath}")
    
    return jsonify({
        "status": "ok",
        "events_received": len(events),
        "events_by_type": event_types,
        "stored_at": str(filepath)
    }), 200


@app.route("/webhook/health", methods=["GET"])
def health_check():
    """Health check endpoint for webhook receiver."""
    return jsonify({
        "status": "ok",
        "service": "gccd-mail-webhook",
        "evidence_dir": str(EVIDENCE_DIR),
        "webhook_url": "/webhook/mail-events"
    }), 200


if __name__ == "__main__":
    print("🚀 GCCD Mail Event Webhook Receiver")
    print(f"   Webhook URL: http://localhost:5002/webhook/mail-events")
    print(f"   Health Check: http://localhost:5002/webhook/health")
    print(f"   Evidence Dir: {EVIDENCE_DIR}")
    print("")
    app.run(host="0.0.0.0", port=5002, debug=True)
```

---

### 2. Running the Webhook Receiver

```bash
cd /home/stu/.openclaw/workspace/projects/forge-cloud-control-desk
export $(grep -v '^#' .env | xargs)
python3 src/mail/webhook_receiver.py
```

**Access:**
- Webhook: `http://YOUR_IP:5002/webhook/mail-events`
- Health: `http://YOUR_IP:5002/webhook/health`

---

### 3. SendGrid Webhook Configuration

**In SendGrid Dashboard:**

1. **Settings → Mail Settings → Event Webhook**
2. **Enable:** Toggle ON
3. **HTTP POST URL:** `http://YOUR_EXTERNAL_IP:5002/webhook/mail-events`
4. **Security:** Enable Signed Event Webhook (copy secret)
5. **Event Types:** Select events to receive:
   - ✅ Processed
   - ✅ Dropped
   - ✅ Delivered
   - ✅ Deferred
   - ✅ Bounce
   - ✅ Open
   - ✅ Click
   - ✅ Spam Report
   - ✅ Unsubscribe
   - ✅ Group Unsubscribe
   - ✅ Group Resubscribe

6. **Save**

---

### 4. Webhook Secret Configuration

Update the webhook receiver with your secret:

```bash
# Option A: Environment variable
export SENDGRID_WEBHOOK_SECRET="your-actual-secret-from-sendgrid"

# Option B: .env file
echo "SENDGRID_WEBHOOK_SECRET=your-actual-secret" >> .env
```

---

## Testing

### Test 1: Health Check

```bash
curl http://localhost:5002/webhook/health
```

**Expected:**
```json
{
  "status": "ok",
  "service": "gccd-mail-webhook",
  "evidence_dir": ".../data/evidence/mail-events",
  "webhook_url": "/webhook/mail-events"
}
```

### Test 2: Simulate Webhook

```bash
curl -X POST http://localhost:5002/webhook/mail-events \
  -H "Content-Type: application/json" \
  -d '[{
    "email": "test@example.com",
    "event": "delivered",
    "timestamp": 1234567890,
    "sg_message_id": "test-message-id"
  }]'
```

**Expected:**
- Response: `{"status": "ok", "events_received": 1, ...}`
- Evidence file created in `data/evidence/mail-events/`

---

## Event Storage Format

**File:** `data/evidence/mail-events/mail_events_TIMESTAMP.json`

```json
{
  "received_at": "2026-04-02T22:00:00",
  "event_count": 3,
  "events": [
    {
      "email": "user@example.com",
      "event": "delivered",
      "timestamp": 1743628800,
      "sg_message_id": "...",
      "response": "250 OK"
    },
    {
      "email": "bounce@example.com",
      "event": "bounce",
      "timestamp": 1743628801,
      "sg_message_id": "...",
      "reason": "550 user unknown"
    }
  ]
}
```

---

## Troubleshooting

### Webhook Not Receiving Events

**Check:**
1. Receiver is running: `curl http://localhost:5002/webhook/health`
2. SendGrid webhook URL is correct (external IP, not localhost)
3. GCP firewall allows inbound port 5002
4. SendGrid webhook status shows "Enabled"

### Signature Verification Fails

**Fix:**
```bash
# Skip verification for testing (not recommended for production)
# Or set correct secret:
export SENDGRID_WEBHOOK_SECRET="actual-secret-from-sendgrid"
```

### Events Not Stored

**Check:**
```bash
ls -la data/evidence/mail-events/
cat data/evidence/mail-events/*.json
```

---

## Production Deployment

### Firewall Rule (GCP)

```bash
gcloud compute firewall-rules create allow-webhook-inbound \
  --direction=INGRESS \
  --network=default \
  --action=ALLOW \
  --rules=tcp:5002 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=forge-mail
```

### Systemd Service

Create `/etc/systemd/system/gccd-mail-webhook.service`:

```ini
[Unit]
Description=GCCD Mail Event Webhook Receiver
After=network.target

[Service]
Type=simple
User=stu
WorkingDirectory=/home/stu/.openclaw/workspace/projects/forge-cloud-control-desk
Environment="PATH=/usr/bin:/bin"
Environment="SENDGRID_WEBHOOK_SECRET=your-secret"
ExecStart=/usr/bin/python3 src/mail/webhook_receiver.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gccd-mail-webhook
sudo systemctl start gccd-mail-webhook
```

---

## Integration with GCCD

### Evidence Linking

Webhook events reference GCCD operations via:
- `custom_args` in SendGrid API calls (include `gccd_operation_id`)
- `sg_message_id` correlation with Postfix logs

### Alerting

Add alerting for critical events:
```python
# In webhook_receiver.py, add to store_events()
for event in events:
    if event.get("event") in ["bounce", "dropped", "spamreport"]:
        # Write notification
        notification_path = Path("data/evidence/notifications") / f"mail_alert_{timestamp}.txt"
        with open(notification_path, "w") as f:
            f.write(f"ALERT: Mail {event['event']} for {event.get('email')}\n")
            f.write(f"Reason: {event.get('reason', 'N/A')}\n")
```

---

## Success Criteria

- [ ] Webhook receiver running on port 5002
- [ ] Health check endpoint responding
- [ ] SendGrid webhook configured and enabled
- [ ] Test event received and stored
- [ ] Evidence files generated in `data/evidence/mail-events/`
- [ ] (Optional) Alerting for bounces/failures

---

## Next Steps (Phase 4E)

After webhook operational:
1. Correlate mail events with GCCD operations
2. Build delivery dashboard
3. Add cost tracking per email sent

See PHASE-4E-EVIDENCE-INTEGRATION.md

---

## Rollback

If webhook needs removal:

```bash
# Disable in SendGrid
# Settings → Mail Settings → Event Webhook → Disable

# Stop receiver
sudo systemctl stop gccd-mail-webhook
sudo systemctl disable gccd-mail-webhook

# Remove firewall rule
gcloud compute firewall-rules delete allow-webhook-inbound --quiet
```

---

*Document created as part of GCCD-001 Phase 4D implementation — 2026-04-02*
