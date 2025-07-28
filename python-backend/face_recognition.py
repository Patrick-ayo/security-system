#!/usr/bin/env python3
"""
Face Recognition Module
Uses DeepFace or face_recognition library for face detection and recognition
"""

import cv2
import numpy as np
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import threading

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    print("DeepFace not available, using OpenCV face detection only")

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("face_recognition library not available")

class FaceRecognitionModule:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.confidence_threshold = config.get('confidence_threshold', 0.8)
        self.known_faces_path = Path(config.get('known_faces_path', 'data/known_faces'))
        
        # Initialize face detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Load known faces
        self.known_faces = []
        self.known_names = []
        self.load_known_faces()
        
        # Threading
        self.is_running = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        print(f"Face recognition module initialized with {len(self.known_faces)} known faces")
    
    def load_known_faces(self):
        """Load known faces from the specified directory"""
        if not self.known_faces_path.exists():
            self.known_faces_path.mkdir(parents=True, exist_ok=True)
            print(f"Created known faces directory: {self.known_faces_path}")
            return
        
        # Load known faces from images
        for image_path in self.known_faces_path.glob('*.jpg'):
            try:
                # Load image
                image = cv2.imread(str(image_path))
                if image is None:
                    continue
                
                # Convert to RGB for face_recognition
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                # Get face encodings
                if FACE_RECOGNITION_AVAILABLE:
                    face_encodings = face_recognition.face_encodings(rgb_image)
                    if face_encodings:
                        self.known_faces.extend(face_encodings)
                        # Use filename as name (without extension)
                        name = image_path.stem
                        self.known_names.extend([name] * len(face_encodings))
                        print(f"Loaded face: {name}")
                
            except Exception as e:
                print(f"Error loading face from {image_path}: {e}")
    
    def add_known_face(self, image: np.ndarray, name: str):
        """Add a new known face"""
        try:
            # Convert to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            if FACE_RECOGNITION_AVAILABLE:
                face_encodings = face_recognition.face_encodings(rgb_image)
                if face_encodings:
                    self.known_faces.extend(face_encodings)
                    self.known_names.extend([name] * len(face_encodings))
                    
                    # Save to file
                    filename = f"{name}_{int(time.time())}.jpg"
                    save_path = self.known_faces_path / filename
                    cv2.imwrite(str(save_path), image)
                    
                    print(f"Added new known face: {name}")
                    return True
            
        except Exception as e:
            print(f"Error adding known face: {e}")
        
        return False
    
    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect faces in the frame using OpenCV"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        return faces
    
    def recognize_faces(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Recognize faces in the frame"""
        if not FACE_RECOGNITION_AVAILABLE or not self.known_faces:
            return []
        
        # Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Get face locations and encodings
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        recognized_faces = []
        
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # Compare with known faces
            matches = face_recognition.compare_faces(self.known_faces, face_encoding)
            face_distances = face_recognition.face_distance(self.known_faces, face_encoding)
            
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                confidence = 1 - face_distances[best_match_index]
                
                if matches[best_match_index] and confidence >= self.confidence_threshold:
                    name = self.known_names[best_match_index]
                    recognized_faces.append({
                        'name': name,
                        'confidence': confidence,
                        'location': (top, right, bottom, left)
                    })
                else:
                    # Unknown face
                    recognized_faces.append({
                        'name': 'Unknown',
                        'confidence': confidence,
                        'location': (top, right, bottom, left)
                    })
        
        return recognized_faces
    
    def analyze_emotion(self, frame: np.ndarray, face_location: Tuple[int, int, int, int]) -> Optional[str]:
        """Analyze emotion using DeepFace"""
        if not DEEPFACE_AVAILABLE:
            return None
        
        try:
            top, right, bottom, left = face_location
            face_img = frame[top:bottom, left:right]
            
            if face_img.size == 0:
                return None
            
            # Analyze emotion
            result = DeepFace.analyze(
                face_img,
                actions=['emotion'],
                enforce_detection=False
            )
            
            if isinstance(result, list):
                result = result[0]
            
            emotion = result.get('dominant_emotion', 'unknown')
            return emotion
            
        except Exception as e:
            print(f"Error analyzing emotion: {e}")
            return None
    
    def process_frame(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """Process a single frame for face recognition"""
        if frame is None:
            return None
        
        # Detect faces
        faces = self.detect_faces(frame)
        
        if len(faces) == 0:
            return None
        
        # Recognize faces
        recognized_faces = self.recognize_faces(frame)
        
        # Analyze emotions for each face
        results = []
        for face in recognized_faces:
            emotion = self.analyze_emotion(frame, face['location'])
            face['emotion'] = emotion
            results.append(face)
        
        # Check for suspicious activity
        suspicious_incidents = []
        
        for face in results:
            # Unknown person detected
            if face['name'] == 'Unknown' and face['confidence'] > 0.6:
                suspicious_incidents.append({
                    'type': 'unknown_person',
                    'confidence': face['confidence'],
                    'details': {
                        'location': face['location'],
                        'emotion': face.get('emotion', 'unknown')
                    }
                })
            
            # Suspicious emotion
            if face.get('emotion') in ['angry', 'fear', 'sad']:
                suspicious_incidents.append({
                    'type': 'suspicious_emotion',
                    'confidence': face['confidence'],
                    'details': {
                        'name': face['name'],
                        'emotion': face['emotion'],
                        'location': face['location']
                    }
                })
        
        if suspicious_incidents:
            # Return the most confident incident
            best_incident = max(suspicious_incidents, key=lambda x: x['confidence'])
            return {
                'detected': True,
                'type': best_incident['type'],
                'confidence': best_incident['confidence'],
                'details': best_incident['details'],
                'frame_data': {
                    'faces_detected': len(faces),
                    'faces_recognized': len(results),
                    'all_faces': results
                }
            }
        
        return None
    
    def start(self):
        """Start the face recognition module"""
        self.is_running = True
        print("Face recognition module started")
    
    def stop(self):
        """Stop the face recognition module"""
        self.is_running = False
        print("Face recognition module stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get module status"""
        return {
            'running': self.is_running,
            'known_faces_count': len(self.known_faces),
            'confidence_threshold': self.confidence_threshold,
            'deepface_available': DEEPFACE_AVAILABLE,
            'face_recognition_available': FACE_RECOGNITION_AVAILABLE
        }

# Example usage
if __name__ == "__main__":
    config = {
        'confidence_threshold': 0.8,
        'known_faces_path': 'data/known_faces'
    }
    
    module = FaceRecognitionModule(config)
    
    # Test with webcam
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        result = module.process_frame(frame)
        if result:
            print(f"Incident detected: {result['type']} ({result['confidence']:.2f})")
        
        cv2.imshow('Face Recognition Test', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows() 