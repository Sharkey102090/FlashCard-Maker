# Test script to call _import_comptia_set programmatically
from pathlib import Path
import sys
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from src.gui.main_window import FlashcardApp

app = FlashcardApp()
try:
    app._import_comptia_set()
    print('Import completed without raising an exception')
except Exception as e:
    print('Import raised exception:', repr(e))
    raise
