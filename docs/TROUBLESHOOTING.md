# Troubleshooting Guide

Common issues and solutions for the SimpliSafe → Alexa alert system.

## General Debugging Steps

### Check Home Assistant Logs

```bash
# View all logs
docker-compose logs -f homeassistant

# Filter for specific components
docker-compose logs homeassistant | grep -i simplisafe
docker-compose logs homeassistant | grep -i alexa
docker-compose logs homeassistant | grep -i automation

# View last 100 lines
docker-compose logs --tail=100 homeassistant
```

### Check Container Status

```bash
# Verify container is running
docker ps | grep homeassistant

# Check container health
docker inspect homeassistant | grep -A 10 Health
```

### Verify Configuration

```bash
# Check YAML syntax
docker-compose exec homeassistant python -m homeassistant --script check_config

# Or via UI: Developer Tools → YAML → Check Configuration
```

## Issue: Automation Not Triggering

### Symptoms
- Motion detected but no Alexa announcement
- Automation trace shows no trigger

### Solutions

1. **Verify automation is enabled**
   - Go to **Settings** → **Automations & Scenes**
   - Find **SimpliSafe Motion → Alexa Alert**
   - Ensure toggle is ON (blue)

2. **Check entity IDs**
   - Verify motion sensor entity IDs in `automations.yaml` match actual entities
   - Use Developer Tools → States to find correct entity IDs
   - See [ENTITY_DISCOVERY.md](./ENTITY_DISCOVERY.md)

3. **Verify trigger configuration**
   - Check `trigger.entity_id` list contains your motion sensors
   - Ensure `to: "on"` matches motion sensor state
   - Check `for:` duration isn't too long

4. **Check automation mode**
   - Verify `mode: single` is set (prevents parallel executions)
   - If using `mode: restart`, change to `single`

5. **Review automation trace**
   - Go to automation → three dots → Trace
   - Check if trigger fired
   - Check if conditions passed
   - Look for errors in action execution

## Issue: Automation Triggers But Alexa Doesn't Announce

### Symptoms
- Automation trace shows successful execution
- No audio from Alexa devices

### Solutions

1. **Test TTS service directly**
   - Developer Tools → Services → `tts.alexa_say`
   - If this fails, issue is with Alexa integration, not automation

2. **Verify Alexa device entities**
   - Check entity IDs in automation match actual devices
   - Verify devices are online (check state in Developer Tools)
   - Ensure devices aren't in Do Not Disturb mode

3. **Check Nabu Casa Cloud connection**
   - Settings → Devices & Services → Nabu Casa Cloud
   - Verify status is "Connected"
   - If disconnected, reconnect or restart Home Assistant

4. **Verify volume level**
   - Check if volume is set too low (automation sets to 0.7)
   - Test volume control manually
   - Ensure device isn't muted

5. **Check for errors in logs**
   ```bash
   docker-compose logs homeassistant | grep -i "alexa\|tts\|error"
   ```

## Issue: Automation Triggers When Alarm Is Disarmed

### Symptoms
- Announcements play even when alarm is off
- Condition check seems to be ignored

### Solutions

1. **Verify alarm entity ID**
   - Check `condition.entity_id` matches your actual alarm entity
   - Use Developer Tools → States to find correct entity ID

2. **Check alarm state values**
   - Verify your alarm uses `armed_away` and `armed_home` states
   - Some systems may use different state names
   - Check entity state in Developer Tools

3. **Test condition manually**
   - Set alarm to `disarmed`
   - Trigger motion sensor manually
   - Check automation trace - condition should fail

4. **Verify condition syntax**
   - Ensure `condition: or` wraps both state conditions
   - Check indentation in YAML

## Issue: Cooldown Not Working

### Symptoms
- Rapid repeated announcements
- Automation triggers multiple times quickly

### Solutions

1. **Verify input_datetime helper exists**
   - Developer Tools → States → Search for `input_datetime.last_motion_announcement`
   - If missing, create it manually or restart Home Assistant

