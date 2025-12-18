# Verification Checklist

Complete verification steps to ensure Home Assistant is configured correctly for Tailscale-only access and the SimpliSafe → Alexa automation is working.

## Pre-Deployment Verification

### 1. Tailscale Setup
```bash
# ✅ Verify Tailscale is installed
which tailscale

# ✅ Verify Tailscale is running
tailscale status

# ✅ Verify Tailscale IP exists
tailscale ip -4
# Should return: 100.x.x.x

# ✅ Verify tailscale0 interface exists
ip addr show tailscale0
# Should show: inet 100.x.x.x/...
```

### 2. Firewall Configuration
```bash
# ✅ Verify UFW is enabled
sudo ufw status

# ✅ CRITICAL: Verify NO rule exists for port 8123
sudo ufw status | grep 8123
# Should return: (nothing) - if it shows a rule, REMOVE IT

# ✅ If rule exists, remove it:
# sudo ufw delete allow 8123/tcp
# sudo ufw reload
```

### 3. Docker Setup
```bash
# ✅ Verify Docker is installed
docker --version

# ✅ Verify Docker Compose is installed
docker-compose --version

# ✅ Verify Docker service is running
sudo systemctl status docker
```

## Post-Deployment Verification

### 4. Container Status
```bash
# ✅ Verify both containers are running
docker ps

# Should show:
# - homeassistant (running)
# - tailscale-proxy (running)

# ✅ Check container health
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### 5. Port Binding Verification

#### 5.1 Home Assistant Listens on Localhost Only
```bash
# ✅ Verify Home Assistant binds to 127.0.0.1:8123 only
sudo netstat -tlnp | grep 8123
# or
sudo ss -tlnp | grep 8123

# Should show:
# tcp  0  0  127.0.0.1:8123  0.0.0.0:*  LISTEN  <pid>/python3
# 
# ❌ Should NOT show:
# tcp  0  0  0.0.0.0:8123  (this would be wrong - bound to all interfaces)
```

#### 5.2 socat Proxy Binds to Tailscale IP
```bash
# ✅ Check socat container logs
docker logs tailscale-proxy

# Should show:
# Tailscale IP: 100.x.x.x
# Forwarding 100.x.x.x:8123 -> 127.0.0.1:8123

# ✅ Verify socat is listening on Tailscale IP
sudo netstat -tlnp | grep 8123
# Should show socat listening on Tailscale IP
```

### 6. Network Access Verification

#### 6.1 Tailscale Access Works
```bash
# ✅ Get Tailscale IP
TAILSCALE_IP=$(tailscale ip -4)

# ✅ Test access via Tailscale IP (from server)
curl -I --connect-timeout 5 http://${TAILSCALE_IP}:8123

# Should return: HTTP/1.1 200 OK or HTTP/1.1 302 Found (redirect to login)

# ✅ Test from another Tailscale device
# From a device connected to Tailscale:
curl -I http://<tailscale-ip>:8123
# Should return HTTP 200 or 302
```

#### 6.2 LAN Access is Blocked
```bash
# ✅ Get LAN IP
LAN_IP=$(hostname -I | awk '{print $1}')

# ✅ Test LAN access (should fail/timeout)
curl -I --connect-timeout 5 http://${LAN_IP}:8123

# Should return: Connection timeout or Connection refused
# This is CORRECT - LAN access should be blocked
```

#### 6.3 Public Access is Blocked (if applicable)
```bash
# ✅ Get public IP (if you have one)
PUBLIC_IP=$(curl -s ifconfig.me)

# ✅ Test public access (should fail/timeout)
curl -I --connect-timeout 5 http://${PUBLIC_IP}:8123

# Should return: Connection timeout or Connection refused
# This is CORRECT - public access should be blocked
```

### 7. Home Assistant Configuration Verification

#### 7.1 HTTP Configuration
```bash
# ✅ Verify HTTP config binds to localhost
grep -A 10 "^http:" config/configuration.yaml

# Should show:
# server_host:
#   - 127.0.0.1
#   - ::1
# server_port: 8123
```

#### 7.2 Trusted Proxies Configuration
```bash
# ✅ Verify trusted_proxies includes Tailscale ranges
grep -A 5 "trusted_proxies:" config/configuration.yaml

