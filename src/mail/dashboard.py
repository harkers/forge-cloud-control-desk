"""GCCD Mail Extension — Delivery Dashboard."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

project_root = Path(__file__).parent.parent.parent
EVIDENCE_DIR = project_root / "data" / "evidence" / "mail-events"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GCCD Mail Delivery Dashboard</title>
    <style>
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #334155;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --accent-blue: #3b82f6;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --accent-yellow: #f59e0b;
            --border: #475569;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 2rem;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        header {
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border);
        }
        h1 { font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem; }
        .subtitle { color: var(--text-secondary); }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        .card {
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid var(--border);
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        .card-title { font-size: 1.1rem; font-weight: 600; }
        .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--accent-blue);
        }
        .stat-label { font-size: 0.85rem; color: var(--text-secondary); }
        .success { color: var(--accent-green); }
        .error { color: var(--accent-red); }
        .warning { color: var(--accent-yellow); }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }
        th, td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }
        th {
            font-weight: 600;
            color: var(--text-secondary);
        }
        .event-delivered { color: var(--accent-green); }
        .event-bounce { color: var(--accent-red); }
        .event-open { color: var(--accent-blue); }
        footer {
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.85rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📧 GCCD Mail Delivery Dashboard</h1>
            <p class="subtitle">Email Extension — Last 24 Hours</p>
        </header>
        
        <div class="grid">
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">Total Sent</h2>
                </div>
                <div class="stat-value">{{ stats.total }}</div>
                <div class="stat-label">Emails processed</div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">Delivered</h2>
                </div>
                <div class="stat-value success">{{ stats.delivered }}</div>
                <div class="stat-label">{{ stats.success_rate }}% success rate</div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">Bounced</h2>
                </div>
                <div class="stat-value {% if stats.bounced > 0 %}error{% endif %}">{{ stats.bounced }}</div>
                <div class="stat-label">Failed deliveries</div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">Opened</h2>
                </div>
                <div class="stat-value">{{ stats.opened }}</div>
                <div class="stat-label">Email opens</div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h2 class="card-title">Recent Events</h2>
            </div>
            {% if events %}
            <table>
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Event</th>
                        <th>Email</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for event in events[:20] %}
                    <tr>
                        <td>{{ event.timestamp | default('N/A') }}</td>
                        <td class="event-{{ event.event }}">{{ event.event }}</td>
                        <td>{{ event.email | default('N/A') }}</td>
                        <td>{{ event.reason | default('OK') }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p style="color: var(--text-secondary); margin-top: 1rem;">No events in last 24 hours</p>
            {% endif %}
        </div>
        
        <footer>
            <p>GCCD Mail Extension • Phase 4E Evidence Integration</p>
            <p style="margin-top: 0.5rem;">Generated: {{ now.strftime('%Y-%m-%d %H:%M UTC') }}</p>
        </footer>
    </div>
</body>
</html>
"""


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
    
    return render_template_string(HTML_TEMPLATE,
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
    print("")
    app.run(host="0.0.0.0", port=5003, debug=True)
