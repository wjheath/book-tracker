#!/usr/bin/env python
"""
Launcher for the Book Tracker UI
Starts the Flask API and opens the browser
"""

import os
import sys
import time
import webbrowser
import subprocess
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

def main():
    print("=" * 60)
    print("📚 Book Tracker & Suggester - Web UI Launcher")
    print("=" * 60)
    print()
    
    # Check if .env exists
    env_path = Path(__file__).parent / '.env'
    if not env_path.exists():
        print("⚠️  Warning: .env file not found!")
        print("   Please create a .env file with your OpenAI API key.")
        print("   See .env.example for a template.")
        print()
    
    # Start Flask app
    print("🚀 Starting Flask API server...")
    print()
    
    try:
        # Run Flask app in a subprocess
        app_path = Path(__file__).parent / 'src' / 'app.py'
        
        # Use the current Python executable
        python_exe = sys.executable
        
        process = subprocess.Popen(
            [python_exe, str(app_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Give Flask time to start and collect output
        print("⏳ Waiting for server to start...")
        time.sleep(3)
        
        # Open browser
        url = 'http://127.0.0.1:5000/'
        print(f"✅ Server started!")
        print(f"🌐 Opening browser at {url}...")
        print()
        
        webbrowser.open(url)
        
        print("=" * 60)
        print("📚 Book Tracker is running!")
        print("=" * 60)
        print()
        print("Press Ctrl+C to stop the server")
        print()
        
        # Keep the process running and print output
        try:
            while True:
                line = process.stdout.readline()
                if line:
                    print(line.rstrip())
                else:
                    time.sleep(0.1)
        except:
            pass
        
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            process.kill()
        print("✅ Server stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   Make sure Flask is installed: pip install flask flask-cors")
        sys.exit(1)

if __name__ == '__main__':
    main()
