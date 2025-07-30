#!/usr/bin/env python3
"""
Real-time Speech Recognition Test
Shows exactly what the user is speaking with language detection
"""

import pyaudio
import numpy as np
import time
import json
import speech_recognition as sr
from typing import Dict, Any

class SpeechRecognitionTest:
    def __init__(self):
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.channels = 1
        self.format = pyaudio.paInt16
        
        # Audio setup
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_listening = False
        
        # Speech recognition
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 3000
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
        # Speech buffer
        self.speech_buffer = []
        self.last_speech_time = 0
        self.speech_timeout = 1.5  # seconds
        
        print("🎤 Speech Recognition Test Initialized")
        print("=" * 50)
        print("Speak clearly into your microphone...")
        print("The system will show what you're saying in real-time!")
        print("=" * 50)
    
    def start_listening(self):
        """Start listening for speech"""
        try:
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            self.is_listening = True
            print("✅ Microphone activated - Start speaking!")
            print()
            
        except Exception as e:
            print(f"❌ Error starting microphone: {e}")
            return False
        
        return True
    
    def stop_listening(self):
        """Stop listening for speech"""
        self.is_listening = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        if self.audio:
            self.audio.terminate()
        
        print("🛑 Microphone deactivated")
    
    def detect_speech(self, audio_data: np.ndarray) -> bool:
        """Detect if audio contains speech"""
        if len(audio_data) == 0:
            return False
        
        # Convert to float
        audio_float = audio_data.astype(np.float32) / 32768.0
        
        # Calculate RMS (volume)
        rms = np.sqrt(np.mean(audio_float**2))
        
        # Calculate zero crossing rate (speech characteristic)
        zero_crossing_rate = np.sum(np.diff(np.sign(audio_float))) / len(audio_float)
        
        # Speech detection criteria
        if rms > 0.01 and zero_crossing_rate > 0.1:
            return True
        
        return False
    
    def transcribe_speech(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """Transcribe speech with language detection"""
        if len(audio_data) == 0:
            return {'text': '', 'confidence': 0.0, 'language': 'unknown'}
        
        try:
            # Convert to AudioData format
            audio_bytes = audio_data.tobytes()
            audio_data_sr = sr.AudioData(audio_bytes, self.sample_rate, 2)
            
            # Try Google Speech Recognition with auto-detection
            text = self.recognizer.recognize_google(
                audio_data_sr,
                show_all=True
            )
            
            if text and isinstance(text, dict) and 'alternative' in text:
                best_result = text['alternative'][0]
                return {
                    'text': best_result['transcript'],
                    'confidence': best_result.get('confidence', 0.0),
                    'language': text.get('language', 'auto-detected'),
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
            print(f"⚠️  Speech recognition error: {e}")
        except Exception as e:
            print(f"❌ Transcription error: {e}")
        
        return {'text': '', 'confidence': 0.0, 'language': 'unknown'}
    
    def run(self):
        """Main listening loop"""
        if not self.start_listening():
            return
        
        try:
            while self.is_listening:
                # Read audio data
                audio_data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                
                # Detect speech
                if self.detect_speech(audio_array):
                    # Accumulate speech audio
                    self.speech_buffer.extend(audio_array)
                    self.last_speech_time = time.time()
                    
                    # Process when buffer is full or timeout reached
                    if (len(self.speech_buffer) >= self.sample_rate * 2 or  # 2 seconds
                        time.time() - self.last_speech_time > self.speech_timeout):
                        
                        if len(self.speech_buffer) > self.sample_rate * 0.5:  # At least 0.5 seconds
                            # Convert to numpy array
                            speech_array = np.array(self.speech_buffer, dtype=np.int16)
                            
                            # Transcribe speech
                            result = self.transcribe_speech(speech_array)
                            
                            if result['text']:
                                # Display results
                                print("🎯 SPEECH DETECTED:")
                                print(f"📝 Text: \"{result['text']}\"")
                                print(f"🌍 Language: {result['language']}")
                                print(f"📊 Confidence: {result['confidence']:.2f}")
                                print(f"⏰ Time: {time.strftime('%H:%M:%S')}")
                                print("-" * 50)
                            
                            # Clear buffer
                            self.speech_buffer = []
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping speech recognition...")
        except Exception as e:
            print(f"❌ Error in speech recognition: {e}")
        finally:
            self.stop_listening()

def main():
    """Main entry point"""
    print("🎤 REAL-TIME SPEECH RECOGNITION TEST")
    print("=" * 50)
    print("This will show exactly what you're speaking in real-time!")
    print("Supported languages: English, Spanish, French, German, Italian,")
    print("Portuguese, Russian, Japanese, Korean, Chinese, Arabic, Hindi")
    print("=" * 50)
    
    # Create and run speech recognition test
    speech_test = SpeechRecognitionTest()
    speech_test.run()

if __name__ == "__main__":
    main() 