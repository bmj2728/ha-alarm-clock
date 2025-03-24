FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Create log directory
RUN mkdir -p /app/logs

# Copy application code
COPY smart-alarm-service.py /app/

# Expose port for health check
EXPOSE 8080

# Set environment variables with defaults (override at runtime)
ENV HA_URL=http://homeassistant:8123 \
    HA_TOKEN="" \
    VOICE_PE_ENTITY="media_player.home_assistant_voice_pe" \
    PERSON_ENTITY="person.user" \
    HOME_ZONE="zone.home" \
    GOTIFY_URL="" \
    GOTIFY_TOKEN="" \
    TIMEZONE="America/New_York" \
    WEEKDAY_ALARM_TIME="07:00" \
    WEEKEND_ALARM_TIME="09:00" \
    WEEKDAY_ALARM_MEDIA="/media/audio/wake_up.mp3" \
    WEEKEND_ALARM_MEDIA="/media/audio/weekend_wakeup.mp3" \
    MEDIA_CONTENT_TYPE="music" \
    VOLUME_STEPS="0.2,0.3,0.4,0.5,0.6,0.7" \
    VOLUME_STEP_DELAY="20"

# Health check
HEALTHCHECK --interval=1m --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "-u", "smart-alarm-service.py"]
