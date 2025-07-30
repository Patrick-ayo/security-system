#!/usr/bin/env python3
"""
Enhanced Audio Monitor Module
Detects different types of audio and transcribes speech with multi-language support
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
import librosa
import soundfile as sf
from scipy import signal
from scipy.stats import entropy
import matplotlib.pyplot as plt

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

class EnhancedAudioMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.channels = 1
        self.format = pyaudio.paInt16
        
        # Audio processing
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_monitoring = False
        
        # Speech recognition
        self.recognizer = None
        self.vosk_model = None
        self.vosk_recognizer = None
        
        # Audio analysis
        self.audio_buffer = []
        self.speech_buffer = []
        self.last_speech_time = 0
        self.speech_timeout = 2.0  # seconds
        
        # Statistics
        self.audio_statistics = {
            'speech': 0,
            'music': 0,
            'noise': 0,
            'silence': 0,
            'total_frames': 0
        }
        
        # Multi-language support
        self.supported_languages = {
            'en': 'English',
            'es': 'Spanish', 
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'auto': 'Auto-detect'
        }
        
        # Initialize speech recognition
        self.initialize_speech_recognition()
        
        print("Enhanced Audio Monitor initialized")
    
    def initialize_speech_recognition(self):
        """Initialize speech recognition components with multi-language support"""
        global VOSK_AVAILABLE, SPEECH_RECOGNITION_AVAILABLE
        
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
            self.recognizer.pause_threshold = 0.8
            print("✓ Speech recognition initialized")
    
    def detect_audio_type(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """Detect the type of audio (speech, music, noise, silence)"""
        if len(audio_data) == 0:
            return {'type': 'silence', 'confidence': 1.0}
        
        # Convert to float
        audio_float = audio_data.astype(np.float32) / 32768.0
        
        # Calculate basic features
        rms = np.sqrt(np.mean(audio_float**2))
        zero_crossing_rate = np.sum(np.diff(np.sign(audio_float))) / len(audio_float)
        
        # Spectral features
        if len(audio_float) >= 1024:
            # Pad if necessary
            if len(audio_float) < 2048:
                audio_float = np.pad(audio_float, (0, 2048 - len(audio_float)))
            
            # FFT
            fft = np.fft.fft(audio_float[:2048])
            magnitude = np.abs(fft[:1024])
            
            # Spectral centroid
            freqs = np.fft.fftfreq(2048, 1/self.sample_rate)[:1024]
            spectral_centroid = np.sum(freqs * magnitude) / np.sum(magnitude)
            
            # Spectral rolloff
            cumulative_magnitude = np.cumsum(magnitude)
            rolloff_threshold = 0.85 * cumulative_magnitude[-1]
            spectral_rolloff = freqs[np.where(cumulative_magnitude >= rolloff_threshold)[0][0]]
            
            # Spectral bandwidth
            spectral_bandwidth = np.sqrt(np.sum(((freqs - spectral_centroid)**2) * magnitude) / np.sum(magnitude))
            
            # MFCC features for better classification
            try:
                mfcc = librosa.feature.mfcc(y=audio_float, sr=self.sample_rate, n_mfcc=13)
                mfcc_mean = np.mean(mfcc, axis=1)
                mfcc_std = np.std(mfcc, axis=1)
            except:
                mfcc_mean = np.zeros(13)
                mfcc_std = np.zeros(13)
        else:
            spectral_centroid = 0
            spectral_rolloff = 0
            spectral_bandwidth = 0
            mfcc_mean = np.zeros(13)
            mfcc_std = np.zeros(13)
        
        # Classification logic
        features = {
            'rms': rms,
            'zero_crossing_rate': zero_crossing_rate,
            'spectral_centroid': spectral_centroid,
            'spectral_rolloff': spectral_rolloff,
            'spectral_bandwidth': spectral_bandwidth,
            'mfcc_mean': mfcc_mean,
            'mfcc_std': mfcc_std
        }
        
        # Determine audio type based on features
        audio_type, confidence = self.classify_audio_type(features)
        
        return {
            'type': audio_type,
            'confidence': confidence,
            'features': features
        }
    
    def classify_audio_type(self, features: Dict[str, Any]) -> tuple:
        """Classify audio type based on extracted features"""
        rms = features['rms']
        zcr = features['zero_crossing_rate']
        spectral_centroid = features['spectral_centroid']
        spectral_rolloff = features['spectral_rolloff']
        
        # Silence detection
        if rms < 0.01:
            return 'silence', 0.95
        
        # Speech detection
        # Speech typically has moderate RMS, high ZCR, and specific spectral characteristics
        if (0.01 < rms < 0.3 and 
            zcr > 0.1 and 
            500 < spectral_centroid < 3000 and
            spectral_rolloff < 4000):
            return 'speech', 0.85
        
        # Music detection
        # Music typically has higher spectral rolloff and more complex spectral characteristics
        if (rms > 0.05 and 
            spectral_rolloff > 4000 and
            spectral_centroid > 1000):
            return 'music', 0.80
        
        # Noise detection
        # High ZCR with moderate RMS often indicates noise
        if zcr > 0.2 and rms > 0.02:
            return 'noise', 0.75
        
        # Default to speech if uncertain
        return 'speech', 0.6
    
    def transcribe_speech(self, audio_data: np.ndarray, language: str = 'auto') -> Dict[str, Any]:
        """Transcribe speech with multi-language support"""
        if len(audio_data) == 0:
            return {'text': '', 'confidence': 0.0, 'language': 'unknown'}
        
        # Convert audio data to the right format
        audio_bytes = audio_data.tobytes()
        
        # Try Vosk first (offline)
        if VOSK_AVAILABLE and self.vosk_recognizer:
            try:
                self.vosk_recognizer.AcceptWaveform(audio_bytes)
                result = self.vosk_recognizer.FinalResult()
                if result:
                    result_dict = json.loads(result)
                    if result_dict.get('text', '').strip():
                        return {
                            'text': result_dict['text'],
                            'confidence': result_dict.get('confidence', 0.0),
                            'language': 'en',  # Vosk model is English
                            'method': 'vosk'
                        }
            except Exception as e:
                print(f"Vosk transcription error: {e}")
        
        # Try Google Speech Recognition (online, multi-language)
        if SPEECH_RECOGNITION_AVAILABLE and self.recognizer:
            try:
                # Create AudioData object
                audio_data_sr = sr.AudioData(audio_bytes, self.sample_rate, 2)
                
                # Try with specified language
                if language != 'auto':
                    text = self.recognizer.recognize_google(
                        audio_data_sr, 
                        language=language,
                        show_all=True
                    )
                else:
                    # Try auto-detection with multiple languages
                    text = self.recognizer.recognize_google(
                        audio_data_sr,
                        show_all=True
                    )
                
                if text and isinstance(text, dict) and 'alternative' in text:
                    best_result = text['alternative'][0]
                    return {
                        'text': best_result['transcript'],
                        'confidence': best_result.get('confidence', 0.0),
                        'language': text.get('language', 'unknown'),
                        'method': 'google'
                    }
                elif text and isinstance(text, str):
                    return {
                        'text': text,
                        'confidence': 0.8,
                        'language': 'auto-detected',
                        'method': 'google'
                    }
                    
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                print(f"Google Speech Recognition error: {e}")
            except Exception as e:
                print(f"Speech recognition error: {e}")
        
        return {'text': '', 'confidence': 0.0, 'language': 'unknown'}
    
    def detect_suspicious_keywords(self, text: str) -> Dict[str, Any]:
        """Detect suspicious keywords in transcribed text"""
        if not text:
            return {'detected': False, 'keywords': [], 'confidence': 0.0}
        
        text_lower = text.lower()
        suspicious_keywords = self.config.get('suspicious_keywords', [])
        
        detected_keywords = []
        for keyword in suspicious_keywords:
            if keyword.lower() in text_lower:
                detected_keywords.append(keyword)
        
        confidence = len(detected_keywords) / max(len(suspicious_keywords), 1)
        
        return {
            'detected': len(detected_keywords) > 0,
            'keywords': detected_keywords,
            'confidence': confidence,
            'text': text
        }
    
    def process_frame(self) -> Optional[Dict[str, Any]]:
        """Process a single audio frame"""
        if not self.is_monitoring or not self.stream:
            return None
        
        try:
            # Read audio data
            audio_data = self.stream.read(self.chunk_size, exception_on_overflow=False)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Detect audio type
            audio_type_result = self.detect_audio_type(audio_array)
            audio_type = audio_type_result['type']
            confidence = audio_type_result['confidence']
            
            # Update statistics
            self.audio_statistics[audio_type] += 1
            self.audio_statistics['total_frames'] += 1
            
            result = {
                'audio_type': audio_type,
                'confidence': confidence,
                'features': audio_type_result.get('features', {}),
                'timestamp': time.time()
            }
            
            # Handle speech detection and transcription
            if audio_type == 'speech' and confidence > 0.7:
                # Accumulate speech audio
                self.speech_buffer.extend(audio_array)
                self.last_speech_time = time.time()
                
                # Process speech buffer when it's long enough or timeout reached
                if (len(self.speech_buffer) >= self.sample_rate * 2 or  # 2 seconds
                    time.time() - self.last_speech_time > self.speech_timeout):
                    
                    if len(self.speech_buffer) > self.sample_rate * 0.5:  # At least 0.5 seconds
                        # Convert to numpy array
                        speech_array = np.array(self.speech_buffer, dtype=np.int16)
                        
                        # Try multiple languages for transcription
                        transcription_result = self.transcribe_speech(speech_array, 'auto')
                        
                        if transcription_result['text']:
                            # Detect suspicious keywords
                            keyword_result = self.detect_suspicious_keywords(transcription_result['text'])
                            
                            result.update({
                                'text': transcription_result['text'],
                                'language': transcription_result['language'],
                                'transcription_confidence': transcription_result['confidence'],
                                'detected': keyword_result['detected'],
                                'details': keyword_result
                            })
                            
                            # Display the transcribed text clearly
                            print("\n" + "="*50)
                            print("🎯 SPEECH TRANSCRIBED!")
                            print("="*50)
                            print(f"📝 Text: \"{transcription_result['text']}\"")
                            print(f"🌍 Language: {transcription_result['language']}")
                            print(f"📊 Confidence: {transcription_result['confidence']:.2f}")
                            if keyword_result['detected']:
                                print(f"⚠️  SUSPICIOUS KEYWORDS: {keyword_result['keywords']}")
                            print("="*50)
                        
                        # Clear speech buffer
                        self.speech_buffer = []
            
            return result
            
        except Exception as e:
            print(f"Error processing audio frame: {e}")
            return None
    
    def start(self):
        """Start audio monitoring"""
        if self.is_monitoring:
            return
        
        try:
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            self.is_monitoring = True
            print("✓ Audio stream started")
            
        except Exception as e:
            print(f"Error starting audio stream: {e}")
    
    def stop(self):
        """Stop audio monitoring"""
        self.is_monitoring = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        if self.audio:
            self.audio.terminate()
        
        print("Enhanced audio monitoring stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        return {
            'is_monitoring': self.is_monitoring,
            'sample_rate': self.sample_rate,
            'chunk_size': self.chunk_size,
            'speech_buffer_size': len(self.speech_buffer),
            'last_speech_time': self.last_speech_time
        }
    
    def get_audio_statistics(self) -> Dict[str, Any]:
        """Get audio statistics"""
        total = self.audio_statistics['total_frames']
        if total == 0:
            return self.audio_statistics
        
        # Calculate percentages
        stats = self.audio_statistics.copy()
        for key in ['speech', 'music', 'noise', 'silence']:
            stats[f'{key}_percentage'] = (stats[key] / total) * 100
        
        return stats
    
    def update_keywords(self, keywords: List[str]):
        """Update suspicious keywords"""
        self.config['suspicious_keywords'] = keywords
        print(f"Updated suspicious keywords: {keywords}")
    
    def update_sensitivity(self, sensitivity: float):
        """Update detection sensitivity"""
        self.config['sensitivity'] = max(0.1, min(1.0, sensitivity))
        print(f"Updated sensitivity: {sensitivity}")

def main():
    """Test the enhanced audio monitor"""
    config = {
        'sensitivity': 0.7,
        'suspicious_keywords': [
            'help', 'emergency', 'danger', 'fire', 'police', 'attack',
            'threat', 'dangerous', 'weapon', 'gun', 'knife', 'fight',
            'intruder', 'break in', 'robbery', 'assault', 'kill', 'hurt',
            'bomb', 'explosive', 'terrorist', 'hostage', 'scream', 'cry'
        ]
    }
    
    monitor = EnhancedAudioMonitor(config)
    
    try:
        monitor.start()
        print("Enhanced audio monitoring started. Press Ctrl+C to stop.")
        
        while True:
            result = monitor.process_frame()
            if result and result.get('audio_type') == 'speech':
                print(f"Audio Type: {result['audio_type']}")
                if result.get('text'):
                    print(f"Transcribed: {result['text']}")
                    print(f"Language: {result.get('language', 'unknown')}")
                print("---")
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("Stopping enhanced audio monitoring...")
        monitor.stop()
        print("Enhanced audio monitoring stopped")

if __name__ == "__main__":
    main() 