# Should include:
# - 100.64.0.0/10  # Tailscale IPv4 range
# - fd7a:115c:a1e0::/48  # Tailscale IPv6 range
```

### 8. Integration Verification

#### 8.1 SimpliSafe Integration
```bash
# ✅ Check SimpliSafe integration status
# Via UI: Settings → Devices & Services → SimpliSafe
# Should show: "Connected" or "Configured"

# ✅ Verify SimpliSafe entities exist
# Via UI: Developer Tools → States
# Search for: simplisafe
# Should show entities like:
# - alarm_control_panel.simplisafe
# - binary_sensor.*motion*
```

#### 8.2 Nabu Casa Cloud Integration
```bash
# ✅ Check Nabu Casa Cloud status
# Via UI: Settings → Devices & Services → Nabu Casa Cloud
# Should show: "Connected"

# ✅ Verify Alexa devices discovered
# Via UI: Developer Tools → States
# Search for: alexa or echo
# Should show entities like:
# - media_player.kitchen_echo
# - media_player.living_room_echo
```

### 9. Automation Verification

#### 9.1 Automation Configuration
```bash
# ✅ Verify automation file exists and is valid
docker-compose exec homeassistant python -m homeassistant --script check_config

# ✅ Check automation is loaded
# Via UI: Settings → Automations & Scenes
# Should see: "SimpliSafe Motion → Alexa Alert"
# Status should be: Enabled (blue toggle)
```

#### 9.2 Automation Entity IDs
```bash
# ✅ Verify entity IDs in automation match actual entities
# Edit config/automations.yaml and verify:
# - trigger.entity_id matches your SimpliSafe motion sensors
# - condition.entity_id matches your alarm control panel
# - action service calls target your Alexa devices

# ✅ Use Developer Tools → States to find correct entity IDs
```

### 10. Functional Testing

#### 10.1 Test Home Assistant UI Access
```bash
# ✅ From a Tailscale-connected device:
# Open browser: http://<tailscale-ip>:8123
# Should load Home Assistant login page

# ✅ Login and verify dashboard loads
# Should see entities, automations, etc.
```

#### 10.2 Test SimpliSafe Motion Detection
```bash
# ✅ Arm the alarm system
# Via SimpliSafe app or Home Assistant UI
# Set to: Armed Away or Armed Home

# ✅ Trigger motion manually (walk in front of camera)
# OR manually set motion sensor state:
# Via UI: Developer Tools → States
# Find: binary_sensor.*motion*
# Set state to: "on"

# ✅ Verify automation triggers
# Via UI: Settings → Automations & Scenes
# Click on automation → Three dots → Trace
# Should show successful trigger and execution
```

#### 10.3 Test Alexa Announcement
```bash
# ✅ Verify automation trace shows TTS call
# Check automation trace (see above)
# Should show: tts.alexa_say service called

# ✅ Verify Alexa device receives announcement
# Listen for audio from configured Alexa devices
# Should hear: "Alert. Motion detected at [location]."

# ✅ Verify volume changes
# Alexa volume should increase to 70% during announcement
# Then restore to previous level (or 50% default)
```

#### 10.4 Test Cooldown Logic
```bash
# ✅ Trigger motion twice within 30 seconds
# First trigger: Should announce
# Second trigger: Should be blocked by cooldown

# ✅ Check automation trace
# First trace: Should show successful execution
# Second trace: Should show condition failed (cooldown)
```

## Security Verification

### 11. Security Hardening

#### 11.1 Port Exposure Check
```bash
# ✅ Verify port 8123 is NOT exposed via UFW
sudo ufw status numbered | grep 8123
# Should return: (nothing)

# ✅ Verify port 8123 is NOT listening on LAN interface
sudo netstat -tlnp | grep ":8123" | grep -v "127.0.0.1"
# Should return: (nothing) or only show Tailscale IP binding

# ✅ Verify port 8123 is NOT accessible from LAN
# From another device on LAN:
nmap -p 8123 <server-lan-ip>
# Should show: PORT STATE SERVICE
#             8123/tcp filtered (or closed)
```

#### 11.2 Tailscale-Only Access
```bash
# ✅ Verify only Tailscale IP allows access
# Test from Tailscale device: ✅ Should work
# Test from LAN device: ❌ Should fail
# Test from public IP: ❌ Should fail

