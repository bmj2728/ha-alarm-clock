import requests
import json
import time
import logging
import os
from datetime import datetime, timedelta
import schedule
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/app/logs/alarm_service.log")
    ]
)
logger = logging.getLogger('smart_alarm_service')

# Home Assistant API connection details
HA_URL = os.environ.get('HA_URL', 'http://homeassistant:8123')
TOKEN = os.environ.get('HA_TOKEN', '')
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "content-type": "application/json",
}

# Voice PE entity ID
VOICE_PE_ENTITY = os.environ.get('VOICE_PE_ENTITY', 'media_player.home_assistant_voice_pe')

# Location entities
PERSON_ENTITY = os.environ.get('PERSON_ENTITY', 'person.user')
HOME_ZONE = os.environ.get('HOME_ZONE', 'zone.home')

# Gotify settings
GOTIFY_URL = os.environ.get('GOTIFY_URL', '')
GOTIFY_TOKEN = os.environ.get('GOTIFY_TOKEN', '')

# Timezone
TIMEZONE = os.environ.get('TIMEZONE', 'America/New_York')
local_tz = pytz.timezone(TIMEZONE)

# Alarm settings
WEEKDAY_ALARM_TIME = os.environ.get('WEEKDAY_ALARM_TIME', '07:00')
WEEKEND_ALARM_TIME = os.environ.get('WEEKEND_ALARM_TIME', '09:00')
WEEKDAY_ALARM_MEDIA = os.environ.get('WEEKDAY_ALARM_MEDIA', '/media/audio/wake_up.mp3')
WEEKEND_ALARM_MEDIA = os.environ.get('WEEKEND_ALARM_MEDIA', '/media/audio/weekend_wakeup.mp3')
MEDIA_CONTENT_TYPE = os.environ.get('MEDIA_CONTENT_TYPE', 'music')  # Default to 'music', but can be 'playlist'

# Volume settings
VOLUME_STEPS = [float(x) for x in os.environ.get('VOLUME_STEPS', '0.2,0.3,0.4,0.5,0.6,0.7').split(',')]
VOLUME_STEP_DELAY = int(os.environ.get('VOLUME_STEP_DELAY', '20'))


def check_ha_available():
    """Check if Home Assistant is available"""
    try:
        response = requests.get(f"{HA_URL}/api/", headers=HEADERS, timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        logger.error("Home Assistant is not available")
        return False


def is_person_home():
    """Check if the person is home based on HA state"""
    if not check_ha_available():
        logger.warning("Can't check location - Home Assistant unavailable")
        return True  # Default to assuming home if can't check

    try:
        response = requests.get(
            f"{HA_URL}/api/states/{PERSON_ENTITY}",
            headers=HEADERS,
            timeout=5
        )

        if response.status_code == 200:
            state_data = response.json()
            return state_data.get('state') == 'home'
        else:
            logger.error(f"Failed to get person state: {response.status_code}")
            return True  # Default to assuming home

    except requests.exceptions.RequestException as e:
        logger.error(f"Error checking location: {str(e)}")
        return True  # Default to assuming home


def send_gotify_notification(title, message, priority=5):
    """Send notification via Gotify"""
    if not GOTIFY_URL or not GOTIFY_TOKEN:
        logger.warning("Gotify not configured, skipping notification")
        return False

    try:
        response = requests.post(
            f"{GOTIFY_URL}/message",
            json={"title": title, "message": message, "priority": priority},
            headers={"X-Gotify-Key": GOTIFY_TOKEN}
        )
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Gotify notification: {str(e)}")
        return False


def set_volume(volume_level):
    """Set the volume of the Voice PE device"""
    data = {
        "entity_id": VOICE_PE_ENTITY,
        "volume_level": volume_level
    }
    try:
        response = requests.post(
            f"{HA_URL}/api/services/media_player/volume_set",
            headers=HEADERS,
            json=data
        )
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to set volume: {str(e)}")
        return False


def play_media(media_url, media_type="music"):
    """Play media on the Voice PE device"""
    data = {
        "entity_id": VOICE_PE_ENTITY,
        "media_content_id": media_url,
        "media_content_type": media_type
    }
    try:
        response = requests.post(
            f"{HA_URL}/api/services/media_player/play_media",
            headers=HEADERS,
            json=data
        )
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to play media: {str(e)}")
        return False


def speak_tts(message):
    """Have the Voice PE speak a message"""
    data = {
        "entity_id": VOICE_PE_ENTITY,
        "message": message
    }
    try:
        response = requests.post(
            f"{HA_URL}/api/services/tts/speak",
            headers=HEADERS,
            json=data
        )
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to speak TTS: {str(e)}")
        return False


def get_weather_info():
    """Get current weather information from HA"""
    try:
        response = requests.get(
            f"{HA_URL}/api/states/weather.forecast_home",
            headers=HEADERS
        )
        if response.status_code == 200:
            weather_data = response.json()
            attributes = weather_data.get('attributes', {})

            current_temp = attributes.get('temperature')
            condition = weather_data.get('state', 'unknown')
            forecast = attributes.get('forecast', [{}])[0]

            weather_text = f"The current weather is {condition} at {current_temp}°. "

            if forecast:
                temp_low = forecast.get('temperature')
                temp_high = forecast.get('templow')
                if temp_low and temp_high:
                    weather_text += f"Today's forecast: high of {temp_high}° and low of {temp_low}°."

            return weather_text
        else:
            return "I couldn't get the weather information right now."
    except Exception as e:
        logger.error(f"Error getting weather: {str(e)}")
        return "I couldn't get the weather information right now."


def get_calendar_events():
    """Get today's calendar events from HA"""
    try:
        now = datetime.now(local_tz)
        start = now.strftime("%Y-%m-%dT00:00:00")
        end = now.strftime("%Y-%m-%dT23:59:59")

        response = requests.get(
            f"{HA_URL}/api/calendars",
            headers=HEADERS
        )

        if response.status_code != 200:
            return "I couldn't check your calendar right now."

        calendars = response.json()
        if not calendars:
            return "No calendars found."

        calendar_ids = [cal['entity_id'] for cal in calendars]
        events_text = "Here are today's events: "
        event_count = 0

        for cal_id in calendar_ids:
            events_response = requests.get(
                f"{HA_URL}/api/calendars/{cal_id}?start={start}&end={end}",
                headers=HEADERS
            )

            if events_response.status_code == 200:
                events = events_response.json()
                for event in events:
                    event_count += 1
                    start_time = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00')).astimezone(
                        local_tz)
                    events_text += f"{event['summary']} at {start_time.strftime('%I:%M %p')}, "

        if event_count == 0:
            return "You have no events scheduled for today."
        else:
            return events_text[:-2] + "."
    except Exception as e:
        logger.error(f"Error getting calendar events: {str(e)}")
        return "I couldn't check your calendar right now."


