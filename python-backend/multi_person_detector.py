#!/usr/bin/env python3
"""
Multi-Person Detection System
Detects when multiple people are in camera view and triggers security alerts
"""

import cv2
import numpy as np
import time
import json
from typing import Dict, List, Any, Optional
import threading
from pathlib import Path

class MultiPersonDetector:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_allowed_people = config.get('max_allowed_people', 1)
        self.alert_threshold = config.get('alert_threshold', 2)  # Alert when 2+ people detected
        self.detection_confidence = config.get('detection_confidence', 0.5)
        self.alert_cooldown = config.get('alert_cooldown', 10)  # seconds
        
        # Detection history
        self.last_alert_time = 0
        self.person_count_history = []
        self.max_history_size = 30  # Keep last 30 detections
        
        # Load YOLO model for person detection
        self.model = None
        self.classes = []
        self.initialize_model()
        
        print(f"Multi-Person Detector initialized")
        print(f"Max allowed people: {self.max_allowed_people}")
        print(f"Alert threshold: {self.alert_threshold} people")
    
    def initialize_model(self):
        """Initialize YOLO model for person detection"""
        try:
            # Load YOLO model
            model_path = Path(__file__).parent / 'yolov8n.pt'
            if not model_path.exists():
                print("⚠️  YOLO model not found, downloading...")
                self.download_yolo_model()
            
            from ultralytics import YOLO
            self.model = YOLO('yolov8n.pt')
            print("✅ YOLO model loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading YOLO model: {e}")
            print("⚠️  Using OpenCV HOG detector as fallback")
            self.model = None
    
    def download_yolo_model(self):
        """Download YOLO model if not available"""
        try:
            from ultralytics import YOLO
            model = YOLO('yolov8n.pt')
            print("✅ YOLO model downloaded successfully")
        except Exception as e:
            print(f"❌ Error downloading YOLO model: {e}")
    
    def detect_people_yolo(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect people using YOLO model"""
        if self.model is None:
            return []
        
        try:
            # Run YOLO detection
            results = self.model(frame, verbose=False)
            
            people = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Check if detected object is a person (class 0 in COCO dataset)
                        if int(box.cls[0]) == 0:  # Person class
                            confidence = float(box.conf[0])
                            if confidence > self.detection_confidence:
                                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                                people.append({
                                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                    'confidence': confidence,
                                    'center': [int((x1 + x2) / 2), int((y1 + y2) / 2)]
                                })
            
            return people
            
        except Exception as e:
            print(f"Error in YOLO detection: {e}")
            return []
    
    def detect_people_hog(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect people using OpenCV HOG detector (fallback)"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Initialize HOG detector
            hog = cv2.HOGDescriptor()
            hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            
            # Detect people
            boxes, weights = hog.detectMultiScale(
                gray, 
                winStride=(8, 8),
                padding=(4, 4),
                scale=1.05
            )
            
            people = []
            for (x, y, w, h), weight in zip(boxes, weights):
                if weight > self.detection_confidence:
                    people.append({
                        'bbox': [x, y, x + w, y + h],
                        'confidence': weight,
                        'center': [x + w // 2, y + h // 2]
                    })
            
            return people
            
        except Exception as e:
            print(f"Error in HOG detection: {e}")
            return []
    
    def detect_people(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect people in the frame"""
        # Try YOLO first
        people = self.detect_people_yolo(frame)
        
        # Fallback to HOG if YOLO fails
        if not people:
            people = self.detect_people_hog(frame)
        
        return people
    
    def analyze_person_count(self, people: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze person count and determine if alert should be triggered"""
        person_count = len(people)
        current_time = time.time()
        
        # Add to history
        self.person_count_history.append({
            'count': person_count,
            'timestamp': current_time,
            'people': people
        })
        
        # Keep only recent history
        if len(self.person_count_history) > self.max_history_size:
            self.person_count_history.pop(0)
        
        # Calculate average person count over recent detections
        recent_counts = [entry['count'] for entry in self.person_count_history[-10:]]
        avg_count = sum(recent_counts) / len(recent_counts) if recent_counts else 0
        
        # Determine alert status
        is_alert = False
        alert_type = None
        alert_message = ""
        
        if person_count > self.max_allowed_people:
            if person_count >= self.alert_threshold:
                # Check cooldown to avoid spam alerts
                if current_time - self.last_alert_time > self.alert_cooldown:
                    is_alert = True
                    alert_type = "multiple_people"
                    alert_message = f"🚨 SECURITY ALERT: {person_count} people detected! Maximum allowed: {self.max_allowed_people}"
                    self.last_alert_time = current_time
        
        return {
            'person_count': person_count,
            'avg_count': avg_count,
            'is_alert': is_alert,
            'alert_type': alert_type,
            'alert_message': alert_message,
            'people': people,
            'timestamp': current_time
        }
    
    def draw_detections(self, frame: np.ndarray, people: List[Dict[str, Any]], analysis: Dict[str, Any]) -> np.ndarray:
        """Draw detection boxes and information on frame"""
        frame_copy = frame.copy()
        
        # Draw person detection boxes
        for i, person in enumerate(people):
            bbox = person['bbox']
            confidence = person['confidence']
            
            # Color based on alert status
            if analysis['is_alert']:
                color = (0, 0, 255)  # Red for alert
            else:
                color = (0, 255, 0)  # Green for normal
            
            # Draw bounding box
            cv2.rectangle(frame_copy, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            
            # Draw person label
            label = f"Person {i+1}: {confidence:.2f}"
            cv2.putText(frame_copy, label, (bbox[0], bbox[1] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Draw information panel
        panel_height = 120
        panel = np.zeros((panel_height, frame.shape[1], 3), dtype=np.uint8)
        
        # Background color based on alert status
        if analysis['is_alert']:
            panel_color = (0, 0, 255)  # Red background
        else:
            panel_color = (0, 255, 0)  # Green background
        
        panel[:] = panel_color
        
        # Add text information
        cv2.putText(panel, f"People Detected: {analysis['person_count']}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(panel, f"Max Allowed: {self.max_allowed_people}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(panel, f"Average: {analysis['avg_count']:.1f}", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Add alert message if applicable
        if analysis['is_alert']:
            cv2.putText(panel, analysis['alert_message'], (10, 110), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Combine frame with panel
        result = np.vstack([frame_copy, panel])
        
        return result
    
    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """Process a single frame for multi-person detection"""
        # Detect people
        people = self.detect_people(frame)
        
        # Analyze person count
        analysis = self.analyze_person_count(people)
        
        # Create result
        result = {
            'timestamp': analysis['timestamp'],
            'person_count': analysis['person_count'],
            'avg_count': analysis['avg_count'],
            'is_alert': analysis['is_alert'],
            'alert_type': analysis['alert_type'],
            'alert_message': analysis['alert_message'],
            'people': people,
            'max_allowed': self.max_allowed_people,
            'alert_threshold': self.alert_threshold
        }
        
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """Get current detector status"""
        return {
            'max_allowed_people': self.max_allowed_people,
            'alert_threshold': self.alert_threshold,
            'detection_confidence': self.detection_confidence,
            'alert_cooldown': self.alert_cooldown,
            'last_alert_time': self.last_alert_time,
            'history_size': len(self.person_count_history)
        }
    
    def update_config(self, config: Dict[str, Any]):
        """Update detector configuration"""
        self.max_allowed_people = config.get('max_allowed_people', self.max_allowed_people)
        self.alert_threshold = config.get('alert_threshold', self.alert_threshold)
        self.detection_confidence = config.get('detection_confidence', self.detection_confidence)
        self.alert_cooldown = config.get('alert_cooldown', self.alert_cooldown)
        print(f"✅ Multi-person detector configuration updated")

def main():
    """Test the multi-person detector"""
    config = {
        'max_allowed_people': 1,
        'alert_threshold': 2,
        'detection_confidence': 0.5,
        'alert_cooldown': 10
    }
    
    detector = MultiPersonDetector(config)
    
    # Test with webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Cannot open webcam")
        return
    
    print("🎥 Multi-Person Detection Test")
    print("Press 'q' to quit")
    print("=" * 50)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Cannot read frame")
                break
            
            # Process frame
            result = detector.process_frame(frame)
            
            # Draw detections
            frame_with_info = detector.draw_detections(frame, result['people'], result)
            
            # Display result
            if result['is_alert']:
                print(f"🚨 ALERT: {result['alert_message']}")
                print(f"   People detected: {result['person_count']}")
                print(f"   Time: {time.strftime('%H:%M:%S')}")
                print("-" * 50)
            
            # Show frame
            cv2.imshow('Multi-Person Detection', frame_with_info)
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping multi-person detection...")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("✅ Multi-person detection stopped")

if __name__ == "__main__":
    main() 