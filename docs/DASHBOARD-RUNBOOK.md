# GCCD Dashboard Runbook

**Document:** GCCD-OPS-003  
**Created:** 2026-04-02  
**Status:** Ready for use  

---

## Overview

The GCCD Status Dashboard provides real-time visibility into:
- Service Health status (Google Cloud incidents)
- VM inventory and state
- Recent operations evidence
- Quick health checks

**Access:** http://localhost:5001

---

## Starting the Dashboard

### Development Mode

```bash
cd /home/stu/.openclaw/workspace/projects/forge-cloud-control-desk
export $(grep -v '^#' .env | xargs)
python3 -m src.dashboard.app
```

**Output:**
```
🚀 GCCD Status Dashboard
   Starting on port 5001...
   Access: http://localhost:5001
   API: http://localhost:5001/api/health
```

### Production Mode (Background)

```bash
# Create systemd service or use screen/tmux
screen -S gccd-dashboard
cd /home/stu/.openclaw/workspace/projects/forge-cloud-control-desk
export $(grep -v '^#' .env | xargs)
python3 -m src.dashboard.app
# Ctrl+A, D to detach
```

### Auto-start with Systemd

Create `/etc/systemd/system/gccd-dashboard.service`:

```ini
[Unit]
Description=GCCD Status Dashboard
After=network.target

[Service]
Type=simple
User=stu
WorkingDirectory=/home/stu/.openclaw/workspace/projects/forge-cloud-control-desk
Environment="PATH=/usr/bin:/bin"
ExecStart=/usr/bin/python3 -m src.dashboard.app
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gccd-dashboard
sudo systemctl start gccd-dashboard
```

---

## Dashboard Views

### Main Dashboard (/)

**Shows:**
- Service Health status card
- VM inventory summary
- Recent evidence files
- Auto-refresh every 60 seconds

**Use case:** Daily operations check-in, quick status overview

---

### Health Check Page (/health-check)

**Shows:**
- Detailed service health information
- Active/resolved incidents
- Regional status

**Use case:** When investigating potential Google Cloud outages

---

## API Endpoints

### GET /api/health

Returns current service health status.

**Response:**
```json
{
  "status": "OPERATIONAL",
  "active_incidents": 0,
  "region": "europe-west2",
  "last_check": "2026-04-02T20:48:43.123456",
  "status_code": "operational"
}
```

---

### GET /api/vms

Returns VM inventory summary.

**Response:**
```json
{
  "total": 3,
  "running": 2,
  "stopped": 1,
  "vms": [...],
  "status": "ok"
}
```

---

### GET /api/evidence?limit=10

Returns recent evidence files.

**Response:**
```json
[
  {
    "name": "health_check_2026-04-02T20-48-43.md",
    "path": "service_health/health_check_...",
    "modified": "2026-04-02T20:48:43",
    "category": "service_health"
  }
]
```

---

## Troubleshooting

### Dashboard Won't Start

**Check:**
1. Port 5001 not in use: `ss -tlnup | grep 5001`
2. Dependencies installed: `pip3 install -r requirements.txt`
3. Environment variables set: `cat .env`

**Fix:**
```bash
# Kill existing process
pkill -f "python3 -m src.dashboard.app"

# Reinstall dependencies
pip3 install -r requirements.txt

# Restart
python3 -m src.dashboard.app
```

---

### VM Data Not Loading

**Cause:** Service account authentication issue

**Check:**
```bash
export $(grep -v '^#' .env | xargs)
python3 -m src.main list
```

**Fix:**
1. Verify `.env` has correct `GOOGLE_APPLICATION_CREDENTIALS`
2. Check service account file exists
3. Verify service account has Compute Viewer role

---

### Service Health Shows UNKNOWN

**Cause:** API access issue or propagation delay

**Check:**
```bash
export $(grep -v '^#' .env | xargs)
python3 -m src.main health
```

**Fix:**
1. Wait 2-5 minutes after enabling API
2. Verify Cloud Resource Manager API is enabled
3. Check service account has proper scopes

---

## Integration Points

### Daily Standup

Add to daily standup checklist:

```markdown
### Dashboard Check
- [ ] Visit http://localhost:5001
- [ ] Confirm Service Health: OPERATIONAL
- [ ] Review VM count matches expectations
- [ ] Check recent evidence for anomalies
```

---

### Monitoring & Alerts

**Recommended:**
- Run dashboard in background (systemd or screen)
- Access via browser bookmark
- Check during daily standup
- Review when investigating incidents

**Future enhancements:**
- Slack/Teams webhook for degraded status
- Email digest integration
- Custom alerting thresholds

---

## Security Notes

**Development mode:**
- Debug mode enabled (auto-reload)
- Weak secret key
- No authentication

**Production deployment:**
- Disable debug mode
- Set strong `DASHBOARD_SECRET_KEY`
- Add authentication layer (OAuth, basic auth, or reverse proxy)
- Use HTTPS via reverse proxy (nginx, Caddy)

Example production config:
```bash
export DASHBOARD_SECRET_KEY=<strong-random-key>
export FLASK_ENV=production
```

---

*Document created as part of GCCD-001 Phase 3 implementation — 2026-04-02*
