"""
Database schema test script for the Home Assistant Smart Alarm Clock.

This script tests the database functionality by creating, reading, updating,
and deleting alarms in the database.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.config import ConfigManager
from app.database import DatabaseManager, Alarm
from app.utils import setup_logging

def test_database():
    """Test database CRUD operations."""
    # Setup logging
    setup_logging('logs/db_test.log', 'INFO')
    logger = logging.getLogger('db_test')
    
    logger.info("Starting database test")
    
    # Initialize database with test database
    db_path = 'test_alarms.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        
    logger.info(f"Using test database at {db_path}")
    
    db_manager = DatabaseManager(db_path)
    
    # Test creating alarms
    logger.info("Testing alarm creation")
    
    # Create a weekday alarm
    weekday_alarm = {
        'name': 'Test Weekday Alarm',
        'time': '07:30',
        'days': [0, 1, 2, 3, 4],  # Monday to Friday
        'enabled': True,
        'media_url': '/media/audio/test_alarm.mp3',
        'media_type': 'music',
        'volume_steps': [0.2, 0.3, 0.4, 0.5],
        'volume_step_delay': 15,
        'person_entity': 'person.test_user'
    }
    
    created_alarm = db_manager.create_alarm(weekday_alarm)
    logger.info(f"Created alarm: {created_alarm}")
    
    # Create a weekend alarm
    weekend_alarm = {
        'name': 'Test Weekend Alarm',
        'time': '09:45',
        'days': [5, 6],  # Saturday and Sunday
        'enabled': True,
        'media_url': '/media/audio/weekend_test.mp3',
        'media_type': 'music',
        'volume_steps': [0.3, 0.4, 0.5, 0.6],
        'volume_step_delay': 20,
        'person_entity': 'person.test_user'
    }
    
    created_alarm2 = db_manager.create_alarm(weekend_alarm)
    logger.info(f"Created alarm: {created_alarm2}")
    
    # Create a specific day alarm
    monday_alarm = {
        'name': 'Monday Only Alarm',
        'time': '06:15',
        'days': [0],  # Monday only
        'enabled': True,
        'media_url': '/media/audio/monday_alarm.mp3',
        'media_type': 'music',
        'volume_steps': [0.1, 0.2, 0.3, 0.4, 0.5],
        'volume_step_delay': 10,
        'person_entity': 'person.test_user'
    }
    
    created_alarm3 = db_manager.create_alarm(monday_alarm)
    logger.info(f"Created alarm: {created_alarm3}")
    
    # Test reading alarms
    logger.info("Testing alarm retrieval")
    
    # Get all alarms
    all_alarms = db_manager.get_all_alarms()
    logger.info(f"Retrieved {len(all_alarms)} alarms")
    
    # Get alarm by ID
    alarm_id = created_alarm.id
    retrieved_alarm = db_manager.get_alarm_by_id(alarm_id)
    logger.info(f"Retrieved alarm by ID: {retrieved_alarm}")
    
    # Get enabled alarms
    enabled_alarms = db_manager.get_enabled_alarms()
    logger.info(f"Retrieved {len(enabled_alarms)} enabled alarms")
    
    # Test updating alarms
    logger.info("Testing alarm updates")
    
    # Update alarm
    update_data = {
        'name': 'Updated Weekday Alarm',
        'time': '08:00',
        'enabled': False
    }
    
    updated_alarm = db_manager.update_alarm(alarm_id, update_data)
    logger.info(f"Updated alarm: {updated_alarm}")
    
    # Verify update
    retrieved_alarm = db_manager.get_alarm_by_id(alarm_id)
    logger.info(f"Retrieved updated alarm: {retrieved_alarm}")
    
    # Test deleting alarms
    logger.info("Testing alarm deletion")
    
    # Delete alarm
    deleted = db_manager.delete_alarm(created_alarm3.id)
    logger.info(f"Deleted alarm: {deleted}")
    
    # Verify deletion
    all_alarms = db_manager.get_all_alarms()
    logger.info(f"Remaining alarms: {len(all_alarms)}")
    
    # Clean up
    os.remove(db_path)
    logger.info("Test database removed")
    
    logger.info("Database test completed successfully")

if __name__ == '__main__':
    test_database()
