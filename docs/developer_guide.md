# Home Assistant Smart Alarm Clock - Developer Guide

## Architecture Overview

The Home Assistant Smart Alarm Clock has been refactored into a modular application with clear separation of concerns. This document provides an overview of the architecture and guidance for developers who want to extend or modify the application.

## Directory Structure

```
ha-alarm-clock/
├── app/                      # Main application code
│   ├── alarm_manager/        # Alarm scheduling and triggering
│   ├── config/               # Configuration management
│   ├── database/             # Database operations and models
│   ├── ha_client/            # Home Assistant API client
│   ├── ui_integration/       # Integration between UI and core functionality
│   ├── utils/                # Utility functions
│   ├── main.py               # Main entry point for the service
│   ├── streamlit_ui.py       # Basic Streamlit UI
│   └── streamlit_ui_integrated.py  # Enhanced UI with integration
├── config/                   # Configuration files
├── data/                     # Database files
├── docs/                     # Documentation
├── logs/                     # Log files
├── media/                    # Media files
│   └── audio/                # Audio files for alarms
├── scripts/                  # Utility scripts
│   ├── alarm_cli.py          # Command-line interface
│   ├── integration_test.py   # Integration tests
│   ├── migrate_database.py   # Database migration
│   └── test_functionality.py # Unit tests
├── docker-compose.yml        # Docker Compose configuration
├── Dockerfile                # Docker build configuration
└── requirements.txt          # Python dependencies
```

## Core Components

### ConfigManager

The `ConfigManager` class in `app/config/config_manager.py` handles loading and saving configuration from various sources:
- YAML/JSON configuration files
- Environment variables
- Default values

```python
from app.config import ConfigManager

# Initialize with optional config file
config = ConfigManager('config.yaml')

# Get configuration values
ha_url = config.get('ha_url')
ha_token = config.get('ha_token')

# Set configuration values
config.set('log_level', 'DEBUG')

# Save configuration
config.save()
```

### DatabaseManager

The `DatabaseManager` class in `app/database/database_manager.py` provides an interface to the SQLite database using SQLAlchemy ORM:

```python
from app.database import DatabaseManager, Alarm

# Initialize database
db_manager = DatabaseManager('alarms.db')

# Create alarm
alarm_data = {
    'name': 'Weekday Alarm',
    'time': '07:00',
    'days': [0, 1, 2, 3, 4],  # Monday to Friday
    'enabled': True,
    'media_url': '/media/audio/wake_up.mp3',
    'media_type': 'music'
}
alarm = db_manager.create_alarm(alarm_data)

# Get all alarms
alarms = db_manager.get_all_alarms()

# Update alarm
db_manager.update_alarm(alarm.id, {'time': '07:30'})

# Delete alarm
db_manager.delete_alarm(alarm.id)
```

### HomeAssistantClient

The `HomeAssistantClient` class in `app/ha_client/ha_client.py` handles all interactions with the Home Assistant API:

```python
from app.ha_client import HomeAssistantClient

# Initialize client
ha_client = HomeAssistantClient(
    'http://homeassistant:8123',
    'your_long_lived_access_token'
)

# Check if Home Assistant is available
if ha_client.is_available():
    # Get entity state
    state = ha_client.get_state('media_player.living_room')
    
    # Play media
    ha_client.play_media(
        'media_player.living_room',
        '/media/audio/wake_up.mp3',
        'music'
    )
    
    # Set volume
    ha_client.set_volume('media_player.living_room', 0.5)
```

### AlarmManager

The `AlarmManager` class in `app/alarm_manager/alarm_manager.py` handles alarm scheduling and triggering:

```python
from app.alarm_manager import AlarmManager

# Initialize alarm manager
alarm_manager = AlarmManager(config, ha_client, db_manager)

# Start alarm manager
alarm_manager.start()

# Schedule alarms
alarm_manager.schedule_alarms()

# Trigger alarm
alarm_manager.trigger_alarm(alarm_id)

# Snooze active alarm
alarm_manager.snooze_alarm(5)  # 5 minutes

# Dismiss active alarm
alarm_manager.dismiss_alarm()

# Stop alarm manager
alarm_manager.stop()
```

### UIIntegration

The `UIIntegration` class in `app/ui_integration/ui_integration.py` connects the Streamlit UI with the alarm functionality:

```python
from app.ui_integration import UIIntegration

# Initialize UI integration
ui_integration = UIIntegration(alarm_manager, db_manager)

# Start status monitoring
ui_integration.start_status_monitoring()

# Get current status
status = ui_integration.get_status()

# Snooze active alarm
ui_integration.snooze_active_alarm(5)  # 5 minutes

# Dismiss active alarm
ui_integration.dismiss_active_alarm()

# Test alarm
ui_integration.test_alarm(alarm_id)

# Restart alarm service
ui_integration.restart_alarm_service()

# Stop status monitoring
ui_integration.stop_status_monitoring()
```

## Database Schema

The application uses SQLAlchemy ORM with the following schema:

### Alarm Model

