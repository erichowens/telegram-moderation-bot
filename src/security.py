"""
Security utilities for token encryption and validation.
"""

import os
import re
import logging
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
from cryptography.fernet import Fernet
import base64
import json

logger = logging.getLogger(__name__)


class TokenManager:
    """Secure token management with encryption."""
    
    def __init__(self):
        self.key_file = Path.home() / ".telegram_bot" / "key.dat"
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
        self.cipher = self._get_or_create_cipher()
    
    def _get_or_create_cipher(self) -> Fernet:
        """Get existing cipher or create new one."""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions (Unix-like systems)
            if os.name != 'nt':
                os.chmod(self.key_file, 0o600)
        return Fernet(key)
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt a token for storage."""
        if not token:
            raise ValueError("Token cannot be empty")
        return self.cipher.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt a stored token."""
        try:
            return self.cipher.decrypt(encrypted_token.encode()).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt token: {e}")
            raise ValueError("Invalid or corrupted token")
    
    def secure_config_load(self, config_path: Path) -> Dict[str, Any]:
        """Load config with encrypted token support."""
        if not config_path.exists():
            return {}
        
        with open(config_path, 'r') as f:
            config = json.load(f) if config_path.suffix == '.json' else {}
        
        # Check for encrypted token
        if 'telegram' in config and 'encrypted_token' in config['telegram']:
            config['telegram']['token'] = self.decrypt_token(
                config['telegram']['encrypted_token']
            )
            del config['telegram']['encrypted_token']
        
        return config
    
    def secure_config_save(self, config: Dict[str, Any], config_path: Path) -> None:
        """Save config with encrypted token."""
        if 'telegram' in config and 'token' in config['telegram']:
            token = config['telegram']['token']
            config['telegram']['encrypted_token'] = self.encrypt_token(token)
            del config['telegram']['token']
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)


class InputValidator:
    """Validate and sanitize user inputs to prevent attacks."""
    
    # Limits based on Telegram's restrictions
    MAX_MESSAGE_SIZE = 4096  # Telegram text message limit
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_REGEX_LENGTH = 100
    REGEX_TIMEOUT = 2.0  # seconds
    
    @staticmethod
    def validate_message_size(message: str) -> bool:
        """Check if message is within Telegram limits."""
        if not message:
            return True
        return len(message.encode('utf-8')) <= InputValidator.MAX_MESSAGE_SIZE
    
    @staticmethod
    def validate_image_size(image_data: bytes) -> bool:
        """Check if image is within size limits."""
        return len(image_data) <= InputValidator.MAX_IMAGE_SIZE
    
    @staticmethod
    def validate_video_size(video_data: bytes) -> bool:
        """Check if video is within size limits."""
        return len(video_data) <= InputValidator.MAX_VIDEO_SIZE
    
    @staticmethod
    def validate_regex_pattern(pattern: str) -> bool:
        """
        Validate regex pattern to prevent ReDoS attacks.
        
        Checks for:
        - Pattern length
        - Nested quantifiers that could cause exponential backtracking
        - Invalid regex syntax
        """
        if not pattern or len(pattern) > InputValidator.MAX_REGEX_LENGTH:
            return False
        
        # Dangerous patterns that could cause ReDoS
        dangerous_patterns = [
            r'\(\.\*\)\+',  # (.*)+ 
            r'\(\.\+\)\+',  # (.+)+
            r'\([^)]*\*\)\+',  # (x*)+
            r'\([^)]*\+\)\+',  # (x+)+
            r'\*\{.*,.*\}\*',  # *{n,m}*
            r'\+\{.*,.*\}\+',  # +{n,m}+
        ]
        
        for dangerous in dangerous_patterns:
            if re.search(dangerous, pattern):
                logger.warning(f"Potentially dangerous regex pattern detected: {pattern}")
                return False
        
        # Try to compile the pattern
        try:
            re.compile(pattern)
            return True
        except re.error as e:
            logger.error(f"Invalid regex pattern: {pattern}, error: {e}")
            return False
    
    @staticmethod
    def sanitize_path(file_path: str, base_dir: Path) -> Optional[Path]:
        """
        Sanitize file path to prevent directory traversal attacks.
        
        Returns sanitized path if valid, None otherwise.
        """
        try:
            # Check for obvious traversal attempts
            if '..' in file_path or file_path.startswith('/') or '\\' in file_path:
                logger.warning(f"Path traversal attempt detected: {file_path}")
                return None
            
            # Build the full path
            requested_path = (base_dir / file_path).resolve()
            base = base_dir.resolve()
            
            # Check if path is within base directory
            try:
                requested_path.relative_to(base)
                return requested_path
            except ValueError:
                # Path is outside base directory
                logger.warning(f"Path traversal attempt detected: {file_path}")
                return None
        except Exception as e:
            logger.error(f"Invalid path: {file_path}, error: {e}")
            return None


class RateLimiter:
    """Rate limiting for message processing."""
    
    def __init__(self, max_messages_per_second: int = 10, burst_size: int = 20):
        """
        Initialize rate limiter.
        
        Args:
            max_messages_per_second: Sustained rate limit
            burst_size: Maximum burst size allowed
        """
        self.max_rate = max_messages_per_second
        self.burst_size = burst_size
        self.semaphore = asyncio.Semaphore(burst_size)
        self.refill_rate = 1.0 / max_messages_per_second
        self.last_refill = 0  # Will be set on first acquire
        self.tokens = float(burst_size)
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """
        Try to acquire permission to process a message.
        
        Returns:
            True if permitted, False if rate limited
        """
        async with self._lock:
            loop = asyncio.get_event_loop()
            now = loop.time()
            
            # Initialize last_refill on first call
            if self.last_refill == 0:
                self.last_refill = now
            
            # Refill tokens based on time elapsed
            time_passed = now - self.last_refill
            self.tokens = min(
                self.burst_size,
                self.tokens + time_passed / self.refill_rate
            )
            self.last_refill = now
            
            # Check if we have tokens available
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False
    
    async def __aenter__(self):
        """Context manager entry."""
        success = await self.acquire()
        if not success:
            raise RuntimeError("Rate limit exceeded")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass