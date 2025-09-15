#!/usr/bin/env python3
"""
Development Environment Setup for ClipFlow
Validates system dependencies and creates minimal test environment
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {sys.version.split()[0]}")
    return True

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    if shutil.which('ffmpeg'):
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        version_line = result.stdout.split('\n')[0] if result.stdout else "Unknown version"
        print(f"✅ FFmpeg: {version_line}")
        return True
    print("❌ FFmpeg not found - required for video processing")
    print("   Install: sudo apt-get install ffmpeg (Ubuntu/Debian)")
    print("           brew install ffmpeg (macOS)")
    return False

def create_minimal_env():
    """Create minimal .env for testing"""
    env_file = Path('.env')
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    # Create minimal .env
    with open(env_file, 'w') as f:
        f.write("""# ClipFlow Configuration
# Add your actual tokens for production

# Telegram Bot (Required)
TELEGRAM_BOT_TOKEN=

# YouTube API (Optional)  
YOUTUBE_CLIENT_ID=
YOUTUBE_CLIENT_SECRET=
YOUTUBE_ACCESS_TOKEN=

# Instagram API (Optional)
INSTAGRAM_ACCESS_TOKEN=
INSTAGRAM_APP_ID=
INSTAGRAM_APP_SECRET=

# TikTok API (Optional)
TIKTOK_CLIENT_KEY=
TIKTOK_CLIENT_SECRET=  
TIKTOK_ACCESS_TOKEN=

# ClipFlow Settings
CLIPFLOW_TIMEZONE=Asia/Baku
CLIPFLOW_DATA_DIR=data
CLIPFLOW_TEMP_DIR=temp
""")
    
    print("✅ Created .env template - add your tokens")
    return True

def test_imports():
    """Test critical imports without external dependencies"""
    try:
        # Test core imports
        sys.path.insert(0, str(Path.cwd()))
        
        from clipflow_main import ClipFlowConfig, ConfigManager
        config = ClipFlowConfig()
        print("✅ Core ClipFlow imports work")
        
        # Test configuration loading
        config = ConfigManager.load_from_env()
        print("✅ Configuration system works")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def main():
    """Run development environment check"""
    print("🚀 ClipFlow Development Environment Setup")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("FFmpeg", check_ffmpeg), 
        ("Environment File", create_minimal_env),
        ("Core Imports", test_imports),
    ]
    
    passed = 0
    for name, check_func in checks:
        print(f"\n📋 Checking {name}...")
        if check_func():
            passed += 1
        else:
            print(f"❌ {name} check failed")
    
    print(f"\n{'='*50}")
    print(f"✅ {passed}/{len(checks)} checks passed")
    
    if passed == len(checks):
        print("\n🎉 Development environment ready!")
        print("\nNext steps:")
        print("1. Add your Telegram bot token to .env file")
        print("2. Run: python3 clipflow_main.py")
        print("3. Send /start to your bot on Telegram")
    else:
        print(f"\n⚠️  Fix {len(checks) - passed} issues before continuing")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())