2. **Check cooldown time**
   - Verify 30 seconds is appropriate (adjust if needed)
   - Check template syntax in condition

3. **Test cooldown logic**
   - Trigger motion twice within 30 seconds
   - Second trigger should be blocked
   - See [TESTING.md](./TESTING.md) for details

4. **Review automation trace**
   - Check cooldown condition evaluation
   - Verify timestamp is being updated

## Issue: SimpliSafe Integration Not Working

### Symptoms
- No SimpliSafe entities visible
- Integration shows error in UI

### Solutions

1. **Verify credentials**
   - Check `secrets.yaml` has correct SimpliSafe username/password
   - Ensure no extra spaces or quotes
   - Test login at simplisafe.com

2. **Check integration status**
   - Settings → Devices & Services → SimpliSafe
   - If error, click "Configure" and re-enter credentials
   - Check for API rate limiting messages

3. **Review SimpliSafe logs**
   ```bash
   docker-compose logs homeassistant | grep -i simplisafe
   ```

4. **Restart Home Assistant**
   ```bash
   docker-compose restart homeassistant
   ```

5. **Re-add integration**
   - Remove SimpliSafe integration
   - Re-add via UI
   - Verify entities appear

## Issue: Alexa Devices Not Discovered

### Symptoms
- No `media_player` entities for Alexa
- Nabu Casa Cloud shows no devices

### Solutions

1. **Verify Nabu Casa Cloud connection**
   - Settings → Devices & Services → Nabu Casa Cloud
   - Status should be "Connected"
   - If disconnected, reconnect

2. **Check Alexa devices**
   - Ensure devices are online in Alexa app
   - Verify devices use same Amazon account as Nabu Casa
   - Check devices aren't in setup mode

3. **Sync devices**
   - In Nabu Casa integration, click "Reload" or "Sync"
   - Wait a few minutes for discovery

4. **Restart Home Assistant**
   ```bash
   docker-compose restart homeassistant
   ```

5. **Check Amazon account**
   - Verify Nabu Casa uses correct Amazon account
   - Some features require Amazon account linking

## Issue: Nabu Casa Cloud Disconnected

### Symptoms
- Nabu Casa integration shows "Disconnected"
- Alexa devices unavailable

### Solutions

1. **Check internet connection**
   ```bash
   docker-compose exec homeassistant ping -c 3 cloud.nabucasa.com
   ```

2. **Verify subscription**
   - Check Nabu Casa account status
   - Ensure subscription is active

3. **Reconnect**
   - Settings → Devices & Services → Nabu Casa Cloud
   - Click "Configure" → "Reconnect"
   - Follow setup wizard

4. **Check firewall**
   - Ensure outbound HTTPS (443) is allowed
   - Nabu Casa requires internet access

5. **Review logs**
   ```bash
   docker-compose logs homeassistant | grep -i nabu
   ```

## Issue: Home Assistant Won't Start

### Solutions

1. **Check YAML syntax**
   ```bash
   docker-compose exec homeassistant python -m homeassistant --script check_config
   ```

2. **Check logs for errors**
   ```bash
   docker-compose logs homeassistant
   ```

3. **Verify file permissions**
   ```bash
   ls -la config/
   sudo chown -R $USER:$USER config/
   ```

4. **Check disk space**
   ```bash
   df -h
   ```

5. **Remove problematic files**
   - Temporarily rename `automations.yaml` to test
   - If starts, issue is in automation YAML

## Issue: Automation Survives Reboot But Stops Working

### Solutions

1. **Verify restart policy**
   - Check `docker-compose.yml` has `restart: unless-stopped`
   - Verify container auto-starts: `docker ps`

2. **Check systemd service** (if configured)
   ```bash
   sudo systemctl status home-assistant
   ```

3. **Verify entities still exist**
   - After reboot, check SimpliSafe and Alexa entities
   - Some integrations need time to reconnect

4. **Check integration status**
   - Verify SimpliSafe and Nabu Casa reconnect after reboot
   - May take 1-2 minutes

## Issue: Volume Not Restoring

