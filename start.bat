@echo off
echo Starting AI Security Monitor...
echo.
echo This will start the Electron application with the simplified Python backend.
echo Some features may be disabled due to missing dependencies.
echo.
echo To enable full features, install CMake and rebuild dlib:
echo 1. Download CMake from https://cmake.org/download/
echo 2. Install and add to PATH
echo 3. Run: pip install dlib face-recognition
echo.
pause
cd electron-app
npm start
pause 