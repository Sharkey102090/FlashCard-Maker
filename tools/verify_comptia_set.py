from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.data_manager import data_manager

path = Path(r"C:\Users\Adam\.flashcard_maker\data\comptia_security_plus.fcs")

try:
    fs = data_manager.load_flashcard_set(path)
    print('Loaded:', path)
    print('Name:', fs.name)
    print('Card count:', len(fs.flashcards))
except Exception as e:
    print('Failed to load:', e)
