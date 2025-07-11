#!/usr/bin/env python3
"""
Demo script for SEO Checker Tool
Run this to test the SEO checker with a small set of URLs
"""

import subprocess
import sys
import os

def run_demo():
    """Run a demo of the SEO checker tool."""
    print("=" * 60)
    print("SEO Checker Tool - Demo")
    print("=" * 60)
    
    # Check if dependencies are installed
    print("Checking dependencies...")
    try:
        import requests
        import bs4
        print("✓ All dependencies are installed")
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return
    
    # Create a small demo URLs file
    demo_urls = [
        "https://example.com",
        "https://github.com"
    ]
    
    with open("demo_urls.txt", "w") as f:
        f.write("# Demo URLs for SEO Analysis\n")
        for url in demo_urls:
            f.write(f"{url}\n")
    
    print(f"Created demo URLs file with {len(demo_urls)} URLs")
    
    # Run the SEO checker
    print("\nRunning SEO analysis...")
    try:
        result = subprocess.run([
            sys.executable, "seo_checker.py",
            "--file", "demo_urls.txt",
            "--output", "demo_report",
            "--log-level", "INFO"
        ], capture_output=True, text=True)
        
        print("Command output:")
        print(result.stdout)
        
        if result.stderr:
            print("Errors/Warnings:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n✓ Demo completed successfully!")
            print("\nGenerated files:")
            
            # List generated files
            for filename in os.listdir("reports"):
                if filename.startswith("demo_report"):
                    print(f"  - reports/{filename}")
            
            print("\nYou can now:")
            print("1. Open the HTML report in your browser for visual analysis")
            print("2. Open the CSV report in a spreadsheet application")
            print("3. Check the logs/ directory for detailed execution logs")
            
        else:
            print(f"\n✗ Demo failed with exit code: {result.returncode}")
            
    except Exception as e:
        print(f"✗ Error running demo: {e}")
    
    # Clean up demo file
    if os.path.exists("demo_urls.txt"):
        os.remove("demo_urls.txt")
        print("\nCleaned up demo URLs file")

if __name__ == "__main__":
    run_demo() 