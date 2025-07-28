#!/usr/bin/env python3
"""
Activity Detection Module
Detects suspicious activities using computer vision and ML techniques
"""

import cv2
import numpy as np
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import threading
from collections import deque

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("MediaPipe not available")

class ActivityDetectionModule:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.suspicious_activities = config.get('suspicious_activities', [
            'fighting', 'theft', 'vandalism', 'loitering', 'suspicious_movement'
        ])
        
        # Initialize pose detection
        self.pose_detector = None
        self.initialize_pose_detection()
        
        # Activity tracking
        self.pose_history = deque(maxlen=30)  # 30 frames
        self.movement_history = deque(maxlen=60)  # 60 frames
        self.activity_scores = {}
        
        # Threading
        self.is_running = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        print("Activity detection module initialized")
    
    def initialize_pose_detection(self):
        """Initialize pose detection using MediaPipe"""
        try:
            if MEDIAPIPE_AVAILABLE:
                self.mp_pose = mp.solutions.pose
                self.pose_detector = self.mp_pose.Pose(
                    static_image_mode=False,
                    model_complexity=1,
                    smooth_landmarks=True,
                    enable_segmentation=False,
                    smooth_segmentation=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                print("✓ MediaPipe pose detection initialized")
            else:
                print("MediaPipe not available, using basic motion detection")
                
        except Exception as e:
            print(f"Error initializing pose detection: {e}")
    
    def detect_pose(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """Detect human pose in the frame"""
        if not self.pose_detector:
            return None
        
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect pose
            results = self.pose_detector.process(rgb_frame)
            
            if results.pose_landmarks:
                # Extract key points
                landmarks = []
                for landmark in results.pose_landmarks.landmark:
                    landmarks.append({
                        'x': landmark.x,
                        'y': landmark.y,
                        'z': landmark.z,
                        'visibility': landmark.visibility
                    })
                
                return {
                    'landmarks': landmarks,
                    'frame_width': frame.shape[1],
                    'frame_height': frame.shape[0]
                }
            
            return None
            
        except Exception as e:
            print(f"Error in pose detection: {e}")
            return None
    
    def detect_motion(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """Detect motion using frame differencing"""
        if not hasattr(self, 'prev_frame'):
            self.prev_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return None
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Calculate frame difference
            frame_diff = cv2.absdiff(self.prev_frame, gray)
            
            # Apply threshold
            _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by area
            motion_regions = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # Minimum area threshold
                    x, y, w, h = cv2.boundingRect(contour)
                    motion_regions.append({
                        'bbox': [x, y, x + w, y + h],
                        'area': area
                    })
            
            # Update previous frame
            self.prev_frame = gray
            
            if motion_regions:
                return {
                    'motion_regions': motion_regions,
                    'total_motion_area': sum(r['area'] for r in motion_regions)
                }
            
            return None
            
        except Exception as e:
            print(f"Error in motion detection: {e}")
            return None
    
    def analyze_pose_activity(self, pose_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze pose data for suspicious activities"""
        if not pose_data or 'landmarks' not in pose_data:
            return None
        
        landmarks = pose_data['landmarks']
        
        # Get key body parts
        nose = landmarks[0] if len(landmarks) > 0 else None
        left_shoulder = landmarks[11] if len(landmarks) > 11 else None
        right_shoulder = landmarks[12] if len(landmarks) > 12 else None
        left_elbow = landmarks[13] if len(landmarks) > 13 else None
        right_elbow = landmarks[14] if len(landmarks) > 14 else None
        left_wrist = landmarks[15] if len(landmarks) > 15 else None
        right_wrist = landmarks[16] if len(landmarks) > 16 else None
        
        if not all([nose, left_shoulder, right_shoulder]):
            return None
        
        # Calculate pose features
        features = {}
        
        # Shoulder width (normalized)
        shoulder_width = abs(left_shoulder['x'] - right_shoulder['x'])
        features['shoulder_width'] = shoulder_width
        
        # Arm positions
        if left_elbow and right_elbow:
            left_arm_raised = left_elbow['y'] < left_shoulder['y']
            right_arm_raised = right_elbow['y'] < right_shoulder['y']
            features['arms_raised'] = left_arm_raised or right_arm_raised
        
        # Hand positions
        if left_wrist and right_wrist:
            left_hand_high = left_wrist['y'] < left_shoulder['y']
            right_hand_high = right_wrist['y'] < right_shoulder['y']
            features['hands_high'] = left_hand_high or right_hand_high
        
        # Add to history
        self.pose_history.append({
            'timestamp': time.time(),
            'features': features
        })
        
        # Analyze for suspicious activities
        return self.detect_suspicious_pose(features)
    
    def detect_suspicious_pose(self, features: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect suspicious pose patterns"""
        suspicious_activities = []
        
        # Fighting pose detection
        if features.get('arms_raised', False) and features.get('hands_high', False):
            suspicious_activities.append({
                'type': 'fighting_pose',
                'confidence': 0.7,
                'details': {
                    'arms_raised': True,
                    'hands_high': True
                }
            })
        
        # Aggressive stance detection
        if features.get('shoulder_width', 0) > 0.3:  # Wide stance
            suspicious_activities.append({
                'type': 'aggressive_stance',
                'confidence': 0.6,
                'details': {
                    'shoulder_width': features['shoulder_width']
                }
            })
        
        # Return the most confident activity
        if suspicious_activities:
            best_activity = max(suspicious_activities, key=lambda x: x['confidence'])
            return {
                'detected': True,
                'type': best_activity['type'],
                'confidence': best_activity['confidence'],
                'details': best_activity['details']
            }
        
        return None
    
    def analyze_motion_activity(self, motion_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze motion data for suspicious activities"""
        if not motion_data:
            return None
        
        motion_regions = motion_data.get('motion_regions', [])
        total_motion_area = motion_data.get('total_motion_area', 0)
        
        # Add to history
        self.movement_history.append({
            'timestamp': time.time(),
            'motion_regions': len(motion_regions),
            'total_motion_area': total_motion_area
        })
        
        # Analyze motion patterns
        return self.detect_suspicious_motion(motion_data)
    
    def detect_suspicious_motion(self, motion_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect suspicious motion patterns"""
        motion_regions = motion_data.get('motion_regions', [])
        total_motion_area = motion_data.get('total_motion_area', 0)
        
        # Calculate motion intensity
        frame_area = 640 * 480  # Assuming standard resolution
        motion_intensity = total_motion_area / frame_area if frame_area > 0 else 0
        
        suspicious_activities = []
        
        # High motion intensity (potential fighting or rapid movement)
        if motion_intensity > 0.1:  # 10% of frame
            suspicious_activities.append({
                'type': 'high_motion_activity',
                'confidence': min(motion_intensity * 2, 0.9),
                'details': {
                    'motion_intensity': motion_intensity,
                    'motion_regions': len(motion_regions)
                }
            })
        
        # Multiple motion regions (potential multiple people or complex activity)
        if len(motion_regions) > 3:
            suspicious_activities.append({
                'type': 'complex_motion',
                'confidence': min(len(motion_regions) * 0.2, 0.8),
                'details': {
                    'motion_regions_count': len(motion_regions),
                    'motion_intensity': motion_intensity
                }
            })
        
        # Return the most confident activity
        if suspicious_activities:
            best_activity = max(suspicious_activities, key=lambda x: x['confidence'])
            return {
                'detected': True,
                'type': best_activity['type'],
                'confidence': best_activity['confidence'],
                'details': best_activity['details']
            }
        
        return None
    
    def analyze_activity_patterns(self) -> Optional[Dict[str, Any]]:
        """Analyze activity patterns over time"""
        if len(self.pose_history) < 10 or len(self.movement_history) < 10:
            return None
        
        # Analyze recent pose history
        recent_poses = list(self.pose_history)[-10:]
        aggressive_poses = sum(
            1 for pose in recent_poses 
            if pose['features'].get('arms_raised', False)
        )
        
        # Analyze recent motion history
        recent_motions = list(self.movement_history)[-10:]
        high_motion_frames = sum(
            1 for motion in recent_motions 
            if motion['total_motion_area'] > 10000  # Threshold
        )
        
        # Pattern-based detection
        if aggressive_poses > 5 and high_motion_frames > 5:
            return {
                'detected': True,
                'type': 'sustained_suspicious_activity',
                'confidence': 0.8,
                'details': {
                    'aggressive_poses': aggressive_poses,
                    'high_motion_frames': high_motion_frames,
                    'duration': 'sustained'
                }
            }
        
        return None
    
    def process_frame(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """Process a single frame for activity detection"""
        if frame is None:
            return None
        
        results = []
        
        # Pose-based activity detection
        pose_data = self.detect_pose(frame)
        if pose_data:
            pose_result = self.analyze_pose_activity(pose_data)
            if pose_result:
                results.append(pose_result)
        
        # Motion-based activity detection
        motion_data = self.detect_motion(frame)
        if motion_data:
            motion_result = self.analyze_motion_activity(motion_data)
            if motion_result:
                results.append(motion_result)
        
        # Pattern-based activity detection
        pattern_result = self.analyze_activity_patterns()
        if pattern_result:
            results.append(pattern_result)
        
        # Return the most confident result
        if results:
            best_result = max(results, key=lambda x: x['confidence'])
            return best_result
        
        return None
    
    def start(self):
        """Start activity detection"""
        self.is_running = True
        print("Activity detection started")
    
    def stop(self):
        """Stop activity detection"""
        self.is_running = False
        print("Activity detection stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get module status"""
        return {
            'running': self.is_running,
            'suspicious_activities': self.suspicious_activities,
            'mediapipe_available': MEDIAPIPE_AVAILABLE,
            'pose_detector_loaded': self.pose_detector is not None,
            'pose_history_size': len(self.pose_history),
            'movement_history_size': len(self.movement_history)
        }
    
    def update_suspicious_activities(self, activities: List[str]):
        """Update list of suspicious activities"""
        self.suspicious_activities = activities
        print(f"Updated suspicious activities: {activities}")
    
    def clear_history(self):
        """Clear activity history"""
        self.pose_history.clear()
        self.movement_history.clear()
        print("Activity history cleared")

# Example usage
if __name__ == "__main__":
    config = {
        'suspicious_activities': ['fighting', 'theft', 'vandalism', 'loitering']
    }
    
    module = ActivityDetectionModule(config)
    
    # Test with webcam
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        result = module.process_frame(frame)
        if result:
            print(f"Activity detected: {result['type']} ({result['confidence']:.2f})")
        
        cv2.imshow('Activity Detection Test', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows() 