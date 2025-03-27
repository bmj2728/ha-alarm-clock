"""
Database models for the Home Assistant Smart Alarm Clock.

This module defines the SQLAlchemy ORM models for the application.
"""

from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import json
from datetime import datetime

Base = declarative_base()

class Alarm(Base):
    """Alarm model representing a scheduled alarm."""
    
    __tablename__ = 'alarms'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    time = Column(String, nullable=False)  # Format: HH:MM
    days = Column(String, nullable=False)  # JSON array of days (0-6, 0=Monday)
    enabled = Column(Boolean, default=True)
    media_url = Column(String, nullable=False)
    media_type = Column(String, default='music')
    volume_steps = Column(String)  # JSON array of volume levels
    volume_step_delay = Column(Integer, default=20)
    person_entity = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        """Initialize a new Alarm instance.
        
        Special handling for days and volume_steps which are stored as JSON strings.
        """
        # Handle days as list
        if 'days' in kwargs and isinstance(kwargs['days'], list):
            kwargs['days'] = json.dumps(kwargs['days'])
            
        # Handle volume_steps as list
        if 'volume_steps' in kwargs and isinstance(kwargs['volume_steps'], list):
            kwargs['volume_steps'] = json.dumps(kwargs['volume_steps'])
            
        super(Alarm, self).__init__(**kwargs)
    
    @property
    def days_list(self):
        """Get days as a list of integers.
        
        Returns:
            List of day numbers (0-6, 0=Monday)
        """
        if self.days:
            return json.loads(self.days)
        return []
    
    @days_list.setter
    def days_list(self, value):
        """Set days from a list of integers.
        
        Args:
            value: List of day numbers (0-6, 0=Monday)
        """
        if isinstance(value, list):
            self.days = json.dumps(value)
    
    @property
    def volume_steps_list(self):
        """Get volume steps as a list of floats.
        
        Returns:
            List of volume levels
        """
        if self.volume_steps:
            return json.loads(self.volume_steps)
        return [0.2, 0.3, 0.4, 0.5, 0.6, 0.7]  # Default
    
    @volume_steps_list.setter
    def volume_steps_list(self, value):
        """Set volume steps from a list of floats.
        
        Args:
            value: List of volume levels
        """
        if isinstance(value, list):
            self.volume_steps = json.dumps(value)
    
    def to_dict(self):
        """Convert alarm to dictionary.
        
        Returns:
            Dictionary representation of alarm
        """
        return {
            'id': self.id,
            'name': self.name,
            'time': self.time,
            'days': self.days_list,
            'enabled': self.enabled,
            'media_url': self.media_url,
            'media_type': self.media_type,
            'volume_steps': self.volume_steps_list,
            'volume_step_delay': self.volume_step_delay,
            'person_entity': self.person_entity,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        """String representation of alarm.
        
        Returns:
            String representation
        """
        return f"<Alarm(id={self.id}, name='{self.name}', time='{self.time}', enabled={self.enabled})>"
