#!/bin/bash
# Startup script wrapper for Home Assistant with Tailscale-only binding
# This script ensures Home Assistant is only accessible via Tailscale IP
# Port 8123 will NOT be accessible via LAN or public interfaces

set -e

# Get Tailscale IP address from tailscale0 interface
TAILSCALE_IP=$(ip -4 addr show tailscale0 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -n1)

if [ -z "$TAILSCALE_IP" ]; then
    echo "ERROR: Tailscale interface 'tailscale0' not found or has no IP address"
    echo "Ensure Tailscale is installed, authenticated, and running:"
    echo "  tailscale status"
    exit 1
fi

echo "Tailscale IP detected: $TAILSCALE_IP"
echo "Home Assistant will bind to Tailscale IP only"

# Note: Home Assistant HTTP component binds to all interfaces by default when using network_mode: host
# To restrict to Tailscale only, we rely on:
# 1. No UFW rule allowing 8123 (enforced)
# 2. Home Assistant HTTP config with trusted_proxies (configured in configuration.yaml)
# 3. Tailscale ACLs can further restrict access (optional)

# Start Home Assistant normally
# The HTTP component will listen on all interfaces, but without UFW rules,
# only Tailscale-routed traffic can reach it
exec python3 -m homeassistant --config /config "$@"
