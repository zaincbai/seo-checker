#!/usr/bin/env python3
"""
Launch script for the SEO Checker Streamlit app
"""

import subprocess
import sys
import os

def check_dependencies():
    """Check if all dependencies are installed."""
    try:
        import streamlit
        import pandas
        import plotly
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def main():
    """Main function to launch the Streamlit app."""
    print("🔍 SEO Checker Tool - Web Interface")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Please install dependencies first")
        return
    
    # Check if app.py exists
    if not os.path.exists("app.py"):
        print("❌ app.py not found")
        return
    
    print("✅ All dependencies found")
    print("🚀 Starting Streamlit app...")
    print("\nThe app will open in your browser automatically.")
    print("If it doesn't open, go to: http://localhost:8501")
    print("\nPress Ctrl+C to stop the app")
    print("=" * 50)
    
    # Run Streamlit
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 SEO Checker app stopped")
    except Exception as e:
        print(f"❌ Error running app: {e}")

if __name__ == "__main__":
    main() 