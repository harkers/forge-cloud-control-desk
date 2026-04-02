"""SendGrid Event Webhook receiver for GCCD Email Extension."""

import json
import hashlib
import hmac
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuration
project_root = Path(__file__).parent.parent.parent
EVIDENCE_DIR = project_root / "data" / "evidence" / "mail-events"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# Load from environment or use placeholder
WEBHOOK_SECRET = os.getenv("SENDGRID_WEBHOOK_SECRET", "your-sendgrid-webhook-secret")


def verify_signature(payload: bytes, signature: str, timestamp: str) -> bool:
    """Verify SendGrid webhook signature."""
    if not WEBHOOK_SECRET or WEBHOOK_SECRET == "your-sendgrid-webhook-secret":
        # Skip verification if secret not configured (dev mode)
        return True
    
    # Construct signed payload
    signed_payload = timestamp.encode() + payload
    expected_sig = hmac.new(
        WEBHOOK_SECRET.encode(),
        signed_payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_sig, signature)


def store_events(events: List[Dict[str, Any]]) -> Path:
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
