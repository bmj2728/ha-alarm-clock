"""
Main application module for the Home Assistant Smart Alarm Clock.

This module ties together all components and provides the main entry point.
"""

import os
import logging
import argparse
from pathlib import Path

from .config import ConfigManager
from .ha_client import HomeAssistantClient
from .database import DatabaseManager
from .alarm_manager import AlarmManager
from .utils import setup_logging

def main():
    """Main entry point for the application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Home Assistant Smart Alarm Clock')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--log-level', type=str, default='INFO', 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging level')
    args = parser.parse_args()
    
    # Initialize configuration
    config = ConfigManager(args.config)
    
    # Setup logging
    log_file = config.get('log_file', 'logs/alarm_service.log')
    log_level = args.log_level or config.get('log_level', 'INFO')
    setup_logging(log_file, log_level)
    
    logger = logging.getLogger('main')
    logger.info("Starting Home Assistant Smart Alarm Clock")
    
    # Initialize components
    ha_client = HomeAssistantClient(
        config.get('ha_url'),
        config.get('ha_token'),
        timeout=10
    )
    
    db_manager = DatabaseManager(
        config.get('database_path', 'alarms.db')
    )
    
    # Migrate alarms from environment variables if database is empty
    if len(db_manager.get_all_alarms()) == 0:
        logger.info("No alarms found in database, migrating from environment variables")
        db_manager.migrate_from_env(config)
    
    # Initialize and start alarm manager
    alarm_manager = AlarmManager(config, ha_client, db_manager)
    alarm_manager.start()
    
    # Start health check server
    from .utils.health_check import start_health_check_server
    health_check_port = int(config.get('health_check_port', 8080))
    start_health_check_server(health_check_port, ha_client)
    
    logger.info("Home Assistant Smart Alarm Clock started successfully")
    
    # Keep the main thread running
    try:
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutting down Home Assistant Smart Alarm Clock")
        alarm_manager.stop()

if __name__ == '__main__':
    main()
