# Tailscale-Only Access Configuration

This document explains how Home Assistant is configured for **Tailscale-only access** and why **no UFW rule for port 8123 is required or permitted**.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Ubuntu Server (boinc-mini)               │
│                                                             │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Home Assistant  │         │  socat Proxy     │         │
│  │  Container       │◄────────│  Container       │         │
│  │  127.0.0.1:8123  │         │  Tailscale:8123  │         │
│  └──────────────────┘         └──────────────────┘         │
│         ▲                              ▲                    │
│         │                              │                    │
│         └──────────────┬───────────────┘                    │
│                        │                                    │
│              tailscale0 interface                            │
│              (100.x.x.x)                                    │
└────────────────────────┼────────────────────────────────────┘
                         │
                         │ Tailscale VPN
                         │
         ┌───────────────┴───────────────┐
         │                               │
    ┌────▼────┐                    ┌────▼────┐
    │ Client  │                    │ Client  │
    │ Device  │                    │ Device  │
    └─────────┘                    └─────────┘
```

## How It Works

### 1. Home Assistant Container
- Binds to `127.0.0.1:8123` (localhost only)
- Configured via `http.server_host` in `configuration.yaml`
- **NOT accessible** from LAN or public interfaces

### 2. socat Proxy Container
- Runs in `network_mode: host` to access Tailscale interface
- Dynamically detects Tailscale IP from `tailscale0` interface
- Forwards `Tailscale-IP:8123` → `127.0.0.1:8123`
- Binds **ONLY** to Tailscale IP address

### 3. Network Security
- **No UFW rule for 8123** - socat binds directly to Tailscale IP
- Tailscale IP is on a virtual interface (`tailscale0`)
- LAN interfaces cannot reach port 8123
- Public IP cannot reach port 8123

## Why No UFW Rule Is Needed

### Traditional Setup (INCORRECT)
```bash
# ❌ WRONG - Do NOT do this
sudo ufw allow 8123/tcp
```
This would expose port 8123 to:
- LAN interfaces (security risk)
- Public interfaces (major security risk)
- All network interfaces

### Our Setup (CORRECT)
```bash
# ✅ CORRECT - No UFW rule needed
# socat binds directly to Tailscale IP only
```
Port 8123 is:
- Bound only to Tailscale IP (100.x.x.x)
- Not accessible via LAN IP
- Not accessible via public IP
- Only accessible via Tailscale VPN

## Verification Commands

### 1. Verify Tailscale is Running
```bash
# Check Tailscale status
tailscale status

# Should show:
# - Your device name (boinc-mini)
# - Tailscale IP (100.x.x.x)
# - Connected devices
```

### 2. Verify Tailscale IP
```bash
# Get Tailscale IPv4 address
tailscale ip -4

# Or via ip command
ip -4 addr show tailscale0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'
```

### 3. Verify No UFW Rule for 8123
```bash
# Check UFW status - should NOT show port 8123
sudo ufw status | grep 8123

# If it shows a rule, remove it:
# sudo ufw delete allow 8123/tcp
# sudo ufw reload
```

### 4. Verify Home Assistant Listens Only on Localhost
```bash
# Check what's listening on port 8123
sudo netstat -tlnp | grep 8123
# or
sudo ss -tlnp | grep 8123

# Should show:
# tcp  0  0  127.0.0.1:8123  0.0.0.0:*  LISTEN  <pid>/python3
# NOT: tcp  0  0  0.0.0.0:8123  (this would be wrong)
```

### 5. Verify socat Proxy is Running
```bash
# Check socat container status
docker ps | grep tailscale-proxy

# Check socat logs
docker logs tailscale-proxy

# Should show:
# Tailscale IP: 100.x.x.x
# Forwarding 100.x.x.x:8123 -> 127.0.0.1:8123
```

### 6. Test Access via Tailscale IP
```bash
# From a device connected to Tailscale:
curl -I http://<tailscale-ip>:8123

# Should return HTTP 200 or 302 (redirect to login)
# Replace <tailscale-ip> with your actual Tailscale IP
```

### 7. Verify LAN Access is Blocked
```bash
# Get LAN IP
hostname -I | awk '{print $1}'

# Try to access via LAN IP (should fail/timeout)
curl -I --connect-timeout 5 http://<lan-ip>:8123

# Should timeout or fail - this is CORRECT behavior
```

### 8. Verify Public Access is Blocked
```bash
# Get public IP (if you have one)
curl -s ifconfig.me

# Try to access via public IP (should fail/timeout)
curl -I --connect-timeout 5 http://<public-ip>:8123

# Should timeout or fail - this is CORRECT behavior
```

## Accessing Home Assistant

### From a Device on Tailscale Network

1. **Ensure device is connected to Tailscale**:
   ```bash
   tailscale status
   ```

2. **Get Home Assistant server's Tailscale IP**:
   ```bash
   # On the server (boinc-mini)
   tailscale ip -4
   ```

3. **Open browser**:
   ```
   http://<tailscale-ip>:8123
   ```
   Example: `http://100.64.1.2:8123`

