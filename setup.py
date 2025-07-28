#!/usr/bin/env python3
"""
Setup script for AI Security Monitor
Automates installation and configuration
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, Any

class SecurityMonitorSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.python_backend = self.project_root / "python-backend"
        self.electron_app = self.project_root / "electron-app"
        self.shared = self.project_root / "shared"
        
    def print_banner(self):
        """Print setup banner"""
        print("=" * 60)
        print("🔒 AI Security Monitor - Setup")
        print("=" * 60)
        print("Setting up your desktop security application...")
        print()
        
    def check_prerequisites(self) -> bool:
        """Check if system meets requirements"""
        print("📋 Checking prerequisites...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ required. Current version:", sys.version)
            return False
        print("✅ Python version:", sys.version.split()[0])
        
        # Check Node.js
        try:
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Node.js version:", result.stdout.strip())
            else:
                print("❌ Node.js not found. Please install Node.js 16+")
                return False
        except FileNotFoundError:
            print("❌ Node.js not found. Please install Node.js 16+")
            return False
            
        # Check npm
        try:
            result = subprocess.run(['npm', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ npm version:", result.stdout.strip())
            else:
                print("❌ npm not found")
                return False
        except FileNotFoundError:
            print("❌ npm not found")
            return False
            
        print("✅ Prerequisites check passed!")
        return True
        
    def create_directories(self):
        """Create necessary directories"""
        print("\n📁 Creating directories...")
        
        directories = [
            "data/incidents",
            "data/logs", 
            "data/recordings",
            "data/snapshots",
            "data/known_faces",
            "models",
            "logs"
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created: {directory}")
            
    def install_python_dependencies(self) -> bool:
        """Install Python dependencies"""
        print("\n🐍 Installing Python dependencies...")
        
        try:
            # Upgrade pip first
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                         check=True, capture_output=True)
            
            # Install requirements
            requirements_file = self.python_backend / "requirements.txt"
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)], 
                         check=True)
            
            print("✅ Python dependencies installed successfully!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Python dependencies: {e}")
            print("💡 Try installing system dependencies first:")
            print("   Windows: Install Visual Studio Build Tools")
            print("   macOS: Install Xcode Command Line Tools")
            print("   Linux: sudo apt-get install build-essential python3-dev")
            return False
            
    def install_node_dependencies(self) -> bool:
        """Install Node.js dependencies"""
        print("\n📦 Installing Node.js dependencies...")
        
        try:
            os.chdir(self.electron_app)
            subprocess.run(['npm', 'install'], check=True)
            print("✅ Node.js dependencies installed successfully!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Node.js dependencies: {e}")
            return False
            
    def setup_configuration(self):
        """Setup initial configuration"""
        print("\n⚙️ Setting up configuration...")
        
        config_file = self.shared / "config.json"
        
        if config_file.exists():
            print("✅ Configuration file already exists")
            return
            
        # Create default config
        default_config = {
            "app": {
                "name": "AI Security Monitor",
                "version": "1.0.0",
                "description": "AI-powered security monitoring application",
                "author": "Your Name",
                "license": "MIT"
            },
            "development": {
                "debug_mode": True,
                "test_mode": False
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
            
        print("✅ Created default configuration file")
        
    def download_models(self):
        """Download AI models (optional)"""
        print("\n🤖 Downloading AI models (optional)...")
        
        models_dir = self.project_root / "models"
        models_dir.mkdir(exist_ok=True)
        
        # YOLOv8 model
        yolo_model = models_dir / "yolov8n.pt"
        if not yolo_model.exists():
            print("📥 Downloading YOLOv8 model...")
            try:
                import urllib.request
                url = "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt"
                urllib.request.urlretrieve(url, yolo_model)
                print("✅ YOLOv8 model downloaded")
            except Exception as e:
                print(f"⚠️ Failed to download YOLOv8 model: {e}")
                print("💡 The model will be downloaded automatically on first run")
        else:
            print("✅ YOLOv8 model already exists")
            
    def create_startup_scripts(self):
        """Create convenient startup scripts"""
        print("\n🚀 Creating startup scripts...")
        
        # Windows batch file
        if os.name == 'nt':
            batch_content = """@echo off
echo Starting AI Security Monitor...
cd /d "%~dp0"
cd electron-app
npm start
pause
"""
            with open(self.project_root / "start.bat", 'w') as f:
                f.write(batch_content)
            print("✅ Created start.bat")
            
        # Unix shell script
        else:
            shell_content = """#!/bin/bash
echo "Starting AI Security Monitor..."
cd "$(dirname "$0")"
cd electron-app
npm start
"""
            script_path = self.project_root / "start.sh"
            with open(script_path, 'w') as f:
                f.write(shell_content)
            os.chmod(script_path, 0o755)
            print("✅ Created start.sh")
            
    def run_tests(self):
        """Run basic tests"""
        print("\n🧪 Running basic tests...")
        
        # Test Python imports
        try:
            sys.path.append(str(self.python_backend))
            import app
            print("✅ Python backend imports successfully")
        except ImportError as e:
            print(f"⚠️ Python backend import warning: {e}")
            
        # Test configuration
        config_file = self.shared / "config.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    json.load(f)
                print("✅ Configuration file is valid JSON")
            except json.JSONDecodeError:
                print("❌ Configuration file has invalid JSON")
                
    def print_next_steps(self):
        """Print next steps for the user"""
        print("\n" + "=" * 60)
        print("🎉 Setup Complete!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. 📝 Review and customize shared/config.json")
        print("2. 🚀 Start the application:")
        if os.name == 'nt':
            print("   - Double-click start.bat")
            print("   - Or run: cd electron-app && npm start")
        else:
            print("   - Run: ./start.sh")
            print("   - Or run: cd electron-app && npm start")
        print("3. 📖 Read docs/README.md for detailed instructions")
        print("4. 🔧 Configure your security settings in the app")
        print()
        print("⚠️ Important:")
        print("- Grant camera and microphone permissions when prompted")
        print("- Ensure you have adequate lighting for face recognition")
        print("- Test with a quiet environment for voice monitoring")
        print("- Review local laws regarding surveillance and recording")
        print()
        print("For help: Check docs/README.md or enable debug mode in config.json")
        
    def run_setup(self):
        """Run the complete setup process"""
        self.print_banner()
        
        if not self.check_prerequisites():
            print("\n❌ Prerequisites not met. Please install required software.")
            return False
            
        self.create_directories()
        
        if not self.install_python_dependencies():
            print("\n❌ Python setup failed. Check error messages above.")
            return False
            
        if not self.install_node_dependencies():
            print("\n❌ Node.js setup failed. Check error messages above.")
            return False
            
        self.setup_configuration()
        self.download_models()
        self.create_startup_scripts()
        self.run_tests()
        self.print_next_steps()
        
        return True

def main():
    """Main setup function"""
    setup = SecurityMonitorSetup()
    success = setup.run_setup()
    
    if success:
        print("\n✅ Setup completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 