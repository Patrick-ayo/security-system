#!/usr/bin/env python3
"""
Integrated Security Application
Combines object detection, voice monitoring, and real-time alerts
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
from voice_monitor import VoiceMonitorModule
from object_detect import ObjectDetectionModule

class IntegratedSecurityApp:
    def __init__(self):
        self.app = FastAPI(title="Security Monitor API", version="1.0.0")
        self.setup_routes()
        self.setup_cors()
        
        # Initialize modules
        self.voice_monitor = None
        self.object_detector = None
        self.is_monitoring = False
        
        # Threading
        self.monitoring_thread = None
        self.incident_queue = queue.Queue()
        
        # WebSocket connections
        self.active_connections: List[WebSocket] = []
        
        # Initialize modules
        self.initialize_modules()
        
        print("Integrated Security App initialized")
    
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
            return {"message": "Security Monitor API", "status": "running"}
        
        @self.app.get("/status")
        async def get_status():
            return {
                "monitoring": self.is_monitoring,
                "voice_monitor": self.voice_monitor.get_status() if self.voice_monitor else None,
                "object_detector": "active" if self.object_detector else "inactive"
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
        
        @self.app.post("/update_voice_keywords")
        async def update_voice_keywords(request: Request):
            data = await request.json()
            keywords = data.get('keywords', [])
            if self.voice_monitor:
                self.voice_monitor.update_keywords(keywords)
                return {"message": "Keywords updated", "keywords": keywords}
            return {"message": "Voice monitor not available", "status": "error"}
        
        @self.app.post("/update_voice_sensitivity")
        async def update_voice_sensitivity(request: Request):
            data = await request.json()
            sensitivity = data.get('sensitivity', 0.7)
            if self.voice_monitor:
                self.voice_monitor.update_sensitivity(sensitivity)
                return {"message": "Sensitivity updated", "sensitivity": sensitivity}
            return {"message": "Voice monitor not available", "status": "error"}
        
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
        """Initialize voice and object detection modules"""
        try:
            # Initialize voice monitor
            voice_config = {
                'sensitivity': 0.7,
                'suspicious_keywords': [
                    'help', 'emergency', 'danger', 'fire', 'police', 'attack',
                    'threat', 'dangerous', 'weapon', 'gun', 'knife', 'fight',
                    'intruder', 'break in', 'robbery', 'assault'
                ]
            }
            self.voice_monitor = VoiceMonitorModule(voice_config)
            print("✓ Voice monitor initialized")
            
            # Initialize object detector
            object_config = {
                'confidence_threshold': 0.6,
                'suspicious_objects': ['phone', 'weapon', 'bottle', 'knife', 'gun']
            }
            self.object_detector = ObjectDetectionModule(object_config)
            print("✓ Object detector initialized")
            
        except Exception as e:
            print(f"Error initializing modules: {e}")
    
    def start_monitoring(self):
        """Start monitoring with both voice and object detection"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        
        # Start voice monitoring
        if self.voice_monitor:
            self.voice_monitor.start()
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitoring_thread.start()
        
        print("✓ Integrated monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        # Stop voice monitoring
        if self.voice_monitor:
            self.voice_monitor.stop()
        
        # Wait for monitoring thread
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        print("✓ Monitoring stopped")
    
    def monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Process voice monitoring
                voice_result = None
                if self.voice_monitor:
                    voice_result = self.voice_monitor.process_frame()
                
                # Process object detection (simulated for now)
                object_result = None
                if self.object_detector:
                    # This would normally process camera frames
                    # For now, we'll simulate object detection
                    pass
                
                # Handle results
                if voice_result:
                    self.handle_voice_incident(voice_result)
                
                if object_result:
                    self.handle_object_incident(object_result)
                
                time.sleep(0.1)  # 10 FPS
                
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(1)
    
    def handle_voice_incident(self, result: Dict[str, Any]):
        """Handle voice monitoring incidents"""
        incident = {
            'timestamp': time.time(),
            'type': 'voice_incident',
            'module': 'voice_monitor',
            'confidence': result.get('confidence', 0.0),
            'details': result.get('details', {}),
            'message': f"Voice incident detected: {result.get('details', {}).get('text', 'Unknown')}"
        }
        
        # Send to WebSocket clients
        self.broadcast_incident(incident)
        
        # Log incident
        print(f"VOICE INCIDENT: {incident['message']} (confidence: {incident['confidence']:.2f})")
    
    def handle_object_incident(self, result: Dict[str, Any]):
        """Handle object detection incidents"""
        incident = {
            'timestamp': time.time(),
            'type': 'object_incident',
            'module': 'object_detector',
            'confidence': result.get('confidence', 0.0),
            'details': result.get('details', {}),
            'message': f"Object incident detected: {result.get('details', {}).get('objects', [])}"
        }
        
        # Send to WebSocket clients
        self.broadcast_incident(incident)
        
        # Log incident
        print(f"OBJECT INCIDENT: {incident['message']} (confidence: {incident['confidence']:.2f})")
    
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
    
    print("Starting Integrated Security Application...")
    print("API available at: http://localhost:8000")
    print("WebSocket endpoint: ws://localhost:8000/ws")
    print("API documentation: http://localhost:8000/docs")
    
    # Start the server
    uvicorn.run(
        app.app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

if __name__ == "__main__":
    main()