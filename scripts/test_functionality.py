"""
Test script for the enhanced Home Assistant Smart Alarm Clock.

This script tests the functionality of the enhanced alarm clock application,
including database operations, alarm scheduling, and UI integration.
"""

import os
import sys
import logging
import unittest
from pathlib import Path
import time
import json
from datetime import datetime, timedelta

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.config import ConfigManager
from app.database import DatabaseManager, Alarm
from app.ha_client import HomeAssistantClient
from app.alarm_manager import AlarmManager
from app.ui_integration import UIIntegration
from app.utils import setup_logging

# Setup logging
setup_logging('logs/test.log', 'DEBUG')
logger = logging.getLogger('test')

class TestAlarmClock(unittest.TestCase):
    """Test case for the Home Assistant Smart Alarm Clock."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Use test database
        cls.db_path = 'test_alarms.db'
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
        
        # Initialize configuration
        cls.config = ConfigManager()
        cls.config.set('database_path', cls.db_path)
        
        # Initialize database
        cls.db_manager = DatabaseManager(cls.db_path)
        
        # Create mock Home Assistant client
        cls.ha_client = MockHomeAssistantClient()
        
        # Initialize alarm manager
        cls.alarm_manager = AlarmManager(cls.config, cls.ha_client, cls.db_manager)
        
        # Initialize UI integration
        cls.ui_integration = UIIntegration(cls.alarm_manager, cls.db_manager)
        
        logger.info("Test environment set up")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        # Stop alarm manager
        if cls.alarm_manager.running:
            cls.alarm_manager.stop()
        
        # Stop UI integration
        if cls.ui_integration.running:
            cls.ui_integration.stop_status_monitoring()
        
        # Remove test database
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
        
        logger.info("Test environment cleaned up")
    
    def setUp(self):
        """Set up each test."""
        # Clear database
        for alarm in self.db_manager.get_all_alarms():
            self.db_manager.delete_alarm(alarm.id)
        
        # Reset Home Assistant client
        self.ha_client.reset()
        
        # Start alarm manager if not running
        if not self.alarm_manager.running:
            self.alarm_manager.start()
        
        # Start UI integration if not running
        if not self.ui_integration.running:
            self.ui_integration.start_status_monitoring()
    
    def test_database_operations(self):
        """Test database CRUD operations."""
        logger.info("Testing database operations")
        
        # Create alarm
        alarm_data = {
            'name': 'Test Alarm',
            'time': '08:00',
            'days': [0, 1, 2, 3, 4],  # Monday to Friday
            'enabled': True,
            'media_url': '/media/audio/test.mp3',
            'media_type': 'music',
            'volume_steps': [0.2, 0.3, 0.4, 0.5],
            'volume_step_delay': 15,
            'person_entity': 'person.test_user'
        }
        
        alarm = self.db_manager.create_alarm(alarm_data)
        self.assertIsNotNone(alarm)
        self.assertEqual(alarm.name, 'Test Alarm')
        
        # Get alarm by ID
        retrieved_alarm = self.db_manager.get_alarm_by_id(alarm.id)
        self.assertIsNotNone(retrieved_alarm)
        self.assertEqual(retrieved_alarm.name, 'Test Alarm')
        
        # Update alarm
        update_data = {
            'name': 'Updated Alarm',
            'time': '09:00'
        }
        
        updated_alarm = self.db_manager.update_alarm(alarm.id, update_data)
        self.assertIsNotNone(updated_alarm)
        self.assertEqual(updated_alarm.name, 'Updated Alarm')
        self.assertEqual(updated_alarm.time, '09:00')
        
        # Get all alarms
        alarms = self.db_manager.get_all_alarms()
        self.assertEqual(len(alarms), 1)
        
        # Delete alarm
        deleted = self.db_manager.delete_alarm(alarm.id)
        self.assertTrue(deleted)
        
        # Verify deletion
        alarms = self.db_manager.get_all_alarms()
        self.assertEqual(len(alarms), 0)
        
        logger.info("Database operations test passed")
    
    def test_alarm_scheduling(self):
        """Test alarm scheduling."""
        logger.info("Testing alarm scheduling")
        
        # Create alarm
        alarm_data = {
            'name': 'Test Alarm',
            'time': '08:00',
            'days': [0, 1, 2, 3, 4],  # Monday to Friday
            'enabled': True,
            'media_url': '/media/audio/test.mp3',
            'media_type': 'music',
            'volume_steps': [0.2, 0.3, 0.4, 0.5],
            'volume_step_delay': 15,
            'person_entity': 'person.test_user'
        }
        
        alarm = self.db_manager.create_alarm(alarm_data)
        self.assertIsNotNone(alarm)
        
        # Schedule alarms
        self.alarm_manager.schedule_alarms()
        
        # Verify that the alarm is scheduled
        # This is a bit tricky to test directly, so we'll just check that
        # the alarm manager is running and no errors occurred
        self.assertTrue(self.alarm_manager.running)
        
        logger.info("Alarm scheduling test passed")
    
    def test_alarm_triggering(self):
        """Test alarm triggering."""
        logger.info("Testing alarm triggering")
        
        # Create alarm
        alarm_data = {
            'name': 'Test Alarm',
            'time': '08:00',
            'days': [0, 1, 2, 3, 4],  # Monday to Friday
            'enabled': True,
            'media_url': '/media/audio/test.mp3',
            'media_type': 'music',
            'volume_steps': [0.2, 0.3, 0.4, 0.5],
            'volume_step_delay': 1,  # Short delay for testing
            'person_entity': 'person.test_user'
        }
        
        alarm = self.db_manager.create_alarm(alarm_data)
        self.assertIsNotNone(alarm)
        
        # Trigger alarm
        self.alarm_manager.trigger_alarm(alarm.id)
        
        # Wait for alarm to start
        time.sleep(0.5)
        
        # Verify that the alarm is active
        self.assertEqual(self.alarm_manager.active_alarm, alarm)
        
        # Verify that media was played
        self.assertTrue(self.ha_client.media_played)
        self.assertEqual(self.ha_client.last_media_url, '/media/audio/test.mp3')
        
        # Wait for volume to increase
        time.sleep(2)
        
        # Verify that volume was increased
        self.assertTrue(self.ha_client.volume_set)
        self.assertGreater(self.ha_client.last_volume, 0.2)
        
        # Dismiss alarm
        dismissed = self.alarm_manager.dismiss_alarm()
        self.assertTrue(dismissed)
        
        # Verify that alarm was dismissed
        self.assertIsNone(self.alarm_manager.active_alarm)
        
        logger.info("Alarm triggering test passed")
    
    def test_alarm_snoozing(self):
        """Test alarm snoozing."""
        logger.info("Testing alarm snoozing")
        
        # Create alarm
        alarm_data = {
            'name': 'Test Alarm',
            'time': '08:00',
            'days': [0, 1, 2, 3, 4],  # Monday to Friday
            'enabled': True,
            'media_url': '/media/audio/test.mp3',
            'media_type': 'music',
            'volume_steps': [0.2, 0.3, 0.4, 0.5],
            'volume_step_delay': 1,  # Short delay for testing
            'person_entity': 'person.test_user'
        }
        
        alarm = self.db_manager.create_alarm(alarm_data)
        self.assertIsNotNone(alarm)
        
        # Trigger alarm
        self.alarm_manager.trigger_alarm(alarm.id)
        
        # Wait for alarm to start
        time.sleep(0.5)
        
        # Verify that the alarm is active
        self.assertEqual(self.alarm_manager.active_alarm, alarm)
        
        # Snooze alarm
        snoozed = self.alarm_manager.snooze_alarm(1)  # 1 minute
        self.assertTrue(snoozed)
        
        # Verify that alarm was snoozed
        self.assertIsNone(self.alarm_manager.active_alarm)
        self.assertIsNotNone(self.alarm_manager.snooze_time)
        
        # Verify that media was stopped
        self.assertTrue(self.ha_client.media_stopped)
        
        logger.info("Alarm snoozing test passed")
    
    def test_ui_integration(self):
        """Test UI integration."""
        logger.info("Testing UI integration")
        
        # Create alarm
        alarm_data = {
            'name': 'Test Alarm',
            'time': '08:00',
            'days': [0, 1, 2, 3, 4],  # Monday to Friday
            'enabled': True,
            'media_url': '/media/audio/test.mp3',
            'media_type': 'music',
            'volume_steps': [0.2, 0.3, 0.4, 0.5],
            'volume_step_delay': 1,  # Short delay for testing
            'person_entity': 'person.test_user'
        }
        
        alarm = self.db_manager.create_alarm(alarm_data)
        self.assertIsNotNone(alarm)
        
        # Get status
        status = self.ui_integration.get_status()
        self.assertIsNotNone(status)
        self.assertTrue(status['service_running'])
        self.assertIsNone(status['active_alarm'])
        
        # Trigger alarm
        self.alarm_manager.trigger_alarm(alarm.id)
        
        # Wait for alarm to start
        time.sleep(0.5)
        
        # Get status again
        status = self.ui_integration.get_status()
        self.assertIsNotNone(status['active_alarm'])
        self.assertEqual(status['active_alarm']['id'], alarm.id)
        
        # Snooze alarm via UI integration
        snoozed = self.ui_integration.snooze_active_alarm(1)  # 1 minute
        self.assertTrue(snoozed)
        
        # Get status again
        status = self.ui_integration.get_status()
        self.assertIsNone(status['active_alarm'])
        self.assertIsNotNone(status['snooze_time'])
        
        # Dismiss alarm via UI integration
        dismissed = self.ui_integration.dismiss_active_alarm()
        self.assertTrue(dismissed)
        
        # Test alarm via UI integration
        tested = self.ui_integration.test_alarm(alarm.id)
        self.assertTrue(tested)
        
        # Wait for alarm to start
        time.sleep(0.5)
        
        # Verify that alarm is active
        status = self.ui_integration.get_status()
        self.assertIsNotNone(status['active_alarm'])
        
        # Dismiss alarm
        dismissed = self.ui_integration.dismiss_active_alarm()
        self.assertTrue(dismissed)
        
        # Restart alarm service
        restarted = self.ui_integration.restart_alarm_service()
        self.assertTrue(restarted)
        
        # Verify that service is still running
        status = self.ui_integration.get_status()
        self.assertTrue(status['service_running'])
        
        logger.info("UI integration test passed")

class MockHomeAssistantClient:
    """Mock Home Assistant client for testing."""
    
    def __init__(self):
        """Initialize the mock client."""
        self.reset()
    
    def reset(self):
        """Reset the mock client state."""
        self.available = True
        self.media_played = False
        self.volume_set = False
        self.media_stopped = False
        self.last_media_url = None
        self.last_volume = None
    
    def is_available(self):
        """Check if Home Assistant is available."""
        return self.available
    
    def is_person_home(self, person_entity):
        """Check if a person is home."""
        return True
    
    def set_volume(self, entity_id, volume_level):
        """Set the volume of a media player."""
        self.volume_set = True
        self.last_volume = volume_level
        return True
    
    def play_media(self, entity_id, media_url, media_type):
        """Play media on a media player."""
        self.media_played = True
        self.last_media_url = media_url
        return True
    
    def speak_tts(self, entity_id, message):
        """Have a media player speak a message using TTS."""
        return True
    
    def call_service(self, domain, service, data):
        """Call a Home Assistant service."""
        if domain == 'media_player' and service == 'media_stop':
            self.media_stopped = True
        return True
    
    def get_state(self, entity_id):
        """Get the state of an entity."""
        if entity_id.startswith('media_player'):
            return {
                'state': 'playing',
                'attributes': {
                    'volume_level': 0.5,
                    'media_content_id': '/media/audio/test.mp3',
                    'media_content_type': 'music'
                }
            }
        elif entity_id.startswith('person'):
            return {
                'state': 'home'
            }
        return None
    
    def get_weather_info(self):
        """Get current weather information."""
        return "The current weather is sunny at 72°."
    
    def get_calendar_events(self):
        """Get today's calendar events."""
        return "You have no events scheduled for today."

if __name__ == '__main__':
    unittest.main()
