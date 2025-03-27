"""
Health check server for the Home Assistant Smart Alarm Clock.

This module provides a simple HTTP server for health checks.
"""

import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime

logger = logging.getLogger('health_check')

class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health check endpoint."""
    
    def __init__(self, *args, ha_client=None, **kwargs):
        """Initialize the handler with a Home Assistant client.
        
        Args:
            ha_client: Home Assistant client for checking connection status
        """
        self.ha_client = ha_client
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/health':
            # Basic health check
            ha_status = "UP" if self.ha_client and self.ha_client.is_available() else "DOWN"
            
            response = {
                "status": "UP",
                "home_assistant": ha_status,
                "timestamp": datetime.now().isoformat()
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

def start_health_check_server(port, ha_client):
    """Start the health check server in a separate thread.
    
    Args:
        port: Port to listen on
        ha_client: Home Assistant client for checking connection status
    """
    # Create handler class with access to ha_client
    handler_class = type('HealthCheckHandlerWithClient', 
                         (HealthCheckHandler,), 
                         {'ha_client': ha_client})
    
    server = HTTPServer(('0.0.0.0', port), handler_class)
    
    # Start server in a separate thread
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    
    logger.info(f"Started health check server on port {port}")
    
    return server, thread
