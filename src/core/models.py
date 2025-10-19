"""
Core Data Models
================

Secure data models for flashcards with validation and encryption support.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
import re
import html
import bleach

class InputValidator:
    """Validates and sanitizes user input."""
    
    # HTML tags allowed in flashcard content
    ALLOWED_HTML_TAGS = [
        'b', 'i', 'u', 'strong', 'em', 'br', 'p', 'ul', 'ol', 'li',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre'
    ]
    
    ALLOWED_HTML_ATTRIBUTES = {
        '*': ['style'],
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'width', 'height']
    }
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 10000) -> str:
        """Sanitize text input."""
        if not isinstance(text, str):
            text = str(text)
        
        # Limit length
        text = text[:max_length]
        
        # Remove null bytes and control characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # HTML encode to prevent XSS
        text = html.escape(text, quote=True)
        
        return text.strip()
    
    @staticmethod
    def sanitize_html(html_content: str, max_length: int = 50000) -> str:
        """Sanitize HTML content using bleach."""
        if not isinstance(html_content, str):
            html_content = str(html_content)
        
        # Limit length
        html_content = html_content[:max_length]
        
        # Clean HTML with bleach
        cleaned = bleach.clean(
            html_content,
            tags=InputValidator.ALLOWED_HTML_TAGS,
            attributes=InputValidator.ALLOWED_HTML_ATTRIBUTES,
            strip=True
        )
        
        return cleaned.strip()
    
    @staticmethod
    def validate_file_path(file_path: Union[str, Path]) -> Path:
        """Validate file path to prevent directory traversal."""
        path = Path(file_path).resolve()
        
        # Check for directory traversal attempts
        if '..' in str(path) or str(path).startswith('/'):
            raise ValueError("Invalid file path")
        
        return path
    
    @staticmethod
    def validate_tag(tag: str) -> str:
        """Validate and sanitize tag names."""
        if not isinstance(tag, str):
            tag = str(tag)
        
        # Remove special characters and limit length
        tag = re.sub(r'[^\w\s-]', '', tag)[:50]
        tag = tag.strip().lower()
        
        if not tag:
            raise ValueError("Invalid tag")
        
        return tag

@dataclass
class FlashcardMetadata:
    """Metadata for flashcard tracking."""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    times_studied: int = 0
    correct_answers: int = 0
    incorrect_answers: int = 0
    difficulty_rating: float = 0.5  # 0.0 = easy, 1.0 = hard
    last_studied: Optional[datetime] = None
    
    def update_study_stats(self, correct: bool):
        """Update study statistics."""
        self.times_studied += 1
        self.last_studied = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        
        if correct:
            self.correct_answers += 1
            # Decrease difficulty if answered correctly
            self.difficulty_rating = max(0.0, self.difficulty_rating - 0.1)
        else:
            self.incorrect_answers += 1
            # Increase difficulty if answered incorrectly
            self.difficulty_rating = min(1.0, self.difficulty_rating + 0.1)
    
    @property
    def accuracy(self) -> float:
        """Calculate accuracy percentage."""
        if self.times_studied == 0:
            return 0.0
        return (self.correct_answers / self.times_studied) * 100

@dataclass
class Flashcard:
    """Secure flashcard data model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    front_text: str = ""
    back_text: str = ""
    front_image: Optional[str] = None  # Base64 encoded or file path
    back_image: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    category: str = "General"
    metadata: FlashcardMetadata = field(default_factory=FlashcardMetadata)
    
    def __post_init__(self):
        """Validate and sanitize data after initialization."""
        self.front_text = InputValidator.sanitize_html(self.front_text)
        self.back_text = InputValidator.sanitize_html(self.back_text)
        self.category = InputValidator.sanitize_text(self.category, 100)
        
        # Validate and sanitize tags
        validated_tags = []
        for tag in self.tags:
            try:
                validated_tag = InputValidator.validate_tag(tag)
                if validated_tag not in validated_tags:
                    validated_tags.append(validated_tag)
            except ValueError:
                continue  # Skip invalid tags
        
        self.tags = validated_tags[:20]  # Limit to 20 tags
    
    def add_tag(self, tag: str) -> bool:
        """Add a tag to the flashcard."""
        try:
            validated_tag = InputValidator.validate_tag(tag)
            if validated_tag not in self.tags and len(self.tags) < 20:
                self.tags.append(validated_tag)
                self.metadata.updated_at = datetime.now(timezone.utc)
                return True
        except ValueError:
            pass
        return False
    
    def remove_tag(self, tag: str) -> bool:
        """Remove a tag from the flashcard."""
        try:
            validated_tag = InputValidator.validate_tag(tag)
            if validated_tag in self.tags:
                self.tags.remove(validated_tag)
                self.metadata.updated_at = datetime.now(timezone.utc)
                return True
        except ValueError:
            pass
        return False
    
    def update_content(self, front_text: Optional[str] = None, back_text: Optional[str] = None):
        """Update flashcard content."""
        if front_text is not None:
            self.front_text = InputValidator.sanitize_html(front_text)
        
        if back_text is not None:
            self.back_text = InputValidator.sanitize_html(back_text)
        
        self.metadata.updated_at = datetime.now(timezone.utc)
    
    def study(self, correct: bool):
        """Record a study session."""
        self.metadata.update_study_stats(correct)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        data['metadata']['created_at'] = self.metadata.created_at.isoformat()
        data['metadata']['updated_at'] = self.metadata.updated_at.isoformat()
        if self.metadata.last_studied:
            data['metadata']['last_studied'] = self.metadata.last_studied.isoformat()
        else:
            data['metadata']['last_studied'] = None
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Flashcard':
        """Create flashcard from dictionary."""
        # Convert ISO strings back to datetime objects
        metadata_data = data.get('metadata', {})
        if 'created_at' in metadata_data:
            metadata_data['created_at'] = datetime.fromisoformat(metadata_data['created_at'])
        if 'updated_at' in metadata_data:
            metadata_data['updated_at'] = datetime.fromisoformat(metadata_data['updated_at'])
        if metadata_data.get('last_studied'):
            metadata_data['last_studied'] = datetime.fromisoformat(metadata_data['last_studied'])
        
        metadata = FlashcardMetadata(**metadata_data)
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            front_text=data.get('front_text', ''),
            back_text=data.get('back_text', ''),
            front_image=data.get('front_image'),
            back_image=data.get('back_image'),
            tags=data.get('tags', []),
            category=data.get('category', 'General'),
            metadata=metadata
        )