```python
class Alarm(Base):
    __tablename__ = 'alarms'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    time = Column(String, nullable=False)  # Format: HH:MM
    days = Column(String, nullable=False)  # JSON array of days (0-6, 0=Monday)
    enabled = Column(Boolean, default=True)
    media_url = Column(String, nullable=False)
    media_type = Column(String, default='music')
    volume_steps = Column(String)  # JSON array of volume levels
    volume_step_delay = Column(Integer, default=20)
    person_entity = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## Streamlit UI

The Streamlit UI is implemented in `app/streamlit_ui_integrated.py` and provides a web-based interface for managing alarms. The UI is organized into several pages:

- **Dashboard**: Overview of all alarms
- **Alarm Detail**: View and edit alarm details
- **Add Alarm**: Create new alarms
- **Settings**: Configure application settings
- **Status**: View system status and logs

## Command-Line Interface

The command-line interface in `scripts/alarm_cli.py` provides a way to manage alarms from the command line:

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

## Docker Deployment

The application can be deployed using Docker and Docker Compose:

```bash
# Build and start containers
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

The Docker setup includes:
- Volume mounts for persistent data
- Exposed ports for the Streamlit UI and health check
- Environment variable configuration

## Testing

The application includes comprehensive tests:

- **Unit Tests**: `scripts/test_functionality.py` tests individual components
- **Integration Tests**: `scripts/integration_test.py` tests the interaction between components

```bash
# Run unit tests
python scripts/test_functionality.py

# Run integration tests
python scripts/integration_test.py
```

## Extending the Application

### Adding New Features

To add new features to the application:

1. Identify the appropriate module for your feature
2. Implement the feature in the module
3. Update the UI to expose the feature
4. Add tests for the feature
5. Update documentation

### Example: Adding Email Notifications

1. Add email configuration to `ConfigManager`:
```python
DEFAULT_CONFIG = {
    # Existing config...
    'email_server': '',
    'email_port': 587,
    'email_username': '',
    'email_password': '',
    'email_recipient': ''
}
```

2. Create a new module for email notifications:
```python
# app/utils/email_notifier.py
import smtplib
from email.mime.text import MIMEText

def send_email(config, subject, message):
    if not config.get('email_server'):
        return False
    
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = config.get('email_username')
    msg['To'] = config.get('email_recipient')
    
    try:
        server = smtplib.SMTP(config.get('email_server'), config.get('email_port'))
        server.starttls()
        server.login(config.get('email_username'), config.get('email_password'))
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False
```

3. Update `AlarmManager` to use email notifications:
```python
from app.utils.email_notifier import send_email

# In trigger_alarm method
send_email(
    self.config,
    "Alarm Triggered",
    f"Your {alarm_time} alarm has been triggered."
)
```

4. Add email settings to the UI:
```python
# In show_settings function
st.markdown('<div class="section-header">Email Notifications</div>', unsafe_allow_html=True)

with st.form("email_settings_form"):
    email_server = st.text_input("SMTP Server", value=config.get("email_server", ""))
    email_port = st.number_input("SMTP Port", value=int(config.get("email_port", 587)))
    email_username = st.text_input("Email Username", value=config.get("email_username", ""))
    email_password = st.text_input("Email Password", value=config.get("email_password", ""), type="password")
    email_recipient = st.text_input("Recipient Email", value=config.get("email_recipient", ""))
    
    submitted = st.form_submit_button("Save Email Settings")
    
    if submitted:
        config.set("email_server", email_server)
        config.set("email_port", email_port)
        config.set("email_username", email_username)
        config.set("email_password", email_password)
        config.set("email_recipient", email_recipient)
        config.save("config.yaml")
        st.success("Email settings saved")
```

5. Add tests for email notifications:
```python
def test_email_notifications(self):
    """Test email notifications."""
    from app.utils.email_notifier import send_email
    
    # Mock config
    mock_config = {
        'email_server': 'smtp.example.com',
        'email_port': 587,
        'email_username': 'test@example.com',
        'email_password': 'password',
        'email_recipient': 'recipient@example.com'
    }
    
    # Mock send_email function
    with unittest.mock.patch('smtplib.SMTP') as mock_smtp:
        result = send_email(mock_config, "Test Subject", "Test Message")
        self.assertTrue(result)
        mock_smtp.assert_called_once_with('smtp.example.com', 587)
```

6. Update documentation to include email notifications.

## Troubleshooting

### Common Issues

- **Database Errors**: Check file permissions and path
- **Home Assistant Connection**: Verify URL and token
- **Scheduler Issues**: Check for conflicting alarms
- **UI Not Loading**: Ensure Streamlit is running on the correct port

### Logging

The application uses Python's logging module with configurable levels:

```python
import logging
from app.utils import setup_logging

# Setup logging
setup_logging('logs/app.log', 'DEBUG')
logger = logging.getLogger('my_module')

# Log messages
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

Log files are stored in the `logs` directory.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for your changes
5. Run the tests
6. Submit a pull request

Please follow the existing code style and include appropriate documentation.
