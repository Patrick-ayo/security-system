# AI Security Monitor

A comprehensive desktop security application built with Electron and Python, featuring real-time face recognition, voice monitoring, object detection, and suspicious activity analysis using open-source AI technologies.

## 🚀 Features

### Core Security Features
- **Face Recognition**: Real-time user presence and identity verification using DeepFace and face_recognition
- **Voice Monitoring**: Continuous audio presence checks and anomaly detection with Vosk
- **Object Detection**: Detection of suspicious objects (phones, weapons) using YOLOv8
- **Activity Detection**: Behavioral analysis for suspicious activities using MediaPipe
- **Rolling Buffer**: 2.5-minute audio/video buffer with incident recording
- **Secure Logging**: Encrypted storage of logs, videos, and images

### Technical Features
- **Cross-Platform**: Windows and macOS support via Electron
- **Open Source**: All AI dependencies are open-source
- **Privacy-First**: User data encryption and retention controls
- **Modular Design**: Easy to extend and maintain
- **Real-Time Processing**: Multi-threaded AI processing

## 📋 Prerequisites

### System Requirements
- **Windows 10/11** or **macOS 10.15+**
- **Python 3.8+**
- **Node.js 16+**
- **Webcam** and **Microphone** access
- **4GB+ RAM** (8GB recommended)
- **2GB+ free disk space**

### Hardware Recommendations
- **GPU**: NVIDIA GPU with CUDA support (optional, for faster AI processing)
- **Camera**: HD webcam (720p or higher)
- **Microphone**: Quality microphone for voice analysis

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd my-electron-ai-security-app
```

### 2. Install Python Dependencies
```bash
cd python-backend
pip install -r requirements.txt
```

**Note**: Some dependencies may require additional system libraries:
- **Windows**: Install Visual Studio Build Tools
- **macOS**: Install Xcode Command Line Tools
- **Linux**: Install build-essential and python3-dev

### 3. Install Node.js Dependencies
```bash
cd ../electron-app
npm install
```

### 4. Download AI Models (Optional)
The application will automatically download required models on first run, but you can pre-download them:

```bash
# YOLOv8 model
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -O python-backend/models/yolov8n.pt

# Vosk speech model
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip -d python-backend/models/
```

## 🚀 Quick Start

### Development Mode
```bash
# Terminal 1: Start the Python backend
cd python-backend
python app.py

# Terminal 2: Start the Electron app
cd electron-app
npm run dev
```

### Production Build
```bash
# Build for your platform
cd electron-app
npm run build

