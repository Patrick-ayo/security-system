@echo off
title Security System Installer
color 0B

echo.
echo ========================================
echo    🛡️  SECURITY SYSTEM INSTALLER 🛡️
echo ========================================
echo.

echo 🔧 Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python 3.8+ first.
    pause
    exit /b 1
)

echo ✅ Python found!

echo.
echo 📦 Installing dependencies...
cd python-backend

echo.
echo 🔧 Installing core packages...
pip install -r requirements.txt

echo.
echo 🎯 Testing installations...

echo.
echo 🧪 Testing OpenCV...
python -c "import cv2; print('✅ OpenCV installed successfully')"

echo.
echo 🧪 Testing YOLO...
python -c "from ultralytics import YOLO; print('✅ YOLO installed successfully')"

echo.
echo 🧪 Testing Speech Recognition...
python -c "import speech_recognition; print('✅ Speech Recognition installed successfully')"

echo.
echo 🧪 Testing Audio Processing...
python -c "import pyaudio; print('✅ PyAudio installed successfully')"

echo.
echo ========================================
echo    🎉 INSTALLATION COMPLETE! 🎉
echo ========================================
echo.
echo 🚀 Your security system is ready to use!
echo.
echo 📋 Available commands:
echo    python multi_person_detector.py
echo    python enhanced_audio_monitor.py
echo    python quick_speech_test.py
echo    python continuous_speech.py
echo    python simple_speech_test.py
echo.
echo 📖 See README.md for detailed instructions
echo.
echo Press any key to exit...
pause >nul 