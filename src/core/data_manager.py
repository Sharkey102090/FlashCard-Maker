"""
Secure Data Storage Manager
===========================

Handles secure storage and retrieval of flashcard data with encryption.
"""

import json
import pickle
import gzip
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import shutil
import hashlib
import os

from ..utils.config import config
from ..utils.security import logger
from .models import FlashcardSet, Flashcard

class SecureDataManager:
    """Manages secure storage of flashcard data."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path.home() / '.flashcard_maker' / 'data'
        self.backup_dir = self.data_dir / 'backups'
        
        # Create directories with secure permissions
        self.data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        
        self._encryption_key = None
    
    def _get_encryption_key(self) -> bytes:
        """Get encryption key for data protection."""
        if self._encryption_key is None:
            # Import here to avoid circular imports
            from ..utils.config import config
            key_file = Path.home() / '.flashcard_maker' / 'data.key'
            
            if key_file.exists():
                with open(key_file, 'rb') as f:
                    self._encryption_key = f.read()
            else:
                from cryptography.fernet import Fernet
                self._encryption_key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(self._encryption_key)
                os.chmod(key_file, 0o600)
        
        return self._encryption_key
    
    def _encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data using Fernet encryption."""
        try:
            from cryptography.fernet import Fernet
            key = self._get_encryption_key()
            fernet = Fernet(key)
            return fernet.encrypt(data)
        except ImportError:
            logger.warning("Cryptography not available, storing data unencrypted")
            return data
    
    def _decrypt_data(self, encrypted_data: bytes) -> bytes:
        """Decrypt data using Fernet encryption."""
        try:
            from cryptography.fernet import Fernet
            key = self._get_encryption_key()
            fernet = Fernet(key)
            return fernet.decrypt(encrypted_data)
        except ImportError:
            logger.warning("Cryptography not available, reading data as unencrypted")
            return encrypted_data
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            raise ValueError("Failed to decrypt data - file may be corrupted")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent directory traversal."""
        # Remove path separators and special characters
        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
        # Limit length
        filename = filename[:200]
        # Ensure it's not empty
        if not filename:
            filename = "unnamed"
        
        return filename
    
    def _create_backup(self, file_path: Path):
        """Create backup of existing file."""
        if file_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = self.backup_dir / backup_name
            
            try:
                shutil.copy2(file_path, backup_path)
                logger.info(f"Backup created: {backup_path}")
                
                # Keep only last 10 backups
                self._cleanup_old_backups(file_path.stem)
            except Exception as e:
                logger.error(f"Failed to create backup: {e}")
    
    def _cleanup_old_backups(self, prefix: str, keep_count: int = 10):
        """Remove old backup files, keeping only the most recent ones."""
        try:
            backups = [
                f for f in self.backup_dir.glob(f"{prefix}_*")
                if f.is_file()
            ]
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x.stat().st_ctime, reverse=True)
            
            # Remove old backups
            for backup in backups[keep_count:]:
                backup.unlink()
                logger.debug(f"Removed old backup: {backup}")
        
        except Exception as e:
            logger.error(f"Failed to cleanup backups: {e}")
    
    def save_flashcard_set(self, flashcard_set: FlashcardSet, filename: Optional[str] = None) -> Path:
        """Save flashcard set to encrypted file."""
        if filename is None:
            filename = self._sanitize_filename(flashcard_set.name)
        else:
            filename = self._sanitize_filename(filename)
        
        file_path = self.data_dir / f"{filename}.fcs"  # Flashcard Set extension
        
        try:
            # Create backup if file exists
            self._create_backup(file_path)
            
            # Serialize data
            data = flashcard_set.to_dict()
            json_data = json.dumps(data, indent=2, ensure_ascii=False)
            
            # Compress data
            compressed_data = gzip.compress(json_data.encode('utf-8'))
            
            # Encrypt if enabled
            if config.get('security.encrypt_data', True):
                final_data = self._encrypt_data(compressed_data)
            else:
                final_data = compressed_data
            
            # Write to file
            with open(file_path, 'wb') as f:
                f.write(final_data)
            
            # Set secure permissions
            os.chmod(file_path, 0o600)
            
            logger.info(f"Flashcard set saved: {file_path}")
            logger.audit("save_flashcard_set", filename=filename, card_count=len(flashcard_set.flashcards))
            
            return file_path
        
        except Exception as e:
            logger.error(f"Failed to save flashcard set: {e}")
            raise
    
    def load_flashcard_set(self, file_path: Union[str, Path]) -> FlashcardSet:
        """Load flashcard set from encrypted file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            # Read file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Decrypt if needed
            if config.get('security.encrypt_data', True):
                try:
                    decrypted_data = self._decrypt_data(file_data)
                except:
                    # Try as unencrypted data (legacy support)
                    decrypted_data = file_data
            else:
                decrypted_data = file_data
            
            # Decompress
            try:
                json_data = gzip.decompress(decrypted_data).decode('utf-8')
            except:
                # Try as uncompressed data (legacy support)
                json_data = decrypted_data.decode('utf-8')
            
            # Parse JSON
            data = json.loads(json_data)
            
            # Create flashcard set
            flashcard_set = FlashcardSet.from_dict(data)
            
            logger.info(f"Flashcard set loaded: {file_path}")
            logger.audit("load_flashcard_set", filename=str(file_path), card_count=len(flashcard_set.flashcards))
            
            return flashcard_set
        
        except Exception as e:
            logger.error(f"Failed to load flashcard set: {e}")
            raise ValueError(f"Failed to load flashcard set: {e}")
    
    def list_flashcard_sets(self) -> List[Dict[str, Any]]:
        """List all available flashcard sets."""
        sets = []
        
        try:
            for file_path in self.data_dir.glob("*.fcs"):
                try:
                    # Get file info
                    stat = file_path.stat()
                    
                    # Try to read set metadata without loading full content
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                    
                    # Quick metadata extraction (first 1KB should contain basic info)
                    preview_data = file_data[:1024]
                    
                    sets.append({
                        'filename': file_path.name,
                        'path': str(file_path),
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime),
                        'created': datetime.fromtimestamp(stat.st_ctime)
                    })
                
                except Exception as e:
                    logger.warning(f"Failed to read flashcard set info: {file_path}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Failed to list flashcard sets: {e}")
        
        return sorted(sets, key=lambda x: x['modified'], reverse=True)
    
    def delete_flashcard_set(self, file_path: Union[str, Path]) -> bool:
        """Delete a flashcard set file."""
        file_path = Path(file_path)
        
        try:
            if file_path.exists():
                # Create backup before deletion
                self._create_backup(file_path)
                
                # Delete file
                file_path.unlink()
                
                logger.info(f"Flashcard set deleted: {file_path}")
                logger.audit("delete_flashcard_set", filename=str(file_path))
                
                return True
        
        except Exception as e:
            logger.error(f"Failed to delete flashcard set: {e}")
        
        return False
    
    def export_to_json(self, flashcard_set: FlashcardSet, export_path: Path) -> bool:
        """Export flashcard set to plain JSON."""
        try:
            data = flashcard_set.to_dict()
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Flashcard set exported to JSON: {export_path}")
            logger.audit("export_to_json", filename=str(export_path))
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to export to JSON: {e}")
            return False
    
    def import_from_json(self, import_path: Path) -> FlashcardSet:
        """Import flashcard set from JSON file."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            flashcard_set = FlashcardSet.from_dict(data)
            
            logger.info(f"Flashcard set imported from JSON: {import_path}")
            logger.audit("import_from_json", filename=str(import_path), card_count=len(flashcard_set.flashcards))
            
            return flashcard_set
        
        except Exception as e:
            logger.error(f"Failed to import from JSON: {e}")
            raise ValueError(f"Failed to import from JSON: {e}")

# Global data manager instance
data_manager = SecureDataManager()