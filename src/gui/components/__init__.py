"""
GUI Component Modules
=====================

This package contains all GUI components for the flashcard application.
"""

# Import main components for easy access
from .flashcard_editor import FlashcardEditor
from .flashcard_viewer import FlashcardViewer
from .settings_panel import SettingsPanel
from .file_manager import FileManager

__all__ = [
    'FlashcardEditor',
    'FlashcardViewer', 
    'SettingsPanel',
    'FileManager'
]