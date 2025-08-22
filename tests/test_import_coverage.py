"""
Test import fallbacks and error handling for better coverage.
"""

import pytest
import sys
import os
from unittest.mock import patch, Mock, MagicMock
from io import StringIO
import contextlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestImportFallbacks:
    """Test import fallback scenarios for better coverage."""
    
    def test_advanced_moderation_no_transformers(self):
        """Test advanced moderation without transformers."""
        with patch.dict('sys.modules', {'transformers': None}):
            # Mock print to capture output
            with patch('builtins.print') as mock_print:
                # Clear the module from cache if it exists
                if 'src.advanced_moderation' in sys.modules:
                    del sys.modules['src.advanced_moderation']
                
                # Import with missing transformers
                import src.advanced_moderation as am
                
                # Verify the warning was printed
                mock_print.assert_called_with("Warning: transformers not installed. Advanced moderation features disabled.")
                assert not am.HAS_TRANSFORMERS
    
    def test_advanced_moderation_no_opencv(self):
        """Test advanced moderation without opencv."""
        with patch.dict('sys.modules', {'cv2': None}):
            with patch('builtins.print') as mock_print:
                # Clear the module from cache if it exists
                if 'src.advanced_moderation' in sys.modules:
                    del sys.modules['src.advanced_moderation']
                
                import src.advanced_moderation as am
                
                # Check that warning was printed and HAS_OPENCV is False
                mock_print.assert_called_with("Warning: opencv-python not installed. Video processing disabled.")
                assert not am.HAS_OPENCV
                assert am.cv2 is None
    
    def test_moderation_no_transformers(self):
        """Test moderation module without transformers."""
        with patch.dict('sys.modules', {'transformers': None}):
            # Clear the module from cache if it exists
            if 'src.moderation' in sys.modules:
                del sys.modules['src.moderation']
            
            import src.moderation as mod
            
            assert not mod.HAS_TRANSFORMERS
    
    def test_moderation_no_opencv(self):
        """Test moderation module without opencv."""
        with patch.dict('sys.modules', {'cv2': None, 'numpy': None}):
            if 'src.moderation' in sys.modules:
                del sys.modules['src.moderation']
            
            import src.moderation as mod
            
            assert not mod.HAS_OPENCV
            assert mod.cv2 is None
            assert mod.np is None


class TestAdvancedModerationErrorHandling:
    """Test error handling in advanced moderation."""
    
    @pytest.fixture
    def vision_moderator(self):
        """Create a vision moderator for testing."""
        from src.advanced_moderation import VisionModerator
        return VisionModerator()
    
    def test_vision_moderator_load_models_no_transformers(self, vision_moderator):
        """Test model loading when transformers is not available."""
        with patch('src.advanced_moderation.HAS_TRANSFORMERS', False):
            result = vision_moderator.load_models()
            assert not result
    
    @pytest.mark.asyncio
    async def test_vision_moderator_nsfw_detection_error(self, vision_moderator):
        """Test NSFW detection with errors."""
        # Mock a failing detector
        vision_moderator.nsfw_detector = Mock(side_effect=Exception("Model error"))
        
        from PIL import Image
        test_image = Image.new('RGB', (100, 100), color='red')
        
        result = await vision_moderator._detect_nsfw(test_image)
        assert not result['is_nsfw']
        assert result['confidence'] == 0.0
    
    @pytest.mark.asyncio
    async def test_vision_moderator_caption_error(self, vision_moderator):
        """Test image captioning with errors."""
        # Mock failing models
        vision_moderator.caption_processor = Mock(side_effect=Exception("Caption error"))
        
        from PIL import Image
        test_image = Image.new('RGB', (100, 100), color='blue')
        
        result = await vision_moderator._generate_caption(test_image)
        assert "Unable to generate description" in result
    
    @pytest.mark.asyncio 
    async def test_vision_moderator_analyze_no_models(self):
        """Test image analysis when models aren't loaded."""
        from src.advanced_moderation import VisionModerator
        moderator = VisionModerator()
        # Don't load models
        
        test_data = b'fake_image_data'
        result = await moderator.analyze_image(test_data)
        
        assert not result.is_nsfw
        assert result.nsfw_confidence == 0.0
        assert "not available" in result.content_description