### Symptoms
- Alexa volume stays at 70% after announcement
- Original volume not restored

### Solutions

**Note**: Current automation doesn't restore volume by design (simplified). To add volume restoration:

1. **Store original volume**
   - Use template to capture current volume before setting
   - Store in input_number helper or variable

2. **Restore after announcement**
   - Add action to restore volume after TTS completes
   - Use delay to ensure announcement finishes first

3. **Example implementation**:
   ```yaml
   - variables:
       original_volume: "{{ state_attr(trigger.entity_id, 'volume_level') }}"
   - service: media_player.volume_set
     data:
       volume_level: 0.7
   - service: tts.alexa_say
     # ... TTS call ...
   - delay:
       seconds: 5
   - service: media_player.volume_set
     data:
       volume_level: "{{ original_volume }}"
   ```

## Common Failure Modes

### Mode 1: Tailscale is Down

**Symptoms**:
- Cannot access Home Assistant UI via Tailscale IP
- `tailscale status` shows disconnected
- socat container logs show "Tailscale IP not found"

**Impact**:
- Home Assistant UI inaccessible remotely
- Home Assistant continues running and processing automations
- Integrations (SimpliSafe, Nabu Casa) continue working
- Local access via SSH still works

**Solutions**:
```bash
# Check Tailscale service status
sudo systemctl status tailscaled

# Restart Tailscale
sudo systemctl restart tailscaled

# Re-authenticate if needed
sudo tailscale up

# Verify connection
tailscale status

# Restart socat proxy after Tailscale is back
docker-compose restart tailscale-proxy
```

**Prevention**:
- Monitor Tailscale service: `sudo systemctl enable tailscaled`
- Set up Tailscale service monitoring
- Consider Tailscale key rotation policies

**What Survives**:
- ✅ Home Assistant container continues running
- ✅ All automations continue executing
- ✅ SimpliSafe integration continues working
- ✅ Local system operations unaffected

---

### Mode 2: Tailscale IP Changed

**Symptoms**:
- Previously working Tailscale URL stops working
- Browser shows "Connection refused"
- New Tailscale IP assigned

**Impact**:
- Temporary loss of remote access
- Home Assistant continues running normally

**Solutions**:
```bash
# Get new Tailscale IP
tailscale ip -4

# Restart socat proxy to detect new IP
docker-compose restart tailscale-proxy

# Verify new IP is being used
docker logs tailscale-proxy | grep "Tailscale IP"

# Update bookmarks/access URLs
```

