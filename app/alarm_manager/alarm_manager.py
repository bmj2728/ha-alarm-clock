"""
Alarm manager for the Home Assistant Smart Alarm Clock.

This module handles alarm scheduling, triggering, and management.
"""

import logging
import time
import schedule
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable

from ..database import DatabaseManager, Alarm
from ..ha_client import HomeAssistantClient
from ..config import ConfigManager

logger = logging.getLogger('alarm_manager')

class AlarmManager:
    """Manages alarm scheduling and triggering."""
    
    def __init__(self, config: ConfigManager, ha_client: HomeAssistantClient, db_manager: DatabaseManager):
        """Initialize the alarm manager.
        
        Args:
            config: Configuration manager
            ha_client: Home Assistant client
            db_manager: Database manager
        """
        self.config = config
        self.ha_client = ha_client
        self.db_manager = db_manager
        self.running = False
        self.scheduler_thread = None
        self.active_alarm = None
        self.snooze_time = None
        
        logger.info("Alarm manager initialized")
    
    def start(self):
        """Start the alarm manager scheduler."""
        if self.running:
            logger.warning("Alarm manager already running")
            return
        
        self.running = True
        self.schedule_alarms()
        
        # Start scheduler in a separate thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Alarm manager started")
    
    def stop(self):
        """Stop the alarm manager scheduler."""
        if not self.running:
            logger.warning("Alarm manager not running")
            return
        
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=1.0)
            self.scheduler_thread = None
        
        # Clear all scheduled jobs
        schedule.clear()
        
        logger.info("Alarm manager stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop."""
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    def schedule_alarms(self):
        """Schedule all enabled alarms."""
        # Clear existing schedules
        schedule.clear()
        
        # Get all enabled alarms
        alarms = self.db_manager.get_enabled_alarms()
        
        for alarm in alarms:
            self._schedule_alarm(alarm)
        
        logger.info(f"Scheduled {len(alarms)} alarms")
    
    def _schedule_alarm(self, alarm: Alarm):
        """Schedule a single alarm.
        
        Args:
            alarm: Alarm to schedule
        """
        # Get days as list of integers (0=Monday, 6=Sunday)
        days = alarm.days_list
        
        # Map day numbers to schedule day names
        day_map = {
            0: 'monday',
            1: 'tuesday',
            2: 'wednesday',
            3: 'thursday',
            4: 'friday',
            5: 'saturday',
            6: 'sunday'
        }
        
        # Schedule for each day
        for day_num in days:
            if day_num in day_map:
                day_name = day_map[day_num]
                job = getattr(schedule.every(), day_name).at(alarm.time).do(
                    self.trigger_alarm, alarm_id=alarm.id
                )
                logger.info(f"Scheduled alarm {alarm.id} ({alarm.name}) for {day_name} at {alarm.time}")
    
    def trigger_alarm(self, alarm_id: int):
        """Trigger an alarm.
        
        Args:
            alarm_id: ID of alarm to trigger
        """
        # Get alarm from database
        alarm = self.db_manager.get_alarm_by_id(alarm_id)
        if not alarm:
            logger.error(f"Alarm not found for triggering: {alarm_id}")
            return
        
        # Set as active alarm
        self.active_alarm = alarm
        
        # Format alarm time for display
        alarm_time = alarm.time
        
        # Check if person is home (if person entity is specified)
        if alarm.person_entity and not self.ha_client.is_person_home(alarm.person_entity):
            logger.info(f"Person not home, skipping alarm {alarm_id}")
            self._send_notification(
                "Alarm Skipped",
                f"Your {alarm_time} alarm was skipped because you're not home.",
                priority=3
            )
            self.active_alarm = None
            return
        
        # Check if HA is available
        if not self.ha_client.is_available():
            logger.error(f"Cannot trigger alarm {alarm_id} - Home Assistant unavailable")
            self._send_notification(
                "Alarm Failed",
                f"Your {alarm_time} alarm couldn't be triggered because Home Assistant is unavailable.",
                priority=8
            )
            self.active_alarm = None
            return
        
        try:
            # Start the alarm process
            logger.info(f"Triggering alarm {alarm_id} with media: {alarm.media_url}")
            
            # Get media player entity
            media_player = self.config.get('voice_pe_entity', 'media_player.home_assistant_voice_pe')
            
            # Set initial volume
            volume_steps = alarm.volume_steps_list
            initial_volume = volume_steps[0] if volume_steps else 0.2
            self.ha_client.set_volume(media_player, initial_volume)
            
            # Play wake-up sound/music
            media_success = self.ha_client.play_media(
                media_player, 
                alarm.media_url, 
                alarm.media_type
            )
            
            if not media_success:
                logger.error(f"Failed to play alarm media for alarm {alarm_id}")
                self._send_notification(
                    "Alarm Issue",
                    f"Your {alarm_time} alarm started but couldn't play the media.",
                    priority=7
                )
            
            # Gradually increase volume
            for vol in volume_steps[1:]:
                # Wait between volume increases
                time.sleep(alarm.volume_step_delay)
                
                # Check if alarm was dismissed
                if not self.active_alarm:
                    logger.info(f"Alarm {alarm_id} was dismissed during volume increase")
                    return
                
                # Recheck HA availability
                if not self.ha_client.is_available():
                    logger.error(f"Lost connection to Home Assistant during volume increase for alarm {alarm_id}")
                    break
                
                # Increase volume
                self.ha_client.set_volume(media_player, vol)
            
            # After music plays for a while, announce the briefing
            time.sleep(60)  # Wait 60 seconds
            
            # Check if alarm was dismissed
            if not self.active_alarm:
                logger.info(f"Alarm {alarm_id} was dismissed before briefing")
                return
            
            # Check if HA is still available
            if self.ha_client.is_available():
                # Get weather and calendar info
                weather_info = self.ha_client.get_weather_info()
                calendar_info = self.ha_client.get_calendar_events()
                
                # Deliver morning briefing
                morning_message = f"Good morning! {weather_info} {calendar_info}"
                self.ha_client.speak_tts(media_player, morning_message)
            
            logger.info(f"Alarm {alarm_id} sequence completed successfully")
            
        except Exception as e:
            error_msg = f"Error during alarm sequence: {str(e)}"
            logger.error(error_msg)
            self._send_notification("Alarm Error", error_msg, priority=8)
        
        # Clear active alarm
        self.active_alarm = None
    
    def snooze_alarm(self, duration: int = 5) -> bool:
        """Snooze the currently active alarm.
        
        Args:
            duration: Snooze duration in minutes
            
        Returns:
            True if alarm was snoozed, False otherwise
        """
        if not self.active_alarm:
            logger.warning("No active alarm to snooze")
            return False
        
        # Stop current media playback
        media_player = self.config.get('voice_pe_entity', 'media_player.home_assistant_voice_pe')
        self.ha_client.call_service("media_player", "media_stop", {"entity_id": media_player})
        
        # Calculate snooze time
        now = datetime.now()
        self.snooze_time = now.timestamp() + (duration * 60)
        
        # Schedule snooze end
        alarm_id = self.active_alarm.id
        schedule.every(duration).minutes.do(
            self.trigger_alarm, alarm_id=alarm_id
        ).tag(f"snooze_{alarm_id}")
        
        logger.info(f"Alarm {alarm_id} snoozed for {duration} minutes")
        
        # Send notification
        self._send_notification(
            "Alarm Snoozed",
            f"Your alarm has been snoozed for {duration} minutes.",
            priority=3
        )
        
        # Clear active alarm (will be reactivated when snooze ends)
        self.active_alarm = None
        
        return True
    
    def dismiss_alarm(self) -> bool:
        """Dismiss the currently active alarm.
        
        Returns:
            True if alarm was dismissed, False otherwise
        """
        if not self.active_alarm:
            logger.warning("No active alarm to dismiss")
            return False
        
        # Stop current media playback
        media_player = self.config.get('voice_pe_entity', 'media_player.home_assistant_voice_pe')
        self.ha_client.call_service("media_player", "media_stop", {"entity_id": media_player})
        
        # Clear any snooze schedules
        alarm_id = self.active_alarm.id
        schedule.clear(f"snooze_{alarm_id}")
        
        logger.info(f"Alarm {alarm_id} dismissed")
        
        # Clear active alarm
        self.active_alarm = None
        
        return True
    
    def _send_notification(self, title: str, message: str, priority: int = 5) -> bool:
        """Send a notification.
        
        Args:
            title: Notification title
            message: Notification message
            priority: Notification priority (1-10)
            
        Returns:
            True if notification was sent, False otherwise
        """
        # Get Gotify settings
        gotify_url = self.config.get('gotify_url', '')
        gotify_token = self.config.get('gotify_token', '')
        
        # Skip if Gotify not configured
        if not gotify_url or not gotify_token:
            logger.warning("Gotify not configured, skipping notification")
            return False
        
        try:
            import requests
            response = requests.post(
                f"{gotify_url}/message",
                json={"title": title, "message": message, "priority": priority},
                headers={"X-Gotify-Key": gotify_token}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            return False
