# 🛡️ Advanced Security System

A comprehensive security monitoring system with multi-person detection, audio analysis, and speech recognition capabilities.

## 🚀 Features

### 🔍 **Multi-Person Detection**
- Real-time person detection using YOLO
- Alerts when multiple people detected (>1 person)
- Visual detection boxes and information panel
- Configurable alert thresholds

### 🎤 **Audio Monitoring & Speech Recognition**
- Continuous audio monitoring
- Speech transcription (multi-language support)
- Audio type detection (speech, music, noise, silence)
- Suspicious keyword detection
- Real-time alerts

### 🌐 **Web Interface**
- Beautiful dashboard for monitoring
- Real-time alerts and statistics
- API endpoints for programmatic control
- WebSocket support for live updates

## 📋 Prerequisites

### System Requirements
- Python 3.8+
- Windows 10/11
- Webcam
- Microphone
- Internet connection (for speech recognition)

### Required Software
- Python 3.8 or higher
- CMake (for dlib compilation)
- Visual Studio Build Tools (for Windows)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/security-system.git
cd security-system
```

### 2. Install Dependencies
```bash
cd python-backend
pip install -r requirements.txt
```

### 3. Install Build Tools (Windows)
```bash
# Install CMake
winget install Kitware.CMake

# Install Visual Studio Build Tools
winget install Microsoft.VisualStudio.2022.BuildTools

# Refresh environment
refreshenv
```

### 4. Install Additional Dependencies
```bash
# Install individual packages if needed
pip install opencv-python
pip install ultralytics
pip install speechrecognition
pip install pyaudio
pip install librosa
pip install soundfile
pip install fastapi
pip install uvicorn
```

## 🎯 Individual Commands

### **1. Multi-Person Detection**
```bash
python multi_person_detector.py
```
**Features:**
- Real-time camera monitoring
- Person detection with YOLO
- Visual detection boxes
- Alert when multiple people detected
- Press 'q' to quit

### **2. Enhanced Audio Monitoring**
```bash
python enhanced_audio_monitor.py
```
**Features:**
- Continuous audio monitoring
- Speech transcription
- Audio type detection
- Suspicious keyword detection
- Press Ctrl+C to stop

### **3. Quick Speech Recognition Test**
```bash
python quick_speech_test.py
```
**Features:**
- One-time speech recognition
- Multi-language support
- Quick microphone test
- Shows transcribed text

### **4. Continuous Speech Recognition**
```bash
python continuous_speech.py
```
**Features:**
- Continuous speech listening
- Real-time transcription
- Multi-language auto-detection
- Press Ctrl+C to stop

### **5. Simple Speech Recognition Test**
```bash
python simple_speech_test.py
```
**Features:**
- Simple speech recognition
- Continuous listening
- Clear text display
- Press Ctrl+C to stop

### **6. Integrated Security App (Optional)**
```bash
python security_app_with_multi_person.py
```
**Features:**
- Combined multi-person + audio monitoring
- Web dashboard at http://localhost:8000
- API documentation at http://localhost:8000/docs
- WebSocket real-time updates
- Press Ctrl+C to stop

## 📊 Feature Comparison

| Command | Purpose | Key Features | Stop Command |
|---------|---------|--------------|--------------|
| `python multi_person_detector.py` | Person Detection | Camera monitoring, alerts | Press 'q' |
| `python enhanced_audio_monitor.py` | Audio Analysis | Speech, audio types, keywords | Ctrl+C |
| `python quick_speech_test.py` | Quick Speech Test | One-time recognition | Auto |
| `python continuous_speech.py` | Continuous Speech | Real-time listening | Ctrl+C |
| `python simple_speech_test.py` | Simple Speech Test | Basic recognition | Ctrl+C |
| `python security_app_with_multi_person.py` | Integrated App | Web interface, combined | Ctrl+C |

## 🚨 Security Alerts

### Multi-Person Detection
- 🟢 **Normal**: 1 person detected
- 🔴 **Alert**: 2+ people detected

### Audio Monitoring
- 🎤 **Speech**: Transcribed text shown
- ⚠️ **Suspicious**: Keywords detected
- 🎵 **Music**: Audio type identified
- 🔇 **Silence**: No audio detected

## ⚙️ Configuration

### Multi-Person Detection Settings
```python
config = {
    'max_allowed_people': 1,      # Maximum people allowed
    'alert_threshold': 2,          # Alert when 2+ people detected
    'detection_confidence': 0.5,   # Detection confidence threshold
    'alert_cooldown': 10           # Seconds between alerts
}
```

### Audio Monitoring Settings
```python
config = {
    'sensitivity': 0.7,
    'suspicious_keywords': [
        'help', 'emergency', 'danger', 'fire', 'police', 'attack',
        'threat', 'dangerous', 'weapon', 'gun', 'knife', 'fight',
        'intruder', 'break in', 'robbery', 'assault', 'kill', 'hurt',
        'bomb', 'explosive', 'terrorist', 'hostage', 'scream', 'cry'
    ]
}
```

## 🌐 Web Interface

### Dashboard
- **URL**: http://localhost:8000
- **Features**: Real-time monitoring, alerts, statistics

### API Documentation
- **URL**: http://localhost:8000/docs
- **Features**: Interactive API documentation

### WebSocket
- **URL**: ws://localhost:8000/ws
- **Features**: Real-time incident updates

## 📁 Project Structure

```
security-system/
├── python-backend/
│   ├── multi_person_detector.py          # Multi-person detection
│   ├── enhanced_audio_monitor.py         # Audio monitoring
│   ├── quick_speech_test.py             # Quick speech test
│   ├── continuous_speech.py             # Continuous speech
│   ├── simple_speech_test.py            # Simple speech test
│   ├── security_app_with_multi_person.py # Integrated app
│   └── requirements.txt                  # Dependencies
├── electron-app/                         # Electron frontend
├── docs/                                 # Documentation
└── README.md                            # This file
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Camera Not Working
```bash
# Check camera permissions
# Ensure no other app is using camera
# Try different camera index
```

#### 2. Microphone Issues
```bash
# Check microphone permissions
# Ensure microphone is not muted
# Test with: python quick_speech_test.py
```

#### 3. YOLO Model Issues
```bash
# Model will auto-download on first run
# Check internet connection
# Verify ultralytics installation
```

#### 4. Dependencies Issues
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Install individual packages
pip install opencv-python ultralytics speechrecognition pyaudio
```

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Test multi-person detection:**
   ```bash
   python multi_person_detector.py
   ```

3. **Test speech recognition:**
   ```bash
   python quick_speech_test.py
   ```

4. **Test audio monitoring:**
   ```bash
   python enhanced_audio_monitor.py
   ```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the documentation

---

**🛡️ Security System - Advanced monitoring with multi-person detection and audio analysis** 