**Prevention**:
- Use Tailscale MagicDNS: `tailscale set --accept-dns=true`
- Access via hostname: `http://boinc-mini:8123` (doesn't change)
- Monitor Tailscale IP changes

**What Survives**:
- ✅ All Home Assistant functionality
- ✅ All automations and integrations
- ✅ Just need to update access URL

---

### Mode 3: socat Proxy Container Fails

**Symptoms**:
- `docker ps` shows `tailscale-proxy` as exited
- Cannot access Home Assistant via Tailscale IP
- Home Assistant logs show no errors

**Impact**:
- Complete loss of remote access via Tailscale
- Home Assistant continues running (accessible via localhost only)

**Solutions**:
```bash
# Check container logs
docker logs tailscale-proxy

# Verify Tailscale interface exists
ip addr show tailscale0

# Restart container
docker-compose restart tailscale-proxy

# If persistent, check Tailscale status
tailscale status

# Full restart if needed
docker-compose down
docker-compose up -d
```

**Prevention**:
- Monitor container health: `docker ps`
- Set up container restart monitoring
- Check logs regularly: `docker logs tailscale-proxy`

**What Survives**:
- ✅ Home Assistant container and all functionality
- ✅ All automations continue working
- ✅ Just remote access is affected

---

### Mode 4: Nabu Casa Cloud Disconnected

**Symptoms**:
- Alexa announcements stop working
- Automation triggers but no audio
- Nabu Casa integration shows "Disconnected" in UI

**Impact**:
- Motion alerts trigger but no Alexa announcements
- SimpliSafe integration continues working
- Other automations unaffected

**Solutions**:
```bash
# Check internet connectivity from container
docker-compose exec homeassistant ping -c 3 cloud.nabucasa.com

# Check Nabu Casa status in Home Assistant UI
# Settings → Devices & Services → Nabu Casa Cloud

# Restart Home Assistant
docker-compose restart homeassistant

# Verify subscription status at nabucasa.com
```

**Prevention**:
- Monitor Nabu Casa connection status
- Set up alerts for integration disconnections
- Ensure stable internet connection

**What Survives**:
- ✅ All Home Assistant functionality
- ✅ SimpliSafe integration and automations
- ✅ Motion detection continues
- ❌ Only Alexa announcements fail

---

### Mode 5: SimpliSafe Integration Disconnected

**Symptoms**:
- Motion sensors stop updating
- Automation doesn't trigger
- SimpliSafe integration shows error in UI

**Impact**:
- Motion detection stops working
- No alerts triggered
- Alexa announcements won't fire (no trigger)

**Solutions**:
```bash
# Check SimpliSafe logs
docker-compose logs homeassistant | grep -i simplisafe

# Verify credentials in secrets.yaml
cat config/secrets.yaml | grep simplisafe

# Restart Home Assistant
docker-compose restart homeassistant

# Re-authenticate SimpliSafe integration via UI
# Settings → Devices & Services → SimpliSafe → Configure
```

**Prevention**:
- Monitor SimpliSafe integration status
- Set up alerts for integration failures
- Keep SimpliSafe credentials updated

**What Survives**:
- ✅ Home Assistant continues running
- ✅ Other automations continue
- ✅ Alexa integration continues working
- ❌ Only SimpliSafe motion detection fails

---

### Mode 6: Server Reboot

**Symptoms**:
- All services restart automatically
- Tailscale reconnects
- Containers restart

**Impact**:
- Brief downtime during reboot
- Services auto-restart (if configured correctly)

**Solutions**:
```bash
# Verify containers auto-started
docker ps

# Check Tailscale reconnected
tailscale status

# Verify socat proxy started
docker logs tailscale-proxy

# Check Home Assistant started
docker logs homeassistant | tail -20
```

**What Survives**:
- ✅ Docker containers auto-restart (`restart: unless-stopped`)
- ✅ Tailscale auto-connects (systemd service)
- ✅ All configurations persist
- ⚠️ Brief downtime during reboot (~1-2 minutes)

**Prevention**:
- Ensure `restart: unless-stopped` in docker-compose.yml
- Enable Tailscale service: `sudo systemctl enable tailscaled`
- Test reboot recovery: `sudo reboot`

---

### Mode 7: Motion Detected But No Announcement

**Symptoms**:
- SimpliSafe motion sensor triggers
- Automation trace shows execution
- No audio from Alexa devices

**Diagnostic Steps**:
```bash
# 1. Check automation trace in UI
# Settings → Automations & Scenes → SimpliSafe Motion → Alexa Alert → Trace

# 2. Verify alarm is armed
# Developer Tools → States → alarm_control_panel.simplisafe

# 3. Test TTS service directly
# Developer Tools → Services → tts.alexa_say

# 4. Check Alexa device states
# Developer Tools → States → media_player.* (your devices)

# 5. Check logs
docker-compose logs homeassistant | grep -i "alexa\|tts\|motion"
```

**Common Causes**:
1. **Alarm not armed**: Automation condition fails
2. **Cooldown active**: Recent announcement blocks new one
3. **Alexa device offline**: Device unavailable
4. **Nabu Casa disconnected**: Cloud connection lost
5. **Volume too low**: Device muted or volume 0
6. **Entity IDs incorrect**: Wrong device IDs in automation

**Solutions**:
- Verify alarm state: `armed_away` or `armed_home`
- Check cooldown: Wait 30+ seconds between tests
- Verify Alexa devices online in Home Assistant
- Test TTS service directly
- Check automation trace for errors
- Verify entity IDs match actual devices

**What Survives**:
- ✅ Motion detection continues
- ✅ Automation continues triggering
- ✅ All other functionality works
- ❌ Only announcement fails (diagnosable)

---

### Mode 8: Network Issues

**Symptoms**:
- Integrations disconnect frequently
- Intermittent connection errors
- Timeouts in logs

**Impact**:
- Unreliable automation execution
- Missed motion alerts
- Integration failures

**Solutions**:
```bash
# Check network connectivity
ping -c 3 8.8.8.8

# Check DNS resolution
nslookup cloud.nabucasa.com

# Check Tailscale connectivity
tailscale ping <other-device>

# Restart network services if needed
sudo systemctl restart networking
sudo systemctl restart tailscaled
```

**Prevention**:
- Monitor network stability
- Use reliable DNS servers
- Ensure stable internet connection
- Monitor integration status

---

### Mode 9: API Rate Limiting

**Symptoms**:
- SimpliSafe integration errors
- "Rate limit exceeded" messages in logs
- Integration stops updating

**Impact**:
- Motion sensors stop updating
- Automation triggers fail

**Solutions**:
```bash
# Check SimpliSafe logs
docker-compose logs homeassistant | grep -i "rate limit\|simplisafe"

# Reduce automation frequency (increase cooldown)
# Edit config/automations.yaml - increase cooldown_seconds

# Restart Home Assistant
docker-compose restart homeassistant
```

**Prevention**:
- Use appropriate cooldown periods (30+ seconds)
- Monitor API usage
- Avoid rapid polling

---

### Mode 10: Entity ID Changes

**Symptoms**:
- Automation stops working after Home Assistant update
- "Entity not found" errors
- Motion sensors not triggering

**Impact**:
- Automation fails silently
- No alerts triggered

**Solutions**:
```bash
# Find current entity IDs
# Developer Tools → States → Search for "simplisafe" or "motion"

# Update automation YAML with correct IDs
nano config/automations.yaml

# Restart Home Assistant
docker-compose restart homeassistant
```

**Prevention**:
- Document entity IDs
- Use friendly names where possible
- Test after Home Assistant updates
- Monitor automation traces

---

## Failure Mode Summary

| Failure Mode | Home Assistant | Automations | SimpliSafe | Alexa | Remote Access |
|--------------|----------------|-------------|------------|-------|---------------|
| Tailscale Down | ✅ Running | ✅ Working | ✅ Working | ✅ Working | ❌ Blocked |
| Tailscale IP Changed | ✅ Running | ✅ Working | ✅ Working | ✅ Working | ⚠️ URL Update |
| socat Proxy Fails | ✅ Running | ✅ Working | ✅ Working | ✅ Working | ❌ Blocked |
| Nabu Casa Down | ✅ Running | ✅ Working | ✅ Working | ❌ Failed | ✅ Working |
| SimpliSafe Down | ✅ Running | ⚠️ No Triggers | ❌ Failed | ✅ Working | ✅ Working |
| Server Reboot | ⚠️ Restarting | ⚠️ Brief Pause | ⚠️ Reconnecting | ⚠️ Reconnecting | ⚠️ Brief Pause |
| Motion/No Announce | ✅ Running | ✅ Triggering | ✅ Working | ❌ Failed | ✅ Working |

**Legend**:
- ✅ = Fully functional
- ⚠️ = Degraded or temporary issue
- ❌ = Failed or blocked

## Getting Help

If issues persist:

1. **Collect information**:
   - Home Assistant version: Settings → System → About
   - Relevant log excerpts
   - Automation trace output
   - Entity IDs and states

2. **Check Home Assistant forums**:
   - [community.home-assistant.io](https://community.home-assistant.io)

3. **Review integration documentation**:
   - SimpliSafe: [Home Assistant SimpliSafe docs](https://www.home-assistant.io/integrations/simplisafe/)
   - Nabu Casa: [Nabu Casa docs](https://www.nabucasa.com/)

4. **Verify system requirements**:
   - Docker version compatibility
   - Ubuntu version compatibility
   - Resource availability (CPU, memory, disk)


