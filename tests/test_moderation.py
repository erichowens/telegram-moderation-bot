"""
Unit tests for the content moderation module.
Tests the core moderation logic without external dependencies.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from moderation import ContentModerator, ModerationResult


class TestContentModerator:
    """Test the core ContentModerator functionality."""
    
    @pytest.fixture
    def moderator(self):
        """Create a ContentModerator instance for testing."""
        config = {
            'max_video_size': 50 * 1024 * 1024,  # 50MB for testing
            'test_mode': True
        }
        return ContentModerator(config)
    
    @pytest.fixture
    def moderator_with_mocked_models(self):
        """Create a ContentModerator with mocked AI models."""
        config = {'test_mode': True}
        moderator = ContentModerator(config)
        
        # Mock AI model
        mock_model = Mock()
        mock_model.return_value = [{'label': 'TOXIC', 'score': 0.85}]
        moderator.models['toxicity'] = mock_model
        
        return moderator
    
    # Test basic rule-based moderation
    
    @pytest.mark.asyncio
    async def test_spam_detection_keywords(self, moderator):
        """Test spam detection using keywords."""
        spam_messages = [
            "Buy now for limited time only!",
            "Make money fast with this trick",
            "Click here for free money",
            "Join now and earn $$$"
        ]
        
        for message in spam_messages:
            result = await moderator._moderate_text_rules(message)
            assert result.is_violation, f"Should detect spam in: {message}"
            assert result.category == "spam"
            assert result.confidence >= 0.6
    
    @pytest.mark.asyncio
    async def test_harassment_detection(self, moderator):
        """Test harassment detection."""
        harassment_messages = [
            "You're such an idiot",
            "Go kill yourself loser", 
            "You're pathetic and worthless",
            "Shut up you disgusting person"
        ]
        
        for message in harassment_messages:
            result = await moderator._moderate_text_rules(message)
            assert result.is_violation, f"Should detect harassment in: {message}"
            assert result.category == "harassment"
            assert result.confidence >= 0.6
    
    @pytest.mark.asyncio
    async def test_clean_messages_pass(self, moderator):
        """Test that clean messages pass moderation."""
        clean_messages = [
            "Hello everyone, how are you today?",
            "Thanks for sharing that interesting article",
            "Looking forward to the meeting tomorrow",
            "Great job on the presentation!"
        ]
        
        for message in clean_messages:
            result = await moderator._moderate_text_rules(message)
            assert not result.is_violation, f"Should not flag clean message: {message}"
    
    @pytest.mark.asyncio
    async def test_excessive_caps_detection(self, moderator):
        """Test detection of excessive capital letters."""
        caps_messages = [
            "THIS IS ALL CAPS AND VERY ANNOYING TO READ",
            "WHY ARE YOU SHOUTING AT EVERYONE HERE",
            "STOP USING SO MANY CAPS PLEASE"
        ]
        
        for message in caps_messages:
            result = await moderator._moderate_text_rules(message.lower())
            # Note: we pass lowercase to _moderate_text_rules, so test the helper directly
            assert moderator.is_excessive_caps(message), f"Should detect excessive caps in: {message}"
    
    def test_cache_functionality(self, moderator):
        """Test that caching works correctly."""
        test_content = "test message for caching"
        cache_key = moderator._get_cache_key(test_content)
        
        # Test cache key generation
        assert isinstance(cache_key, str)
        assert len(cache_key) == 32  # MD5 hash length
        
        # Test cache storage and retrieval
        test_result = ModerationResult(is_violation=True, confidence=0.8, reason="test")
        moderator.cache[cache_key] = test_result
        
        assert cache_key in moderator.cache
        assert moderator.cache[cache_key].is_violation == True
        assert moderator.cache[cache_key].confidence == 0.8
    
    # Test AI model integration
    
    @pytest.mark.asyncio
    async def test_ai_moderation_with_mock(self, moderator_with_mocked_models):
        """Test AI moderation with mocked models."""
        result = await moderator_with_mocked_models._moderate_text_ai("This is toxic content")
        
        assert result.is_violation
        assert result.confidence == 0.85
        assert result.category == "toxicity"
        assert "AI detected" in result.reason
    
    @pytest.mark.asyncio
    async def test_fallback_to_rules_when_ai_fails(self, moderator):
        """Test fallback to rule-based when AI models aren't available."""
        # Ensure no AI models are loaded
        moderator.models = {}
        
        spam_message = "Buy now for limited time only!"
        result = await moderator.moderate_text(spam_message)
        
        # Should still detect via rules
        assert result.is_violation
        assert result.category == "spam"
    
    # Test custom rules
    
    def test_custom_rule_application(self, moderator):
        """Test custom rule functionality."""
        # Add a custom keyword rule
        custom_rule = {
            'type': 'keyword',
            'keywords': ['forbidden_word', 'banned_phrase'],
            'confidence': 0.9,
            'reason': 'Custom rule violation',
            'category': 'custom'
        }
        moderator.custom_rules = [custom_rule]
        
        # Test rule matching
        result = moderator.apply_custom_rules("This contains forbidden_word in it")
        assert result is not None
        assert result.is_violation
        assert result.confidence == 0.9
        assert result.category == "custom"
        
        # Test non-matching
        result = moderator.apply_custom_rules("This is a clean message")
        assert result is None
    
    def test_custom_url_rule(self, moderator):
        """Test custom URL blocking rules."""
        url_rule = {
            'type': 'url',
            'pattern': r'.*suspicious-site\.com.*',
            'confidence': 0.95,
            'reason': 'Blocked domain',
            'category': 'custom'
        }
        moderator.custom_rules = [url_rule]
        
        result = moderator.apply_custom_rules("Check out this link: https://suspicious-site.com/offer")
        assert result is not None
        assert result.is_violation
        assert result.confidence == 0.95
    
    def test_custom_length_rule(self, moderator):
        """Test message length restrictions."""
        length_rule = {
            'type': 'length',
            'max_length': 50,
            'confidence': 0.8,
            'reason': 'Message too long',
            'category': 'custom'
        }
        moderator.custom_rules = [length_rule]
        
        long_message = "This is a very long message that exceeds the fifty character limit that we set for testing purposes and should be flagged"
        result = moderator.apply_custom_rules(long_message)
        assert result is not None
        assert result.is_violation
        
        short_message = "Short message"
        result = moderator.apply_custom_rules(short_message)
        assert result is None
    
    # Test image moderation
    
    @pytest.mark.asyncio
    async def test_image_size_limits(self, moderator):
        """Test image size restrictions."""
        # Create mock image data
        small_image = b"fake_image_data" * 100  # Small image
        medium_image = b"fake_image_data" * 10000  # Medium size image (under 10MB)
        large_file = b"fake_image_data" * 1000000  # Large file (15MB+)
        
        # Mock PIL Image
        with patch('moderation.Image') as mock_image:
            # Test normal size image
            mock_image.open.return_value.size = (2000, 2000)  # Normal size
            result = await moderator.moderate_image(small_image)
            assert not result.is_violation
            
            # Test oversized resolution (but normal file size)
            mock_image.open.return_value.size = (5000, 5000)  # Oversized resolution
            result = await moderator.moderate_image(medium_image)
            assert result.is_violation
            assert "resolution too high" in result.reason
            
            # Test oversized file
            result = await moderator.moderate_image(large_file)
            assert result.is_violation
            assert "file too large" in result.reason
    
    @pytest.mark.asyncio
    async def test_image_processing_error(self, moderator):
        """Test handling of image processing errors."""
        with patch('moderation.Image') as mock_image:
            mock_image.open.side_effect = Exception("Corrupted image")
            
            result = await moderator.moderate_image(b"corrupted_data")
            assert result.is_violation
            assert result.category == "error"
            assert "Unable to analyze image" in result.reason
    
    # Test video moderation
    
    @pytest.mark.asyncio
    async def test_video_size_limits(self, moderator):
        """Test video size restrictions."""
        small_video = b"fake_video_data" * 1000  # Small video (~15KB)
        # Create a video larger than 100MB (100 * 1024 * 1024 = 104,857,600 bytes)
        large_video = b"x" * (110 * 1024 * 1024)  # 110MB video
        
        result = await moderator.moderate_video(small_video)
        assert not result.is_violation
        
        result = await moderator.moderate_video(large_video)
        assert result.is_violation
        assert "too large" in result.reason
        assert result.category == "policy"
    
    # Test utility functions
    
    def test_keyword_checking(self, moderator):
        """Test keyword checking utility."""
        keywords = ["spam", "scam", "fake"]
        
        # Should match
        score = moderator.check_keywords("this is spam content", keywords)
        assert score > 0
        
        # Should not match
        score = moderator.check_keywords("this is clean content", keywords)
        assert score == 0
    
    def test_repetitive_detection(self, moderator):
        """Test repetitive content detection."""
        repetitive_text = "same same same same same same same"
        normal_text = "this is a normal message with varied words"
        
        assert moderator.is_repetitive(repetitive_text)
        assert not moderator.is_repetitive(normal_text)
    
    def test_caps_ratio_calculation(self, moderator):
        """Test capital letters ratio calculation."""
        all_caps = "THISISCAPS"  # No spaces, all caps
        mixed_case = "This Is Mixed Case"
        no_caps = "this is all lowercase"
        
        # All caps should be close to 1.0
        caps_ratio = moderator._calculate_caps_ratio(all_caps)
        assert caps_ratio > 0.9, f"Expected >0.9, got {caps_ratio}"
        
        # Mixed case should be moderate
        mixed_ratio = moderator._calculate_caps_ratio(mixed_case)
        assert 0.2 < mixed_ratio < 0.5, f"Expected 0.2-0.5, got {mixed_ratio}"
        
        # No caps should be 0
        no_caps_ratio = moderator._calculate_caps_ratio(no_caps)
        assert no_caps_ratio == 0.0, f"Expected 0.0, got {no_caps_ratio}"
    
    def test_rule_summary(self, moderator):
        """Test rule summary functionality."""
        # Add some custom rules
        moderator.custom_rules = [
            {'type': 'keyword', 'keywords': ['test']},
            {'type': 'url', 'pattern': 'test.com'},
            {'type': 'length', 'max_length': 100},
            {'type': 'other', 'rule': 'something'}
        ]
        
        summary = moderator.get_rule_summary()
        
        assert summary['keyword_rules'] == 1
        assert summary['url_rules'] == 1  
        assert summary['length_rules'] == 1
        assert summary['other_rules'] == 1
        assert summary['total_custom_rules'] == 4
        assert 'cache_size' in summary
        assert 'ai_models_loaded' in summary


