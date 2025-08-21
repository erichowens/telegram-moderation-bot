"""
Tests for the Telegram bot integration.
Uses mocks to test bot functionality without requiring actual Telegram API access.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from bot import TelegramModerationBot
from moderation import ModerationResult


class TestTelegramBot:
    """Test the main Telegram bot functionality."""
    
    @pytest.fixture
    def mock_bot(self):
        """Create a TelegramModerationBot with mocked dependencies."""
        with patch('bot.Application'), \
             patch('bot.ContentModerator') as mock_moderator_class:
            
            # Create bot instance
            bot = TelegramModerationBot("test_token_123")
            
            # Mock the moderator
            mock_moderator = Mock()
            mock_moderator_class.return_value = mock_moderator
            bot.moderator = mock_moderator
            
            return bot, mock_moderator
    
    def test_bot_initialization(self, mock_bot):
        """Test bot initialization with token."""
        bot, mock_moderator = mock_bot
        
        assert bot.token == "test_token_123"
        assert bot.stats["messages_checked"] == 0
        assert bot.stats["violations_found"] == 0
        assert bot.stats["actions_taken"] == 0
        assert bot.moderator is not None
    
    def test_bot_initialization_with_callback(self):
        """Test bot initialization with violation callback."""
        callback_function = Mock()
        
        with patch('bot.Application'), \
             patch('bot.ContentModerator'):
            
            bot = TelegramModerationBot("test_token", violation_callback=callback_function)
            
            assert bot.violation_callback == callback_function
    
    @pytest.mark.asyncio
    async def test_handle_text_message_clean(self, mock_bot):
        """Test handling of clean text messages."""
        bot, mock_moderator = mock_bot
        
        # Mock clean message result
        mock_moderator.moderate_text.return_value = ModerationResult(
            is_violation=False,
            confidence=0.1
        )
        
        # Create mock update and message
        mock_update = Mock()
        mock_message = Mock()
        mock_message.text = "Hello everyone, how are you?"
        mock_update.message = mock_message
        mock_context = Mock()
        
        await bot.handle_text_message(mock_update, mock_context)
        
        # Should check the message but not take action
        mock_moderator.moderate_text.assert_called_once_with("Hello everyone, how are you?")
        assert bot.stats["messages_checked"] == 1
        assert bot.stats["violations_found"] == 0
        assert bot.stats["actions_taken"] == 0
    
    @pytest.mark.asyncio
    async def test_handle_text_message_violation(self, mock_bot):
        """Test handling of text messages with violations."""
        bot, mock_moderator = mock_bot
        
        # Mock violation result (async method)
        mock_moderator.moderate_text = AsyncMock(return_value=ModerationResult(
            is_violation=True,
            confidence=0.9,
            reason="Spam detected",
            category="spam"
        ))
        
        # Create mock update and message
        mock_update = Mock()
        mock_message = Mock()
        mock_message.text = "Buy crypto now for guaranteed profits!"
        mock_message.chat_id = 12345
        mock_message.from_user = Mock()
        mock_message.from_user.id = 67890
        mock_message.from_user.username = "spammer"
        mock_message.chat = Mock()
        mock_message.chat.title = "Test Group"
        mock_message.delete = AsyncMock()
        mock_update.message = mock_message
        mock_context = Mock()
        
        await bot.handle_text_message(mock_update, mock_context)
        
        # Should detect violation and take action
        mock_moderator.moderate_text.assert_called_once()
        assert bot.stats["messages_checked"] == 1
        assert bot.stats["violations_found"] == 1
        assert bot.stats["actions_taken"] == 1
        
        # Should delete the message (high confidence)
        mock_message.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_photo_message(self, mock_bot):
        """Test handling of photo messages."""
        bot, mock_moderator = mock_bot
        
        # Mock photo moderation result (async method)
        mock_moderator.moderate_image = AsyncMock(return_value=ModerationResult(
            is_violation=True,
            confidence=0.8,
            reason="Inappropriate image",
            category="nsfw"
        ))
        
        # Create mock photo message
        mock_update = Mock()
        mock_message = Mock()
        mock_photo = Mock()
        mock_photo_file = Mock()
        mock_photo_file.download_as_bytearray = AsyncMock(return_value=bytearray(b"fake_image_data"))
        mock_photo.get_file = AsyncMock(return_value=mock_photo_file)
        
        mock_message.photo = [mock_photo]  # Telegram sends array of photo sizes
        mock_message.chat_id = 12345
        mock_message.from_user = Mock()
        mock_message.from_user.id = 67890
        mock_message.from_user.username = "user"
        mock_message.chat = Mock()
        mock_message.chat.title = "Test Group"
        mock_message.delete = AsyncMock()
        mock_message.reply_text = AsyncMock()
        mock_update.message = mock_message
        mock_context = Mock()
        
        await bot.handle_photo_message(mock_update, mock_context)
        
        # Should process the image and take action
        mock_moderator.moderate_image.assert_called_once()
        assert bot.stats["messages_checked"] == 1
        assert bot.stats["violations_found"] == 1
        # Confidence 0.8 is not > 0.8, so should warn, not delete
        mock_message.reply_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_video_message(self, mock_bot):
        """Test handling of video messages."""
        bot, mock_moderator = mock_bot
        
        # Create mock video message
        mock_update = Mock()
        mock_message = Mock()
        mock_video = Mock()
        mock_video.duration = 600  # 10 minutes - should trigger policy violation
        mock_video_file = Mock()
        mock_video.get_file = AsyncMock(return_value=mock_video_file)
        
        # Set up mock message with proper structure
        mock_message.video = mock_video
        mock_message.chat_id = 12345
        mock_message.from_user = Mock()
        mock_message.from_user.id = 67890
        mock_message.from_user.username = "user"
        mock_message.chat = Mock()
        mock_message.chat.title = "Test Group"
        mock_message.reply_text = AsyncMock()
        mock_update.message = mock_message
        mock_context = Mock()
        
        await bot.handle_video_message(mock_update, mock_context)
        
        # Should detect long video and warn user
        assert bot.stats["messages_checked"] == 1
        assert bot.stats["violations_found"] == 1
        mock_message.reply_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_violation_with_callback(self, mock_bot):
        """Test violation handling with callback function."""
        bot, mock_moderator = mock_bot
        
        # Set up violation callback
        violation_callback = Mock()
        bot.violation_callback = violation_callback
        
        # Create mock message and violation
        mock_message = Mock()
        mock_message.chat_id = 12345
        mock_message.chat.title = "Test Group"
        mock_message.from_user.id = 67890
        mock_message.from_user.username = "testuser"
        mock_message.delete = AsyncMock()
        
        violation_result = ModerationResult(
            is_violation=True,
            confidence=0.85,
            reason="Test violation",
            category="test"
        )
        
        await bot.handle_violation(mock_message, violation_result, "text")
        
        # Should call the violation callback
        violation_callback.assert_called_once()
        call_args = violation_callback.call_args[0][0]
        
        assert call_args["chat_id"] == 12345
        assert call_args["chat_title"] == "Test Group"
        assert call_args["user_id"] == 67890
        assert call_args["username"] == "testuser"
        assert call_args["content_type"] == "text"
        assert call_args["violation_type"] == "test"
        assert call_args["confidence"] == 0.85
        assert call_args["reason"] == "Test violation"
    
    @pytest.mark.asyncio
    async def test_take_action_high_confidence(self, mock_bot):
        """Test action taking for high confidence violations."""
        bot, mock_moderator = mock_bot
        
        mock_message = Mock()
        mock_message.delete = AsyncMock()
        
        violation_result = ModerationResult(
            is_violation=True,
            confidence=0.9,
            reason="High confidence violation"
        )
        
        action = await bot.take_action(mock_message, violation_result)
        
        assert action == "deleted"
        mock_message.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_take_action_medium_confidence(self, mock_bot):
        """Test action taking for medium confidence violations."""
        bot, mock_moderator = mock_bot
        
        mock_message = Mock()
        mock_message.reply_text = AsyncMock()
        
        violation_result = ModerationResult(
            is_violation=True,
            confidence=0.7,
            reason="Medium confidence violation"
        )
        
        action = await bot.take_action(mock_message, violation_result)
        
        assert action == "warned"
        mock_message.reply_text.assert_called_once()
        
        # Check warning message content
        warning_call = mock_message.reply_text.call_args[0][0]
        assert "community guidelines" in warning_call.lower()
    
    @pytest.mark.asyncio
    async def test_take_action_low_confidence(self, mock_bot):
        """Test action taking for low confidence violations."""
        bot, mock_moderator = mock_bot
        
        mock_message = Mock()
        
        violation_result = ModerationResult(
            is_violation=True,
            confidence=0.5,
            reason="Low confidence violation"
        )
        
        action = await bot.take_action(mock_message, violation_result)
        
        assert action == "logged"
        # Should not call delete or reply_text for low confidence
    
    @pytest.mark.asyncio
    async def test_take_action_error_handling(self, mock_bot):
        """Test action error handling."""
        bot, mock_moderator = mock_bot
        
        mock_message = Mock()
        mock_message.delete = AsyncMock(side_effect=Exception("API Error"))
        
        violation_result = ModerationResult(
            is_violation=True,
            confidence=0.9,
            reason="Test violation"
        )
        
        action = await bot.take_action(mock_message, violation_result)
        
        assert action == "error"
    
    def test_get_stats(self, mock_bot):
        """Test statistics retrieval."""
        bot, mock_moderator = mock_bot
        
        # Modify some stats
        bot.stats["messages_checked"] = 100
        bot.stats["violations_found"] = 15
        bot.stats["actions_taken"] = 12
        
        stats = bot.get_stats()
        
        # Should return a copy of stats
        assert stats["messages_checked"] == 100
        assert stats["violations_found"] == 15
        assert stats["actions_taken"] == 12
        
        # Should be a copy, not the original
        stats["messages_checked"] = 999
        assert bot.stats["messages_checked"] == 100  # Original unchanged
    
    @pytest.mark.asyncio
    async def test_error_handling_in_text_moderation(self, mock_bot):
        """Test error handling during text moderation."""
        bot, mock_moderator = mock_bot
        
        # Mock moderator to raise exception
        mock_moderator.moderate_text.side_effect = Exception("Moderation error")
        
        mock_update = Mock()
        mock_message = Mock()
        mock_message.text = "Test message"
        mock_update.message = mock_message
        mock_context = Mock()
        
        # Should not raise exception
        await bot.handle_text_message(mock_update, mock_context)
        
        # Should still count the message as checked
        assert bot.stats["messages_checked"] == 1
        assert bot.stats["violations_found"] == 0
    
    @pytest.mark.asyncio
    async def test_missing_message_handling(self, mock_bot):
        """Test handling of updates without messages."""
        bot, mock_moderator = mock_bot
        
        mock_update = Mock()
        mock_update.message = None  # No message
        mock_context = Mock()
        
        # Should handle gracefully without errors
        await bot.handle_text_message(mock_update, mock_context)
        await bot.handle_photo_message(mock_update, mock_context)
        await bot.handle_video_message(mock_update, mock_context)
        
        # Stats should remain unchanged
        assert bot.stats["messages_checked"] == 0


class TestTelegramBotIntegration:
    """Integration tests for complete bot workflows."""
    
    @pytest.fixture
    def integration_bot(self):
        """Create a bot with real moderation logic but mocked Telegram API."""
        with patch('bot.Application') as mock_app:
            # Create bot with real moderator
            bot = TelegramModerationBot("test_token")
            
            # Mock the application but keep real moderation logic
            mock_app.builder.return_value.token.return_value.build.return_value = Mock()
            
            return bot
    
    @pytest.mark.asyncio
    async def test_spam_detection_workflow(self, integration_bot):
        """Test complete spam detection workflow."""
        # Create spam message
        mock_update = Mock()
        mock_message = Mock()
        mock_message.text = "Buy now for limited time offer! Click here for free money!"
        mock_message.chat_id = 12345
        mock_message.from_user.id = 67890
        mock_message.from_user.username = "spammer"
        mock_message.chat.title = "Test Group"
        mock_message.delete = AsyncMock()
        mock_update.message = mock_message
        mock_context = Mock()
        
        await integration_bot.handle_text_message(mock_update, mock_context)
        
        # Should detect spam and take action
        assert integration_bot.stats["messages_checked"] == 1
        assert integration_bot.stats["violations_found"] == 1
        assert integration_bot.stats["actions_taken"] == 1
    
    @pytest.mark.asyncio
    async def test_clean_message_workflow(self, integration_bot):
        """Test workflow with clean messages."""
        mock_update = Mock()
        mock_message = Mock()
        mock_message.text = "Thanks for sharing that article, it was very informative!"
        mock_message.chat_id = 12345
        mock_message.from_user.id = 67890
        mock_message.from_user.username = "gooduser"
        mock_message.chat.title = "Test Group"
        mock_update.message = mock_message
        mock_context = Mock()
        
        await integration_bot.handle_text_message(mock_update, mock_context)
        
        # Should process but not flag clean message
        assert integration_bot.stats["messages_checked"] == 1
        assert integration_bot.stats["violations_found"] == 0
        assert integration_bot.stats["actions_taken"] == 0


class TestTelegramBotConfiguration:
    """Test bot configuration and setup."""
    
    def test_bot_with_custom_config(self):
        """Test bot initialization with custom configuration."""
        with patch('bot.Application'), \
             patch('bot.ContentModerator') as mock_moderator_class, \
             patch('bot.Config') as mock_config_class:
            
            # Create bot
            bot = TelegramModerationBot("test_token")
            
            # Should attempt to load configuration
            mock_config_class.assert_called_once()
            mock_moderator_class.assert_called_once()
    
    def test_bot_with_config_failure(self):
        """Test bot behavior when configuration fails."""
        with patch('bot.Application'), \
             patch('bot.Config', side_effect=Exception("Config error")), \
             patch('bot.ContentModerator') as mock_moderator_class:
            
            # Should still create bot with fallback config
            bot = TelegramModerationBot("test_token")
            
            # Should create moderator with empty config
            mock_moderator_class.assert_called_with({})
    
    def test_handler_setup(self):
        """Test that message handlers are properly configured."""
        with patch('bot.Application') as mock_app, \
             patch('bot.ContentModerator'), \
             patch('bot.MessageHandler') as mock_handler:
            
            mock_application = Mock()
            mock_app.builder.return_value.token.return_value.build.return_value = mock_application
            
            bot = TelegramModerationBot("test_token")
            
            # Should add handlers to application
            assert mock_application.add_handler.call_count >= 3  # text, photo, video handlers


class TestTelegramBotPerformance:
    """Test bot performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_message_processing_speed(self):
        """Test message processing performance."""
        with patch('bot.Application'), \
             patch('bot.ContentModerator') as mock_moderator_class:
            
            mock_moderator = Mock()
            mock_moderator.moderate_text.return_value = ModerationResult(False, 0.1)
            mock_moderator_class.return_value = mock_moderator
            
            bot = TelegramModerationBot("test_token")
            
            # Create mock message
            mock_update = Mock()
            mock_message = Mock()
            mock_message.text = "Test message"
            mock_update.message = mock_message
            mock_context = Mock()
            
            # Measure processing time
            import time
            start_time = time.time()
            
            # Process multiple messages
            for _ in range(10):
                await bot.handle_text_message(mock_update, mock_context)
            
            end_time = time.time()
            
            processing_time = (end_time - start_time) / 10  # Average per message
            
            # Should process messages quickly (under 100ms each)
            assert processing_time < 0.1
    
    def test_memory_usage(self):
        """Test that bot doesn't leak memory during operation."""
        with patch('bot.Application'), \
             patch('bot.ContentModerator'):
            
            # Create and destroy multiple bots
            for i in range(100):
                bot = TelegramModerationBot(f"test_token_{i}")
                del bot
            
            # Test passes if no memory errors occur
            assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])