# Or build for specific platforms
npm run build:win    # Windows
npm run build:mac    # macOS
npm run build:linux  # Linux
```

## ⚙️ Configuration

Edit `shared/config.json` to customize the application:

### Key Configuration Sections
- **Face Recognition**: Confidence thresholds, known faces path
- **Voice Monitor**: Sensitivity, suspicious keywords
- **Object Detection**: Suspicious objects list, confidence thresholds
- **Activity Detection**: Suspicious activities, motion detection settings
- **Storage**: Encryption keys, retention policies
- **Performance**: CPU/memory limits, threading settings

### Example Configuration
```json
{
  "face_recognition": {
    "enabled": true,
    "confidence_threshold": 0.8,
    "suspicious_emotions": ["angry", "fear", "sad"]
  },
  "voice_monitor": {
    "enabled": true,
    "suspicious_keywords": ["help", "emergency", "danger"]
  },
  "object_detection": {
    "suspicious_objects": ["cell phone", "weapon", "gun"]
  }
}
```

## 🔧 Usage

### Starting the Application
1. Launch the Electron app
2. Grant camera and microphone permissions when prompted
3. Click "Start Monitoring" to begin security monitoring
4. The app will continuously monitor for:
   - Unknown faces
   - Suspicious voice patterns
   - Dangerous objects
   - Suspicious activities

### Monitoring Dashboard
- **Live Feed**: Real-time camera view
- **Recent Incidents**: List of detected security events
- **System Logs**: Application status and error messages
- **Controls**: Start/stop monitoring, load incidents

### Incident Management
- **Automatic Recording**: 5-minute clips (2.5 min before/after incidents)
- **Encrypted Storage**: All data is encrypted and securely stored
- **Searchable Logs**: Filter by user, event type, and time
- **Snapshot Capture**: Images of detected threats

## 🛡️ Security Features

### Data Protection
- **Encryption**: All logs and recordings are encrypted using Fernet
- **Access Control**: Optional authentication system
- **Privacy Controls**: Face blurring and data anonymization
- **Retention Policies**: Automatic cleanup of old data

### Privacy Compliance
- **GDPR Compliance**: Built-in data protection features
- **User Consent**: Explicit permission requests
- **Data Minimization**: Only necessary data is collected
- **Right to Deletion**: Easy data removal tools

## 🔍 Troubleshooting

### Common Issues

**Python Dependencies**
```bash
# If face_recognition fails to install
pip install cmake
pip install dlib
pip install face_recognition
```

**Audio Issues**
```bash
# Windows: Install Visual C++ Redistributable
# macOS: Grant microphone permissions in System Preferences
# Linux: Install portaudio
sudo apt-get install portaudio19-dev
```

**Camera Issues**
```bash
# Ensure camera permissions are granted
# Check if camera is being used by another application
# Restart the application
```

**Performance Issues**
```bash
# Reduce AI processing load
# Edit config.json: lower confidence thresholds
# Disable unused modules
# Increase buffer sizes for smoother operation
```

### Debug Mode
Enable debug mode in `shared/config.json`:
```json
{
  "development": {
    "debug_mode": true,
    "test_mode": false
  }
}
```

## 📊 Performance Optimization

### System Tuning
- **CPU Usage**: Adjust threading settings in config
- **Memory Usage**: Optimize buffer sizes
- **GPU Acceleration**: Enable CUDA for faster AI processing
- **Storage**: Configure retention policies

### Module-Specific Optimization
- **Face Recognition**: Lower confidence thresholds for faster processing
- **Object Detection**: Use smaller YOLO models (nano vs large)
- **Voice Monitor**: Adjust chunk sizes and sensitivity
- **Activity Detection**: Tune motion detection parameters

## 🔧 Development

### Project Structure
```
my-electron-ai-security-app/
├── electron-app/          # Electron frontend
│   ├── main.js           # Main process
│   ├── preload.js        # Secure API bridge
│   ├── renderer/         # React UI
│   └── package.json      # Node.js dependencies
├── python-backend/       # AI processing backend
│   ├── app.py           # Main orchestrator
│   ├── face_recognition.py
│   ├── voice_monitor.py
│   ├── object_detect.py
│   ├── activity_detect.py
│   ├── buffer_manager.py
│   ├── log_storage.py
│   └── requirements.txt
├── shared/              # Shared configuration
│   └── config.json
└── docs/               # Documentation
    └── README.md
```

### Adding New Features
1. **New AI Module**: Create a new Python file in `python-backend/`
2. **UI Integration**: Add React components in `electron-app/renderer/`
3. **Configuration**: Update `shared/config.json`
4. **Documentation**: Update this README

### Testing
```bash
# Run Python tests
cd python-backend
python -m pytest

# Run Electron tests
cd electron-app
npm test
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section above
- Review the configuration options
- Enable debug mode for detailed logs
- Check system requirements and dependencies

## 🔮 Roadmap

### Planned Features
- **Mobile App**: Companion mobile application
- **Cloud Sync**: Secure cloud storage and sync
- **Advanced AI**: More sophisticated threat detection
- **API Integration**: Third-party security system integration
- **Multi-Camera**: Support for multiple camera feeds

### Performance Improvements
- **GPU Optimization**: Better CUDA utilization
- **Model Optimization**: Quantized AI models
- **Memory Management**: Improved buffer handling
- **Real-Time Processing**: Lower latency detection

---

**⚠️ Important**: This application is for educational and personal security purposes. Always comply with local laws and regulations regarding surveillance and data collection. 