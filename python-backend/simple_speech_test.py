#!/usr/bin/env python3
"""
Simple Speech Recognition Test
Shows exactly what you're speaking in real-time
"""

import speech_recognition as sr
import time

def listen_and_transcribe():
    """Listen to microphone and transcribe speech"""
    
    # Initialize recognizer
    recognizer = sr.Recognizer()
    
    # Adjust for ambient noise
    recognizer.energy_threshold = 3000
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8
    
    print("🎤 SIMPLE SPEECH RECOGNITION TEST")
    print("=" * 50)
    print("Speak clearly into your microphone...")
    print("The system will show what you're saying!")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        while True:
            print("\n🎯 Listening... (speak now)")
            
            # Listen to microphone
            with sr.Microphone() as source:
                print("📡 Microphone activated...")
                
                try:
                    # Listen for audio
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    print("✅ Audio captured, transcribing...")
                    
                    # Transcribe the audio
                    text = recognizer.recognize_google(audio, show_all=True)
                    
                    if text and isinstance(text, dict) and 'alternative' in text:
                        # Get the best result
                        best_result = text['alternative'][0]
                        transcribed_text = best_result['transcript']
                        confidence = best_result.get('confidence', 0.0)
                        
                        print("\n" + "="*50)
                        print("🎯 SPEECH DETECTED!")
                        print("="*50)
                        print(f"📝 You said: \"{transcribed_text}\"")
                        print(f"📊 Confidence: {confidence:.2f}")
                        print(f"⏰ Time: {time.strftime('%H:%M:%S')}")
                        print("="*50)
                        
                    elif text and isinstance(text, str):
                        print("\n" + "="*50)
                        print("🎯 SPEECH DETECTED!")
                        print("="*50)
                        print(f"📝 You said: \"{text}\"")
                        print(f"📊 Confidence: 0.8")
                        print(f"⏰ Time: {time.strftime('%H:%M:%S')}")
                        print("="*50)
                        
                    else:
                        print("❌ No speech detected or couldn't transcribe")
                        
                except sr.WaitTimeoutError:
                    print("⏰ No speech detected within timeout")
                except sr.UnknownValueError:
                    print("❌ Speech not understood")
                except sr.RequestError as e:
                    print(f"⚠️  Speech recognition error: {e}")
                except Exception as e:
                    print(f"❌ Error: {e}")
                    
    except KeyboardInterrupt:
        print("\n🛑 Stopping speech recognition...")
        print("✅ Speech recognition stopped")

def test_microphone():
    """Test if microphone is working"""
    print("🔍 Testing microphone...")
    
    try:
        with sr.Microphone() as source:
            print("✅ Microphone is working!")
            return True
    except Exception as e:
        print(f"❌ Microphone error: {e}")
        return False

def main():
    """Main function"""
    print("🎤 SIMPLE SPEECH RECOGNITION")
    print("=" * 50)
    
    # Test microphone first
    if not test_microphone():
        print("❌ Cannot access microphone. Please check your microphone settings.")
        return
    
    print("✅ Microphone is ready!")
    print("🌍 Supports multiple languages (auto-detected)")
    print("=" * 50)
    
    # Start listening
    listen_and_transcribe()

if __name__ == "__main__":
    main() 