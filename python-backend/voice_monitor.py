#!/usr/bin/env python3
"""
Voice Monitor Module
Uses Vosk or DeepSpeech for voice analysis and keyword detection
"""

import pyaudio
import wave
import numpy as np
import time
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
import queue

try:
    import vosk
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("Vosk not available")

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    print("Speech recognition not available")

class VoiceMonitorModule:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sensitivity = config.get('sensitivity', 0.7)
        self.suspicious_keywords = config.get('suspicious_keywords', [
            'help', 'emergency', 'danger', 'fire', 'police', 'attack',
            'threat', 'dangerous', 'weapon', 'gun', 'knife', 'fight'
        ])
        
        # Audio settings
        self.chunk_size = 1024
        self.sample_rate = 16000
        self.channels = 1
        self.format = pyaudio.paInt16
        
        # Initialize audio
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # Initialize speech recognition
        self.initialize_speech_recognition()
        
        # Threading
        self.is_running = False
        self.audio_queue = queue.Queue()
        self.result_queue = queue.Queue()
        
        # Audio buffer
        self.audio_buffer = []
        self.buffer_duration = 3.0  # seconds
        self.max_buffer_size = int(self.sample_rate * self.buffer_duration)
        
        print("Voice monitor module initialized")
    
    def initialize_speech_recognition(self):
        """Initialize speech recognition components"""
        if VOSK_AVAILABLE:
            # Try to load Vosk model
            model_path = Path(__file__).parent / 'models' / 'vosk-model-small-en-us'
            if model_path.exists():
                self.vosk_model = vosk.Model(str(model_path))
                self.vosk_recognizer = vosk.KaldiRecognizer(self.vosk_model, self.sample_rate)
                print("✓ Vosk model loaded")
            else:
                print("Vosk model not found, using speech_recognition fallback")
                VOSK_AVAILABLE = False
        
        if SPEECH_RECOGNITION_AVAILABLE and not VOSK_AVAILABLE:
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 4000
            self.recognizer.dynamic_energy_threshold = True
            print("✓ Speech recognition initialized")
    
    def start_audio_stream(self):
        """Start audio stream for continuous monitoring"""
        try:
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self.audio_callback
            )
            self.stream.start_stream()
            print("✓ Audio stream started")
            return True
        except Exception as e:
            print(f"Error starting audio stream: {e}")
            return False
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream"""
        if self.is_running:
            # Convert audio data to numpy array
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            
            # Add to buffer
            self.audio_buffer.extend(audio_data)
            
            # Keep buffer size manageable
            if len(self.audio_buffer) > self.max_buffer_size:
                self.audio_buffer = self.audio_buffer[-self.max_buffer_size:]
            
            # Check for speech activity
            if self.detect_speech_activity(audio_data):
                # Process audio for speech recognition
                self.audio_queue.put(audio_data.copy())
        
        return (in_data, pyaudio.paContinue)
    
    def detect_speech_activity(self, audio_data: np.ndarray) -> bool:
        """Detect if there's speech activity in the audio"""
        # Calculate RMS (Root Mean Square) for volume detection
        rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
        
        # Threshold for speech detection (adjust based on environment)
        threshold = 1000  # Adjust this value based on your microphone
        
        return rms > threshold
    
    def process_audio_chunk(self, audio_data: np.ndarray) -> Optional[str]:
        """Process audio chunk for speech recognition"""
        try:
            if VOSK_AVAILABLE:
                return self.process_with_vosk(audio_data)
            elif SPEECH_RECOGNITION_AVAILABLE:
                return self.process_with_speech_recognition(audio_data)
            else:
                return None
        except Exception as e:
            print(f"Error processing audio: {e}")
            return None
    
    def process_with_vosk(self, audio_data: np.ndarray) -> Optional[str]:
        """Process audio using Vosk"""
        try:
            # Convert to bytes
            audio_bytes = audio_data.tobytes()
            
            # Process with Vosk
            if self.vosk_recognizer.AcceptWaveform(audio_bytes):
                result = json.loads(self.vosk_recognizer.Result())
                text = result.get('text', '').strip()
                return text if text else None
            else:
                # Partial result
                partial = json.loads(self.vosk_recognizer.PartialResult())
                text = partial.get('partial', '').strip()
                return text if text else None
                
        except Exception as e:
            print(f"Error in Vosk processing: {e}")
            return None
    
    def process_with_speech_recognition(self, audio_data: np.ndarray) -> Optional[str]:
        """Process audio using speech_recognition"""
        try:
            # Convert to AudioData format
            audio_data_bytes = audio_data.tobytes()
            audio = sr.AudioData(audio_data_bytes, self.sample_rate, 2)
            
            # Recognize speech
            text = self.recognizer.recognize_google(audio)
            return text.strip() if text else None
            
        except sr.UnknownValueError:
            # Speech not understood
            return None
        except sr.RequestError as e:
            print(f"Speech recognition request error: {e}")
            return None
        except Exception as e:
            print(f"Error in speech recognition: {e}")
            return None
    
    def analyze_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Analyze text for suspicious keywords and patterns"""
        if not text:
            return None
        
        text_lower = text.lower()
        detected_keywords = []
        
        # Check for suspicious keywords
        for keyword in self.suspicious_keywords:
            if keyword.lower() in text_lower:
                detected_keywords.append(keyword)
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'\b(help|emergency|danger)\b',
            r'\b(fire|police|attack)\b',
            r'\b(threat|dangerous|weapon)\b',
            r'\b(gun|knife|fight)\b'
        ]
        
        import re
        for pattern in suspicious_patterns:
            if re.search(pattern, text_lower):
                detected_keywords.extend(re.findall(pattern, text_lower))
        
        if detected_keywords:
            # Calculate confidence based on keyword frequency and sensitivity
            confidence = min(len(detected_keywords) * 0.3, 1.0)
            confidence = max(confidence, self.sensitivity)
            
            return {
                'detected': True,
                'type': 'suspicious_speech',
                'confidence': confidence,
                'details': {
                    'text': text,
                    'keywords': list(set(detected_keywords)),
                    'timestamp': time.time()
                }
            }
        
        return None
    
    def process_frame(self) -> Optional[Dict[str, Any]]:
        """Process current audio frame (called by main app)"""
        if not self.is_running:
            return None
        
        try:
            # Get audio data from queue
            audio_data = self.audio_queue.get_nowait()
            
            # Process for speech recognition
            text = self.process_audio_chunk(audio_data)
            
            if text:
                # Analyze text for suspicious content
                result = self.analyze_text(text)
                if result:
                    return result
            
        except queue.Empty:
            # No audio data available
            pass
        except Exception as e:
            print(f"Error processing audio frame: {e}")
        
        return None
    
    def start(self):
        """Start voice monitoring"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start audio stream
        if self.start_audio_stream():
            print("Voice monitoring started")
        else:
            self.is_running = False
            print("Failed to start voice monitoring")
    
    def stop(self):
        """Stop voice monitoring"""
        self.is_running = False
        
        # Stop audio stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        print("Voice monitoring stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get module status"""
        return {
            'running': self.is_running,
            'sensitivity': self.sensitivity,
            'suspicious_keywords': self.suspicious_keywords,
            'vosk_available': VOSK_AVAILABLE,
            'speech_recognition_available': SPEECH_RECOGNITION_AVAILABLE,
            'audio_buffer_size': len(self.audio_buffer)
        }
    
    def update_keywords(self, keywords: List[str]):
        """Update suspicious keywords"""
        self.suspicious_keywords = keywords
        print(f"Updated suspicious keywords: {keywords}")
    
    def update_sensitivity(self, sensitivity: float):
        """Update sensitivity threshold"""
        self.sensitivity = max(0.0, min(1.0, sensitivity))
        print(f"Updated sensitivity: {self.sensitivity}")

# Example usage
if __name__ == "__main__":
    config = {
        'sensitivity': 0.7,
        'suspicious_keywords': ['help', 'emergency', 'danger', 'fire']
    }
    
    module = VoiceMonitorModule(config)
    
    try:
        module.start()
        print("Voice monitoring started. Press Ctrl+C to stop.")
        
        while True:
            result = module.process_frame()
            if result:
                print(f"Incident detected: {result['type']} ({result['confidence']:.2f})")
                print(f"Text: {result['details']['text']}")
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nStopping voice monitoring...")
        module.stop() 