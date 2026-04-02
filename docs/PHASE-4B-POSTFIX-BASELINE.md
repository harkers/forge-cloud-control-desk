# Phase 4B — Postfix Relay-Only Baseline

**Document:** GCCD-PH4B-001  
**Created:** 2026-04-02  
**Status:** In Progress  
**Parent:** EMAIL-SERVER-EXTENSION.md  
**Depends:** Phase 4A (forge-mail-server VM provisioned)  

---

## Overview

Phase 4B installs and configures Postfix on the `forge-mail-server` VM as a **relay-only** mail server. This VM will forward all outbound mail to SendGrid on port 587.

**Scope:**
- ✅ Install Postfix
- ✅ Configure relay-only mode (no local delivery)
- ✅ Enable STARTTLS on port 587
- ✅ Test local mail submission
- ❌ No inbound MX
- ❌ No local mailboxes
- ❌ No Dovecot

---

## Prerequisites

- [x] Phase 4A complete: `forge-mail-server` VM running
- [ ] SSH access configured
- [ ] SendGrid account ready for Phase 4C

---

## SSH into VM

```bash
gcloud compute ssh forge-mail-server --zone=europe-west2-b
```

Or via IP:
```bash
# Get external IP
export $(grep -v '^#' .env | xargs)
python3 -m src.main inspect forge-mail-server

# SSH (replace with actual IP)
ssh -i ~/.ssh/google_compute_engine user@EXTERNAL_IP
```

---

## Installation Steps

### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Postfix

```bash
sudo apt install -y postfix mailutils
```

During installation:
- Select **"Internet Site"**
- System mail name: `forge-mail-server`

### 3. Configure Postfix as Relay-Only

Backup original config:
```bash
sudo cp /etc/postfix/main.cf /etc/postfix/main.cf.orig
```

Edit `/etc/postfix/main.cf`:

```bash
sudo nano /etc/postfix/main.cf
```

Replace or add these settings:

```ini
# Basic identity
myhostname = forge-mail-server
mydomain = orderededge-groupware.iam.gserviceaccount.com
myorigin = $mydomain
inet_interfaces = loopback-only
inet_protocols = ipv4

# Relay configuration (SendGrid - Phase 4C will add authentication)
relayhost = [smtp.sendgrid.net]:587
smtp_sasl_auth_enable = yes
smtp_sasl_security_options = noanonymous
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_tls_security_level = encrypt
smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt

# No local delivery
mydestination =
local_recipient_maps =
mailbox_size_limit = 0
recipient_delimiter = +

# Logging
maillog_file = /var/log/mail.log
```

### 4. Create SASL Password File (Placeholder)

```bash
sudo touch /etc/postfix/sasl_passwd
sudo chmod 600 /etc/postfix/sasl_passwd
```

**Note:** Actual SendGrid credentials added in Phase 4C.

### 5. Update Postfix

```bash
sudo postmap /etc/postfix/sasl_passwd
sudo systemctl restart postfix
sudo systemctl enable postfix
```

### 6. Verify Installation

```bash
# Check service status
sudo systemctl status postfix

# Check listening ports
sudo ss -tlnp | grep master

# Verify configuration
sudo postfix check
```

---

## Testing

### Local Test (Before SendGrid Auth)

```bash
# Test local submission (will queue, not yet deliver)
echo "Test email body" | mail -s "Test Subject" user@example.com

# Check queue
sudo postqueue -p

# View logs
sudo tail -f /var/log/mail.log
```

Expected: Mail queues but fails to deliver (no SendGrid auth yet). This is correct for Phase 4B.

---

## Evidence Collection

After successful installation:

```bash
# Document current state
sudo postconf -n > /tmp/postfix-config.txt
cat /tmp/postfix-config.txt
```

Save this as evidence for Phase 4B completion.

---

## Success Criteria

- [x] Postfix installed on `forge-mail-server`
- [x] Configured as relay-only (no local delivery)
- [x] STARTTLS enabled for SendGrid communication
- [x] Service running and enabled at boot
- [x] Local mail submission functional (queues to relay)
- [ ] SendGrid authentication configured (Phase 4C)

---

## Troubleshooting

### Postfix Won't Start

```bash
# Check config syntax
sudo postfix check

# View detailed error
sudo journalctl -u postfix -n 50
```

### Permission Denied on SASL File

```bash
sudo chmod 600 /etc/postfix/sasl_passwd
sudo chown root:root /etc/postfix/sasl_passwd
sudo postmap /etc/postfix/sasl_passwd
```

### Port 587 Blocked

```bash
# Check GCP firewall
gcloud compute firewall-rules list --filter="name~'default-allow'"

# May need to add rule for egress 587
gcloud compute firewall-rules create allow-smtp-outbound \
  --direction=EGRESS \
  --network=default \
  --action=ALLOW \
  --rules=tcp:587 \
  --destination-ranges=0.0.0.0/0
```

---

## Rollback

If Postfix configuration is broken:

```bash
sudo systemctl stop postfix
sudo cp /etc/postfix/main.cf.orig /etc/postfix/main.cf
sudo systemctl start postfix
```

If VM needs complete rebuild:

```bash
# From GCCD host
export $(grep -v '^#' .env | xargs)
python3 -m src.main delete forge-mail-server \
  --reason="Phase 4B rollback: Postfix configuration failed"

# Then re-run Phase 4A
```

---

## Next Steps (Phase 4C)

After successful Postfix baseline:
1. Create SendGrid account/subuser
2. Authenticate sending subdomain
3. Add API key to Postfix SASL config
4. Test end-to-end delivery

See PHASE-4C-SENDGRID-AUTH.md for detailed steps.

---

*Document created as part of GCCD-001 Phase 4B implementation — 2026-04-02*
