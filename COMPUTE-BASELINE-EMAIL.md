# Google Cloud Compute Baseline — Email Server

## Project: Forge Compute Control Desk

## Region & Zone
- **Region:** `europe-west2` (London)
- **Zone:** `europe-west2-b`

## Instance Configuration
| Setting | Value |
|---------|-------|
| **Machine Type** | `e2-medium` |
| **Disk Type** | `pd-balanced` |
| **Disk Size** | `20 GB` |

## Compute Engine API Reference

### Create Instance Request (partial)
```json
{
  "name": "email-server",
  "zone": "projects/PROJECT_ID/zones/europe-west2-b",
  "machineType": "projects/PROJECT_ID/zones/europe-west2-b/machineTypes/e2-medium",
  "disks": [
    {
      "autoDelete": true,
      "boot": true,
      "deviceName": "email-server",
      "initializeParams": {
        "diskSizeGb": "20",
        "diskType": "projects/PROJECT_ID/zones/europe-west2-b/diskTypes/pd-balanced",
        "sourceImage": "projects/debian-cloud/global/images/debian-12-bookworm-v20260317"
      },
      "type": "PERSISTENT"
    }
  ],
  "networkInterfaces": [
    {
      "network": "projects/PROJECT_ID/global/networks/default",
      "accessConfigs": [
        {
          "name": "External NAT",
          "type": "ONE_TO_ONE_NAT"
        }
      ]
    }
  ],
  "metadata": {
    "items": [
      {
        "key": "startup-script",
        "value": "#!/bin/bash\napt-get update && apt-get install -y postfix"
      }
    ]
  },
  "tags": {
    "items": ["mail-server"]
  }
}
```

## Email Server Considerations

| Concern | Recommendation |
|---------|----------------|
| **Firewall** | Allow TCP 25 (SMTP), 587 (Submission), 993 (IMAPS), 465 (SMTPS) |
| **SPF/DKIM/DMARC** | Configure DNS records before cutover |
| **Reverse DNS** | Request PTR record from Google Cloud (requires quota increase) |
| **Spam Filtering** | Consider amavis + spamassassin or rspamd |
| **Backup** | Regular configuration backups (postfix main.cf, master.cf) |
| **Monitoring** | Postfix queue size, rejection rates, TLS handshake success |

## Next Steps

1. **Select project ID** — update `PROJECT_ID` in API calls
2. **Select OS image** — Debian 12 recommended for stability
3. **Configure firewall rules** — allow mail ports before first boot
4. **DNS setup** — SPF, DKIM, DMARC, MX, and reverse DNS
5. **Service account** — create service account with `compute.instances.create` permission

## Cost Estimate (e2-medium, Europe)

| Component | Monthly Cost (approx) |
|-----------|----------------------|
| e2-medium (2 vCPU, 4GB RAM) | ~$30 |
| pd-balanced 20GB | ~$3 |
| Network egress (100GB) | ~$9 |
| **Total** | ~$42/month |

---

*Baseline documented for Phase 1 — Google foundation workstream.*