def trigger_alarm(alarm_settings):
    """Trigger the alarm with location check and Gotify fallback"""
    alarm_time = datetime.now(local_tz).strftime("%H:%M")

    # Check if person is home
    if not is_person_home():
        logger.info("Person not home, skipping alarm")
        send_gotify_notification(
            "Alarm Skipped",
            f"Your {alarm_time} alarm was skipped because you're not home.",
            priority=3
        )
        return

    # Check if HA is available
    if not check_ha_available():
        logger.error("Cannot trigger alarm - Home Assistant unavailable")
        send_gotify_notification(
            "Alarm Failed",
            f"Your {alarm_time} alarm couldn't be triggered because Home Assistant is unavailable.",
            priority=8
        )
        return

    try:
        # Start the alarm process
        logger.info(f"Triggering alarm with media: {alarm_settings['media_url']}")

        # Set initial volume
        initial_volume = VOLUME_STEPS[0] if VOLUME_STEPS else 0.2
        set_volume(initial_volume)

        # Play wake-up sound/music
        media_type = alarm_settings.get('media_type', MEDIA_CONTENT_TYPE)
        media_success = play_media(alarm_settings['media_url'], media_type)
        if not media_success:
            logger.error("Failed to play alarm media")
            send_gotify_notification(
                "Alarm Issue",
                f"Your {alarm_time} alarm started but couldn't play the media.",
                priority=7
            )

        # Gradually increase volume
        for vol in VOLUME_STEPS[1:]:
            time.sleep(VOLUME_STEP_DELAY)  # Wait between volume increases
            if check_ha_available():  # Recheck availability
                set_volume(vol)
            else:
                logger.error("Lost connection to Home Assistant during volume increase")
                break

        # After music plays for a while, announce the briefing
        time.sleep(60)
        if check_ha_available():
            # Get weather and calendar info
            weather_info = get_weather_info()
            calendar_info = get_calendar_events()

            # Deliver morning briefing
            morning_message = f"Good morning! {weather_info} {calendar_info}"
            speak_tts(morning_message)

            logger.info("Alarm sequence completed successfully")

    except Exception as e:
        error_msg = f"Error during alarm sequence: {str(e)}"
        logger.error(error_msg)
        send_gotify_notification("Alarm Error", error_msg, priority=8)


# Schedule the alarms
def set_alarms():
    # Weekday alarm (Monday to Friday)
    for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
        getattr(schedule.every(), day).at(WEEKDAY_ALARM_TIME).do(
            trigger_alarm,
            {"media_url": WEEKDAY_ALARM_MEDIA}
        )

    # Weekend alarms
    schedule.every().saturday.at(WEEKEND_ALARM_TIME).do(
        trigger_alarm,
        {"media_url": WEEKEND_ALARM_MEDIA}
    )
    schedule.every().sunday.at(WEEKEND_ALARM_TIME).do(
        trigger_alarm,
        {"media_url": WEEKEND_ALARM_MEDIA}
    )

    logger.info(f"Alarms scheduled: Weekdays at {WEEKDAY_ALARM_TIME}, Weekends at {WEEKEND_ALARM_TIME}")
    send_gotify_notification(
        "Alarm Service Started",
        f"Smart Alarm service is running. Weekdays: {WEEKDAY_ALARM_TIME}, Weekends: {WEEKEND_ALARM_TIME}",
        priority=4
    )


# Health check endpoint handler (for Docker health checks)
def health_check_server():
    """Start a simple HTTP server for health checks"""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading

    class HealthCheckHandler(BaseHTTPRequestHandler):
        def do_get(self):
            if self.path == '/health':
                # Basic health check
                ha_status = "UP" if check_ha_available() else "DOWN"
                response = {
                    "status": "UP",
                    "home_assistant": ha_status,
                    "timestamp": datetime.now().isoformat()
                }

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(404)
                self.end_headers()

    def run_server():
        server = HTTPServer(('0.0.0.0', 8080), HealthCheckHandler)
        logger.info("Started health check server on port 8080")
        server.serve_forever()

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()


# Main function
def main():
    # Set up health check endpoint (for Docker)
    health_check_server()

    # Schedule alarms
    set_alarms()

    # Run every minute
    logger.info("Smart Alarm Service started")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    main()