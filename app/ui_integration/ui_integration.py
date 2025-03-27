"""
Integration module for connecting the Streamlit UI with the alarm functionality.

This module provides functions for the Streamlit UI to interact with the alarm manager.
"""

import logging
import threading
import time
from typing import Dict, Any, List, Optional

from ..alarm_manager import AlarmManager
from ..database import DatabaseManager, Alarm

logger = logging.getLogger('ui_integration')

class UIIntegration:
    """Integration class for connecting UI with alarm functionality."""
    
    def __init__(self, alarm_manager: AlarmManager, db_manager: DatabaseManager):
        """Initialize the UI integration.
        
        Args:
            alarm_manager: Alarm manager instance
            db_manager: Database manager instance
        """
        self.alarm_manager = alarm_manager
        self.db_manager = db_manager
        self.status_thread = None
        self.running = False
        self.status = {
            "service_running": True,
            "active_alarm": None,
            "snooze_time": None,
            "next_alarms": []
        }
        logger.info("UI integration initialized")
    
    def start_status_monitoring(self):
        """Start monitoring alarm status in a background thread."""
        if self.running:
            logger.warning("Status monitoring already running")
            return
        
        self.running = True
        self.status_thread = threading.Thread(target=self._status_monitor, daemon=True)
        self.status_thread.start()
        logger.info("Status monitoring started")
    
    def stop_status_monitoring(self):
        """Stop monitoring alarm status."""
        if not self.running:
            logger.warning("Status monitoring not running")
            return
        
        self.running = False
        if self.status_thread:
            self.status_thread.join(timeout=1.0)
            self.status_thread = None
        logger.info("Status monitoring stopped")
    
    def _status_monitor(self):
        """Monitor alarm status in a loop."""
        while self.running:
            try:
                # Update status
                self.status["service_running"] = True
                self.status["active_alarm"] = self._get_active_alarm_info()
                self.status["snooze_time"] = self._get_snooze_time()
                self.status["next_alarms"] = self._get_next_alarms()
            except Exception as e:
                logger.error(f"Error updating status: {str(e)}")
                self.status["service_running"] = False
            
            # Sleep for a short time
            time.sleep(5)
    
    def _get_active_alarm_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the currently active alarm.
        
        Returns:
            Dictionary with active alarm information or None if no active alarm
        """
        active_alarm = self.alarm_manager.active_alarm
        if not active_alarm:
            return None
        
        return {
            "id": active_alarm.id,
            "name": active_alarm.name,
            "time": active_alarm.time
        }
    
    def _get_snooze_time(self) -> Optional[float]:
        """Get the current snooze time.
        
        Returns:
            Snooze time as timestamp or None if not snoozed
        """
        return self.alarm_manager.snooze_time
    
    def _get_next_alarms(self) -> List[Dict[str, Any]]:
        """Get the next scheduled alarms.
        
        Returns:
            List of dictionaries with next alarm information
        """
        # This is a simplified implementation
        # In a real implementation, we would get the actual next scheduled alarms
        # from the scheduler, but that would require modifying the scheduler
        # to track scheduled jobs
        return []
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status.
        
        Returns:
            Dictionary with current status information
        """
        return self.status.copy()
    
    def snooze_active_alarm(self, duration: int = 5) -> bool:
        """Snooze the currently active alarm.
        
        Args:
            duration: Snooze duration in minutes
            
        Returns:
            True if alarm was snoozed, False otherwise
        """
        return self.alarm_manager.snooze_alarm(duration)
    
    def dismiss_active_alarm(self) -> bool:
        """Dismiss the currently active alarm.
        
        Returns:
            True if alarm was dismissed, False otherwise
        """
        return self.alarm_manager.dismiss_alarm()
    
    def restart_alarm_service(self) -> bool:
        """Restart the alarm service.
        
        Returns:
            True if service was restarted, False otherwise
        """
        try:
            # Stop the alarm manager
            self.alarm_manager.stop()
            
            # Wait a short time
            time.sleep(1)
            
            # Reschedule alarms
            self.alarm_manager.schedule_alarms()
            
            # Start the alarm manager
            self.alarm_manager.start()
            
            logger.info("Alarm service restarted")
            return True
        except Exception as e:
            logger.error(f"Error restarting alarm service: {str(e)}")
            return False
    
    def test_alarm(self, alarm_id: int) -> bool:
        """Test an alarm by triggering it.
        
        Args:
            alarm_id: ID of alarm to test
            
        Returns:
            True if alarm was triggered, False otherwise
        """
        try:
            # Get alarm from database
            alarm = self.db_manager.get_alarm_by_id(alarm_id)
            if not alarm:
                logger.error(f"Alarm not found for testing: {alarm_id}")
                return False
            
            # Trigger alarm in a separate thread to avoid blocking
            threading.Thread(
                target=self.alarm_manager.trigger_alarm,
                args=(alarm_id,),
                daemon=True
            ).start()
            
            logger.info(f"Test triggered for alarm {alarm_id}")
            return True
        except Exception as e:
            logger.error(f"Error testing alarm: {str(e)}")
            return False
