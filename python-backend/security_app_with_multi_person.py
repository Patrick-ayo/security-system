#!/usr/bin/env python3
"""
Integrated Security Application with Multi-Person Detection
Combines object detection, audio monitoring, and multi-person detection
"""

import cv2
import numpy as np
import time
import json
import threading
import queue
from pathlib import Path
from typing import Dict, Any, Optional, List
import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import base64

# Import our modules
from enhanced_audio_monitor import EnhancedAudioMonitor
from multi_person_detector import MultiPersonDetector

class IntegratedSecurityApp:
    def __init__(self):
        self.app = FastAPI(title="Security Monitor API with Multi-Person Detection", version="3.0.0")
        self.setup_routes()
        self.setup_cors()
        
        # Initialize modules
        self.audio_monitor = None
        self.multi_person_detector = None
        self.is_monitoring = False
        
        # Threading
        self.monitoring_thread = None
        self.incident_queue = queue.Queue()
        
        # WebSocket connections
        self.active_connections: List[WebSocket] = []
        
        # Initialize modules
        self.initialize_modules()
        
        print("Integrated Security App with Multi-Person Detection initialized")
    
    def setup_cors(self):
        """Setup CORS middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/")
        async def root():
            return {"message": "Security Monitor API with Multi-Person Detection", "status": "running"}
        
        @self.app.get("/status")
        async def get_status():
            return {
                "monitoring": self.is_monitoring,
                "audio_monitor": self.audio_monitor.get_status() if self.audio_monitor else None,
                "multi_person_detector": self.multi_person_detector.get_status() if self.multi_person_detector else None,
                "audio_statistics": self.audio_monitor.get_audio_statistics() if self.audio_monitor else None
            }
        
        @self.app.post("/start_monitoring")
        async def start_monitoring():
            if not self.is_monitoring:
                self.start_monitoring()
                return {"message": "Monitoring started", "status": "success"}
            return {"message": "Monitoring already active", "status": "info"}
        
        @self.app.post("/stop_monitoring")
        async def stop_monitoring():
            if self.is_monitoring:
                self.stop_monitoring()
                return {"message": "Monitoring stopped", "status": "success"}
            return {"message": "Monitoring not active", "status": "info"}
        
        @self.app.post("/update_multi_person_config")
        async def update_multi_person_config(request: Request):
            data = await request.json()
            if self.multi_person_detector:
                self.multi_person_detector.update_config(data)
                return {"message": "Multi-person detector config updated", "config": data}
            return {"message": "Multi-person detector not available", "status": "error"}
        
        @self.app.post("/update_audio_keywords")
        async def update_audio_keywords(request: Request):
            data = await request.json()
            keywords = data.get('keywords', [])
            if self.audio_monitor:
                self.audio_monitor.update_keywords(keywords)
                return {"message": "Audio keywords updated", "keywords": keywords}
            return {"message": "Audio monitor not available", "status": "error"}
        
        @self.app.get("/audio_statistics")
        async def get_audio_statistics():
            if self.audio_monitor:
                return {
                    "audio_types": self.audio_monitor.get_audio_statistics(),
                    "status": "success"
                }
            return {"message": "Audio monitor not available", "status": "error"}
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)
            try:
                while True:
                    # Keep connection alive
                    await websocket.receive_text()
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
    
    def initialize_modules(self):
        """Initialize all monitoring modules"""
        try:
            # Initialize enhanced audio monitor
            audio_config = {
                'sensitivity': 0.7,
                'suspicious_keywords': [
                    'help', 'emergency', 'danger', 'fire', 'police', 'attack',
                    'threat', 'dangerous', 'weapon', 'gun', 'knife', 'fight',
                    'intruder', 'break in', 'robbery', 'assault', 'kill', 'hurt',
                    'bomb', 'explosive', 'terrorist', 'hostage', 'scream', 'cry'
                ]
            }
            self.audio_monitor = EnhancedAudioMonitor(audio_config)
            print("✓ Enhanced audio monitor initialized")
            
            # Initialize multi-person detector
            multi_person_config = {
                'max_allowed_people': 1,  # Only 1 person allowed
                'alert_threshold': 2,      # Alert when 2+ people detected
                'detection_confidence': 0.5,
                'alert_cooldown': 10       # 10 seconds between alerts
            }
            self.multi_person_detector = MultiPersonDetector(multi_person_config)
            print("✓ Multi-person detector initialized")
            
        except Exception as e:
            print(f"Error initializing modules: {e}")
    
    def start_monitoring(self):
        """Start monitoring with all features"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        
        # Start enhanced audio monitoring
        if self.audio_monitor:
            self.audio_monitor.start()
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitoring_thread.start()
        
        print("✓ Integrated monitoring with multi-person detection started")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        # Stop audio monitoring
        if self.audio_monitor:
            self.audio_monitor.stop()
        
        # Wait for monitoring thread
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        print("✓ Monitoring stopped")
    
    def monitor_loop(self):
        """Main monitoring loop"""
        # Initialize camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Cannot open camera for multi-person detection")
            return
        
        try:
            while self.is_monitoring:
                # Read camera frame
                ret, frame = cap.read()
                if not ret:
                    continue
                
                # Process multi-person detection
                multi_person_result = None
                if self.multi_person_detector:
                    multi_person_result = self.multi_person_detector.process_frame(frame)
                
                # Process enhanced audio monitoring
                audio_result = None
                if self.audio_monitor:
                    audio_result = self.audio_monitor.process_frame()
                
                # Handle results
                if multi_person_result and multi_person_result.get('is_alert'):
                    self.handle_multi_person_incident(multi_person_result)
                
                if audio_result:
                    self.handle_audio_incident(audio_result)
                
                time.sleep(0.1)  # 10 FPS
                
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
        finally:
            cap.release()
    
    def handle_multi_person_incident(self, result: Dict[str, Any]):
        """Handle multi-person detection incidents"""
        incident = {
            'timestamp': time.time(),
            'type': 'multi_person_alert',
            'module': 'multi_person_detector',
            'person_count': result.get('person_count', 0),
            'max_allowed': result.get('max_allowed', 1),
            'alert_message': result.get('alert_message', ''),
            'people_detected': result.get('people', []),
            'message': f"🚨 MULTI-PERSON ALERT: {result.get('person_count', 0)} people detected! Maximum allowed: {result.get('max_allowed', 1)}"
        }
        
        # Send to WebSocket clients
        self.broadcast_incident(incident)
        
        # Log incident
        print(f"MULTI-PERSON ALERT: {incident['message']}")
        print(f"People detected: {incident['person_count']}")
        print(f"Max allowed: {incident['max_allowed']}")
        print("---")
    
    def handle_audio_incident(self, result: Dict[str, Any]):
        """Handle audio monitoring incidents"""
        incident = {
            'timestamp': time.time(),
            'type': 'audio_incident',
            'module': 'enhanced_audio_monitor',
            'audio_type': result.get('audio_type', 'unknown'),
            'confidence': result.get('confidence', 0.0),
            'details': result.get('details', {}),
            'features': result.get('features', {}),
            'text': result.get('text', ''),
            'message': f"Audio incident detected: {result.get('audio_type', 'unknown')}"
        }
        
        # Add specific message for suspicious speech
        if result.get('detected'):
            incident['message'] = f"SUSPICIOUS SPEECH DETECTED: {result.get('details', {}).get('text', 'Unknown')}"
            incident['confidence'] = result.get('confidence', 0.0)
            incident['keywords'] = result.get('details', {}).get('keywords', [])
        
        # Send to WebSocket clients
        self.broadcast_incident(incident)
        
        # Log incident with detailed information
        print(f"AUDIO INCIDENT: {incident['message']}")
        print(f"Audio Type: {incident['audio_type']}")
        if incident.get('text'):
            print(f"Transcribed Text: {incident['text']}")
        if incident.get('keywords'):
            print(f"Detected Keywords: {incident['keywords']}")
        print(f"Confidence: {incident['confidence']:.2f}")
        print("---")
    
    async def broadcast_incident(self, incident: Dict[str, Any]):
        """Broadcast incident to all WebSocket clients"""
        if self.active_connections:
            message = json.dumps({
                'type': 'incident',
                'data': incident
            })
            
            # Send to all connected clients
            for connection in self.active_connections:
                try:
                    await connection.send_text(message)
                except:
                    # Remove disconnected clients
                    self.active_connections.remove(connection)

def main():
    """Main entry point"""
    app = IntegratedSecurityApp()
    
    print("Starting Integrated Security Application with Multi-Person Detection...")
    print("API available at: http://localhost:8000")
    print("WebSocket endpoint: ws://localhost:8000/ws")
    print("API documentation: http://localhost:8000/docs")
    print("\nSecurity Features:")
    print("- Multi-person detection (alerts when >1 person detected)")
    print("- Speech transcription and analysis")
    print("- Audio type detection (speech, music, noise, silence)")
    print("- Suspicious keyword detection")
    print("- Real-time alerts and notifications")
    
    # Start the server
    uvicorn.run(
        app.app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

if __name__ == "__main__":
    main() 