@dataclass
class FlashcardSet:
    """Collection of flashcards with metadata."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Flashcard Set"
    description: str = ""
    flashcards: List[Flashcard] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        """Validate and sanitize data after initialization."""
        self.name = InputValidator.sanitize_text(self.name, 200)
        self.description = InputValidator.sanitize_text(self.description, 1000)
    
    def add_flashcard(self, flashcard: Flashcard):
        """Add a flashcard to the set."""
        if flashcard.id not in [fc.id for fc in self.flashcards]:
            self.flashcards.append(flashcard)
            self.updated_at = datetime.now(timezone.utc)
    
    def remove_flashcard(self, flashcard_id: str) -> bool:
        """Remove a flashcard from the set."""
        for i, flashcard in enumerate(self.flashcards):
            if flashcard.id == flashcard_id:
                del self.flashcards[i]
                self.updated_at = datetime.now(timezone.utc)
                return True
        return False
    
    def get_flashcard(self, flashcard_id: str) -> Optional[Flashcard]:
        """Get a flashcard by ID."""
        for flashcard in self.flashcards:
            if flashcard.id == flashcard_id:
                return flashcard
        return None
    
    def search_flashcards(self, query: str) -> List[Flashcard]:
        """Search flashcards by text content or tags."""
        query = query.lower().strip()
        if not query:
            return self.flashcards
        
        results = []
        for flashcard in self.flashcards:
            # Search in text content
            if (query in flashcard.front_text.lower() or 
                query in flashcard.back_text.lower() or
                query in flashcard.category.lower()):
                results.append(flashcard)
                continue
            
            # Search in tags
            for tag in flashcard.tags:
                if query in tag.lower():
                    results.append(flashcard)
                    break
        
        return results
    
    def get_flashcards_by_tag(self, tag: str) -> List[Flashcard]:
        """Get flashcards with a specific tag."""
        try:
            validated_tag = InputValidator.validate_tag(tag)
            return [fc for fc in self.flashcards if validated_tag in fc.tags]
        except ValueError:
            return []
    
    def get_all_tags(self) -> List[str]:
        """Get all unique tags in the set."""
        tags = set()
        for flashcard in self.flashcards:
            tags.update(flashcard.tags)
        return sorted(list(tags))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the flashcard set."""
        if not self.flashcards:
            return {
                'total_cards': 0,
                'studied_cards': 0,
                'average_accuracy': 0.0,
                'total_study_sessions': 0,
                'categories': [],
                'tags': []
            }
        
        studied_cards = [fc for fc in self.flashcards if fc.metadata.times_studied > 0]
        total_sessions = sum(fc.metadata.times_studied for fc in self.flashcards)
        
        if studied_cards:
            avg_accuracy = sum(fc.metadata.accuracy for fc in studied_cards) / len(studied_cards)
        else:
            avg_accuracy = 0.0
        
        categories = list(set(fc.category for fc in self.flashcards))
        
        return {
            'total_cards': len(self.flashcards),
            'studied_cards': len(studied_cards),
            'average_accuracy': round(avg_accuracy, 2),
            'total_study_sessions': total_sessions,
            'categories': sorted(categories),
            'tags': self.get_all_tags()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'flashcards': [fc.to_dict() for fc in self.flashcards],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FlashcardSet':
        """Create flashcard set from dictionary."""
        flashcards = [Flashcard.from_dict(fc_data) for fc_data in data.get('flashcards', [])]
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', 'New Flashcard Set'),
            description=data.get('description', ''),
            flashcards=flashcards,
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now(timezone.utc).isoformat())),
            updated_at=datetime.fromisoformat(data.get('updated_at', datetime.now(timezone.utc).isoformat()))
        )