# ✅ Verify Tailscale authentication required
tailscale status
# Should show only authenticated devices
```

## Post-Verification Checklist

After completing all verifications, confirm:

- [ ] Tailscale is running and authenticated
- [ ] NO UFW rule exists for port 8123
- [ ] Both containers (homeassistant, tailscale-proxy) are running
- [ ] Home Assistant binds to 127.0.0.1:8123 only
- [ ] socat proxy forwards Tailscale IP:8123 → 127.0.0.1:8123
- [ ] Access works via Tailscale IP
- [ ] Access is BLOCKED via LAN IP
- [ ] Access is BLOCKED via public IP (if applicable)
- [ ] SimpliSafe integration is connected
- [ ] Nabu Casa Cloud is connected
- [ ] Alexa devices are discovered
- [ ] Automation is enabled and configured
- [ ] Motion detection triggers automation
- [ ] Alexa announcement plays correctly
- [ ] Cooldown logic prevents spam
- [ ] Volume restoration works

## Quick Verification Script

Save this as `verify-setup.sh` and run: `bash verify-setup.sh`

```bash
#!/bin/bash
set -e

echo "=== Home Assistant Tailscale-Only Setup Verification ==="
echo ""

echo "1. Checking Tailscale..."
if tailscale status > /dev/null 2>&1; then
    TAILSCALE_IP=$(tailscale ip -4)
    echo "   ✅ Tailscale running, IP: $TAILSCALE_IP"
else
    echo "   ❌ Tailscale not running"
    exit 1
fi

echo ""
echo "2. Checking firewall..."
if sudo ufw status | grep -q "8123"; then
    echo "   ❌ UFW rule exists for 8123 - REMOVE IT!"
    exit 1
else
    echo "   ✅ No UFW rule for 8123"
fi

echo ""
echo "3. Checking containers..."
if docker ps | grep -q "homeassistant"; then
    echo "   ✅ Home Assistant container running"
else
    echo "   ❌ Home Assistant container not running"
    exit 1
fi

if docker ps | grep -q "tailscale-proxy"; then
    echo "   ✅ socat proxy container running"
else
    echo "   ❌ socat proxy container not running"
    exit 1
fi

echo ""
echo "4. Checking port binding..."
if sudo ss -tlnp | grep ":8123" | grep -q "127.0.0.1"; then
    echo "   ✅ Home Assistant bound to localhost only"
else
    echo "   ⚠️  Check port binding manually"
fi

echo ""
echo "5. Testing Tailscale access..."
if curl -I --connect-timeout 5 "http://${TAILSCALE_IP}:8123" > /dev/null 2>&1; then
    echo "   ✅ Accessible via Tailscale IP"
else
    echo "   ❌ Not accessible via Tailscale IP"
fi

echo ""
echo "6. Testing LAN access (should fail)..."
LAN_IP=$(hostname -I | awk '{print $1}')
if curl -I --connect-timeout 2 "http://${LAN_IP}:8123" > /dev/null 2>&1; then
    echo "   ❌ ACCESSIBLE VIA LAN - SECURITY ISSUE!"
    exit 1
else
    echo "   ✅ LAN access blocked (correct)"
fi

echo ""
echo "=== Verification Complete ==="
echo "Access Home Assistant at: http://${TAILSCALE_IP}:8123"
```

## Troubleshooting Failed Verifications

If any verification fails:

1. **Check logs**: `docker-compose logs homeassistant` and `docker-compose logs tailscale-proxy`
2. **Review configuration**: Verify `configuration.yaml` and `docker-compose.yml`
3. **Check Tailscale**: `tailscale status` and `tailscale ip -4`
4. **Restart services**: `docker-compose restart`
5. **See**: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for detailed solutions

## Regular Maintenance Checks

Run these checks periodically:

- **Weekly**: Verify containers running, Tailscale connected
- **Monthly**: Test automation end-to-end, check integration status
- **After updates**: Re-run full verification checklist
- **After reboots**: Verify auto-restart worked correctly
