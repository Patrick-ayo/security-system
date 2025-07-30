# 🚀 Quick Reference - Security System Commands

## 🎯 Individual Commands

### **Multi-Person Detection**
```bash
python multi_person_detector.py
```
- Real-time camera monitoring
- Person detection with YOLO
- Alerts when multiple people detected
- Press 'q' to quit

### **Audio Monitoring & Speech Recognition**
```bash
python enhanced_audio_monitor.py
```
- Continuous audio monitoring
- Speech transcription
- Audio type detection
- Suspicious keyword detection
- Press Ctrl+C to stop

### **Quick Speech Test**
```bash
python quick_speech_test.py
```
- One-time speech recognition
- Multi-language support
- Quick microphone test
- Shows transcribed text

### **Continuous Speech Recognition**
```bash
python continuous_speech.py
```
- Continuous speech listening
- Real-time transcription
- Multi-language auto-detection
- Press Ctrl+C to stop

### **Simple Speech Test**
```bash
python simple_speech_test.py
```
- Simple speech recognition
- Continuous listening
- Clear text display
- Press Ctrl+C to stop

### **Integrated Web App (Optional)**
```bash
python security_app_with_multi_person.py
```
- Combined multi-person + audio monitoring
- Web dashboard: http://localhost:8000
- API docs: http://localhost:8000/docs
- Press Ctrl+C to stop

## 🚨 Security Alerts

| Feature | Normal | Alert |
|---------|--------|-------|
| **Multi-Person** | 🟢 1 person | 🔴 2+ people |
| **Audio** | 🎤 Speech detected | ⚠️ Suspicious keywords |
| **Speech** | 📝 Transcribed text | 🚨 Dangerous words |

## ⚡ Quick Start

1. **Install**: `install.bat` or `pip install -r requirements.txt`
2. **Test Camera**: `python multi_person_detector.py`
3. **Test Microphone**: `python quick_speech_test.py`
4. **Test Audio**: `python enhanced_audio_monitor.py`

## 📊 Feature Summary

| Command | Purpose | Stop Command |
|---------|---------|--------------|
| `python multi_person_detector.py` | Person Detection | Press 'q' |
| `python enhanced_audio_monitor.py` | Audio Analysis | Ctrl+C |
| `python quick_speech_test.py` | Quick Speech Test | Auto |
| `python continuous_speech.py` | Continuous Speech | Ctrl+C |
| `python simple_speech_test.py` | Simple Speech Test | Ctrl+C |
| `python security_app_with_multi_person.py` | Integrated App | Ctrl+C |

## 🔧 Troubleshooting

### Camera Issues
- Check camera permissions
- Ensure no other app using camera
- Try different camera index

### Microphone Issues
- Check microphone permissions
- Ensure microphone not muted
- Test with: `python quick_speech_test.py`

### Dependencies Issues
```bash
pip install -r requirements.txt --force-reinstall
```

## 📞 Support

- Check README.md for detailed instructions
- Review troubleshooting section
- Create GitHub issue for problems

---

**🛡️ Security System - Individual modules for flexible security monitoring** 