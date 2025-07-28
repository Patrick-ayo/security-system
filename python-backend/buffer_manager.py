#!/usr/bin/env python3
"""
Buffer Manager Module
Manages audio/video rolling buffers and incident recording
"""

import cv2
import numpy as np
import time
import json
import threading
import queue
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import deque
import wave
import pyaudio

class BufferManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.video_buffer_size = config.get('video_buffer_size', 30)  # seconds
        self.audio_buffer_size = config.get('audio_buffer_size', 10)  # seconds
        self.max_incident_duration = config.get('max_incident_duration', 60)  # seconds
        
        # Video buffer (frames)
        self.video_buffer = deque(maxlen=self.video_buffer_size * 30)  # 30 FPS
        self.video_lock = threading.Lock()
        
        # Audio buffer (chunks)
        self.audio_buffer = deque(maxlen=self.audio_buffer_size * 160)  # 160 chunks per second
        self.audio_lock = threading.Lock()
        
        # Audio settings
        self.audio_chunk_size = 1024
        self.audio_sample_rate = 16000
        self.audio_channels = 1
        self.audio_format = pyaudio.paInt16
        
        # Incident recording
        self.incident_recordings = {}
        self.recording_lock = threading.Lock()
        
        # Threading
        self.is_running = False
        self.video_queue = queue.Queue(maxsize=100)
        self.audio_queue = queue.Queue(maxsize=100)
        
        # Create output directory
        self.output_dir = Path(__file__).parent / 'data' / 'recordings'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print("Buffer manager initialized")
    
    def add_video_frame(self, frame: np.ndarray, timestamp: float = None):
        """Add a video frame to the buffer"""
        if timestamp is None:
            timestamp = time.time()
        
        try:
            # Add to queue for processing
            self.video_queue.put_nowait({
                'frame': frame.copy(),
                'timestamp': timestamp
            })
        except queue.Full:
            # Remove oldest frame if queue is full
            try:
                self.video_queue.get_nowait()
                self.video_queue.put_nowait({
                    'frame': frame.copy(),
                    'timestamp': timestamp
                })
            except queue.Full:
                pass  # Skip frame if still full
    
    def add_audio_chunk(self, audio_data: np.ndarray, timestamp: float = None):
        """Add an audio chunk to the buffer"""
        if timestamp is None:
            timestamp = time.time()
        
        try:
            # Add to queue for processing
            self.audio_queue.put_nowait({
                'audio': audio_data.copy(),
                'timestamp': timestamp
            })
        except queue.Full:
            # Remove oldest chunk if queue is full
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.put_nowait({
                    'audio': audio_data.copy(),
                    'timestamp': timestamp
                })
            except queue.Full:
                pass  # Skip chunk if still full
    
    def process_video_buffer(self):
        """Process video frames from queue"""
        while self.is_running:
            try:
                # Get frame from queue
                frame_data = self.video_queue.get(timeout=1)
                
                with self.video_lock:
                    # Add to buffer
                    self.video_buffer.append(frame_data)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing video buffer: {e}")
    
    def process_audio_buffer(self):
        """Process audio chunks from queue"""
        while self.is_running:
            try:
                # Get audio chunk from queue
                audio_data = self.audio_queue.get(timeout=1)
                
                with self.audio_lock:
                    # Add to buffer
                    self.audio_buffer.append(audio_data)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing audio buffer: {e}")
    
    def get_video_buffer(self, duration: float = None) -> List[Dict[str, Any]]:
        """Get video frames from buffer for specified duration"""
        if duration is None:
            duration = self.video_buffer_size
        
        with self.video_lock:
            current_time = time.time()
            cutoff_time = current_time - duration
            
            # Get frames within the time window
            frames = [
                frame_data for frame_data in self.video_buffer
                if frame_data['timestamp'] >= cutoff_time
            ]
            
            return frames
    
    def get_audio_buffer(self, duration: float = None) -> List[Dict[str, Any]]:
        """Get audio chunks from buffer for specified duration"""
        if duration is None:
            duration = self.audio_buffer_size
        
        with self.audio_lock:
            current_time = time.time()
            cutoff_time = current_time - duration
            
            # Get chunks within the time window
            chunks = [
                chunk_data for chunk_data in self.audio_buffer
                if chunk_data['timestamp'] >= cutoff_time
            ]
            
            return chunks
    
    def start_incident_recording(self, incident_id: str, incident_type: str) -> bool:
        """Start recording an incident"""
        try:
            with self.recording_lock:
                if incident_id in self.incident_recordings:
                    print(f"Recording already in progress for incident {incident_id}")
                    return False
                
                # Create incident directory
                incident_dir = self.output_dir / incident_id
                incident_dir.mkdir(exist_ok=True)
                
                # Initialize recording
                self.incident_recordings[incident_id] = {
                    'type': incident_type,
                    'start_time': time.time(),
                    'video_frames': [],
                    'audio_chunks': [],
                    'directory': incident_dir,
                    'video_writer': None,
                    'audio_writer': None
                }
                
                # Initialize video writer
                video_path = incident_dir / f"{incident_id}_video.mp4"
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                height, width = 480, 640  # Default size
                self.incident_recordings[incident_id]['video_writer'] = cv2.VideoWriter(
                    str(video_path), fourcc, 30.0, (width, height)
                )
                
                # Initialize audio writer
                audio_path = incident_dir / f"{incident_id}_audio.wav"
                self.incident_recordings[incident_id]['audio_writer'] = wave.open(
                    str(audio_path), 'wb'
                )
                self.incident_recordings[incident_id]['audio_writer'].setnchannels(self.audio_channels)
                self.incident_recordings[incident_id]['audio_writer'].setsampwidth(2)  # 16-bit
                self.incident_recordings[incident_id]['audio_writer'].setframerate(self.audio_sample_rate)
                
                print(f"Started recording incident {incident_id}")
                return True
                
        except Exception as e:
            print(f"Error starting incident recording: {e}")
            return False
    
    def add_incident_frame(self, incident_id: str, frame: np.ndarray):
        """Add a frame to incident recording"""
        try:
            with self.recording_lock:
                if incident_id not in self.incident_recordings:
                    return
                
                recording = self.incident_recordings[incident_id]
                
                # Add to video writer
                if recording['video_writer']:
                    recording['video_writer'].write(frame)
                
                # Store frame data
                recording['video_frames'].append({
                    'frame': frame.copy(),
                    'timestamp': time.time()
                })
                
        except Exception as e:
            print(f"Error adding incident frame: {e}")
    
    def add_incident_audio(self, incident_id: str, audio_data: np.ndarray):
        """Add audio chunk to incident recording"""
        try:
            with self.recording_lock:
                if incident_id not in self.incident_recordings:
                    return
                
                recording = self.incident_recordings[incident_id]
                
                # Add to audio writer
                if recording['audio_writer']:
                    recording['audio_writer'].writeframes(audio_data.tobytes())
                
                # Store audio data
                recording['audio_chunks'].append({
                    'audio': audio_data.copy(),
                    'timestamp': time.time()
                })
                
        except Exception as e:
            print(f"Error adding incident audio: {e}")
    
    def stop_incident_recording(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Stop recording an incident and return metadata"""
        try:
            with self.recording_lock:
                if incident_id not in self.incident_recordings:
                    return None
                
                recording = self.incident_recordings[incident_id]
                end_time = time.time()
                duration = end_time - recording['start_time']
                
                # Close video writer
                if recording['video_writer']:
                    recording['video_writer'].release()
                
                # Close audio writer
                if recording['audio_writer']:
                    recording['audio_writer'].close()
                
                # Create metadata
                metadata = {
                    'incident_id': incident_id,
                    'type': recording['type'],
                    'start_time': recording['start_time'],
                    'end_time': end_time,
                    'duration': duration,
                    'video_frames_count': len(recording['video_frames']),
                    'audio_chunks_count': len(recording['audio_chunks']),
                    'directory': str(recording['directory'])
                }
                
                # Save metadata
                metadata_path = recording['directory'] / f"{incident_id}_metadata.json"
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                # Remove from active recordings
                del self.incident_recordings[incident_id]
                
                print(f"Stopped recording incident {incident_id} (duration: {duration:.2f}s)")
                return metadata
                
        except Exception as e:
            print(f"Error stopping incident recording: {e}")
            return None
    
    def get_incident_recording_status(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an incident recording"""
        with self.recording_lock:
            if incident_id not in self.incident_recordings:
                return None
            
            recording = self.incident_recordings[incident_id]
            current_time = time.time()
            
            return {
                'incident_id': incident_id,
                'type': recording['type'],
                'start_time': recording['start_time'],
                'duration': current_time - recording['start_time'],
                'video_frames_count': len(recording['video_frames']),
                'audio_chunks_count': len(recording['audio_chunks']),
                'is_active': True
            }
    
    def cleanup_old_recordings(self, max_age_days: int = 30):
        """Clean up old incident recordings"""
        try:
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 3600
            
            for recording_dir in self.output_dir.iterdir():
                if recording_dir.is_dir():
                    # Check if directory is old
                    dir_age = current_time - recording_dir.stat().st_mtime
                    if dir_age > max_age_seconds:
                        # Remove old recording
                        import shutil
                        shutil.rmtree(recording_dir)
                        print(f"Cleaned up old recording: {recording_dir.name}")
                        
        except Exception as e:
            print(f"Error cleaning up old recordings: {e}")
    
    def start(self):
        """Start buffer manager"""
        self.is_running = True
        
        # Start processing threads
        self.video_thread = threading.Thread(target=self.process_video_buffer, daemon=True)
        self.audio_thread = threading.Thread(target=self.process_audio_buffer, daemon=True)
        
        self.video_thread.start()
        self.audio_thread.start()
        
        print("Buffer manager started")
    
    def stop(self):
        """Stop buffer manager"""
        self.is_running = False
        
        # Stop all incident recordings
        incident_ids = list(self.incident_recordings.keys())
        for incident_id in incident_ids:
            self.stop_incident_recording(incident_id)
        
        # Wait for threads to finish
        if hasattr(self, 'video_thread'):
            self.video_thread.join(timeout=5)
        if hasattr(self, 'audio_thread'):
            self.audio_thread.join(timeout=5)
        
        print("Buffer manager stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get buffer manager status"""
        with self.video_lock:
            video_buffer_size = len(self.video_buffer)
        
        with self.audio_lock:
            audio_buffer_size = len(self.audio_buffer)
        
        with self.recording_lock:
            active_recordings = len(self.incident_recordings)
        
        return {
            'running': self.is_running,
            'video_buffer_size': video_buffer_size,
            'audio_buffer_size': audio_buffer_size,
            'active_recordings': active_recordings,
            'video_buffer_duration': video_buffer_size / 30.0,  # seconds
            'audio_buffer_duration': audio_buffer_size / 160.0,  # seconds
            'output_directory': str(self.output_dir)
        }

# Example usage
if __name__ == "__main__":
    config = {
        'video_buffer_size': 30,
        'audio_buffer_size': 10,
        'max_incident_duration': 60
    }
    
    buffer_manager = BufferManager(config)
    
    try:
        buffer_manager.start()
        print("Buffer manager started. Press Ctrl+C to stop.")
        
        # Simulate adding frames and audio
        for i in range(100):
            # Simulate video frame
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            buffer_manager.add_video_frame(frame)
            
            # Simulate audio chunk
            audio_chunk = np.random.randint(-32768, 32767, 1024, dtype=np.int16)
            buffer_manager.add_audio_chunk(audio_chunk)
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nStopping buffer manager...")
        buffer_manager.stop() 