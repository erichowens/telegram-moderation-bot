"""
Test security features and improvements.
"""

import pytest
import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.security import TokenManager, InputValidator, RateLimiter


class TestTokenManager:
    """Test token encryption and management."""
    
    @pytest.fixture
    def token_manager(self):
        """Create a token manager with temp directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = TokenManager()
            manager.key_file = Path(tmpdir) / "key.dat"
            manager.cipher = manager._get_or_create_cipher()
            yield manager
    
    def test_token_encryption_decryption(self, token_manager):
        """Test that tokens can be encrypted and decrypted."""
        original_token = "5678901234:ABCdefGHIjklMNOpqrSTUvwxYZ123456789"
        
        # Encrypt token
        encrypted = token_manager.encrypt_token(original_token)
        assert encrypted != original_token
        assert len(encrypted) > 0
        
        # Decrypt token
        decrypted = token_manager.decrypt_token(encrypted)
        assert decrypted == original_token
    
    def test_empty_token_raises_error(self, token_manager):
        """Test that empty token raises ValueError."""
        with pytest.raises(ValueError, match="Token cannot be empty"):
            token_manager.encrypt_token("")
    
    def test_invalid_encrypted_token(self, token_manager):
        """Test that invalid encrypted token raises error."""
        with pytest.raises(ValueError, match="Invalid or corrupted token"):
            token_manager.decrypt_token("invalid_encrypted_data")
    
    def test_secure_config_save_and_load(self, token_manager):
        """Test saving and loading config with encrypted token."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            
            # Save config with token
            config = {
                "telegram": {
                    "token": "test_token_12345"
                },
                "other": "data"
            }
            token_manager.secure_config_save(config, config_path)
            
            # Verify token was encrypted in saved file
            import json
            with open(config_path, 'r') as f:
                saved_config = json.load(f)
            assert 'encrypted_token' in saved_config['telegram']
            assert 'token' not in saved_config['telegram']
            
            # Load config and verify token is decrypted
            loaded_config = token_manager.secure_config_load(config_path)
            assert loaded_config['telegram']['token'] == "test_token_12345"
            assert 'encrypted_token' not in loaded_config['telegram']


class TestInputValidator:
    """Test input validation for security."""
    
    def test_message_size_validation(self):
        """Test message size validation."""
        validator = InputValidator()
        
        # Valid message
        assert validator.validate_message_size("Hello world!")
        
        # Empty message
        assert validator.validate_message_size("")
        
        # Message at limit
        message_at_limit = "x" * 4096
        assert validator.validate_message_size(message_at_limit)
        
        # Message over limit
        message_over_limit = "x" * 4097
        assert not validator.validate_message_size(message_over_limit)
    
    def test_image_size_validation(self):
        """Test image size validation."""
        validator = InputValidator()
        
        # Valid image size (1MB)
        assert validator.validate_image_size(b"x" * (1024 * 1024))
        
        # Image at limit (10MB)
        assert validator.validate_image_size(b"x" * (10 * 1024 * 1024))
        
        # Image over limit
        assert not validator.validate_image_size(b"x" * (11 * 1024 * 1024))
    
    def test_regex_pattern_validation(self):
        """Test regex pattern validation to prevent ReDoS."""
        validator = InputValidator()
        
        # Valid patterns
        assert validator.validate_regex_pattern(r"hello.*world")
        assert validator.validate_regex_pattern(r"\d{3}-\d{4}")
        assert validator.validate_regex_pattern(r"[a-zA-Z]+")
        
        # Invalid patterns (ReDoS vulnerable)
        assert not validator.validate_regex_pattern(r"(.*)+")
        assert not validator.validate_regex_pattern(r"(.+)+")
        assert not validator.validate_regex_pattern(r"(x*)+")
        assert not validator.validate_regex_pattern(r"(x+)+")
        
        # Too long pattern
        assert not validator.validate_regex_pattern("x" * 101)
        
        # Invalid regex syntax
        assert not validator.validate_regex_pattern(r"[unclosed")
    
    def test_path_sanitization(self):
        """Test path sanitization to prevent directory traversal."""
        validator = InputValidator()
        base_dir = Path("/app/data")
        
        # Valid paths
        assert validator.sanitize_path("config.json", base_dir) == base_dir / "config.json"
        assert validator.sanitize_path("subdir/file.txt", base_dir) == base_dir / "subdir/file.txt"
        
        # Directory traversal attempts
        assert validator.sanitize_path("../../../etc/passwd", base_dir) is None
        assert validator.sanitize_path("..\\..\\windows\\system32", base_dir) is None
        
        # Absolute path outside base
        assert validator.sanitize_path("/etc/passwd", base_dir) is None


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limiting_allows_normal_traffic(self):
        """Test that rate limiter allows normal traffic."""
        limiter = RateLimiter(max_messages_per_second=5, burst_size=10)
        
        # Should allow first 10 messages (burst size)
        for i in range(10):
            assert await limiter.acquire()
    
    @pytest.mark.asyncio
    async def test_rate_limiting_blocks_excessive_traffic(self):
        """Test that rate limiter blocks excessive traffic."""
        limiter = RateLimiter(max_messages_per_second=5, burst_size=5)
        
        # Consume burst capacity
        for i in range(5):
            assert await limiter.acquire()
        
        # Next message should be rate limited
        assert not await limiter.acquire()
    
    @pytest.mark.asyncio
    async def test_rate_limiter_context_manager(self):
        """Test rate limiter as context manager."""
        limiter = RateLimiter(max_messages_per_second=10, burst_size=2)
        
        # Should work for first messages
        async with limiter:
            pass
        
        async with limiter:
            pass
        
        # Should raise when limit exceeded
        with pytest.raises(RuntimeError, match="Rate limit exceeded"):
            async with limiter:
                pass
    
    @pytest.mark.asyncio
    async def test_token_refill(self):
        """Test that tokens refill over time."""
        limiter = RateLimiter(max_messages_per_second=10, burst_size=2)
        
        # Consume all tokens
        assert await limiter.acquire()
        assert await limiter.acquire()
        assert not await limiter.acquire()
        
        # Wait for token refill
        await asyncio.sleep(0.15)  # Wait for ~1 token to refill
        
        # Should be able to acquire again
        assert await limiter.acquire()


