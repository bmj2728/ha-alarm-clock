###
###Dockerfile for the Home Assistant Smart Alarm Clock.
###
###This Dockerfile builds a container image for the enhanced alarm clock application
###with Streamlit UI and SQLite database support.
###

FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY scripts/ ./scripts/

# Create directories for logs and database
RUN mkdir -p logs media/audio

# Create default config file
RUN mkdir -p config
RUN echo "database_path: /data/alarms.db\nlog_file: /logs/alarm_service.log" > config/config.yaml

# Create volume mount points
VOLUME ["/data", "/logs", "/media", "/config"]

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose ports for Streamlit UI and health check
EXPOSE 8501 8080

# Create entrypoint script
RUN echo '#!/bin/bash\n\
# Copy config if it doesn'\''t exist\n\
if [ ! -f /config/config.yaml ]; then\n\
  cp /app/config/config.yaml /config/\n\
fi\n\
\n\
# Run database migration if needed\n\
python /app/scripts/migrate_database.py\n\
\n\
# Start the application based on mode\n\
if [ "$1" = "ui" ]; then\n\
  # Start Streamlit UI\n\
  streamlit run /app/app/streamlit_ui_integrated.py --server.port=8501 --server.address=0.0.0.0\n\
elif [ "$1" = "service" ]; then\n\
  # Start alarm service\n\
  python -m app.main --config /config/config.yaml\n\
else\n\
  # Default to running both\n\
  python -m app.main --config /config/config.yaml &\n\
  streamlit run /app/app/streamlit_ui_integrated.py --server.port=8501 --server.address=0.0.0.0\n\
fi' > /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

# Default command (can be overridden)
CMD ["ui"]
