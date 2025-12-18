# Entity Discovery Guide

How to find and identify SimpliSafe and Alexa entities in Home Assistant.

## Finding SimpliSafe Entities

### Alarm Control Panel

1. Go to **Developer Tools** → **States**
2. Search for `alarm_control_panel`
3. Look for entities containing `simplisafe`, for example:
   - `alarm_control_panel.simplisafe`
   - `alarm_control_panel.simplisafe_12345` (with account ID)

**Verify states**: Click on the entity to see available states:
- `disarmed`
- `armed_away`
- `armed_home`
- `armed_night`
- `triggered`

### Camera Motion Sensors

1. Go to **Developer Tools** → **States**
2. Search for `binary_sensor` and filter by `simplisafe`
3. Look for motion-related entities, for example:
   - `binary_sensor.front_door_camera_motion`
   - `binary_sensor.back_door_camera_motion`
   - `binary_sensor.garage_camera_motion`

**Verify behavior**:
- State should be `off` when no motion
- State changes to `on` when motion is detected
- Check `attributes` → `friendly_name` to identify camera location

### Finding All SimpliSafe Entities

Use the filter in Developer Tools → States:
- Type: `simplisafe` (shows all SimpliSafe entities)
- Or use YAML: Check `config/.storage/core.entity_registry` (advanced)

## Finding Alexa Entities

### Via Nabu Casa Cloud

1. Go to **Developer Tools** → **States**
2. Search for `media_player`
3. Filter by `alexa` or `echo`
4. Look for entities like:
   - `media_player.kitchen_echo`
   - `media_player.living_room_echo`
   - `media_player.bedroom_alexa`

**Entity naming**: Alexa entities typically follow the pattern:
- `media_player.{device_name}_{device_type}`
- Device name comes from your Alexa app device settings

### Verify Alexa Device States

Click on a `media_player` entity to check:
- `state`: `idle`, `playing`, `paused`, etc.
- `attributes`:
  - `friendly_name`: Human-readable name
  - `volume_level`: Current volume (0.0 to 1.0)
  - `is_volume_muted`: Boolean

### Finding All Alexa Devices

1. Go to **Settings** → **Devices & Services**
2. Click on **Nabu Casa Cloud** integration
3. Click **Devices** tab
4. All discovered Alexa devices will be listed here

## Testing Entity States Manually

### Test SimpliSafe Motion Sensor

1. Go to **Developer Tools** → **States**
2. Find your motion sensor entity (e.g., `binary_sensor.front_door_camera_motion`)
3. Click on the entity
4. Click **SET STATE** button
5. Change `state` from `off` to `on`
6. Click **SET STATE**
7. This will trigger the automation (if alarm is armed)

**Note**: This is a manual test. Real motion detection comes from SimpliSafe API.

### Test Alexa TTS

1. Go to **Developer Tools** → **Services**
2. Select service: `tts.alexa_say`
3. Fill in:
   - `entity_id`: Your Alexa device (e.g., `media_player.kitchen_echo`)
   - `message`: "Test announcement"
4. Click **CALL SERVICE**
5. Alexa should speak the message

### Test Volume Control

1. Go to **Developer Tools** → **Services**
2. Select service: `media_player.volume_set`
3. Fill in:
   - `entity_id`: Your Alexa device
   - `volume_level`: `0.7` (70%)
4. Click **CALL SERVICE**
5. Check the entity state to verify volume changed

## Common Entity Patterns

### SimpliSafe

- Alarm: `alarm_control_panel.simplisafe*`
- Motion: `binary_sensor.*motion*`
- Cameras: `camera.simplisafe*`
- Sensors: `binary_sensor.*` or `sensor.*`

### Alexa

- Devices: `media_player.*alexa*` or `media_player.*echo*`
- Sometimes: `media_player.{room_name}` (if device name matches room)

## Using Entity IDs in Automation

Once you've identified your entities:

1. Copy the full entity ID (e.g., `binary_sensor.front_door_camera_motion`)
2. Update `config/automations.yaml`:
   - Replace placeholder entity IDs in `trigger.entity_id` list
   - Replace placeholder in `condition.entity_id`
   - Replace placeholders in `action` service calls

## Troubleshooting Entity Discovery

### SimpliSafe entities not appearing

1. Check SimpliSafe integration status:
   - **Settings** → **Devices & Services** → **SimpliSafe**
   - Verify status is "Configured"
2. Check logs:
   ```bash
   docker-compose logs homeassistant | grep simplisafe
   ```
3. Verify credentials in `secrets.yaml`
4. Restart Home Assistant

### Alexa entities not appearing

1. Check Nabu Casa Cloud status:
   - **Settings** → **Devices & Services** → **Nabu Casa Cloud**
   - Verify status is "Connected"
2. Ensure Alexa devices are:
   - Online in Alexa app
   - Same Amazon account as Nabu Casa
   - Not in Do Not Disturb mode
3. Restart Home Assistant
4. Re-sync devices in Nabu Casa integration settings

### Entity names don't match expected pattern

Entity names depend on:
- SimpliSafe device names (set in SimpliSafe app)
- Alexa device names (set in Alexa app)
- Home Assistant's entity registry

If names are unclear:
1. Check `friendly_name` attribute in Developer Tools
2. Use friendly names in automation templates
3. Rename entities in Home Assistant UI if needed


