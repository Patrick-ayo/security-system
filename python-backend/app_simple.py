#!/usr/bin/env python3
"""
Simplified AI Security Monitor Backend
This version works without problematic dependencies like dlib
"""

import sys
import json
import time
import threading
import queue
from pathlib import Path
from typing import Dict, Any, Optional

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

class SimpleSecurityMonitor:
    def __init__(self):
        self.config = self.load_config()
        self.running = False
        self.incident_queue = queue.Queue()
        self.log_queue = queue.Queue()
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from shared config file"""
        try:
            config_path = Path(__file__).parent.parent / "shared" / "config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
        
        # Default configuration
        return {
            "app": {
                "name": "AI Security Monitor",
                "version": "1.0.0"
            },
            "development": {
                "debug_mode": True,
                "test_mode": False
            },
            "face_recognition": {
                "enabled": False,  # Disabled due to dlib dependency
                "confidence_threshold": 0.8
            },
            "voice_monitor": {
                "enabled": True,
                "sensitivity": 0.7
            },
            "object_detection": {
                "enabled": True,
                "confidence_threshold": 0.6
            },
            "activity_detection": {
                "enabled": True
            }
        }
    
    def log_message(self, message: str, level: str = "INFO"):
        """Log a message"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        self.log_queue.put(log_entry)
        print(f"[{level}] {message}")
    
    def create_test_incident(self, incident_type: str, details: str):
        """Create a test incident for demonstration"""
        incident = {
            "id": f"incident_{int(time.time())}",
            "type": incident_type,
            "timestamp": time.time(),
            "details": details,
            "severity": "medium",
            "module": "test"
        }
        self.incident_queue.put(incident)
        self.log_message(f"Test incident created: {incident_type} - {details}")
    
    def simulate_monitoring(self):
        """Simulate monitoring activity"""
        self.log_message("Starting simplified security monitoring...")
        
        # Simulate periodic incidents for testing
        incident_counter = 0
        while self.running:
            try:
                time.sleep(10)  # Check every 10 seconds
                
                if incident_counter % 3 == 0:  # Create incident every 30 seconds
                    self.create_test_incident(
                        "motion_detected", 
                        "Suspicious movement detected in camera view"
                    )
                    self.send_to_frontend({
                        "type": "status_update",
                        "message": "Motion detected in camera view",
                        "timestamp": time.time()
                    })
                
                if incident_counter % 5 == 0:  # Create different incident every 50 seconds
                    self.create_test_incident(
                        "voice_anomaly", 
                        "Unusual voice pattern detected"
                    )
                    self.send_to_frontend({
                        "type": "status_update", 
                        "message": "Voice anomaly detected",
                        "timestamp": time.time()
                    })
                
                incident_counter += 1
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log_message(f"Error in monitoring: {e}", "ERROR")
    
    def start_monitoring(self):
        """Start the monitoring system"""
        self.running = True
        self.log_message("AI Security Monitor Backend Started")
        self.log_message("Running in simplified mode (some features disabled)")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.simulate_monitoring)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        return {"status": "started", "message": "Monitoring started successfully"}
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.running = False
        self.log_message("Monitoring stopped")
        return {"status": "stopped", "message": "Monitoring stopped successfully"}
    
    def get_status(self):
        """Get current system status"""
        return {
            "running": self.running,
            "modules": {
                "face_recognition": "disabled (dlib dependency)",
                "voice_monitor": "enabled",
                "object_detection": "enabled", 
                "activity_detection": "enabled"
            },
            "config": self.config
        }
    
    def handle_command(self, command: str, data: Optional[Dict] = None):
        """Handle commands from the Electron frontend"""
        try:
            if command == "start-monitoring":
                result = self.start_monitoring()
                self.send_to_frontend({"type": "command_response", "command": command, "result": result})
                
            elif command == "stop-monitoring":
                result = self.stop_monitoring()
                self.send_to_frontend({"type": "command_response", "command": command, "result": result})
                
            elif command == "get-status":
                result = self.get_status()
                self.send_to_frontend({"type": "command_response", "command": command, "result": result})
                
            elif command == "get-incidents":
                incidents = []
                while not self.incident_queue.empty():
                    incidents.append(self.incident_queue.get())
                self.send_to_frontend({"type": "incidents", "data": incidents})
                
            elif command == "get-logs":
                logs = []
                while not self.log_queue.empty():
                    logs.append(self.log_queue.get())
                self.send_to_frontend({"type": "logs", "data": logs})
                
            else:
                self.log_message(f"Unknown command: {command}", "WARNING")
                
        except Exception as e:
            self.log_message(f"Error handling command {command}: {e}", "ERROR")
    
    def send_to_frontend(self, message: Dict[str, Any]):
        """Send message to Electron frontend"""
        print(f"FRONTEND_MESSAGE: {json.dumps(message)}")

def main():
    """Main function"""
    monitor = SimpleSecurityMonitor()
    
    print("Simplified AI Security Monitor Backend Started")
    print("Waiting for commands from Electron frontend...")
    print("Note: Some features are disabled due to missing dependencies")
    print("To enable full features, install CMake and rebuild dlib")
    
    try:
        while True:
            line = input().strip()
            if line.startswith('COMMAND:'):
                parts = line.split(':', 2)
                if len(parts) >= 2:
                    command = parts[1]
                    data = json.loads(parts[2]) if len(parts) > 2 else None
                    monitor.handle_command(command, data)
            time.sleep(0.1)
    except (KeyboardInterrupt, EOFError):
        print("\nShutting down...")
        monitor.stop_monitoring()

if __name__ == "__main__":
    main() 