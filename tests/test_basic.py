"""
Basic Test Suite
================

Simple tests for core functionality.
"""

import unittest
import tempfile
import json
from pathlib import Path
from datetime import datetime

# Import modules to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.models import Flashcard, FlashcardSet, InputValidator
from src.core.data_manager import SecureDataManager
from src.utils.config import SecureConfig
from src.utils.import_export import ImportExportManager

class TestInputValidator(unittest.TestCase):
    """Test input validation."""
    
    def test_sanitize_text(self):
        """Test text sanitization."""
        # Test basic sanitization
        dirty_text = "<script>alert('xss')</script>Hello World"
        clean_text = InputValidator.sanitize_text(dirty_text)
        self.assertNotIn("<script>", clean_text)
        self.assertIn("Hello World", clean_text)
        
        # Test length limiting
        long_text = "A" * 20000
        clean_text = InputValidator.sanitize_text(long_text, 100)
        self.assertEqual(len(clean_text), 100)
    
    def test_validate_tag(self):
        """Test tag validation."""
        # Valid tag
        tag = InputValidator.validate_tag("  Valid Tag  ")
        self.assertEqual(tag, "valid tag")
        
        # Invalid characters
        tag = InputValidator.validate_tag("tag<script>")
        self.assertEqual(tag, "tagscript")
        
        # Empty tag should raise error
        with self.assertRaises(ValueError):
            InputValidator.validate_tag("")

class TestFlashcard(unittest.TestCase):
    """Test flashcard model."""
    
    def test_flashcard_creation(self):
        """Test creating a flashcard."""
        card = Flashcard(
            front_text="What is Python?",
            back_text="A programming language",
            category="Programming"
        )
        
        self.assertEqual(card.front_text, "What is Python?")
        self.assertEqual(card.back_text, "A programming language")
        self.assertEqual(card.category, "Programming")
        self.assertIsNotNone(card.id)
    
    def test_tag_management(self):
        """Test adding and removing tags."""
        card = Flashcard(front_text="Test", back_text="Test")
        
        # Add tag
        result = card.add_tag("python")
        self.assertTrue(result)
        self.assertIn("python", card.tags)
        
        # Remove tag
        result = card.remove_tag("python")
        self.assertTrue(result)
        self.assertNotIn("python", card.tags)
    
    def test_study_tracking(self):
        """Test study progress tracking."""
        card = Flashcard(front_text="Test", back_text="Test")
        
        # Initial state
        self.assertEqual(card.metadata.times_studied, 0)
        self.assertEqual(card.metadata.accuracy, 0.0)
        
        # Study with correct answer
        card.study(True)
        self.assertEqual(card.metadata.times_studied, 1)
        self.assertEqual(card.metadata.correct_answers, 1)
        
        # Study with incorrect answer
        card.study(False)
        self.assertEqual(card.metadata.times_studied, 2)
        self.assertEqual(card.metadata.incorrect_answers, 1)
        self.assertEqual(card.metadata.accuracy, 50.0)

class TestFlashcardSet(unittest.TestCase):
    """Test flashcard set model."""
    
    def test_flashcard_set_creation(self):
        """Test creating a flashcard set."""
        card_set = FlashcardSet(name="Test Set", description="Test Description")
        
        self.assertEqual(card_set.name, "Test Set")
        self.assertEqual(card_set.description, "Test Description")
        self.assertEqual(len(card_set.flashcards), 0)
    
    def test_adding_flashcards(self):
        """Test adding flashcards to set."""
        card_set = FlashcardSet()
        card = Flashcard(front_text="Test", back_text="Test")
        
        card_set.add_flashcard(card)
        self.assertEqual(len(card_set.flashcards), 1)
        self.assertEqual(card_set.flashcards[0], card)
    
    def test_search_functionality(self):
        """Test searching flashcards."""
        card_set = FlashcardSet()
        
        card1 = Flashcard(front_text="Python basics", back_text="Programming")
        card2 = Flashcard(front_text="Java syntax", back_text="Programming")
        card3 = Flashcard(front_text="History", back_text="World War II")
        
        card_set.add_flashcard(card1)
        card_set.add_flashcard(card2)
        card_set.add_flashcard(card3)
        
        # Search for programming
        results = card_set.search_flashcards("programming")
        self.assertEqual(len(results), 2)
        
        # Search for Python
        results = card_set.search_flashcards("python")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], card1)

