# Home Assistant Smart Alarm Clock - User Guide

## Overview

The Home Assistant Smart Alarm Clock is an enhanced application that integrates with Home Assistant to provide a flexible alarm clock system with multiple alarms, a user-friendly interface, and robust functionality.

## Features

- **Multiple Alarms**: Create and manage multiple alarms for any day of the week
- **Streamlit UI**: User-friendly web interface for managing alarms
- **Flexible Scheduling**: Set alarms for specific days or day patterns (weekdays, weekends)
- **Volume Ramping**: Gradually increase volume for gentle wake-up
- **Presence Detection**: Skip alarms when you're not home
- **Morning Briefing**: Get weather and calendar information after your alarm
- **Snooze Functionality**: Snooze active alarms as needed
- **Persistent Storage**: All alarms are stored in a database for reliability

## Installation

### Docker Installation (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/bmj2728/ha-alarm-clock.git
   cd ha-alarm-clock
   ```

2. Configure the application by creating a `config/config.yaml` file:
   ```yaml
   ha_url: http://your-home-assistant-url:8123
   ha_token: your_long_lived_access_token
   voice_pe_entity: media_player.your_media_player
   person_entity: person.your_name
   home_zone: zone.home
   ```

3. Start the application using Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. Access the UI at `http://your-server-ip:8501`

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/bmj2728/ha-alarm-clock.git
   cd ha-alarm-clock
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the application by creating a `config/config.yaml` file:
   ```yaml
   ha_url: http://your-home-assistant-url:8123
   ha_token: your_long_lived_access_token
   voice_pe_entity: media_player.your_media_player
   person_entity: person.your_name
   home_zone: zone.home
   ```

4. Start the application:
   ```bash
   # Start both the service and UI
   python -m app.main --config config/config.yaml &
   streamlit run app/streamlit_ui_integrated.py
   
   # Or start just the UI
   streamlit run app/streamlit_ui_integrated.py
   ```

5. Access the UI at `http://your-server-ip:8501`

## Using the UI

### Dashboard

The dashboard provides an overview of your alarms:

- **Upcoming Alarms**: Shows all enabled alarms
- **Disabled Alarms**: Shows alarms that are currently disabled
- **Quick Actions**: Buttons to view/edit, enable/disable, or test alarms

### Adding an Alarm

1. Click the "Add New Alarm" button in the sidebar
2. Fill in the alarm details:
   - **Name**: A descriptive name for the alarm
   - **Time**: The alarm time in HH:MM format
   - **Days**: Select the days when the alarm should trigger
   - **Media URL**: URL or path to the media to play
   - **Media Type**: Type of media (music or playlist)
3. Expand "Advanced Settings" to configure:
   - **Volume Steps**: Comma-separated list of volume levels (0.0-1.0)
   - **Volume Step Delay**: Seconds between volume increases
   - **Person Entity**: Home Assistant entity for presence detection
   - **Enabled**: Whether the alarm is active
4. Click "Create Alarm"

### Viewing and Editing Alarms

1. Click on an alarm in the sidebar or dashboard
2. The "View" tab shows alarm details and provides actions:
   - **Enable/Disable**: Toggle alarm activation
   - **Test Alarm**: Trigger the alarm for testing
   - **Duplicate Alarm**: Create a copy of the alarm
   - **Delete Alarm**: Remove the alarm
3. The "Edit" tab allows you to modify all alarm settings

### Handling Active Alarms

When an alarm is active:

1. A banner appears at the top of the UI
2. You can choose to:
   - **Snooze**: Pause the alarm for 5 minutes
   - **Dismiss**: Stop the alarm completely

### Settings

The Settings page allows you to configure:

- **Home Assistant Connection**: URL and access token
- **Notifications**: Gotify integration for notifications
- **System Settings**: Timezone, logging, and health check
- **Database Operations**: Export and import alarms
- **Service Control**: Restart the alarm service

## Command Line Interface

For advanced users, a command-line interface is available:

```bash
# List all alarms
python scripts/alarm_cli.py list

# Create a new alarm
python scripts/alarm_cli.py create --name "Work Alarm" --time "07:30" --days "[0,1,2,3,4]" --media-url "/media/audio/wake_up.mp3"

# Update an alarm
python scripts/alarm_cli.py update 1 --name "Updated Alarm" --time "08:00"

# Delete an alarm
python scripts/alarm_cli.py delete 1
```

## Troubleshooting

### UI Not Loading

- Ensure Streamlit is running on port 8501
- Check for errors in the logs at `logs/streamlit_ui.log`

### Alarms Not Triggering

- Verify Home Assistant connection in Settings
- Check that the media player entity is correct
- Ensure the alarm is enabled and scheduled for the current day
- Check logs at `logs/alarm_service.log`

### Database Issues

- If alarms aren't persisting, check database permissions
- Try exporting and reimporting alarms from the Settings page

## Advanced Configuration

### Custom Media

Place custom audio files in the `media/audio` directory and reference them in alarms:

```
/media/audio/your_custom_file.mp3
```

### Environment Variables

Instead of a config file, you can use environment variables:

```
HA_URL=http://your-home-assistant-url:8123
HA_TOKEN=your_long_lived_access_token
VOICE_PE_ENTITY=media_player.your_media_player
PERSON_ENTITY=person.your_name
HOME_ZONE=zone.home
```

## Support

For issues or feature requests, please open an issue on GitHub:
https://github.com/bmj2728/ha-alarm-clock/issues
