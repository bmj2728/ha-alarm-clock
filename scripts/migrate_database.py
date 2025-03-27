"""
Database schema migration script for the Home Assistant Smart Alarm Clock.

This script creates the initial database schema and migrates existing
configuration from environment variables to the database.
"""

import os
import sys
import logging
import json
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.config import ConfigManager
from app.database import DatabaseManager, Alarm
from app.utils import setup_logging

def migrate_database():
    """Create database schema and migrate existing configuration."""
    # Setup logging
    setup_logging('logs/migration.log', 'INFO')
    logger = logging.getLogger('migration')
    
    logger.info("Starting database migration")
    
    # Initialize configuration
    config = ConfigManager()
    
    # Initialize database
    db_path = config.get('database_path', 'alarms.db')
    logger.info(f"Using database at {db_path}")
    
    db_manager = DatabaseManager(db_path)
    
    # Check if database already has alarms
    existing_alarms = db_manager.get_all_alarms()
    if existing_alarms:
        logger.info(f"Database already contains {len(existing_alarms)} alarms, skipping migration")
        return
    
    # Migrate from environment variables
    logger.info("Migrating alarms from environment variables")
    
    # Create weekday alarm
    weekday_alarm = {
        'name': 'Weekday Alarm',
        'time': config.get('weekday_alarm_time', '07:00'),
        'days': [0, 1, 2, 3, 4],  # Monday to Friday
        'enabled': True,
        'media_url': config.get('weekday_alarm_media', '/media/audio/wake_up.mp3'),
        'media_type': config.get('media_content_type', 'music'),
        'volume_steps': config.get('volume_steps'),
        'volume_step_delay': config.get('volume_step_delay', 20),
        'person_entity': config.get('person_entity', 'person.user')
    }
    
    # Create weekend alarm
    weekend_alarm = {
        'name': 'Weekend Alarm',
        'time': config.get('weekend_alarm_time', '09:00'),
        'days': [5, 6],  # Saturday and Sunday
        'enabled': True,
        'media_url': config.get('weekend_alarm_media', '/media/audio/weekend_wakeup.mp3'),
        'media_type': config.get('media_content_type', 'music'),
        'volume_steps': config.get('volume_steps'),
        'volume_step_delay': config.get('volume_step_delay', 20),
        'person_entity': config.get('person_entity', 'person.user')
    }
    
    # Add alarms to database
    db_manager.create_alarm(weekday_alarm)
    db_manager.create_alarm(weekend_alarm)
    
    logger.info("Migration completed successfully")

if __name__ == '__main__':
    migrate_database()
