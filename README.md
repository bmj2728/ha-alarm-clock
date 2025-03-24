# Home Assistant Smart Alarm Clock

A smart alarm clock service for Home Assistant that plays media on your Home Assistant Voice (or any media player) with gradually increasing volume. It includes features such as:

- Different alarm times for weekdays and weekends
- Person presence detection (won't trigger alarm if you're not home)
- Gradually increasing volume
- Support for local media files or streaming services
- Gotify notifications
- Health check endpoint for monitoring

## Deployment Options

There are three ways to deploy this service:

### Option 1: Using Pre-built Image (Recommended)

1. Create a new directory for the project:
   ```bash
   mkdir -p ~/ha-smart-alarm/logs
   cd ~/ha-smart-alarm
   ```

2. Download the sample docker-compose file:
   ```bash
   curl -O https://raw.githubusercontent.com/bmj2728/ha-smart-alarm/main/docker-compose-prebuild.yml -o docker-compose.yml
   ```

3. Edit the docker-compose.yml file to configure your environment variables:
   ```bash
   nano docker-compose.yml
   ```

4. Start the container:
   ```bash
   docker compose up -d
   ```

### Option 2: Building from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/bmj2728/ha-smart-alarm.git
   cd ha-smart-alarm
   mkdir -p logs
   ```

2. Edit the docker-compose.yml file to configure your environment variables:
   ```bash
   nano docker-compose.yml
   ```

3. Build and start the container:
   ```bash
   docker compose up -d --build
   ```

### Option 3: Using Docker GUI (Portainer, Synology, etc.)

1. Create a new stack/container in your Docker GUI
2. Use `ghcr.io/bmj2728/ha-smart-alarm:latest` as the image
3. Configure the environment variables as described below
4. Map port 8080 to your desired port for health checks
5. Create a volume mapping from a local folder to `/app/logs` in the container

## Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `HA_URL` | URL to your Home Assistant instance | `http://homeassistant:8123` | `http://192.168.1.100:8123` |
| `HA_TOKEN` | Long-lived access token for HA API | (Required) | `eyJhbGc...` |
| `VOICE_PE_ENTITY` | Entity ID of your media player | `media_player.home_assistant_voice_pe` | `media_player.living_room_speaker` |
| `PERSON_ENTITY` | Entity ID of the person to track | `person.user` | `person.your_name` |
| `HOME_ZONE` | Zone entity ID for your home | `zone.home` | `zone.home` |
| `GOTIFY_URL` | URL to your Gotify server (optional) | (None) | `https://gotify.example.com` |
| `GOTIFY_TOKEN` | Gotify application token (optional) | (None) | `Az9TXMfQTT29bH-` |
| `TIMEZONE` | Your local timezone | `America/New_York` | `Europe/London` |
| `WEEKDAY_ALARM_TIME` | Alarm time for weekdays (Mon-Fri) | `07:00` | `06:30` |
| `WEEKEND_ALARM_TIME` | Alarm time for weekends (Sat-Sun) | `09:00` | `08:00` |
| `WEEKDAY_ALARM_MEDIA` | Media to play for weekday alarms | `/media/audio/wake_up.mp3` | `spotify://playlist/123456` |
| `WEEKEND_ALARM_MEDIA` | Media to play for weekend alarms | `/media/audio/weekend_wakeup.mp3` | `spotify://playlist/654321` |
| `MEDIA_CONTENT_TYPE` | Media content type | `music` | `playlist` |
| `VOLUME_STEPS` | Comma-separated list of volume levels | `0.2,0.3,0.4,0.5,0.6,0.7` | `0.1,0.2,0.3,0.4` |
| `VOLUME_STEP_DELAY` | Seconds between volume increases | `20` | `30` |

## Creating a Home Assistant Long-Lived Access Token

1. In your Home Assistant instance, click on your user profile (bottom left)
2. Scroll to the bottom and click "Create Token" under Long-Lived Access Tokens
3. Give it a name (e.g., "Smart Alarm")
4. Copy the token and use it for the `HA_TOKEN` environment variable

## Health Check

The service exposes a health check endpoint on port 8080. You can use this to monitor the service's status:

```
http://your-server:8080/health
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 