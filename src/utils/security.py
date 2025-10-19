"""
Secure Logging Configuration
============================

Provides secure logging with sanitization and structured output.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import re
import json
from datetime import datetime

class SanitizedFormatter(logging.Formatter):
    """Custom formatter that sanitizes sensitive data from log messages."""
    
    # Patterns to sanitize
    SENSITIVE_PATTERNS = [
        (r'password[=:]\s*["\']?([^"\'\s]+)["\']?', r'password=***'),
        (r'token[=:]\s*["\']?([^"\'\s]+)["\']?', r'token=***'),
        (r'key[=:]\s*["\']?([^"\'\s]+)["\']?', r'key=***'),
        (r'secret[=:]\s*["\']?([^"\'\s]+)["\']?', r'secret=***'),
        (r'(\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4})', r'****-****-****-****'),  # Credit cards
        (r'(\d{3}-\d{2}-\d{4})', r'***-**-****'),  # SSN
    ]
    
    def format(self, record):
        """Format log record with sanitization."""
        # Get the original formatted message
        formatted = super().format(record)
        
        # Apply sanitization patterns
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            formatted = re.sub(pattern, replacement, formatted, flags=re.IGNORECASE)
        
        return formatted

class StructuredLogger:
    """Structured logger with security features."""
    
    def __init__(self, name: str, log_dir: Optional[Path] = None):
        self.name = name
        self.log_dir = log_dir or Path.home() / '.flashcard_maker' / 'logs'
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up logging handlers."""
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # File handler with rotation
        log_file = self.log_dir / f"{self.name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Error file handler
        error_file = self.log_dir / f"{self.name}_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        # Set formatters
        formatter = SanitizedFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        
        # Set restrictive permissions on log files
        try:
            os.chmod(log_file, 0o600)
            os.chmod(error_file, 0o600)
        except OSError:
            pass  # Permissions may not be supported on all systems
    
    def _sanitize_extra(self, extra: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize extra data for logging."""
        if not extra:
            return {}
        
        sanitized = {}
        for key, value in extra.items():
            if isinstance(value, str):
                # Apply sanitization patterns
                for pattern, replacement in SanitizedFormatter.SENSITIVE_PATTERNS:
                    value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
            sanitized[key] = value
        
        return sanitized
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        extra = self._sanitize_extra(kwargs)
        self.logger.debug(message, extra=extra)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        extra = self._sanitize_extra(kwargs)
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        extra = self._sanitize_extra(kwargs)
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message."""
        extra = self._sanitize_extra(kwargs)
        if exception:
            self.logger.error(f"{message}: {str(exception)}", extra=extra, exc_info=True)
        else:
            self.logger.error(message, extra=extra)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log critical message."""
        extra = self._sanitize_extra(kwargs)
        if exception:
            self.logger.critical(f"{message}: {str(exception)}", extra=extra, exc_info=True)
        else:
            self.logger.critical(message, extra=extra)
    
    def audit(self, action: str, user: str = "system", **kwargs):
        """Log audit events."""
        audit_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'user': user,
            **self._sanitize_extra(kwargs)
        }
        self.logger.info(f"AUDIT: {json.dumps(audit_data)}")

# Global logger instance
logger = StructuredLogger('flashcard_app')