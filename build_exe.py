#!/usr/bin/env python3
"""Build script for creating PrintLabel executable."""
import os
import subprocess
import sys
from pathlib import Path

def main():
    """Build the executable using PyInstaller."""
    print("Building PrintLabel executable...")
    
    # Get the project root directory
    project_root = Path(__file__).parent
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",  # Single executable file
        "--windowed",  # No console window
        "--name=PrintLabel",  # Executable name
        "--icon=icon.ico",  # Icon (if exists)
        "--add-data=app;app",  # Include app directory
        "--hidden-import=win32print",
        "--hidden-import=win32api", 
        "--hidden-import=win32con",
        "--hidden-import=PIL",
        "--hidden-import=PIL.Image",
        "--hidden-import=PIL.ImageDraw",
        "--hidden-import=PIL.ImageFont",
        "--hidden-import=PIL.ImageTk",
        "--hidden-import=barcode",
        "--hidden-import=barcode.writer",
        "--hidden-import=barcode.writer.ImageWriter",
        "--hidden-import=sqlite3",
        "--collect-all=app",
        "app/main.py"
    ]
    
    # Remove icon if it doesn't exist
    if not (project_root / "icon.ico").exists():
        cmd = [arg for arg in cmd if arg != "--icon=icon.ico"]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, cwd=project_root, check=True, capture_output=True, text=True)
        print("Build completed successfully!")
        print(f"Executable location: {project_root / 'dist' / 'PrintLabel.exe'}")
        
        # Show file size
        exe_path = project_root / "dist" / "PrintLabel.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"Executable size: {size_mb:.1f} MB")
            
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error code {e.returncode}")
        print(f"Error output: {e.stderr}")
        return 1
    except Exception as e:
        print(f"Build failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