class TestModerationResult:
    """Test the ModerationResult data class."""
    
    def test_moderation_result_creation(self):
        """Test creating ModerationResult instances."""
        result = ModerationResult(
            is_violation=True,
            confidence=0.85,
            reason="Test violation",
            category="test"
        )
        
        assert result.is_violation == True
        assert result.confidence == 0.85
        assert result.reason == "Test violation"
        assert result.category == "test"
    
    def test_moderation_result_defaults(self):
        """Test ModerationResult with default values."""
        result = ModerationResult(is_violation=False, confidence=0.0)
        
        assert result.is_violation == False
        assert result.confidence == 0.0
        assert result.reason is None
        assert result.category is None


# Integration test that requires the full flow
class TestModerationIntegration:
    """Integration tests for the complete moderation flow."""
    
    @pytest.fixture
    def full_moderator(self):
        """Create a fully configured moderator."""
        config = {
            'test_mode': True,
            'max_video_size': 50 * 1024 * 1024
        }
        moderator = ContentModerator(config)
        
        # Add some custom rules
        moderator.custom_rules = [
            {
                'type': 'keyword',
                'keywords': ['crypto_scam', 'pyramid_scheme'],
                'confidence': 0.9,
                'reason': 'Suspected scam content',
                'category': 'scam'
            }
        ]
        return moderator
    
    @pytest.mark.asyncio
    async def test_priority_order(self, full_moderator):
        """Test that custom rules take priority over AI and built-in rules."""
        # Message that would trigger both custom and built-in rules
        message = "Buy crypto_scam tokens now for limited time!"
        
        result = await full_moderator.moderate_text(message)
        
        # Should be flagged by custom rule first
        assert result.is_violation
        assert result.category == "scam"  # Custom rule category
        assert result.confidence == 0.9   # Custom rule confidence
    
    @pytest.mark.asyncio
    async def test_caching_across_calls(self, full_moderator):
        """Test that caching works across multiple calls."""
        message = "This is a test message for caching"
        
        # First call
        result1 = await full_moderator.moderate_text(message)
        cache_size_after_first = len(full_moderator.cache)
        
        # Second call (should use cache)
        result2 = await full_moderator.moderate_text(message)
        cache_size_after_second = len(full_moderator.cache)
        
        # Results should be identical
        assert result1.is_violation == result2.is_violation
        assert result1.confidence == result2.confidence
        assert result1.reason == result2.reason
        
        # Cache size shouldn't increase on second call
        assert cache_size_after_first == cache_size_after_second


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])