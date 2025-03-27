"""
Command-line interface for managing alarms in the Home Assistant Smart Alarm Clock.

This script provides a CLI for creating, listing, updating, and deleting alarms
without requiring the Streamlit UI.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
import json

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.config import ConfigManager
from app.database import DatabaseManager, Alarm
from app.utils import setup_logging, format_days_list, validate_alarm_data

def list_alarms(db_manager, args):
    """List all alarms in the database.
    
    Args:
        db_manager: Database manager instance
        args: Command line arguments
    """
    alarms = db_manager.get_all_alarms()
    
    if not alarms:
        print("No alarms found in database.")
        return
    
    print(f"Found {len(alarms)} alarms:")
    for alarm in alarms:
        status = "ENABLED" if alarm.enabled else "DISABLED"
        days = format_days_list(alarm.days_list)
        print(f"ID: {alarm.id} | {status} | {alarm.name} | {alarm.time} | {days}")
        
        if args.verbose:
            print(f"  Media: {alarm.media_url} ({alarm.media_type})")
            print(f"  Volume steps: {alarm.volume_steps_list}")
            print(f"  Volume step delay: {alarm.volume_step_delay} seconds")
            print(f"  Person entity: {alarm.person_entity}")
            print(f"  Created: {alarm.created_at}")
            print(f"  Updated: {alarm.updated_at}")
            print()

def create_alarm(db_manager, args):
    """Create a new alarm.
    
    Args:
        db_manager: Database manager instance
        args: Command line arguments
    """
    # Parse days
    try:
        days = json.loads(args.days)
        if not isinstance(days, list):
            print("Error: Days must be a JSON array of integers (0-6)")
            return
    except json.JSONDecodeError:
        print("Error: Days must be a valid JSON array (e.g., '[0,1,2,3,4]')")
        return
    
    # Parse volume steps
    volume_steps = None
    if args.volume_steps:
        try:
            volume_steps = json.loads(args.volume_steps)
            if not isinstance(volume_steps, list):
                print("Error: Volume steps must be a JSON array of floats")
                return
        except json.JSONDecodeError:
            print("Error: Volume steps must be a valid JSON array (e.g., '[0.2,0.3,0.4,0.5]')")
            return
    
    # Create alarm data
    alarm_data = {
        'name': args.name,
        'time': args.time,
        'days': days,
        'enabled': not args.disabled,
        'media_url': args.media_url,
        'media_type': args.media_type,
        'person_entity': args.person_entity
    }
    
    if volume_steps:
        alarm_data['volume_steps'] = volume_steps
        
    if args.volume_step_delay:
        alarm_data['volume_step_delay'] = args.volume_step_delay
    
    # Validate alarm data
    errors = validate_alarm_data(alarm_data)
    if errors:
        print("Error: Invalid alarm data:")
        for field, error in errors.items():
            print(f"  {field}: {error}")
        return
    
    # Create alarm
    alarm = db_manager.create_alarm(alarm_data)
    print(f"Created alarm: ID {alarm.id} - {alarm.name}")

def update_alarm(db_manager, args):
    """Update an existing alarm.
    
    Args:
        db_manager: Database manager instance
        args: Command line arguments
    """
    # Get alarm
    alarm = db_manager.get_alarm_by_id(args.id)
    if not alarm:
        print(f"Error: Alarm with ID {args.id} not found")
        return
    
    # Create update data
    update_data = {}
    
    if args.name:
        update_data['name'] = args.name
        
    if args.time:
        update_data['time'] = args.time
        
    if args.days:
        try:
            days = json.loads(args.days)
            if not isinstance(days, list):
                print("Error: Days must be a JSON array of integers (0-6)")
                return
            update_data['days'] = days
        except json.JSONDecodeError:
            print("Error: Days must be a valid JSON array (e.g., '[0,1,2,3,4]')")
            return
    
    if args.media_url:
        update_data['media_url'] = args.media_url
        
    if args.media_type:
        update_data['media_type'] = args.media_type
        
    if args.person_entity:
        update_data['person_entity'] = args.person_entity
        
    if args.volume_steps:
        try:
            volume_steps = json.loads(args.volume_steps)
            if not isinstance(volume_steps, list):
                print("Error: Volume steps must be a JSON array of floats")
                return
            update_data['volume_steps'] = volume_steps
        except json.JSONDecodeError:
            print("Error: Volume steps must be a valid JSON array (e.g., '[0.2,0.3,0.4,0.5]')")
            return
    
    if args.volume_step_delay:
        update_data['volume_step_delay'] = args.volume_step_delay
        
    if args.enable:
        update_data['enabled'] = True
        
    if args.disable:
        update_data['enabled'] = False
    
    # Validate update data
    if update_data:
        # For partial updates, we only validate the fields being updated
        errors = {}
        for field, value in update_data.items():
            field_data = {field: value}
            field_errors = validate_alarm_data(field_data)
            if field in field_errors:
                errors[field] = field_errors[field]
                
        if errors:
            print("Error: Invalid update data:")
            for field, error in errors.items():
                print(f"  {field}: {error}")
            return
        
        # Update alarm
        updated_alarm = db_manager.update_alarm(args.id, update_data)
        print(f"Updated alarm: ID {updated_alarm.id} - {updated_alarm.name}")
    else:
        print("No update data provided")

def delete_alarm(db_manager, args):
    """Delete an alarm.
    
    Args:
        db_manager: Database manager instance
        args: Command line arguments
    """
    # Get alarm
    alarm = db_manager.get_alarm_by_id(args.id)
    if not alarm:
        print(f"Error: Alarm with ID {args.id} not found")
        return
    
    # Confirm deletion
    if not args.force:
        confirm = input(f"Are you sure you want to delete alarm '{alarm.name}' (ID: {alarm.id})? [y/N] ")
        if confirm.lower() != 'y':
            print("Deletion cancelled")
            return
    
    # Delete alarm
    deleted = db_manager.delete_alarm(args.id)
    if deleted:
        print(f"Deleted alarm: ID {args.id}")
    else:
        print(f"Failed to delete alarm: ID {args.id}")

def main():
    """Main entry point for the CLI."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Home Assistant Smart Alarm Clock CLI')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--log-level', type=str, default='INFO', 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging level')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # List alarms command
    list_parser = subparsers.add_parser('list', help='List alarms')
    list_parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed alarm information')
    
    # Create alarm command
    create_parser = subparsers.add_parser('create', help='Create a new alarm')
    create_parser.add_argument('--name', required=True, help='Alarm name')
    create_parser.add_argument('--time', required=True, help='Alarm time (HH:MM)')
    create_parser.add_argument('--days', required=True, help='Days to trigger alarm (JSON array of integers, 0=Monday, 6=Sunday)')
    create_parser.add_argument('--media-url', required=True, help='Media URL to play')
    create_parser.add_argument('--media-type', default='music', help='Media type (default: music)')
    create_parser.add_argument('--volume-steps', help='Volume steps (JSON array of floats)')
    create_parser.add_argument('--volume-step-delay', type=int, help='Delay between volume steps in seconds')
    create_parser.add_argument('--person-entity', help='Person entity to check for presence')
    create_parser.add_argument('--disabled', action='store_true', help='Create alarm in disabled state')
    
    # Update alarm command
    update_parser = subparsers.add_parser('update', help='Update an existing alarm')
    update_parser.add_argument('id', type=int, help='Alarm ID to update')
    update_parser.add_argument('--name', help='Alarm name')
    update_parser.add_argument('--time', help='Alarm time (HH:MM)')
    update_parser.add_argument('--days', help='Days to trigger alarm (JSON array of integers, 0=Monday, 6=Sunday)')
    update_parser.add_argument('--media-url', help='Media URL to play')
    update_parser.add_argument('--media-type', help='Media type')
    update_parser.add_argument('--volume-steps', help='Volume steps (JSON array of floats)')
    update_parser.add_argument('--volume-step-delay', type=int, help='Delay between volume steps in seconds')
    update_parser.add_argument('--person-entity', help='Person entity to check for presence')
    update_parser.add_argument('--enable', action='store_true', help='Enable alarm')
    update_parser.add_argument('--disable', action='store_true', help='Disable alarm')
    
    # Delete alarm command
    delete_parser = subparsers.add_parser('delete', help='Delete an alarm')
    delete_parser.add_argument('id', type=int, help='Alarm ID to delete')
    delete_parser.add_argument('-f', '--force', action='store_true', help='Force deletion without confirmation')
    
    args = parser.parse_args()
    
    # Initialize configuration
    config = ConfigManager(args.config)
    
    # Setup logging
    log_file = config.get('log_file', 'logs/cli.log')
    log_level = args.log_level or config.get('log_level', 'INFO')
    setup_logging(log_file, log_level)
    
    logger = logging.getLogger('cli')
    logger.info(f"Starting CLI with command: {args.command}")
    
    # Initialize database
    db_path = config.get('database_path', 'alarms.db')
    db_manager = DatabaseManager(db_path)
    
    # Execute command
    if args.command == 'list':
        list_alarms(db_manager, args)
    elif args.command == 'create':
        create_alarm(db_manager, args)
    elif args.command == 'update':
        update_alarm(db_manager, args)
    elif args.command == 'delete':
        delete_alarm(db_manager, args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
