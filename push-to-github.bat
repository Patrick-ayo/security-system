@echo off
title GitHub Upload Helper
color 0C

echo.
echo ========================================
echo    🚀 GITHUB UPLOAD HELPER 🚀
echo ========================================
echo.

echo 📋 Follow these steps to upload to GitHub:
echo.
echo 1. Go to GitHub.com and sign in
echo 2. Click the "+" icon in the top right
echo 3. Select "New repository"
echo 4. Name it: security-system
echo 5. Make it Public or Private (your choice)
echo 6. DO NOT initialize with README (we already have one)
echo 7. Click "Create repository"
echo.
echo 📝 Copy the repository URL (it will look like):
echo    https://github.com/yourusername/security-system.git
echo.
echo 🔗 After creating the repository, run these commands:
echo.
echo git remote add origin YOUR_REPOSITORY_URL
echo git branch -M main
echo git push -u origin main
echo.
echo 📖 Example:
echo    git remote add origin https://github.com/yourusername/security-system.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo 🎉 Your security system will be uploaded to GitHub!
echo.
echo 📋 Repository includes:
echo    ✅ Multi-person detection
echo    ✅ Audio monitoring & speech recognition
echo    ✅ Individual command modules
echo    ✅ Web interface
echo    ✅ Comprehensive documentation
echo    ✅ Installation scripts
echo.
echo Press any key to continue...
pause >nul

echo.
echo 🔧 Current Git Status:
git status

echo.
echo 📊 Repository Summary:
echo    - Total files: $(git ls-files | wc -l)
echo    - Python modules: 8
echo    - Documentation: 3 files
echo    - Installation: 2 scripts
echo.
echo 🛡️ Security System Features:
echo    - Multi-person detection with YOLO
echo    - Speech recognition (multi-language)
echo    - Audio type detection
echo    - Suspicious keyword monitoring
echo    - Real-time alerts
echo    - Web dashboard interface
echo.
echo 📖 Individual Commands Available:
echo    python multi_person_detector.py
echo    python enhanced_audio_monitor.py
echo    python quick_speech_test.py
echo    python continuous_speech.py
echo    python simple_speech_test.py
echo    python security_app_with_multi_person.py
echo.
echo 🎯 Ready for GitHub upload!
echo.
echo Press any key to exit...
pause >nul 