class TestModerationThresholds:
    """Test that magic numbers are replaced with constants."""
    
    def test_threshold_constants_exist(self):
        """Test that threshold constants are defined."""
        from src.moderation import ModerationThresholds
        
        assert hasattr(ModerationThresholds, 'TOXICITY_THRESHOLD')
        assert hasattr(ModerationThresholds, 'SPAM_THRESHOLD')
        assert hasattr(ModerationThresholds, 'HARASSMENT_THRESHOLD')
        assert hasattr(ModerationThresholds, 'CAPS_RATIO_THRESHOLD')
        assert hasattr(ModerationThresholds, 'CONFIDENCE_BASE')
        assert hasattr(ModerationThresholds, 'CONFIDENCE_SCALE')
        assert hasattr(ModerationThresholds, 'MAX_CONFIDENCE')
        
        # Verify values are sensible
        assert 0 < ModerationThresholds.TOXICITY_THRESHOLD <= 1
        assert 0 < ModerationThresholds.SPAM_THRESHOLD <= 1
        assert 0 < ModerationThresholds.HARASSMENT_THRESHOLD <= 1
        assert 0 < ModerationThresholds.CAPS_RATIO_THRESHOLD <= 1


class TestHealthCheck:
    """Test health check functionality."""
    
    @pytest.mark.asyncio
    async def test_health_check_returns_status(self):
        """Test that health check returns proper status."""
        from src.bot import TelegramModerationBot
        
        with patch('src.bot.Application'), \
             patch('src.bot.Config'), \
             patch('src.bot.ContentModerator'):
            
            bot = TelegramModerationBot("test_token")
            
            # Mock bot.get_me()
            mock_bot_info = Mock()
            mock_bot_info.username = "test_bot"
            bot.application.bot = Mock()
            async def mock_get_me():
                return mock_bot_info
            bot.application.bot.get_me = mock_get_me
            
            health = await bot.health_check()
            
            assert health['status'] in ['healthy', 'degraded', 'unhealthy']
            assert 'uptime_seconds' in health
            assert 'bot_info' in health
            assert 'moderator' in health
            assert 'statistics' in health
            assert 'timestamp' in health
    
    @pytest.mark.asyncio
    async def test_health_check_handles_errors(self):
        """Test that health check handles errors gracefully."""
        from src.bot import TelegramModerationBot
        
        with patch('src.bot.Application'), \
             patch('src.bot.Config'), \
             patch('src.bot.ContentModerator'):
            
            bot = TelegramModerationBot("test_token")
            
            # Mock bot.get_me() to raise error
            bot.application.bot = Mock()
            async def mock_get_me_error():
                raise Exception("Connection error")
            bot.application.bot.get_me = mock_get_me_error
            
            health = await bot.health_check()
            
            # Should still return a response even with errors
            assert health['status'] in ['degraded', 'unhealthy']
            assert 'timestamp' in health


class TestResourceCleanup:
    """Test resource cleanup functionality."""
    
    def test_moderator_cleanup(self):
        """Test that moderator cleanup is called."""
        from src.bot import TelegramModerationBot
        
        with patch('src.bot.Application'), \
             patch('src.bot.Config'), \
             patch('src.bot.ContentModerator') as mock_moderator_class:
            
            mock_moderator = Mock()
            mock_moderator_class.return_value = mock_moderator
            
            bot = TelegramModerationBot("test_token")
            bot.stop()
            
            # Verify cleanup was called
            mock_moderator.cleanup.assert_called_once()
    
    def test_moderator_context_manager(self):
        """Test moderator context manager for resource cleanup."""
        from src.moderation import ContentModerator
        
        with patch('src.moderation.HAS_TRANSFORMERS', False):
            config = {}
            
            with ContentModerator(config) as moderator:
                assert not moderator._closed
            
            # After exiting context, should be closed
            assert moderator._closed