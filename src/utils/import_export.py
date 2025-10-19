"""
Import/Export Utilities
=======================

Secure handling of file imports and exports with validation.
"""

import csv
import json
import io
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import pandas as pd
from datetime import datetime

from ..core.models import FlashcardSet, Flashcard, InputValidator
from ..utils.security import logger
from ..utils.config import config

class ImportExportManager:
    """Manages secure import and export operations."""
    
    SUPPORTED_FORMATS = {
        '.csv': 'CSV',
        '.xlsx': 'Excel',
        '.xls': 'Excel Legacy',
        '.json': 'JSON'
    }
    
    def __init__(self):
        self.max_file_size = config.get('security.max_file_size', 50 * 1024 * 1024)
        self.allowed_extensions = config.get('security.allowed_extensions', ['.csv', '.xlsx', '.json'])
    
    def _validate_file(self, file_path: Path) -> bool:
        """Validate file before processing."""
        # Check if file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check file extension
        if file_path.suffix.lower() not in self.allowed_extensions:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        # Check file size
        if file_path.stat().st_size > self.max_file_size:
            raise ValueError(f"File too large. Maximum size: {self.max_file_size // (1024*1024)}MB")
        
        return True
    
    def _sanitize_import_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize imported data."""
        sanitized = {}
        
        for key, value in data.items():
            # Sanitize key
            clean_key = InputValidator.sanitize_text(str(key), 100)
            
            # Sanitize value
            if isinstance(value, str):
                clean_value = InputValidator.sanitize_html(value, 50000)
            elif isinstance(value, (int, float, bool)):
                clean_value = value
            elif isinstance(value, list):
                clean_value = [InputValidator.sanitize_text(str(item), 1000) for item in value[:20]]
            else:
                clean_value = InputValidator.sanitize_text(str(value), 1000)
            
            sanitized[clean_key] = clean_value
        
        return sanitized
    
    def import_from_csv(self, file_path: Path, delimiter: str = ',', encoding: str = 'utf-8') -> FlashcardSet:
        """Import flashcards from CSV file."""
        self._validate_file(file_path)
        
        try:
            flashcard_set = FlashcardSet(name=f"Imported from {file_path.name}")
            
            with open(file_path, 'r', encoding=encoding, newline='') as csvfile:
                # Detect delimiter if auto
                sample = csvfile.read(1024)
                csvfile.seek(0)
                
                if delimiter == 'auto':
                    sniffer = csv.Sniffer()
                    delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                
                for row_num, row in enumerate(reader, 1):
                    if row_num > 10000:  # Limit to prevent memory issues
                        logger.warning(f"CSV import limited to 10,000 rows")
                        break
                    
                    try:
                        # Sanitize row data
                        clean_row = self._sanitize_import_data(row)
                        
                        # Map columns to flashcard fields
                        front_text = self._get_column_value(clean_row, ['front', 'question', 'prompt', 'term'])
                        back_text = self._get_column_value(clean_row, ['back', 'answer', 'response', 'definition'])
                        
                        if not front_text and not back_text:
                            continue  # Skip empty rows
                        
                        # Create flashcard
                        flashcard = Flashcard(
                            front_text=front_text or f"Row {row_num}",
                            back_text=back_text or "",
                            category=self._get_column_value(clean_row, ['category', 'topic', 'subject']) or "Imported"
                        )
                        
                        # Add tags if available
                        tags_value = self._get_column_value(clean_row, ['tags', 'keywords', 'labels'])
                        if tags_value:
                            tags = [tag.strip() for tag in str(tags_value).split(',') if tag.strip()]
                            for tag in tags[:10]:  # Limit tags
                                flashcard.add_tag(tag)
                        
                        flashcard_set.add_flashcard(flashcard)
                    
                    except Exception as e:
                        logger.warning(f"Failed to import row {row_num}: {e}")
                        continue
            
            logger.info(f"CSV import completed: {len(flashcard_set.flashcards)} cards imported")
            return flashcard_set
        
        except Exception as e:
            logger.error(f"CSV import failed: {e}")
            raise ValueError(f"Failed to import CSV: {e}")
    
    def import_from_excel(self, file_path: Path, sheet_name: Optional[str] = None) -> FlashcardSet:
        """Import flashcards from Excel file."""
        self._validate_file(file_path)
        
        try:
            # Read Excel file
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                df = pd.read_excel(file_path)
            
            # Limit rows
            if len(df) > 10000:
                df = df.head(10000)
                logger.warning("Excel import limited to 10,000 rows")
            
            flashcard_set = FlashcardSet(name=f"Imported from {file_path.name}")
            
            for row_num, (index, row) in enumerate(df.iterrows()):
                try:
                    # Convert row to dictionary and sanitize
                    row_dict = row.to_dict()
                    clean_row = self._sanitize_import_data(row_dict)
                    
                    # Map columns
                    front_text = self._get_column_value(clean_row, ['front', 'question', 'prompt', 'term'])
                    back_text = self._get_column_value(clean_row, ['back', 'answer', 'response', 'definition'])
                    
                    if not front_text and not back_text:
                        continue
                    
                    # Create flashcard
                    flashcard = Flashcard(
                        front_text=front_text or f"Row {row_num + 1}",
                        back_text=back_text or "",
                        category=self._get_column_value(clean_row, ['category', 'topic', 'subject']) or "Imported"
                    )
                    
                    # Add tags
                    tags_value = self._get_column_value(clean_row, ['tags', 'keywords', 'labels'])
                    if tags_value:
                        tags = [tag.strip() for tag in str(tags_value).split(',') if tag.strip()]
                        for tag in tags[:10]:
                            flashcard.add_tag(tag)
                    
                    flashcard_set.add_flashcard(flashcard)
                
                except Exception as e:
                    logger.warning(f"Failed to import Excel row {index}: {e}")
                    continue
            
            logger.info(f"Excel import completed: {len(flashcard_set.flashcards)} cards imported")
            return flashcard_set
        
        except Exception as e:
            logger.error(f"Excel import failed: {e}")
            raise ValueError(f"Failed to import Excel: {e}")
    
    def import_from_json(self, file_path: Path) -> FlashcardSet:
        """Import flashcards from JSON file."""
        self._validate_file(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, dict):
                if 'flashcards' in data:
                    # Flashcard set format
                    return FlashcardSet.from_dict(data)
                elif 'cards' in data:
                    # Alternative format
                    flashcard_set = FlashcardSet(name=f"Imported from {file_path.name}")
                    for card_data in data['cards'][:10000]:
                        clean_data = self._sanitize_import_data(card_data)
                        flashcard = self._create_flashcard_from_dict(clean_data)
                        flashcard_set.add_flashcard(flashcard)
                    return flashcard_set
                else:
                    # Single flashcard
                    flashcard_set = FlashcardSet(name=f"Imported from {file_path.name}")
                    clean_data = self._sanitize_import_data(data)
                    flashcard = self._create_flashcard_from_dict(clean_data)
                    flashcard_set.add_flashcard(flashcard)
                    return flashcard_set
            
            elif isinstance(data, list):
                # Array of flashcards
                flashcard_set = FlashcardSet(name=f"Imported from {file_path.name}")
                for card_data in data[:10000]:
                    clean_data = self._sanitize_import_data(card_data)
                    flashcard = self._create_flashcard_from_dict(clean_data)
                    flashcard_set.add_flashcard(flashcard)
                return flashcard_set
            
            else:
                raise ValueError("Invalid JSON format")
        
        except Exception as e:
            logger.error(f"JSON import failed: {e}")
            raise ValueError(f"Failed to import JSON: {e}")
    
    def _get_column_value(self, row_dict: Dict[str, Any], possible_keys: List[str]) -> Optional[str]:
        """Get value from row dictionary using possible column names."""
        for key in possible_keys:
            # Try exact match
            if key in row_dict and row_dict[key] is not None:
                return str(row_dict[key]).strip()
            
            # Try case-insensitive match
            for row_key in row_dict.keys():
                if row_key.lower() == key.lower() and row_dict[row_key] is not None:
                    return str(row_dict[row_key]).strip()
        
        return None
    
    def _create_flashcard_from_dict(self, data: Dict[str, Any]) -> Flashcard:
        """Create flashcard from dictionary data."""
        front_text = self._get_column_value(data, ['front', 'front_text', 'question', 'prompt', 'term']) or ""
        back_text = self._get_column_value(data, ['back', 'back_text', 'answer', 'response', 'definition']) or ""
        category = self._get_column_value(data, ['category', 'topic', 'subject']) or "Imported"
        
        flashcard = Flashcard(
            front_text=front_text,
            back_text=back_text,
            category=category
        )
        
        # Add tags
        tags_value = self._get_column_value(data, ['tags', 'keywords', 'labels'])
        if tags_value:
            if isinstance(tags_value, list):
                tags = tags_value
            else:
                tags = [tag.strip() for tag in str(tags_value).split(',') if tag.strip()]
            
            for tag in tags[:10]:
                flashcard.add_tag(tag)
        
        return flashcard
    
    def export_to_csv(self, flashcard_set: FlashcardSet, file_path: Path, 
                     include_metadata: bool = False) -> bool:
        """Export flashcard set to CSV file."""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['front', 'back', 'category', 'tags']
                
                if include_metadata:
                    fieldnames.extend([
                        'created_at', 'updated_at', 'times_studied', 
                        'correct_answers', 'incorrect_answers', 'accuracy'
                    ])
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for flashcard in flashcard_set.flashcards:
                    # Remove HTML tags for CSV export
                    import re
                    front_clean = re.sub(r'<[^>]+>', '', flashcard.front_text)
                    back_clean = re.sub(r'<[^>]+>', '', flashcard.back_text)
                    
                    row = {
                        'front': front_clean,
                        'back': back_clean,
                        'category': flashcard.category,
                        'tags': ', '.join(flashcard.tags)
                    }
                    
                    if include_metadata:
                        metadata_dict = {
                            'created_at': flashcard.metadata.created_at.isoformat(),
                            'updated_at': flashcard.metadata.updated_at.isoformat(),
                            'times_studied': flashcard.metadata.times_studied,
                            'correct_answers': flashcard.metadata.correct_answers,
                            'incorrect_answers': flashcard.metadata.incorrect_answers,
                            'accuracy': flashcard.metadata.accuracy
                        }
                        row.update(metadata_dict)
                    
                    writer.writerow(row)
            
            logger.info(f"CSV export completed: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            return False
    
    def export_to_excel(self, flashcard_set: FlashcardSet, file_path: Path,
                       include_metadata: bool = False) -> bool:
        """Export flashcard set to Excel file."""
        try:
            # Prepare data
            data = []
            
            for flashcard in flashcard_set.flashcards:
                # Remove HTML tags
                import re
                front_clean = re.sub(r'<[^>]+>', '', flashcard.front_text)
                back_clean = re.sub(r'<[^>]+>', '', flashcard.back_text)
                
                row = {
                    'Front': front_clean,
                    'Back': back_clean,
                    'Category': flashcard.category,
                    'Tags': ', '.join(flashcard.tags)
                }
                
                if include_metadata:
                    metadata_dict = {
                        'Created': flashcard.metadata.created_at,
                        'Updated': flashcard.metadata.updated_at,
                        'Times Studied': flashcard.metadata.times_studied,
                        'Correct Answers': flashcard.metadata.correct_answers,
                        'Incorrect Answers': flashcard.metadata.incorrect_answers,
                        'Accuracy (%)': flashcard.metadata.accuracy
                    }
                    row.update(metadata_dict)
                
                data.append(row)
            
            # Create DataFrame and export
            df = pd.DataFrame(data)
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Flashcards', index=False)
                
                # Add metadata sheet
                metadata_df = pd.DataFrame([{
                    'Set Name': flashcard_set.name,
                    'Description': flashcard_set.description,
                    'Total Cards': len(flashcard_set.flashcards),
                    'Created': flashcard_set.created_at,
                    'Updated': flashcard_set.updated_at,
                    'Export Date': datetime.now()
                }])
                
                metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
            
            logger.info(f"Excel export completed: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Excel export failed: {e}")
            return False
    
    def export_to_json(self, flashcard_set: FlashcardSet, file_path: Path,
                      pretty_print: bool = True) -> bool:
        """Export flashcard set to JSON file."""
        try:
            data = flashcard_set.to_dict()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                if pretty_print:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, f, ensure_ascii=False)
            
            logger.info(f"JSON export completed: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            return False
    
    def get_preview(self, file_path: Path, rows: int = 5) -> List[Dict[str, Any]]:
        """Get preview of import file."""
        self._validate_file(file_path)
        
        try:
            if file_path.suffix.lower() == '.csv':
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    return [dict(row) for _, row in zip(range(rows), reader)]
            
            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path, nrows=rows)
                records = df.to_dict('records')
                # Type: ignore for pandas return type compatibility
                return records  # type: ignore
            
            elif file_path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    return data[:rows]
                elif isinstance(data, dict) and 'flashcards' in data:
                    return data['flashcards'][:rows]
                else:
                    return [data]
            
            return []  # Default case if no format matches
        
        except Exception as e:
            logger.error(f"Preview generation failed: {e}")
            return []

# Global import/export manager instance
import_export_manager = ImportExportManager()