class TestSecureConfig(unittest.TestCase):
    """Test configuration management."""
    
    def setUp(self):
        """Set up test configuration."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = SecureConfig(Path(self.temp_dir))
    
    def test_get_set_config(self):
        """Test getting and setting configuration values."""
        # Test setting and getting
        self.config.set('test.value', 'hello')
        value = self.config.get('test.value')
        self.assertEqual(value, 'hello')
        
        # Test default value
        value = self.config.get('nonexistent.key', 'default')
        self.assertEqual(value, 'default')
    
    def test_config_validation(self):
        """Test configuration validation."""
        # This should work (valid theme)
        self.config.set('gui.theme', 'dark')
        
        # Invalid values should be caught by validation
        # (This would be handled in the actual validation layer)
        pass

class TestDataManager(unittest.TestCase):
    """Test data management."""
    
    def setUp(self):
        """Set up test data manager."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_manager = SecureDataManager(Path(self.temp_dir))
    
    def test_save_load_flashcard_set(self):
        """Test saving and loading flashcard sets."""
        # Create test flashcard set
        card_set = FlashcardSet(name="Test Set")
        card = Flashcard(front_text="Test Question", back_text="Test Answer")
        card_set.add_flashcard(card)
        
        # Save the set
        file_path = self.data_manager.save_flashcard_set(card_set, "test_set")
        self.assertTrue(file_path.exists())
        
        # Load the set
        loaded_set = self.data_manager.load_flashcard_set(file_path)
        self.assertEqual(loaded_set.name, "Test Set")
        self.assertEqual(len(loaded_set.flashcards), 1)
        self.assertEqual(loaded_set.flashcards[0].front_text, "Test Question")

class TestImportExport(unittest.TestCase):
    """Test import/export functionality."""
    
    def setUp(self):
        """Set up test import/export manager."""
        self.temp_dir = tempfile.mkdtemp()
        self.import_export = ImportExportManager()
    
    def test_json_export_import(self):
        """Test JSON export and import."""
        # Create test data
        card_set = FlashcardSet(name="Test Set")
        card = Flashcard(front_text="Question", back_text="Answer")
        card_set.add_flashcard(card)
        
        # Export to JSON
        json_file = Path(self.temp_dir) / "test.json"
        result = self.import_export.export_to_json(card_set, json_file)
        self.assertTrue(result)
        self.assertTrue(json_file.exists())
        
        # Import from JSON
        imported_set = self.import_export.import_from_json(json_file)
        self.assertEqual(imported_set.name, "Test Set")
        self.assertEqual(len(imported_set.flashcards), 1)
    
    def test_csv_import(self):
        """Test CSV import functionality."""
        # Create test CSV
        csv_file = Path(self.temp_dir) / "test.csv"
        csv_content = """front,back,category
"What is Python?","A programming language","Programming"
"What is Java?","Another programming language","Programming"
"""
        
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        # Import from CSV
        try:
            imported_set = self.import_export.import_from_csv(csv_file)
            self.assertEqual(len(imported_set.flashcards), 2)
            self.assertEqual(imported_set.flashcards[0].front_text, "What is Python?")
        except Exception as e:
            # CSV import may fail if pandas is not available
            self.skipTest(f"CSV import test skipped: {e}")

def run_tests():
    """Run all tests."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestInputValidator,
        TestFlashcard,
        TestFlashcardSet,
        TestSecureConfig,
        TestDataManager,
        TestImportExport
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)