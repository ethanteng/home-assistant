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

### Mode 1: Network Issues
- **Symptom**: Integrations disconnect frequently
- **Solution**: Check network stability, firewall rules, DNS

### Mode 2: API Rate Limiting
- **Symptom**: SimpliSafe integration errors, "rate limit" messages
- **Solution**: Reduce automation frequency, check SimpliSafe API limits

### Mode 3: Entity ID Changes
- **Symptom**: Automation stops working after Home Assistant update
- **Solution**: Verify entity IDs haven't changed, update automation

### Mode 4: Service Unavailable
- **Symptom**: TTS or media_player services fail
- **Solution**: Check service availability, restart Home Assistant

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