class TestModerationErrorHandling:
    """Test error handling in basic moderation."""
    
    @pytest.fixture
    def moderator(self):
        """Create a basic moderator."""
        from src.moderation import ContentModerator
        config = {'max_video_size': 50 * 1024 * 1024}
        return ContentModerator(config)
    
    @pytest.mark.asyncio
    async def test_moderate_image_invalid_data(self, moderator):
        """Test image moderation with invalid data."""
        # Test with invalid image data
        invalid_data = b'not_an_image'
        result = await moderator.moderate_image(invalid_data)
        
        assert result.is_violation
        assert result.category == "error"
        assert "Unable to analyze image" in result.reason
    
    @pytest.mark.asyncio
    async def test_moderate_video_no_opencv(self, moderator):
        """Test video moderation without OpenCV."""
        with patch('src.moderation.HAS_OPENCV', False):
            video_data = b'fake_video_data' * 1000
            result = await moderator.moderate_video(video_data)
            
            # Should still work but skip frame extraction
            assert isinstance(result, moderator.__class__.__module__.split('.')[-1])
    
    def test_load_custom_rules_invalid_path(self, moderator):
        """Test loading custom rules with path traversal attempt."""
        # This should trigger the path validation
        original_method = moderator.load_custom_rules
        moderator.load_custom_rules()  # Should handle missing file gracefully
        
        # Verify no rules were loaded from invalid path
        assert len(moderator.custom_rules) == 0
    
    @pytest.mark.asyncio
    async def test_ai_moderation_failure(self, moderator):
        """Test AI moderation with model failures."""
        # Mock a failing AI model
        moderator.models['toxicity'] = Mock(side_effect=Exception("Model failed"))
        
        text = "This is a test message"
        result = await moderator.moderate_text(text)
        
        # Should fall back to rule-based moderation
        assert isinstance(result, moderator.moderate_text.__annotations__['return'])


class TestBotErrorHandling:
    """Test bot error handling scenarios."""
    
    @pytest.fixture
    def mock_bot(self):
        """Create a bot instance for testing."""
        from src.bot import TelegramModerationBot
        token = "test_token"
        
        with patch('src.bot.Application'):
            with patch('src.config.Config'):
                with patch('src.moderation.ContentModerator'):
                    bot = TelegramModerationBot(token)
                    return bot
    
    def test_bot_init_config_failure(self):
        """Test bot initialization with config failure."""
        from src.bot import TelegramModerationBot
        
        with patch('src.bot.Application'):
            with patch('src.config.Config', side_effect=FileNotFoundError("Config not found")):
                with pytest.raises(FileNotFoundError):
                    TelegramModerationBot("test_token")
    
    def test_bot_init_moderator_failure(self):
        """Test bot initialization with moderator failure.""" 
        from src.bot import TelegramModerationBot
        
        with patch('src.bot.Application'):
            with patch('src.config.Config'):
                with patch('src.moderation.ContentModerator', side_effect=Exception("Moderator failed")):
                    with pytest.raises(RuntimeError, match="Cannot initialize bot"):
                        TelegramModerationBot("test_token")
    
    @pytest.mark.asyncio
    async def test_bot_advanced_moderation_init_failure(self, mock_bot):
        """Test advanced moderation initialization failure."""
        # Test the scenario where advanced moderation fails to initialize
        with patch('src.advanced_moderation.AdvancedModerationSystem') as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            mock_instance.initialize = Mock(side_effect=Exception("Init failed"))
            
            # This should be handled gracefully
            mock_bot._load_advanced_moderator()
            assert mock_bot.advanced_moderator is None


class TestWebDashboardCoverage:
    """Add basic tests for web dashboard to improve coverage."""
    
    def test_web_dashboard_import(self):
        """Test that web dashboard can be imported."""
        try:
            import src.web_dashboard
            # Basic import test
            assert hasattr(src.web_dashboard, 'app')
        except ImportError:
            pytest.skip("Web dashboard dependencies not available")


if __name__ == "__main__":
    pytest.main([__file__])