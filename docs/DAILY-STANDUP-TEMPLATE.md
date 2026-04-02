# GCCD Daily Standup Template

**Template:** GCCD-DST-001  
**Created:** 2026-04-02  
**Use:** Daily operations check-in  

---

## Date: YYYY-MM-DD

### Yesterday's Work

<!-- What did you accomplish? -->

- [ ] 

---

### Today's Plan

<!-- What will you work on? -->

- [ ] 

---

### Blockers / Questions

<!-- Anything preventing progress? -->

- [ ] 

---

## Operational Checklist

### VM Health Check

```bash
cd /home/stu/.openclaw/workspace/projects/forge-cloud-control-desk
export $(grep -v '^#' .env | xargs)
python3 -m src.main list
```

**Status:**
- Total VMs: ___
- Running: ___
- Stopped: ___
- Issues: ___

---

### Service Health Check

```bash
python3 -m src.main health
```

**Status:**
- Overall: OPERATIONAL / DEGRADED / UNKNOWN
- Active Incidents: ___
- Notes: ___

---

### Evidence Review

**Last 24h Actions:**
```bash
python3 -m src.main digest
cat data/evidence/reports/daily_digest_*.md
```

**Actions Reviewed:** YES / NO  
**Anomalies Found:** ___

---

### Sheets Register Sync

**URL:** https://docs.google.com/spreadsheets/d/1-AA3fWiNEBxaygbV3oZ-naoCrLufAMmr468m6eDdkWE

**Last Updated:** ___  
**Matches Reality:** YES / NO  
**Corrections Needed:** ___

---

## Incidents / Alerts

| Time | Description | Impact | Resolution |
|------|-------------|--------|------------|
|      |             |        |            |

---

## Cost Watch

**Running Instances >7 Days:**
- (List any instances that should be reviewed for cost optimization)

**New VMs Created:**
- 

**VMs Decommissioned:**
- 

---

## Notes

<!-- Any additional context, decisions, or follow-ups -->



---

*Template for GCCD-001 daily operations — Forge Compute Control Desk*
