# Phase 4C — SendGrid Authentication

**Document:** GCCD-PH4C-001  
**Created:** 2026-04-02  
**Status:** Ready for credentials  
**Parent:** EMAIL-SERVER-EXTENSION.md  
**Depends:** Phase 4B (Postfix relay baseline operational)  

---

## Overview

Phase 4C authenticates the `forge-mail-server` with SendGrid to enable actual email delivery. This requires:

1. SendGrid account with SMTP credentials
2. Updating Postfix SASL password file
3. Testing end-to-end mail delivery

**⚠️ Manual Step Required:** You must provide SendGrid API key or create a subuser with SMTP credentials.

---

## Prerequisites

- [x] Phase 4B complete: Postfix running on `forge-mail-server`
- [ ] SendGrid account with SMTP credentials
- [ ] Authenticated domain (recommended: `forge.orderededge.co`)

---

## SendGrid Setup Options

### Option A: Existing Account (Recommended)
Use existing SendGrid account with SMTP credentials.

**Need:**
- SMTP username (usually "apikey" or subuser)
- SMTP password (API key)

### Option B: New Subuser
Create dedicated subuser for GCCD relay.

**Steps:**
1. Login to SendGrid dashboard
2. Settings → Subusers → Create New Subuser
3. Name: `forge-mail-server`
4. Assign IP or use shared pool
5. Generate API key with "Mail Send" permission

### Option C: Authenticated Domain
Best for production: authenticate sending domain.

**Steps:**
1. SendGrid dashboard → Settings → Sender Authentication
2. Domain Authentication → Start
3. Enter domain: `forge.orderededge.co` (or your domain)
4. Add DNS records as instructed
5. Wait for verification

---

## Postfix Configuration

### Step 1: Update SASL Password File

SSH to VM and edit credentials:

```bash
gcloud compute ssh forge-mail-server --zone=europe-west2-b

# Create SASL password file
sudo tee /etc/postfix/sasl_passwd << 'EOF'
[smtp.sendgrid.net]:587 YOUR_SMTP_USERNAME:YOUR_SMTP_PASSWORD
EOF

# Secure and hash the file
sudo chmod 600 /etc/postfix/sasl_passwd
sudo postmap /etc/postfix/sasl_passwd
```

### Step 2: Restart Postfix

```bash
sudo systemctl restart postfix
sudo systemctl status postfix --no-pager
```

### Step 3: Verify Configuration

```bash
# Check Postfix can read the SASL file
sudo postconf -n | grep sasl

# Expected output:
# smtp_sasl_auth_enable = yes
# smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
# smtp_sasl_security_options = noanonymous
```

---

## Testing

### Test 1: Local Submission

```bash
echo "Test email from GCCD relay" | mail -s "Phase 4C Test" your-email@example.com
```

### Test 2: Check Queue

```bash
sudo postqueue -p
```

- **Empty queue:** Mail sent successfully
- **Messages pending:** Check logs for errors

### Test 3: Check Logs

```bash
sudo tail -f /var/log/mail.log
```

**Success indicators:**
- `status=sent (250 OK)`
- No authentication errors
- No TLS errors

---

## Troubleshooting

### Authentication Failed

**Symptoms:**
```
SASL authentication failed
```

**Fix:**
1. Verify credentials in `/etc/postfix/sasl_passwd`
2. Ensure file format is exact: `[smtp.sendgrid.net]:587 username:password`
3. Run `sudo postmap /etc/postfix/sasl_passwd` after changes
4. Check SendGrid dashboard for API key status

### TLS Error

**Symptoms:**
```
TLS handshake failed
```

**Fix:**
```bash
# Verify CA certificates
ls -la /etc/ssl/certs/ca-certificates.crt

# Update certificates if needed
sudo apt update && sudo apt install -y ca-certificates
```

### Connection Refused

**Symptoms:**
```
Connection refused to smtp.sendgrid.net:587
```

**Fix:**
1. Verify GCP firewall allows outbound port 587
2. Check if external IP is assigned
3. Verify SendGrid status at status.sendgrid.com

---

## Evidence Collection

After successful authentication:

```bash
# Document configuration (with redacted credentials)
sudo postconf -n | grep -v "password" > /tmp/postfix-config-auth.txt
echo "SASL file present: $(ls -la /etc/postfix/sasl_passwd.hash)" >> /tmp/postfix-config-auth.txt
```

Save as Phase 4C evidence.

---

## Success Criteria

- [ ] SendGrid credentials obtained
- [ ] SASL password file configured
- [ ] Postfix restarted successfully
- [ ] Test email delivered to inbox
- [ ] No authentication errors in logs
- [ ] Evidence file created

---

## Next Steps (Phase 4D)

After successful email delivery:
1. Configure Event Webhook endpoint
2. Capture delivery telemetry
3. Store events in evidence folder

See PHASE-4D-EVENT-WEBHOOK.md

---

## Rollback

If SendGrid auth fails:

```bash
# Remove credentials
sudo rm /etc/postfix/sasl_passwd /etc/postfix/sasl_passwd.hash

# Restore original relay config
sudo cp /etc/postfix/main.cf.orig /etc/postfix/main.cf
sudo systemctl restart postfix
```

---

*Document created as part of GCCD-001 Phase 4C implementation — 2026-04-02*
