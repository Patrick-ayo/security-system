#!/usr/bin/env python3
"""
AI Security Monitor - Main Backend Application
Handles IPC communication with Electron frontend and coordinates all AI modules
"""

import sys
import json
import time
import threading
import queue
from pathlib import Path
from typing import Dict, Any, Optional

# Add the current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

from face_recognition import FaceRecognitionModule
from voice_monitor import VoiceMonitorModule
from object_detect import ObjectDetectionModule
from activity_detect import ActivityDetectionModule
from buffer_manager import BufferManager
from log_storage import LogStorage

class SecurityMonitor:
    def __init__(self):
        self.config = self.load_config()
        self.is_monitoring = False
        self.modules = {}
        self.message_queue = queue.Queue()
        self.incident_queue = queue.Queue()
        
        # Initialize modules
        self.initialize_modules()
        
        # Initialize storage
        self.log_storage = LogStorage(self.config.get('storage', {}))
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from shared config file"""
        config_path = Path(__file__).parent.parent / 'shared' / 'config.json'
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Config file not found: {config_path}")
            return self.get_default_config()
        except json.JSONDecodeError:
            print(f"Invalid JSON in config file: {config_path}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            'face_recognition': {
                'enabled': True,
                'confidence_threshold': 0.8,
                'known_faces_path': 'data/known_faces'
            },
            'voice_monitor': {
                'enabled': True,
                'sensitivity': 0.7,
                'suspicious_keywords': ['help', 'emergency', 'danger']
            },
            'object_detection': {
                'enabled': True,
                'confidence_threshold': 0.6,
                'suspicious_objects': ['phone', 'weapon', 'bottle']
            },
            'activity_detection': {
                'enabled': True,
                'suspicious_activities': ['fighting', 'theft', 'vandalism']
            },
            'buffer': {
                'video_buffer_size': 30,  # seconds
                'audio_buffer_size': 10,   # seconds
                'max_incident_duration': 60  # seconds
            },
            'storage': {
                'incidents_path': 'data/incidents',
                'logs_path': 'data/logs',
                'encryption_key': 'your-secret-key-here'
            }
        }
    
    def initialize_modules(self):
        """Initialize all AI monitoring modules"""
        try:
            if self.config.get('face_recognition', {}).get('enabled', True):
                self.modules['face_recognition'] = FaceRecognitionModule(
                    self.config['face_recognition']
                )
                print("✓ Face recognition module initialized")
            
            if self.config.get('voice_monitor', {}).get('enabled', True):
                self.modules['voice_monitor'] = VoiceMonitorModule(
                    self.config['voice_monitor']
                )
                print("✓ Voice monitoring module initialized")
            
            if self.config.get('object_detection', {}).get('enabled', True):
                self.modules['object_detection'] = ObjectDetectionModule(
                    self.config['object_detection']
                )
                print("✓ Object detection module initialized")
            
            if self.config.get('activity_detection', {}).get('enabled', True):
                self.modules['activity_detection'] = ActivityDetectionModule(
                    self.config['activity_detection']
                )
                print("✓ Activity detection module initialized")
                
        except Exception as e:
            print(f"Error initializing modules: {e}")
    
    def start_monitoring(self):
        """Start all monitoring modules"""
        if self.is_monitoring:
            print("Monitoring already active")
            return
        
        self.is_monitoring = True
        print("Starting AI security monitoring...")
        
        # Start buffer manager
        self.buffer_manager = BufferManager(self.config.get('buffer', {}))
        
        # Start monitoring threads for each module
        self.monitoring_threads = []
        
        for module_name, module in self.modules.items():
            thread = threading.Thread(
                target=self.monitor_module,
                args=(module_name, module),
                daemon=True
            )
            thread.start()
            self.monitoring_threads.append(thread)
            print(f"Started {module_name} monitoring thread")
        
        # Start incident processing thread
        incident_thread = threading.Thread(
            target=self.process_incidents,
            daemon=True
        )
        incident_thread.start()
        self.monitoring_threads.append(incident_thread)
        
        print("✓ All monitoring modules started")
    
    def stop_monitoring(self):
        """Stop all monitoring modules"""
        if not self.is_monitoring:
            print("Monitoring not active")
            return
        
        self.is_monitoring = False
        print("Stopping AI security monitoring...")
        
        # Stop buffer manager
        if hasattr(self, 'buffer_manager'):
            self.buffer_manager.stop()
        
        # Wait for threads to finish
        for thread in self.monitoring_threads:
            thread.join(timeout=5)
        
        print("✓ All monitoring modules stopped")
    
    def monitor_module(self, module_name: str, module):
        """Monitor a specific AI module"""
        try:
            while self.is_monitoring:
                # Get data from module
                result = module.process_frame()
                
                if result and result.get('detected'):
                    # Create incident
                    incident = {
                        'timestamp': time.time(),
                        'module': module_name,
                        'type': result.get('type', 'unknown'),
                        'confidence': result.get('confidence', 0.0),
                        'details': result.get('details', {}),
                        'frame_data': result.get('frame_data')
                    }
                    
                    # Add to incident queue
                    self.incident_queue.put(incident)
                
                time.sleep(0.1)  # 10 FPS
                
        except Exception as e:
            print(f"Error in {module_name} monitoring: {e}")
    
    def process_incidents(self):
        """Process incidents from the queue"""
        while self.is_monitoring:
            try:
                # Get incident from queue (non-blocking)
                incident = self.incident_queue.get(timeout=1)
                
                # Log incident
                self.log_storage.log_incident(incident)
                
                # Save incident data
                self.log_storage.save_incident(incident)
                
                # Send to frontend (if IPC is available)
                self.send_to_frontend({
                    'type': 'incident',
                    'data': incident
                })
                
                print(f"Incident detected: {incident['type']} ({incident['confidence']:.2f})")
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing incident: {e}")
    
    def send_to_frontend(self, message: Dict[str, Any]):
        """Send message to Electron frontend"""
        # This would be implemented based on your IPC mechanism
        # For now, just print to stdout for Electron to capture
        print(f"FRONTEND_MESSAGE: {json.dumps(message)}")
    
    def handle_command(self, command: str, data: Optional[Dict] = None):
        """Handle commands from Electron frontend"""
        if command == 'start_monitoring':
            self.start_monitoring()
        elif command == 'stop_monitoring':
            self.stop_monitoring()
        elif command == 'get_status':
            return {
                'monitoring': self.is_monitoring,
                'modules': list(self.modules.keys()),
                'config': self.config
            }
        elif command == 'update_config':
            if data:
                self.config.update(data)
                self.save_config()
        else:
            print(f"Unknown command: {command}")
    
    def save_config(self):
        """Save current configuration to file"""
        config_path = Path(__file__).parent.parent / 'shared' / 'config.json'
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            print("Configuration saved")
        except Exception as e:
            print(f"Error saving config: {e}")

def main():
    """Main entry point for the security monitor"""
    monitor = SecurityMonitor()
    
    print("AI Security Monitor Backend Started")
    print("Waiting for commands from Electron frontend...")
    
    # Simple command loop for testing
    try:
        while True:
            # Read from stdin for IPC with Electron
            line = input().strip()
            
            if line.startswith('COMMAND:'):
                # Parse command
                parts = line.split(':', 2)
                if len(parts) >= 2:
                    command = parts[1]
                    data = json.loads(parts[2]) if len(parts) > 2 else None
                    monitor.handle_command(command, data)
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        monitor.stop_monitoring()
    except EOFError:
        print("EOF received, shutting down...")
        monitor.stop_monitoring()

if __name__ == "__main__":
    main() 