"""
Home Assistant client for interacting with the Home Assistant API.

This module provides a client for making API calls to Home Assistant,
handling authentication, error handling, and reconnection logic.
"""

import requests
import logging
import time
from typing import Dict, Any, Optional, List, Union, Tuple

logger = logging.getLogger('ha_client')

class HomeAssistantClient:
    """Client for interacting with the Home Assistant API."""
    
    def __init__(self, base_url: str, token: str, timeout: int = 10):
        """Initialize the Home Assistant client.
        
        Args:
            base_url: Base URL of the Home Assistant instance
            token: Long-lived access token for authentication
            timeout: Default timeout for API requests in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {token}",
            "content-type": "application/json",
        }
        logger.info(f"Initialized Home Assistant client for {base_url}")
    
    def is_available(self) -> bool:
        """Check if Home Assistant is available.
        
        Returns:
            True if Home Assistant is available, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/",
                headers=self.headers,
                timeout=self.timeout
            )
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(f"Home Assistant is not available: {str(e)}")
            return False
    
    def get_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get the state of an entity.
        
        Args:
            entity_id: Entity ID to get state for
            
        Returns:
            Entity state dictionary or None if not found
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/states/{entity_id}",
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get state for {entity_id}: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting state for {entity_id}: {str(e)}")
            return None
    
    def is_person_home(self, person_entity: str, home_zone: str = 'zone.home') -> bool:
        """Check if a person is home based on their state.
        
        Args:
            person_entity: Person entity ID to check
            home_zone: Zone entity ID for home
            
        Returns:
            True if person is home, False otherwise
        """
        if not self.is_available():
            logger.warning("Can't check location - Home Assistant unavailable")
            return True  # Default to assuming home if can't check
        
        state_data = self.get_state(person_entity)
        if state_data:
            return state_data.get('state') == 'home'
        
        return True  # Default to assuming home if can't check
    
    def call_service(self, domain: str, service: str, data: Dict[str, Any]) -> bool:
        """Call a Home Assistant service.
        
        Args:
            domain: Service domain (e.g., 'media_player')
            service: Service name (e.g., 'play_media')
            data: Service data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/services/{domain}/{service}",
                headers=self.headers,
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Failed to call service {domain}.{service}: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling service {domain}.{service}: {str(e)}")
            return False
    
    def set_volume(self, entity_id: str, volume_level: float) -> bool:
        """Set the volume of a media player.
        
        Args:
            entity_id: Media player entity ID
            volume_level: Volume level (0.0 to 1.0)
            
        Returns:
            True if successful, False otherwise
        """
        data = {
            "entity_id": entity_id,
            "volume_level": volume_level
        }
        return self.call_service("media_player", "volume_set", data)
    
    def play_media(self, entity_id: str, media_url: str, media_type: str = "music") -> bool:
        """Play media on a media player.
        
        Args:
            entity_id: Media player entity ID
            media_url: URL or path to media
            media_type: Media type (e.g., 'music', 'playlist')
            
        Returns:
            True if successful, False otherwise
        """
        data = {
            "entity_id": entity_id,
            "media_content_id": media_url,
            "media_content_type": media_type
        }
        return self.call_service("media_player", "play_media", data)
    
    def speak_tts(self, entity_id: str, message: str) -> bool:
        """Have a media player speak a message using TTS.
        
        Args:
            entity_id: Media player entity ID
            message: Message to speak
            
        Returns:
            True if successful, False otherwise
        """
        data = {
            "entity_id": entity_id,
            "message": message
        }
        return self.call_service("tts", "speak", data)
    
    def get_weather_info(self) -> str:
        """Get current weather information from Home Assistant.
        
        Returns:
            Weather information as a formatted string
        """
        try:
            weather_data = self.get_state("weather.forecast_home")
            if not weather_data:
                return "I couldn't get the weather information right now."
            
            attributes = weather_data.get('attributes', {})
            current_temp = attributes.get('temperature')
            condition = weather_data.get('state', 'unknown')
            
            weather_text = f"The current weather is {condition} at {current_temp}°. "
            
            forecast = attributes.get('forecast', [{}])[0]
            if forecast:
                temp_low = forecast.get('temperature')
                temp_high = forecast.get('templow')
                if temp_low and temp_high:
                    weather_text += f"Today's forecast: high of {temp_high}° and low of {temp_low}°."
            
            return weather_text
        except Exception as e:
            logger.error(f"Error getting weather: {str(e)}")
            return "I couldn't get the weather information right now."
    
    def get_calendar_events(self) -> str:
        """Get today's calendar events from Home Assistant.
        
        Returns:
            Calendar events as a formatted string
        """
        try:
            import pytz
            from datetime import datetime
            
            # Get timezone from HA config
            timezone_response = self.get_state("sensor.time")
            timezone_str = "America/New_York"  # Default
            if timezone_response and 'attributes' in timezone_response:
                timezone_str = timezone_response.get('attributes', {}).get('timezone', timezone_str)
            
            local_tz = pytz.timezone(timezone_str)
            now = datetime.now(local_tz)
            
            start = now.strftime("%Y-%m-%dT00:00:00")
            end = now.strftime("%Y-%m-%dT23:59:59")
            
            # Get list of calendars
            response = requests.get(
                f"{self.base_url}/api/calendars",
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                return "I couldn't check your calendar right now."
            
            calendars = response.json()
            if not calendars:
                return "No calendars found."
            
            calendar_ids = [cal['entity_id'] for cal in calendars]
            events_text = "Here are today's events: "
            event_count = 0
            
            for cal_id in calendar_ids:
                events_response = requests.get(
                    f"{self.base_url}/api/calendars/{cal_id}?start={start}&end={end}",
                    headers=self.headers,
                    timeout=self.timeout
                )
                
                if events_response.status_code == 200:
                    events = events_response.json()
                    for event in events:
                        event_count += 1
                        start_time = datetime.fromisoformat(
                            event['start']['dateTime'].replace('Z', '+00:00')
                        ).astimezone(local_tz)
                        events_text += f"{event['summary']} at {start_time.strftime('%I:%M %p')}, "
            
            if event_count == 0:
                return "You have no events scheduled for today."
            else:
                return events_text[:-2] + "."
        except Exception as e:
            logger.error(f"Error getting calendar events: {str(e)}")
            return "I couldn't check your calendar right now."
    
    def get_entities_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """Get all entities of a specific domain.
        
        Args:
            domain: Entity domain (e.g., 'media_player', 'light')
            
        Returns:
            List of entity state dictionaries
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/states",
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                all_entities = response.json()
                return [
                    entity for entity in all_entities
                    if entity['entity_id'].startswith(f"{domain}.")
                ]
            else:
                logger.error(f"Failed to get entities: {response.status_code}")
                return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting entities: {str(e)}")
            return []
