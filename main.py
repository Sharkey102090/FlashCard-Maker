"""
Secure GUI-Based Flashcard Generator
====================================

A comprehensive flashcard generation application with double-sided printing support,
rich text editing, study modes, and robust security features.

Features:
- Rich text flashcard editor with formatting
- Multiple import/export formats (CSV, Excel, JSON, PDF)
- Double-sided printing with proper alignment
- Interactive study modes with progress tracking
- Secure data handling and validation
- Customizable themes and layouts
- Search and tagging system
- QR code generation
- Plugin architecture

Author: Adam
Version: 1.0.0
License: MIT
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.gui.main_window import FlashcardApp

def main():
    """Entry point for the flashcard application."""
    try:
        app = FlashcardApp()
        app.run()
    except KeyboardInterrupt:
        print("Application interrupted by user")
    except SystemExit:
        # Normal application exit, don't treat as error
        pass
    except Exception as e:
        print(f"Failed to start application: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)