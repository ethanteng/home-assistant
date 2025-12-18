# Home Assistant Setup Guide

Complete setup instructions for Home Assistant on Ubuntu server with SimpliSafe and Alexa integration.

## Prerequisites

- Ubuntu server (tested on Ubuntu 20.04+)
- Docker installed
- Docker Compose installed
- Root or sudo access
- SimpliSafe account credentials
- Nabu Casa Cloud subscription (for Alexa integration)

## Step 1: Install Docker and Docker Compose

If not already installed:

```bash
# Update package index
sudo apt update

# Install Docker
sudo apt install -y docker.io docker-compose

# Add your user to docker group (optional, allows running without sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker-compose --version
```

## Step 2: Clone Repository

```bash
cd /opt  # or your preferred directory
git clone https://github.com/ethanteng/home-assistant.git
cd home-assistant
```

## Step 3: Configure Secrets

```bash
# Copy the secrets template
cp config/secrets.yaml.example config/secrets.yaml

# Edit secrets.yaml with your actual credentials
nano config/secrets.yaml  # or use your preferred editor
```

Fill in:
- `simplisafe_username`: Your SimpliSafe account email
- `simplisafe_password`: Your SimpliSafe account password

**Note**: If using Nabu Casa Cloud (recommended), you don't need Alexa credentials in secrets.yaml.

## Step 4: Set Permissions

```bash
# Ensure config directory has correct permissions
sudo chown -R $USER:$USER config/
chmod -R 755 config/
```

## Step 5: Configure Firewall

```bash
# Allow Home Assistant port (8123)
sudo ufw allow 8123/tcp
sudo ufw reload
```

## Step 6: Start Home Assistant

```bash
# Start container
docker-compose up -d

# View logs
docker-compose logs -f homeassistant
```

Home Assistant will start and create initial configuration files. Wait for the startup to complete (look for "Home Assistant has started" in logs).

## Step 7: Initial Home Assistant Setup

1. Open browser to `http://your-server-ip:8123`
2. Complete the initial setup wizard:
   - Create admin account
   - Set location
   - Choose integrations (skip for now, we'll add manually)

## Step 8: Configure SimpliSafe Integration

### Option A: Via UI (Recommended)

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **SimpliSafe**
4. Enter your SimpliSafe credentials
5. Follow the setup wizard
6. Note the created entities (especially alarm control panel and camera motion sensors)

### Option B: Via YAML

If UI setup fails, add to `configuration.yaml`:

```yaml
simplisafe:
  username: !secret simplisafe_username
  password: !secret simplisafe_password
```

Then restart Home Assistant.

## Step 9: Configure Nabu Casa Cloud

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **Nabu Casa Cloud**
4. Sign in with your Nabu Casa account (or create one)
5. Complete the setup wizard
6. This will automatically discover your Alexa devices

**Note**: Nabu Casa Cloud requires a subscription ($6.50/month USD). This is the recommended way to integrate Alexa with Home Assistant.

## Step 10: Verify Entities

1. Go to **Developer Tools** → **States**
2. Search for `simplisafe` - you should see:
   - `alarm_control_panel.simplisafe` (or similar)
   - `binary_sensor.*motion*` entities for cameras
3. Search for `alexa` or `echo` - you should see:
   - `media_player.*` entities for each Alexa device

See [ENTITY_DISCOVERY.md](./ENTITY_DISCOVERY.md) for detailed instructions.

## Step 11: Configure Automation

1. Edit `config/automations.yaml`
2. Update the following:
   - `entity_id` list under `trigger` with your actual SimpliSafe camera motion entities
   - `entity_id` under `condition` with your actual alarm control panel entity
   - `entity_id` lists under `action` with your actual Alexa media_player entities
3. Restart Home Assistant:
   ```bash
   docker-compose restart homeassistant
   ```

## Step 12: Verify Automation

1. Go to **Settings** → **Automations & Scenes**
2. Find **SimpliSafe Motion → Alexa Alert**
3. Verify it's enabled
4. Check the automation trace (click on automation → three dots → trace)

See [TESTING.md](./TESTING.md) for testing procedures.

## Step 13: Set Up Auto-Start (Optional)

Create a systemd service for auto-start on boot:

```bash
sudo nano /etc/systemd/system/home-assistant.service
```

Add:

```ini
[Unit]
Description=Home Assistant
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/home-assistant
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable home-assistant.service
sudo systemctl start home-assistant.service
```

## Verification Checklist

- [ ] Docker container is running: `docker ps | grep homeassistant`
- [ ] Home Assistant web UI is accessible
- [ ] SimpliSafe integration is configured and entities are visible
- [ ] Nabu Casa Cloud is configured and Alexa devices are visible
- [ ] Automation is enabled and configured correctly
- [ ] Automation triggers successfully (test with manual trigger)

## Next Steps

- Read [ENTITY_DISCOVERY.md](./ENTITY_DISCOVERY.md) to find your entity IDs
- Read [TESTING.md](./TESTING.md) to test the automation
- Read [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) if you encounter issues

## Updating Home Assistant

```bash
cd /opt/home-assistant
docker-compose pull
docker-compose up -d
```

## Backup Configuration

```bash
# Backup entire config directory
tar -czf home-assistant-backup-$(date +%Y%m%d).tar.gz config/
```

