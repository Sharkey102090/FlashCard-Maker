"""Temporary runner to start the GUI without the start.py dependency checks.

This script adds the project root to sys.path and imports the application
package as `src.gui.main_window` so relative imports inside the package
resolve correctly (e.g. `from ..core.models import ...`).
"""
import sys
from pathlib import Path

# Add the project root (one directory above 'src') to sys.path so we can
# import the package using its top-level name `src` and keep relative imports
# inside the package working as intended.
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from src.gui.main_window import FlashcardApp


if __name__ == '__main__':
    app = FlashcardApp()
    app.run()
