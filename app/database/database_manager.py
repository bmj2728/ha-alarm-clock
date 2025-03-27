"""
Database manager for the Home Assistant Smart Alarm Clock.

This module handles database operations for the application.
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from typing import List, Optional, Dict, Any, Union
from pathlib import Path

from .models import Base, Alarm

logger = logging.getLogger('database_manager')

class DatabaseManager:
    """Manages database operations for the application."""
    
    def __init__(self, database_path: str = 'alarms.db'):
        """Initialize the database manager.
        
        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = database_path
        
        # Ensure directory exists
        db_dir = os.path.dirname(os.path.abspath(database_path))
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # Create database connection
        self.engine = create_engine(f'sqlite:///{database_path}')
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)
        
        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
        
        logger.info(f"Database initialized at {database_path}")
    
    def get_session(self):
        """Get a new database session.
        
        Returns:
            SQLAlchemy session
        """
        return self.Session()
    
    def close_session(self, session):
        """Close a database session.
        
        Args:
            session: SQLAlchemy session to close
        """
        session.close()
    
    def get_all_alarms(self) -> List[Alarm]:
        """Get all alarms from the database.
        
        Returns:
            List of Alarm objects
        """
        session = self.get_session()
        try:
            alarms = session.query(Alarm).all()
            return alarms
        finally:
            self.close_session(session)
    
    def get_alarm_by_id(self, alarm_id: int) -> Optional[Alarm]:
        """Get an alarm by ID.
        
        Args:
            alarm_id: Alarm ID
            
        Returns:
            Alarm object or None if not found
        """
        session = self.get_session()
        try:
            alarm = session.query(Alarm).filter(Alarm.id == alarm_id).first()
            return alarm
        finally:
            self.close_session(session)
    
    def create_alarm(self, alarm_data: Dict[str, Any]) -> Alarm:
        """Create a new alarm.
        
        Args:
            alarm_data: Dictionary of alarm data
            
        Returns:
            Created Alarm object
        """
        session = self.get_session()
        try:
            alarm = Alarm(**alarm_data)
            session.add(alarm)
            session.commit()
            logger.info(f"Created alarm: {alarm}")
            return alarm
        finally:
            self.close_session(session)
    
    def update_alarm(self, alarm_id: int, alarm_data: Dict[str, Any]) -> Optional[Alarm]:
        """Update an existing alarm.
        
        Args:
            alarm_id: ID of alarm to update
            alarm_data: Dictionary of alarm data to update
            
        Returns:
            Updated Alarm object or None if not found
        """
        session = self.get_session()
        try:
            alarm = session.query(Alarm).filter(Alarm.id == alarm_id).first()
            if not alarm:
                logger.warning(f"Alarm not found for update: {alarm_id}")
                return None
            
            # Update alarm attributes
            for key, value in alarm_data.items():
                if key == 'days' and isinstance(value, list):
                    alarm.days_list = value
                elif key == 'volume_steps' and isinstance(value, list):
                    alarm.volume_steps_list = value
                elif hasattr(alarm, key):
                    setattr(alarm, key, value)
            
            session.commit()
            logger.info(f"Updated alarm: {alarm}")
            return alarm
        finally:
            self.close_session(session)
    
    def delete_alarm(self, alarm_id: int) -> bool:
        """Delete an alarm.
        
        Args:
            alarm_id: ID of alarm to delete
            
        Returns:
            True if alarm was deleted, False otherwise
        """
        session = self.get_session()
        try:
            alarm = session.query(Alarm).filter(Alarm.id == alarm_id).first()
            if not alarm:
                logger.warning(f"Alarm not found for deletion: {alarm_id}")
                return False
            
            session.delete(alarm)
            session.commit()
            logger.info(f"Deleted alarm: {alarm_id}")
            return True
        finally:
            self.close_session(session)
    
    def get_enabled_alarms(self) -> List[Alarm]:
        """Get all enabled alarms.
        
        Returns:
            List of enabled Alarm objects
        """
        session = self.get_session()
        try:
            alarms = session.query(Alarm).filter(Alarm.enabled == True).all()
            return alarms
        finally:
            self.close_session(session)
    
    def migrate_from_env(self, config) -> List[Alarm]:
        """Migrate alarms from environment variables to database.
        
        Args:
            config: ConfigManager instance
            
        Returns:
            List of created Alarm objects
        """
        # Check if we already have alarms
        if len(self.get_all_alarms()) > 0:
            logger.info("Skipping migration, database already contains alarms")
            return []
        
        created_alarms = []
        
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
        created_alarms.append(self.create_alarm(weekday_alarm))
        
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
        created_alarms.append(self.create_alarm(weekend_alarm))
        
        logger.info(f"Migrated {len(created_alarms)} alarms from environment variables")
        return created_alarms
