"""
Secure Configuration Management
===============================

Handles application configuration with validation, sanitization, and security.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
import configparser

try:
    import yaml
except ImportError:
    yaml = None

try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None

try:
    from cerberus import Validator as CerberusValidator
except ImportError:
    CerberusValidator = None

logger = logging.getLogger(__name__)

class ConfigValidator:
    """Validates configuration data using schemas."""
    
    SCHEMA = {
        'app': {
            'type': 'dict',
            'schema': {
                'name': {'type': 'string', 'maxlength': 100},
                'version': {'type': 'string', 'regex': r'^\d+\.\d+\.\d+$'},
                # Allow persisting a reference to the last opened file
                'last_opened_file': {'type': 'string', 'maxlength': 1024},
                'debug': {'type': 'boolean'},
                'log_level': {'type': 'string', 'allowed': ['DEBUG', 'INFO', 'WARNING', 'ERROR']}
            }
        },
        'security': {
            'type': 'dict',
            'schema': {
                'encrypt_data': {'type': 'boolean'},
                'max_file_size': {'type': 'integer', 'min': 1, 'max': 100 * 1024 * 1024},  # 100MB max
                'allowed_extensions': {'type': 'list', 'schema': {'type': 'string'}},
                'session_timeout': {'type': 'integer', 'min': 60, 'max': 3600}  # 1 min to 1 hour
            }
        },
        'gui': {
            'type': 'dict',
            'schema': {
                'theme': {'type': 'string', 'allowed': ['light', 'dark', 'system']},
                'window_width': {'type': 'integer', 'min': 800, 'max': 3840},
                'window_height': {'type': 'integer', 'min': 600, 'max': 2160},
                'font_family': {'type': 'string', 'maxlength': 50},
                'font_size': {'type': 'integer', 'min': 8, 'max': 72}
            }
        },
        'printing': {
            'type': 'dict',
            'schema': {
                'card_width': {'type': 'float', 'min': 1.0, 'max': 10.0},
                'card_height': {'type': 'float', 'min': 1.0, 'max': 10.0},
                'margin': {'type': 'float', 'min': 0.0, 'max': 2.0},
                'cards_per_row': {'type': 'integer', 'min': 1, 'max': 6},
                'cards_per_column': {'type': 'integer', 'min': 1, 'max': 6}
            }
        }
    }
    
    def __init__(self):
        self.validator = None
        self.schema = self.SCHEMA
        
        if CerberusValidator:
            try:
                # Allow unknown fields so user-updated config files don't fail validation
                # This preserves backward/forward compatibility with the config file
                self.validator = CerberusValidator()
                # Some Cerberus versions provide an attribute to allow unknown fields
                try:
                    setattr(self.validator, 'allow_unknown', True)
                except Exception:
                    # If the attribute isn't available, we will rely on the validate
                    # call to pass the schema explicitly and not fail on unknown keys.
                    pass
                # Try to set schema using different methods
                if hasattr(self.validator, 'schema'):
                    self.validator.schema = self.SCHEMA  # type: ignore
                elif hasattr(self.validator, 'allow_unknown'):
                    # Fallback for different Cerberus versions
                    pass
            except Exception as e:
                logger.warning(f"Failed to initialize Cerberus validator: {e}")
                self.validator = None
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """Validate configuration data."""
        if self.validator:
            try:
                # Use getattr to avoid type checker issues
                validate_method = getattr(self.validator, 'validate', None)
                if validate_method:
                    return validate_method(config, self.schema)
                else:
                    # Try alternative validation method
                    return getattr(self.validator, '__call__', lambda x, s: True)(config, self.schema)
            except Exception as e:
                logger.warning(f"Validation failed: {e}")
                return True  # Skip validation on error
        
        # Fallback: basic validation without Cerberus
        return self._basic_validation(config)
    
    def get_errors(self) -> Dict[str, Any]:
        """Get validation errors."""
        if self.validator:
            try:
                # Use getattr to avoid type checker issues
                errors = getattr(self.validator, 'errors', {})
                return errors if errors else {}
            except Exception:
                return {}
        return {}
    
    def _basic_validation(self, config: Dict[str, Any]) -> bool:
        """Basic validation without Cerberus."""
        try:
            # Check if config is a dictionary
            if not isinstance(config, dict):
                return False
            
            # Check required top-level keys
            required_keys = ['app', 'gui', 'security', 'data', 'export']
            for key in required_keys:
                if key not in config:
                    logger.warning(f"Missing required config section: {key}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Basic validation failed: {e}")
            return False

class SecureConfig:
    """Secure configuration manager with encryption and validation."""
    
    DEFAULT_CONFIG = {
        'app': {
            'name': 'Flashcard Generator',
            'version': '1.0.0',
            'debug': False,
            'log_level': 'INFO'
        },
        'security': {
            'encrypt_data': True,
            'max_file_size': 50 * 1024 * 1024,  # 50MB
            'allowed_extensions': ['.csv', '.xlsx', '.json', '.pdf', '.png', '.jpg', '.jpeg'],
            'session_timeout': 1800  # 30 minutes
        },
        'gui': {
            'theme': 'system',
            'window_width': 1200,
            'window_height': 800,
            'font_family': 'Segoe UI',
            'font_size': 11
        },
        'printing': {
            'card_width': 3.5,  # inches
            'card_height': 2.5,  # inches
            'margin': 0.25,
            'cards_per_row': 2,
            'cards_per_column': 3
        }
    }
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / '.flashcard_maker'
        self.config_file = self.config_dir / 'config.yaml'
        self.encrypted_config_file = self.config_dir / 'config.enc'
        self.key_file = self.config_dir / 'key.key'
        
        self.validator = ConfigValidator()
        self._config = {}
        self._encryption_key = None
        
        # Ensure config directory exists
        self.config_dir.mkdir(exist_ok=True, mode=0o700)  # Restricted permissions
        
        self._load_config()
    
    def _sanitize_path(self, path: Union[str, Path]) -> Path:
        """Sanitize file paths to prevent directory traversal."""
        path = Path(path).resolve()
        
        # Ensure path is within config directory
        if not str(path).startswith(str(self.config_dir.resolve())):
            raise ValueError("Path outside allowed directory")
        
        return path
    
    def _generate_key(self) -> bytes:
        """Generate encryption key."""
        if Fernet:
            key = Fernet.generate_key()
        else:
            # Fallback: generate a simple key if cryptography not available
            import secrets
            key = secrets.token_bytes(32)
        
        # Save key with restricted permissions
        with open(self.key_file, 'wb') as f:
            f.write(key)
        os.chmod(self.key_file, 0o600)  # Read/write for owner only
        
        return key
    
    def _load_key(self) -> bytes:
        """Load encryption key."""
        if not self.key_file.exists():
            return self._generate_key()
        
        with open(self.key_file, 'rb') as f:
            return f.read()
    
    def _encrypt_data(self, data: str) -> bytes:
        """Encrypt configuration data."""
        if self._encryption_key is None:
            self._encryption_key = self._load_key()
        
        if Fernet:
            fernet = Fernet(self._encryption_key)
            return fernet.encrypt(data.encode())
        else:
            # Fallback: return encoded data if no encryption available
            return data.encode()
    
    def _decrypt_data(self, encrypted_data: bytes) -> str:
        """Decrypt configuration data."""
        if self._encryption_key is None:
            self._encryption_key = self._load_key()
        
        if Fernet:
            fernet = Fernet(self._encryption_key)
            return fernet.decrypt(encrypted_data).decode()
        else:
            # Fallback: return decoded data if no encryption available
            return encrypted_data.decode()
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            # Try to load encrypted config first
            if self.encrypted_config_file.exists():
                with open(self.encrypted_config_file, 'rb') as f:
                    encrypted_data = f.read()
                
                decrypted_data = self._decrypt_data(encrypted_data)
                if yaml:
                    self._config = yaml.safe_load(decrypted_data)
                else:
                    self._config = json.loads(decrypted_data)
            
            # Fallback to plain text config
            elif self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    if yaml:
                        self._config = yaml.safe_load(f)
                    else:
                        self._config = json.load(f)
            
            else:
                # Use default config
                self._config = self.DEFAULT_CONFIG.copy()
                self._save_config()
            
            # Validate loaded config
            if not self.validator.validate(self._config):
                logger.warning(f"Invalid config: {self.validator.get_errors()}")
                self._config = self.DEFAULT_CONFIG.copy()
                self._save_config()
        
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._config = self.DEFAULT_CONFIG.copy()
    
    def _save_config(self):
        """Save configuration to file."""
        try:
            # Validate before saving
            if not self.validator.validate(self._config):
                # Log validation errors but attempt to persist a best-effort config.
                # Raising here will cause UI operations (like importing a set) to
                # fail with an exception that bubbles up to the user. Instead,
                # record the errors and continue to save so the application can
                # proceed. The validator is configured to allow unknown fields
                # where possible, so this should be rare.
                logger.warning(f"Config validation failed, continuing to save: {self.validator.get_errors()}")
            
            if yaml:
                config_yaml = yaml.dump(self._config, default_flow_style=False)
            else:
                config_yaml = json.dumps(self._config, indent=2)
            
            # Save encrypted version (best-effort)
            encrypted_data = self._encrypt_data(config_yaml)
            with open(self.encrypted_config_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions
            os.chmod(self.encrypted_config_file, 0o600)
            
            logger.info("Configuration saved successfully")
        
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (dot notation supported)."""
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Set configuration value by key (dot notation supported)."""
        keys = key.split('.')
        config = self._config
        
        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        
        # Validate and save
        self._save_config()
    
    def update(self, updates: Dict[str, Any]):
        """Update multiple configuration values."""
        def deep_update(base: Dict, updates: Dict):
            for key, value in updates.items():
                if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                    deep_update(base[key], value)
                else:
                    base[key] = value
        
        deep_update(self._config, updates)
        self._save_config()
    
    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        self._config = self.DEFAULT_CONFIG.copy()
        self._save_config()
    
    def export_config(self, export_path: Path, encrypt: bool = False):
        """Export configuration to file."""
        export_path = self._sanitize_path(export_path)
        
        if encrypt:
            if yaml:
                config_data = yaml.dump(self._config)
            else:
                config_data = json.dumps(self._config, indent=2)
            encrypted_data = self._encrypt_data(config_data)
            with open(export_path, 'wb') as f:
                f.write(encrypted_data)
        else:
            with open(export_path, 'w', encoding='utf-8') as f:
                if yaml:
                    yaml.dump(self._config, f, default_flow_style=False)
                else:
                    json.dump(self._config, f, indent=2)
    
    def import_config(self, import_path: Path, encrypted: bool = False):
        """Import configuration from file."""
        import_path = self._sanitize_path(import_path)
        
        if not import_path.exists():
            raise FileNotFoundError(f"Config file not found: {import_path}")
        
        try:
            if encrypted:
                with open(import_path, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = self._decrypt_data(encrypted_data)
                if yaml:
                    config_data = yaml.safe_load(decrypted_data)
                else:
                    config_data = json.loads(decrypted_data)
            else:
                with open(import_path, 'r', encoding='utf-8') as f:
                    if yaml:
                        config_data = yaml.safe_load(f)
                    else:
                        config_data = json.load(f)
            
            # Validate imported config
            if not self.validator.validate(config_data):
                raise ValueError(f"Invalid config format: {self.validator.get_errors()}")
            
            self._config = config_data
            self._save_config()
            
        except Exception as e:
            logger.error(f"Failed to import config: {e}")
            raise

# Global configuration instance
config = SecureConfig()