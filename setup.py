#!/usr/bin/env python3
"""
Setup script for SEO Checker Tool
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories."""
    dirs = ["logs", "reports"]
    for dir_name in dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"✓ Created directory: {dir_name}")
        else:
            print(f"✓ Directory already exists: {dir_name}")

def test_imports():
    """Test if all required modules can be imported."""
    print("Testing imports...")
    try:
        import requests
        import bs4
        import streamlit
        import pandas
        import plotly
        from datetime import datetime
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def main():
    """Main setup function."""
    print("=" * 50)
    print("SEO Checker Tool - Setup")
    print("=" * 50)
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        print("\nSetup failed. Please install dependencies manually:")
        print("pip install -r requirements.txt")
        return
    
    # Test imports
    if not test_imports():
        print("\nSetup failed. Please check your Python installation.")
        return
    
    print("\n" + "=" * 50)
    print("Setup completed successfully!")
    print("=" * 50)
    print("\nYou can now use the SEO checker:")
    print("1. Run 'python run_app.py' to launch the web interface (Streamlit)")
    print("2. Run 'python seo_checker.py --help' for command-line usage")
    print("3. Run 'python demo.py' for a quick CLI demo")
    print("4. Edit 'urls.txt' with your own URLs and run 'python seo_checker.py --file urls.txt'")

if __name__ == "__main__":
    main() 