### From Mobile Device

1. Install Tailscale app
2. Connect to your Tailscale network
3. Open browser: `http://<tailscale-ip>:8123`

### From Another Server

1. Install Tailscale: `curl -fsSL https://tailscale.com/install.sh | sh`
2. Authenticate: `sudo tailscale up`
3. Access: `http://<tailscale-ip>:8123`

## Troubleshooting

### Issue: Cannot Access Home Assistant

**Symptoms**: Browser shows "Connection refused" or timeout

**Solutions**:
1. Verify Tailscale is running on server:
   ```bash
   tailscale status
   ```

2. Verify Tailscale IP hasn't changed:
   ```bash
   tailscale ip -4
   ```

3. Check socat container is running:
   ```bash
   docker ps | grep tailscale-proxy
   docker logs tailscale-proxy
   ```

4. Verify Home Assistant container is running:
   ```bash
   docker ps | grep homeassistant
   docker logs homeassistant | tail -20
   ```

5. Test from server itself:
   ```bash
   curl -I http://127.0.0.1:8123
   ```

### Issue: socat Container Fails to Start

**Symptoms**: `tailscale-proxy` container exits immediately

**Solutions**:
1. Check Tailscale interface exists:
   ```bash
   ip addr show tailscale0
   ```

2. Verify Tailscale is authenticated:
   ```bash
   tailscale status
   ```

3. Check socat logs:
   ```bash
   docker logs tailscale-proxy
   ```

4. Restart Tailscale if needed:
   ```bash
   sudo systemctl restart tailscaled
   ```

### Issue: Tailscale IP Changed

**Symptoms**: Previously working access stops working

**Solutions**:
1. Get new Tailscale IP:
   ```bash
   tailscale ip -4
   ```

2. Restart docker-compose (socat will detect new IP):
   ```bash
   cd /opt/home-assistant  # or your install directory
   docker-compose restart tailscale-proxy
   ```

3. Update bookmarks/access URLs with new IP

## Advanced: Tailscale ACLs (Optional)

You can further restrict access using Tailscale Access Control Lists (ACLs):

1. **Enable ACLs** in Tailscale admin console
2. **Create ACL file** (`/etc/tailscale/acl.json`):

```json
{
  "groups": {
    "group:home-assistant-users": ["user@example.com"]
  },
  "hosts": {
    "boinc-mini": "100.64.1.2"
  },
  "acls": [
    {
      "action": "accept",
      "src": ["group:home-assistant-users"],
      "dst": ["boinc-mini:8123"]
    }
  ]
}
```

3. **Apply ACLs**:
   ```bash
   tailscale set --acls /etc/tailscale/acl.json
   ```

This restricts port 8123 access to specific Tailscale users/groups.

## Security Considerations

### ✅ What's Protected
- Port 8123 is NOT accessible via LAN
- Port 8123 is NOT accessible via public IP
- Only Tailscale-authenticated devices can access
- No firewall rules expose the port

### ⚠️ Additional Hardening (Optional)
1. **Enable Tailscale ACLs** (see above)
2. **Use Tailscale MagicDNS** for easier access:
   ```bash
   tailscale set --accept-dns=true
   ```
   Then access via: `http://boinc-mini:8123`

3. **Enable Home Assistant IP ban** (already configured):
   - `ip_ban_enabled: true`
   - `login_attempts_threshold: 5`

4. **Use strong Home Assistant passwords**
5. **Enable 2FA** in Home Assistant (Settings → People → Your User)

## Network Diagram: What Can Access What

```
┌─────────────────────────────────────────────────────────┐
│                    Internet                              │
│                                                         │
│  ❌ Public IP:8123 → BLOCKED (no route)                │
│                                                         │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼────┐            ┌────▼────┐
    │  LAN    │            │ Tailscale│
    │ Network │            │ Network │
    └────┬────┘            └────┬────┘
         │                      │
         │ ❌ LAN IP:8123       │ ✅ Tailscale IP:8123
         │    BLOCKED           │    ALLOWED
         │                      │
    ┌────▼──────────────────────▼────┐
    │      Ubuntu Server             │
    │      (boinc-mini)              │
    │                                │
    │  ┌──────────┐  ┌──────────┐   │
    │  │   HA     │  │  socat   │   │
    │  │127.0.0.1 │◄─│Tailscale │   │
    │  │  :8123   │  │  :8123   │   │
    │  └──────────┘  └──────────┘   │
    └────────────────────────────────┘
```

## Summary

- ✅ **Home Assistant binds to 127.0.0.1:8123** (localhost only)
- ✅ **socat forwards Tailscale IP:8123 → 127.0.0.1:8123**
- ✅ **No UFW rule needed** - socat binds directly to Tailscale IP
- ✅ **LAN access blocked** - port not bound to LAN interfaces
- ✅ **Public access blocked** - port not bound to public interfaces
- ✅ **Only Tailscale access** - authenticated devices only

This configuration ensures Home Assistant is **only accessible via Tailscale**, meeting the security requirement that port 8123 must never be opened via UFW or exposed to LAN/public interfaces.
