"""
Configuration manager for the Home Assistant Smart Alarm Clock.

This module handles loading and saving configuration from various sources:
- YAML/JSON configuration files
- Environment variables
- Database settings
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

logger = logging.getLogger('config_manager')

class ConfigManager:
    """Manages application configuration from multiple sources."""
    
    DEFAULT_CONFIG = {
        'ha_url': 'http://homeassistant:8123',
        'ha_token': '',
        'voice_pe_entity': 'media_player.home_assistant_voice_pe',
        'person_entity': 'person.user',
        'home_zone': 'zone.home',
        'gotify_url': '',
        'gotify_token': '',
        'timezone': 'America/New_York',
        'volume_steps': [0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
        'volume_step_delay': 20,
        'database_path': 'alarms.db',
        'log_level': 'INFO',
        'log_file': 'logs/alarm_service.log',
        'health_check_port': 8080
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the configuration manager.
        
        Args:
            config_file: Path to configuration file (YAML or JSON)
        """
        self.config_file = config_file
        self.config = self.DEFAULT_CONFIG.copy()
        
        # Load configuration in order of precedence
        self._load_from_file()
        self._load_from_env()
        
        logger.info(f"Configuration loaded with {len(self.config)} settings")
    
    def _load_from_file(self) -> None:
        """Load configuration from file if it exists."""
        if not self.config_file:
            return
            
        config_path = Path(self.config_file)
        if not config_path.exists():
            logger.warning(f"Configuration file not found: {self.config_file}")
            return
            
        try:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                with open(config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
            else:
                logger.warning(f"Unsupported configuration file format: {config_path.suffix}")
                return
                
            if file_config and isinstance(file_config, dict):
                self.config.update(file_config)
                logger.info(f"Loaded configuration from {self.config_file}")
            else:
                logger.warning(f"Invalid configuration format in {self.config_file}")
        except Exception as e:
            logger.error(f"Error loading configuration file: {str(e)}")
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # Map of environment variable names to config keys
        env_mapping = {
            'HA_URL': 'ha_url',
            'HA_TOKEN': 'ha_token',
            'VOICE_PE_ENTITY': 'voice_pe_entity',
            'PERSON_ENTITY': 'person_entity',
            'HOME_ZONE': 'home_zone',
            'GOTIFY_URL': 'gotify_url',
            'GOTIFY_TOKEN': 'gotify_token',
            'TIMEZONE': 'timezone',
            'VOLUME_STEP_DELAY': 'volume_step_delay',
            'DATABASE_PATH': 'database_path',
            'LOG_LEVEL': 'log_level',
            'LOG_FILE': 'log_file',
            'HEALTH_CHECK_PORT': 'health_check_port'
        }
        
        # Special handling for volume steps which is a list
        if 'VOLUME_STEPS' in os.environ:
            try:
                self.config['volume_steps'] = [
                    float(x) for x in os.environ.get('VOLUME_STEPS', '').split(',')
                ]
            except ValueError:
                logger.warning("Invalid VOLUME_STEPS format in environment, using default")
        
        # Load other variables
        for env_var, config_key in env_mapping.items():
            if env_var in os.environ and os.environ[env_var]:
                # Convert numeric values
                value = os.environ[env_var]
                if config_key in ['volume_step_delay', 'health_check_port']:
                    try:
                        value = int(value)
                    except ValueError:
                        logger.warning(f"Invalid numeric value for {env_var}, using default")
                        continue
                
                self.config[config_key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        self.config[key] = value
    
    def save(self, file_path: Optional[str] = None) -> bool:
        """Save configuration to file.
        
        Args:
            file_path: Path to save configuration to (defaults to self.config_file)
            
        Returns:
            True if successful, False otherwise
        """
        save_path = file_path or self.config_file
        if not save_path:
            logger.error("No configuration file specified for saving")
            return False
            
        try:
            path = Path(save_path)
            # Create directory if it doesn't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            
            if path.suffix.lower() in ['.yaml', '.yml']:
                with open(path, 'w') as f:
                    yaml.dump(self.config, f, default_flow_style=False)
            elif path.suffix.lower() == '.json':
                with open(path, 'w') as f:
                    json.dump(self.config, f, indent=2)
            else:
                logger.error(f"Unsupported configuration file format: {path.suffix}")
                return False
                
            logger.info(f"Configuration saved to {save_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
            return False
    
    def as_dict(self) -> Dict[str, Any]:
        """Get the entire configuration as a dictionary.
        
        Returns:
            Dictionary of all configuration values
        """
        return self.config.copy()
