"""
Integration test script for the Home Assistant Smart Alarm Clock.

This script tests the integration between all components of the enhanced alarm clock application.
"""

import os
import sys
import logging
import time
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.config import ConfigManager
from app.database import DatabaseManager, Alarm
from app.ha_client import HomeAssistantClient
from app.alarm_manager import AlarmManager
from app.ui_integration import UIIntegration
from app.utils import setup_logging

# Setup logging
setup_logging('logs/integration_test.log', 'INFO')
logger = logging.getLogger('integration_test')

def run_integration_test():
    """Run integration tests for the Home Assistant Smart Alarm Clock."""
    logger.info("Starting integration test")
    
    # Initialize configuration
    config = ConfigManager()
    
    # Use test database
    db_path = 'integration_test.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    
    config.set('database_path', db_path)
    
    # Initialize database
    db_manager = DatabaseManager(db_path)
    
    # Initialize Home Assistant client
    ha_client = HomeAssistantClient(
        config.get('ha_url', 'http://homeassistant:8123'),
        config.get('ha_token', 'test_token'),
        timeout=10
    )
    
    # Check if Home Assistant is available
    ha_available = ha_client.is_available()
    logger.info(f"Home Assistant available: {ha_available}")
    
    # Initialize alarm manager
    alarm_manager = AlarmManager(config, ha_client, db_manager)
    
    # Start alarm manager
    alarm_manager.start()
    logger.info("Alarm manager started")
    
    # Initialize UI integration
    ui_integration = UIIntegration(alarm_manager, db_manager)
    ui_integration.start_status_monitoring()
    logger.info("UI integration started")
    
    try:
        # Create test alarms
        logger.info("Creating test alarms")
        
        # Weekday alarm
        weekday_alarm = {
            'name': 'Weekday Alarm',
            'time': '07:30',
            'days': [0, 1, 2, 3, 4],  # Monday to Friday
            'enabled': True,
            'media_url': '/media/audio/wake_up.mp3',
            'media_type': 'music',
            'volume_steps': [0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
            'volume_step_delay': 20,
            'person_entity': 'person.user'
        }
        
        weekday_alarm_obj = db_manager.create_alarm(weekday_alarm)
        logger.info(f"Created weekday alarm: {weekday_alarm_obj}")
        
        # Weekend alarm
        weekend_alarm = {
            'name': 'Weekend Alarm',
            'time': '09:00',
            'days': [5, 6],  # Saturday and Sunday
            'enabled': True,
            'media_url': '/media/audio/weekend_wakeup.mp3',
            'media_type': 'music',
            'volume_steps': [0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
            'volume_step_delay': 20,
            'person_entity': 'person.user'
        }
        
        weekend_alarm_obj = db_manager.create_alarm(weekend_alarm)
        logger.info(f"Created weekend alarm: {weekend_alarm_obj}")
        
        # Custom alarm
        custom_alarm = {
            'name': 'Custom Alarm',
            'time': '08:15',
            'days': [1, 3, 5],  # Tuesday, Thursday, Saturday
            'enabled': False,
            'media_url': '/media/audio/custom_alarm.mp3',
            'media_type': 'music',
            'volume_steps': [0.1, 0.2, 0.3, 0.4, 0.5],
            'volume_step_delay': 15,
            'person_entity': 'person.user'
        }
        
        custom_alarm_obj = db_manager.create_alarm(custom_alarm)
        logger.info(f"Created custom alarm: {custom_alarm_obj}")
        
        # Schedule alarms
        alarm_manager.schedule_alarms()
        logger.info("Alarms scheduled")
        
        # Get all alarms
        all_alarms = db_manager.get_all_alarms()
        logger.info(f"Total alarms: {len(all_alarms)}")
        
        # Get enabled alarms
        enabled_alarms = db_manager.get_enabled_alarms()
        logger.info(f"Enabled alarms: {len(enabled_alarms)}")
        
        # Test alarm triggering
        logger.info("Testing alarm triggering")
        
        # Trigger weekday alarm
        logger.info(f"Triggering weekday alarm: {weekday_alarm_obj.id}")
        alarm_manager.trigger_alarm(weekday_alarm_obj.id)
        
        # Wait for alarm to start
        time.sleep(2)
        
        # Check if alarm is active
        active_alarm = alarm_manager.active_alarm
        logger.info(f"Active alarm: {active_alarm}")
        
        # Get status from UI integration
        status = ui_integration.get_status()
        logger.info(f"UI integration status: {status}")
        
        # Snooze alarm
        logger.info("Snoozing alarm")
        snoozed = ui_integration.snooze_active_alarm(1)  # 1 minute
        logger.info(f"Alarm snoozed: {snoozed}")
        
        # Wait for snooze
        time.sleep(2)
        
        # Get status again
        status = ui_integration.get_status()
        logger.info(f"UI integration status after snooze: {status}")
        
        # Dismiss alarm
        logger.info("Dismissing alarm")
        dismissed = ui_integration.dismiss_active_alarm()
        logger.info(f"Alarm dismissed: {dismissed}")
        
        # Update alarm
        logger.info("Updating alarm")
        update_data = {
            'name': 'Updated Weekday Alarm',
            'time': '07:45',
            'enabled': False
        }
        
        updated_alarm = db_manager.update_alarm(weekday_alarm_obj.id, update_data)
        logger.info(f"Updated alarm: {updated_alarm}")
        
        # Reschedule alarms
        alarm_manager.schedule_alarms()
        logger.info("Alarms rescheduled")
        
        # Delete alarm
        logger.info("Deleting alarm")
        deleted = db_manager.delete_alarm(custom_alarm_obj.id)
        logger.info(f"Alarm deleted: {deleted}")
        
        # Get all alarms again
        all_alarms = db_manager.get_all_alarms()
        logger.info(f"Total alarms after deletion: {len(all_alarms)}")
        
        # Restart alarm service
        logger.info("Restarting alarm service")
        restarted = ui_integration.restart_alarm_service()
        logger.info(f"Alarm service restarted: {restarted}")
        
        logger.info("Integration test completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Integration test failed: {str(e)}")
        return False
    
    finally:
        # Stop alarm manager
        alarm_manager.stop()
        logger.info("Alarm manager stopped")
        
        # Stop UI integration
        ui_integration.stop_status_monitoring()
        logger.info("UI integration stopped")
        
        # Clean up test database
        if os.path.exists(db_path):
            os.remove(db_path)
            logger.info("Test database removed")

if __name__ == '__main__':
    success = run_integration_test()
    sys.exit(0 if success else 1)
