"""
Utility functions for the Home Assistant Smart Alarm Clock.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger('utils')

def setup_logging(log_file: str = None, log_level: str = 'INFO'):
    """Set up logging configuration.
    
    Args:
        log_file: Path to log file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert string level to logging level
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    level = level_map.get(log_level.upper(), logging.INFO)
    
    # Create handlers
    handlers = [logging.StreamHandler()]
    
    # Add file handler if log file is specified
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(os.path.abspath(log_file))
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        handlers.append(logging.FileHandler(log_file))
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    logger.info(f"Logging configured with level {log_level}")

def day_name_to_number(day_name: str) -> Optional[int]:
    """Convert day name to day number (0=Monday, 6=Sunday).
    
    Args:
        day_name: Day name (e.g., 'monday', 'tuesday')
        
    Returns:
        Day number or None if invalid
    """
    day_map = {
        'monday': 0,
        'tuesday': 1,
        'wednesday': 2,
        'thursday': 3,
        'friday': 4,
        'saturday': 5,
        'sunday': 6
    }
    return day_map.get(day_name.lower())

def day_number_to_name(day_number: int) -> Optional[str]:
    """Convert day number to day name (0=Monday, 6=Sunday).
    
    Args:
        day_number: Day number (0-6)
        
    Returns:
        Day name or None if invalid
    """
    day_map = {
        0: 'Monday',
        1: 'Tuesday',
        2: 'Wednesday',
        3: 'Thursday',
        4: 'Friday',
        5: 'Saturday',
        6: 'Sunday'
    }
    return day_map.get(day_number)

def format_days_list(days_list: list) -> str:
    """Format a list of day numbers as a human-readable string.
    
    Args:
        days_list: List of day numbers (0-6)
        
    Returns:
        Formatted string (e.g., "Monday, Wednesday, Friday")
    """
    day_names = [day_number_to_name(day) for day in days_list if day_number_to_name(day)]
    
    if not day_names:
        return "No days selected"
    
    if len(day_names) == 7:
        return "Every day"
    
    if set(days_list) == {0, 1, 2, 3, 4}:
        return "Weekdays"
    
    if set(days_list) == {5, 6}:
        return "Weekends"
    
    return ", ".join(day_names)

def is_valid_time_format(time_str: str) -> bool:
    """Check if a string is in valid HH:MM format.
    
    Args:
        time_str: Time string to check
        
    Returns:
        True if valid, False otherwise
    """
    try:
        hours, minutes = time_str.split(':')
        hours = int(hours)
        minutes = int(minutes)
        return 0 <= hours < 24 and 0 <= minutes < 60
    except (ValueError, AttributeError):
        return False

def validate_alarm_data(alarm_data: Dict[str, Any]) -> Dict[str, str]:
    """Validate alarm data for creation or update.
    
    Args:
        alarm_data: Dictionary of alarm data
        
    Returns:
        Dictionary of validation errors (empty if valid)
    """
    errors = {}
    
    # Validate name
    if 'name' not in alarm_data or not alarm_data['name']:
        errors['name'] = "Name is required"
    
    # Validate time
    if 'time' not in alarm_data or not alarm_data['time']:
        errors['time'] = "Time is required"
    elif not is_valid_time_format(alarm_data['time']):
        errors['time'] = "Time must be in HH:MM format"
    
    # Validate days
    if 'days' not in alarm_data or not alarm_data['days']:
        errors['days'] = "At least one day must be selected"
    elif not isinstance(alarm_data['days'], list):
        errors['days'] = "Days must be a list"
    elif not all(isinstance(day, int) and 0 <= day <= 6 for day in alarm_data['days']):
        errors['days'] = "Days must be integers between 0 and 6"
    
    # Validate media URL
    if 'media_url' not in alarm_data or not alarm_data['media_url']:
        errors['media_url'] = "Media URL is required"
    
    # Validate volume steps if provided
    if 'volume_steps' in alarm_data and alarm_data['volume_steps']:
        if not isinstance(alarm_data['volume_steps'], list):
            errors['volume_steps'] = "Volume steps must be a list"
        elif not all(isinstance(vol, (int, float)) and 0 <= vol <= 1 for vol in alarm_data['volume_steps']):
            errors['volume_steps'] = "Volume steps must be numbers between 0 and 1"
    
    # Validate volume step delay if provided
    if 'volume_step_delay' in alarm_data and alarm_data['volume_step_delay']:
        if not isinstance(alarm_data['volume_step_delay'], int) or alarm_data['volume_step_delay'] < 1:
            errors['volume_step_delay'] = "Volume step delay must be a positive integer"
    
    return errors
