#!/usr/bin/env python3
"""
Quick Speech Recognition Test
Simple and direct - shows exactly what you're speaking
"""

import speech_recognition as sr
import time

def main():
    print("🎤 QUICK SPEECH RECOGNITION TEST")
    print("=" * 50)
    print("This will show exactly what you're speaking!")
    print("=" * 50)
    
    # Initialize recognizer
    r = sr.Recognizer()
    
    # Test microphone
    try:
        with sr.Microphone() as source:
            print("✅ Microphone is working!")
            print("🎯 Speak something now...")
            
            # Listen for audio
            audio = r.listen(source, timeout=10, phrase_time_limit=15)
            print("✅ Audio captured!")
            
            # Transcribe
            try:
                text = r.recognize_google(audio)
                print("\n" + "="*50)
                print("🎯 TRANSCRIPTION RESULT:")
                print("="*50)
                print(f"📝 You said: \"{text}\"")
                print(f"⏰ Time: {time.strftime('%H:%M:%S')}")
                print("="*50)
                
            except sr.UnknownValueError:
                print("❌ Could not understand the audio")
            except sr.RequestError as e:
                print(f"❌ Speech recognition error: {e}")
                
    except Exception as e:
        print(f"❌ Microphone error: {e}")

if __name__ == "__main__":
    main() 