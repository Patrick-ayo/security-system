#!/usr/bin/env python3
"""
Integrated Security Application with Audio Recognition
Combines object detection, enhanced audio monitoring, and real-time alerts
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

class IntegratedSecurityApp:
    def __init__(self):
        self.app = FastAPI(title="Security Monitor API with Audio", version="2.0.0")
        self.setup_routes()
        self.setup_cors()
        
        # Initialize modules
        self.audio_monitor = None
        self.is_monitoring = False
        
        # Threading
        self.monitoring_thread = None
        self.incident_queue = queue.Queue()
        
        # WebSocket connections
        self.active_connections: List[WebSocket] = []
        
        # Initialize modules
        self.initialize_modules()
        
        print("Integrated Security App with Audio Recognition initialized")
    
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
            return {"message": "Security Monitor API with Audio Recognition", "status": "running"}
        
        @self.app.get("/status")
        async def get_status():
            return {
                "monitoring": self.is_monitoring,
                "audio_monitor": self.audio_monitor.get_status() if self.audio_monitor else None,
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
        
        @self.app.post("/update_audio_keywords")
        async def update_audio_keywords(request: Request):
            data = await request.json()
            keywords = data.get('keywords', [])
            if self.audio_monitor:
                self.audio_monitor.update_keywords(keywords)
                return {"message": "Audio keywords updated", "keywords": keywords}
            return {"message": "Audio monitor not available", "status": "error"}
        
        @self.app.post("/update_audio_sensitivity")
        async def update_audio_sensitivity(request: Request):
            data = await request.json()
            sensitivity = data.get('sensitivity', 0.7)
            if self.audio_monitor:
                self.audio_monitor.update_sensitivity(sensitivity)
                return {"message": "Audio sensitivity updated", "sensitivity": sensitivity}
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
        """Initialize enhanced audio monitoring module"""
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
            
        except Exception as e:
            print(f"Error initializing modules: {e}")
    
    def start_monitoring(self):
        """Start monitoring with enhanced audio detection"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        
        # Start enhanced audio monitoring
        if self.audio_monitor:
            self.audio_monitor.start()
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitoring_thread.start()
        
        print("✓ Integrated monitoring with audio recognition started")
    
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
        while self.is_monitoring:
            try:
                # Process enhanced audio monitoring
                audio_result = None
                if self.audio_monitor:
                    audio_result = self.audio_monitor.process_frame()
                
                # Handle results
                if audio_result:
                    self.handle_audio_incident(audio_result)
                
                time.sleep(0.1)  # 10 FPS
                
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(1)
    
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
    
    print("Starting Integrated Security Application with Audio Recognition...")
    print("API available at: http://localhost:8000")
    print("WebSocket endpoint: ws://localhost:8000/ws")
    print("API documentation: http://localhost:8000/docs")
    print("\nAudio Recognition Features:")
    print("- Speech transcription")
    print("- Audio type detection (speech, music, noise, silence)")
    print("- Suspicious keyword detection")
    print("- Real-time audio analysis")
    print("- Spectral feature extraction")
    
    # Start the server
    uvicorn.run(
        app.app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

if __name__ == "__main__":
    main() 