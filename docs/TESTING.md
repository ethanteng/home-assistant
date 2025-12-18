# Testing Guide

How to test the SimpliSafe motion → Alexa alert automation without waiting for real motion events.

## Prerequisites

- Home Assistant is running and accessible
- SimpliSafe integration is configured
- Nabu Casa Cloud is configured
- Alexa devices are discovered
- Automation is configured in `automations.yaml`

## Method 1: Manual State Change (Simplest)

### Step 1: Arm the Alarm

1. Go to **Developer Tools** → **States**
2. Find your SimpliSafe alarm entity (e.g., `alarm_control_panel.simplisafe`)
3. Click on the entity
4. Click **SET STATE**
5. Change `state` to `armed_away` or `armed_home`
6. Click **SET STATE**

### Step 2: Trigger Motion Sensor

1. Stay in **Developer Tools** → **States**
2. Find your SimpliSafe motion sensor (e.g., `binary_sensor.front_door_camera_motion`)
3. Click on the entity
4. Click **SET STATE**
5. Change `state` from `off` to `on`
6. Click **SET STATE**

**Expected Result**: Automation should trigger immediately and Alexa should announce.

### Step 3: Verify Automation Triggered

1. Go to **Settings** → **Automations & Scenes**
2. Find **SimpliSafe Motion → Alexa Alert**
3. Click on the automation
4. Click the **three dots** menu → **Trace**
5. Review the trace to see:
   - Trigger fired
   - Conditions evaluated
   - Actions executed

## Method 2: Using Automation Trace Tool

### View Automation Trace

1. Go to **Settings** → **Automations & Scenes**
2. Click on **SimpliSafe Motion → Alexa Alert**
3. Click **three dots** menu → **Trace**
4. Click **Start new trace**
5. Trigger motion manually (Method 1, Step 2)
6. Trace will show execution flow

### What to Check in Trace

- **Trigger**: Should show motion sensor state change
- **Condition**: Should show alarm state check passed
- **Cooldown**: Should show cooldown check (first run will pass, subsequent runs within 30s will fail)
- **Actions**: Should show:
  - Timestamp update
  - Volume set
  - TTS announcement
  - Log entry

## Method 3: Test Individual Services

### Test Alexa TTS Directly

1. Go to **Developer Tools** → **Services**
2. Select service: `tts.alexa_say`
3. Fill in:
   ```yaml
   entity_id: media_player.kitchen_echo  # Your device
   message: "Test announcement from Home Assistant"
   ```
4. Click **CALL SERVICE**
5. Alexa should speak immediately

### Test Volume Control

1. Go to **Developer Tools** → **Services**
2. Select service: `media_player.volume_set`
3. Fill in:
   ```yaml
   entity_id: media_player.kitchen_echo  # Your device
   volume_level: 0.7
   ```
4. Click **CALL SERVICE**
5. Check entity state to verify volume changed

### Test Input Datetime Helper

1. Go to **Developer Tools** → **States**
2. Search for `input_datetime.last_motion_announcement`
3. Verify it exists (created automatically)
4. Manually set it to test cooldown:
   - Click entity → **SET STATE**
   - Set `datetime` to a recent time
   - This will prevent automation from triggering (cooldown active)

## Method 4: Real Motion Test (Production)

### Trigger Real SimpliSafe Motion

1. Ensure alarm is armed (`armed_away` or `armed_home`)
2. Walk in front of SimpliSafe camera
3. Wait for motion detection (may take 1-2 seconds)
4. Alexa should announce within 2-3 seconds

### Monitor in Real-Time

```bash
# Watch Home Assistant logs
docker-compose logs -f homeassistant

# Filter for automation logs
docker-compose logs -f homeassistant | grep -i "simplisafe\|motion\|alexa"
```

## Testing Cooldown Logic

### Test 1: Rapid Triggers

1. Arm alarm
2. Trigger motion sensor (Method 1)
3. Immediately trigger again (within 30 seconds)
4. **Expected**: Second trigger should be blocked by cooldown
5. Check automation trace to see cooldown condition failed

### Test 2: Delayed Triggers

1. Arm alarm
2. Trigger motion sensor
3. Wait 35 seconds
4. Trigger motion sensor again
5. **Expected**: Second trigger should succeed (cooldown expired)

### Verify Cooldown State

1. Go to **Developer Tools** → **States**
2. Find `input_datetime.last_motion_announcement`
3. Check `datetime` value - should update after each successful trigger

## Testing Multiple Alexa Devices

### Verify All Devices Receive Announcement

1. Configure automation with multiple Alexa devices
2. Trigger motion
3. **Expected**: All devices should announce simultaneously
4. If one device fails, others should still work (`continue_on_error: true`)

### Test Individual Devices

Test each device separately using Method 3 (Test Individual Services) to verify they're working before testing automation.

## Common Test Scenarios

### Scenario 1: Alarm Disarmed

1. Set alarm to `disarmed`
2. Trigger motion sensor
3. **Expected**: Automation should NOT trigger (condition fails)

### Scenario 2: Alarm Armed, No Motion

1. Set alarm to `armed_away`
2. Don't trigger motion
3. **Expected**: No announcement (normal state)

### Scenario 3: Motion While Armed

1. Set alarm to `armed_away`
2. Trigger motion sensor
3. **Expected**: Announcement plays on all configured Alexa devices

### Scenario 4: Alexa Device Offline

1. Unplug or disable one Alexa device
2. Trigger motion
3. **Expected**: Other devices still announce, offline device skipped (no error)

## Debugging Failed Tests

### Automation Not Triggering

1. Check automation is enabled:
   - **Settings** → **Automations & Scenes** → Verify toggle is ON
2. Check trigger entity ID matches actual entity
3. Check condition entity ID matches actual alarm entity
4. Review automation trace for errors

### Alexa Not Announcing

1. Test TTS service directly (Method 3)
2. Verify Alexa device is online
3. Check Nabu Casa Cloud connection status
4. Verify entity ID is correct
5. Check Home Assistant logs for errors

### Cooldown Not Working

1. Verify `input_datetime.last_motion_announcement` exists
2. Check automation trace - cooldown condition should show evaluation
3. Verify cooldown time (30 seconds) in automation YAML

## Test Checklist

Before considering automation production-ready:

- [ ] Automation triggers on motion sensor state change
- [ ] Automation only triggers when alarm is armed
- [ ] Automation does NOT trigger when alarm is disarmed
- [ ] Alexa announces message correctly
- [ ] Multiple Alexa devices receive announcement
- [ ] Cooldown prevents rapid repeated announcements
- [ ] Cooldown allows announcements after delay
- [ ] Automation trace shows successful execution
- [ ] No errors in Home Assistant logs
- [ ] Real motion detection works (walk test)

## Production Testing

After all manual tests pass:

1. Arm alarm in real mode (`armed_away`)
2. Walk in front of SimpliSafe camera
3. Verify announcement plays
4. Test multiple times to verify reliability
5. Monitor for 24 hours to catch edge cases


