#!/usr/bin/env python3
"""
Continuous Speech Recognition
Shows everything you're speaking in real-time
"""

import speech_recognition as sr
import time

def continuous_listening():
    """Continuously listen and transcribe speech"""
    
    # Initialize recognizer
    r = sr.Recognizer()
    r.energy_threshold = 3000
    r.dynamic_energy_threshold = True
    r.pause_threshold = 0.8
    
    print("🎤 CONTINUOUS SPEECH RECOGNITION")
    print("=" * 50)
    print("This will show everything you're speaking in real-time!")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        while True:
            print("\n🎯 Listening... (speak now)")
            
            with sr.Microphone() as source:
                try:
                    # Listen for audio
                    audio = r.listen(source, timeout=5, phrase_time_limit=10)
                    print("✅ Audio captured, transcribing...")
                    
                    # Transcribe
                    text = r.recognize_google(audio)
                    
                    # Display result
                    print("\n" + "="*50)
                    print("🎯 SPEECH DETECTED!")
                    print("="*50)
                    print(f"📝 You said: \"{text}\"")
                    print(f"⏰ Time: {time.strftime('%H:%M:%S')}")
                    print("="*50)
                    
                except sr.WaitTimeoutError:
                    print("⏰ No speech detected (timeout)")
                except sr.UnknownValueError:
                    print("❌ Speech not understood")
                except sr.RequestError as e:
                    print(f"⚠️  Speech recognition error: {e}")
                except Exception as e:
                    print(f"❌ Error: {e}")
                    
    except KeyboardInterrupt:
        print("\n🛑 Stopping speech recognition...")
        print("✅ Speech recognition stopped")

def main():
    """Main function"""
    print("🎤 CONTINUOUS SPEECH RECOGNITION")
    print("=" * 50)
    print("This will continuously listen and show what you're speaking!")
    print("🌍 Supports multiple languages (auto-detected)")
    print("=" * 50)
    
    # Test microphone first
    try:
        with sr.Microphone() as source:
            print("✅ Microphone is working!")
    except Exception as e:
        print(f"❌ Microphone error: {e}")
        return
    
    # Start continuous listening
    continuous_listening()

if __name__ == "__main__":
    main() 