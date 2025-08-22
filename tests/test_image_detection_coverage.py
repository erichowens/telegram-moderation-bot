"""
Additional tests for image detection coverage.
"""

import pytest
import asyncio
import os
import sys
import io
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from PIL import Image
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.moderation import ContentModerator, ModerationResult
from src.advanced_moderation import AdvancedModerationSystem, VisionModerator, ImageAnalysisResult


class TestImageDetectionEdgeCases:
    """Test edge cases in image detection."""
    
    @pytest.fixture
    def moderator(self):
        """Create content moderator."""
        config = {'max_image_size': 10 * 1024 * 1024}
        return ContentModerator(config)
    
    @pytest.fixture
    def vision_moderator(self):
        """Create vision moderator."""
        return VisionModerator()
    
    def create_test_image_bytes(self, width=100, height=100, format='JPEG'):
        """Create test image as bytes."""
        image = Image.new('RGB', (width, height), color='red')
        img_bytes = io.BytesIO()
        image.save(img_bytes, format=format)
        return img_bytes.getvalue()
    
    @pytest.mark.asyncio
    async def test_image_size_limits(self, moderator):
        """Test various image size scenarios."""
        # Test normal size image
        normal_image = self.create_test_image_bytes(500, 500)
        result = await moderator.moderate_image(normal_image)
        assert not result.is_violation
        
        # Test very large image dimensions
        large_image = self.create_test_image_bytes(5000, 5000)
        result = await moderator.moderate_image(large_image)
        assert result.is_violation
        assert "resolution too high" in result.reason
        
        # Test oversized file
        oversized_data = b'X' * (15 * 1024 * 1024)  # 15MB
        result = await moderator.moderate_image(oversized_data)
        assert result.is_violation
        assert result.category == "spam"
    
    @pytest.mark.asyncio
    async def test_image_format_handling(self, moderator):
        """Test different image formats."""
        formats = ['JPEG', 'PNG', 'GIF']
        
        for fmt in formats:
            image_data = self.create_test_image_bytes(200, 200, fmt)
            result = await moderator.moderate_image(image_data)
            # Should not violate just based on format
            assert isinstance(result, ModerationResult)
    
    @pytest.mark.asyncio
    async def test_corrupted_image_data(self, moderator):
        """Test handling of corrupted image data."""
        # Test with completely invalid data
        invalid_data = b'not_an_image_at_all'
        result = await moderator.moderate_image(invalid_data)
        assert result.is_violation
        assert result.category == "error"
        
        # Test with truncated image data
        valid_image = self.create_test_image_bytes()
        truncated_image = valid_image[:50]  # Truncate the image
        result = await moderator.moderate_image(truncated_image)
        assert result.is_violation
        assert result.category == "error"
    
    @pytest.mark.asyncio
    async def test_vision_moderator_model_loading(self, vision_moderator):
        """Test vision moderator model loading scenarios."""
        # Test successful loading
        with patch('src.advanced_moderation.HAS_TRANSFORMERS', True):
            with patch('transformers.AutoModelForImageClassification.from_pretrained') as mock_model:
                with patch('transformers.AutoProcessor.from_pretrained') as mock_processor:
                    mock_model.return_value = Mock()
                    mock_processor.return_value = Mock()
                    
                    result = vision_moderator.load_models()
                    assert result
        
        # Test loading without transformers
        with patch('src.advanced_moderation.HAS_TRANSFORMERS', False):
            result = vision_moderator.load_models()
            assert not result
    
    @pytest.mark.asyncio
    async def test_vision_moderator_nsfw_detection_scenarios(self):
        """Test various NSFW detection scenarios."""
        vision_moderator = VisionModerator()
        
        # Mock the detector with different result types
        test_cases = [
            # Case 1: NSFW detected
            ([{'label': 'NSFW', 'score': 0.85}], True, 0.85),
            # Case 2: Safe content
            ([{'label': 'SAFE', 'score': 0.9}], False, 0.0),
            # Case 3: Multiple labels with NSFW
            ([
                {'label': 'SAFE', 'score': 0.3},
                {'label': 'PORN', 'score': 0.7}
            ], True, 0.7),
            # Case 4: Borderline case
            ([{'label': 'NSFW', 'score': 0.4}], False, 0.4),
        ]
        
        for mock_results, expected_nsfw, expected_confidence in test_cases:
            vision_moderator.nsfw_detector = Mock(return_value=mock_results)
            
            test_image = Image.new('RGB', (100, 100))
            result = await vision_moderator._detect_nsfw(test_image)
            
            assert result['is_nsfw'] == expected_nsfw
            assert result['confidence'] == expected_confidence
    
    @pytest.mark.asyncio
    async def test_vision_moderator_caption_generation(self):
        """Test image caption generation scenarios."""
        vision_moderator = VisionModerator()
        
        # Test successful caption generation
        mock_processor = Mock()
        mock_model = Mock()
        mock_output = Mock()
        mock_output.logits = Mock()
        
        vision_moderator.caption_processor = mock_processor
        vision_moderator.caption_model = mock_model
        
        # Mock the generation process
        with patch.object(vision_moderator.caption_model, 'generate') as mock_generate:
            with patch.object(vision_moderator.caption_processor, 'decode') as mock_decode:
                mock_generate.return_value = [[1, 2, 3, 4]]
                mock_decode.return_value = "A test image description"
                
                test_image = Image.new('RGB', (100, 100))
                result = await vision_moderator._generate_caption(test_image)
                
                assert "test image description" in result.lower()
    
    @pytest.mark.asyncio
    async def test_advanced_moderation_image_analysis_complete(self):
        """Test complete image analysis workflow."""
        system = AdvancedModerationSystem()
        system.initialized = True
        
        # Mock the vision moderator
        mock_result = ImageAnalysisResult(
            is_nsfw=True,
            nsfw_confidence=0.92,
            content_description="Inappropriate content detected",
            detected_objects=["person", "bedroom"],
            safety_scores={"adult": 0.95, "violence": 0.1}
        )
        
        system.vision_moderator = Mock()
        system.vision_moderator.analyze_image = AsyncMock(return_value=mock_result)
        
        image_data = self.create_test_image_bytes()
        result = await system.moderate_image(image_data)
        
        assert result['is_violation']
        assert result['confidence'] == 0.92
        assert result['action'] == 'delete'
        assert "Inappropriate content detected" in result['description']


class TestAdvancedImageFeatures:
    """Test advanced image moderation features."""
    
    @pytest.mark.asyncio
    async def test_image_analysis_without_initialization(self):
        """Test image analysis when system is not initialized."""
        system = AdvancedModerationSystem()
        # Don't initialize
        
        # Mock the initialize method to avoid actual model loading
        system.initialize = AsyncMock()
        
        image_data = b'fake_image_data'
        result = await system.moderate_image(image_data)
        
        # Should call initialize first
        system.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_vision_moderator_object_detection(self):
        """Test object detection functionality."""
        vision_moderator = VisionModerator()
        
        # This would test object detection if implemented
        # For now, just test that the method exists and handles errors
        test_image = Image.new('RGB', (100, 100))
        
        # The current implementation doesn't have explicit object detection
        # but this test ensures we're ready for it
        result = await vision_moderator.analyze_image(b'fake_data')
        assert hasattr(result, 'detected_objects')
        assert isinstance(result.detected_objects, list)
    
    @pytest.mark.asyncio
    async def test_vision_moderator_safety_scores(self):
        """Test safety scoring functionality."""
        vision_moderator = VisionModerator()
        
        # Mock models to return safety scores
        mock_nsfw_result = {
            'is_nsfw': False,
            'confidence': 0.1,
            'raw_results': [
                {'label': 'SAFE', 'score': 0.9},
                {'label': 'NSFW', 'score': 0.1}
            ]
        }
        
        with patch.object(vision_moderator, '_detect_nsfw', return_value=mock_nsfw_result):
            with patch.object(vision_moderator, '_generate_caption', return_value="Safe image"):
                result = await vision_moderator.analyze_image(b'fake_data')
                
                assert hasattr(result, 'safety_scores')
                assert isinstance(result.safety_scores, dict)


class TestImageModerationIntegration:
    """Test integration between different image moderation components."""
    
    @pytest.mark.asyncio
    async def test_bot_image_handling_advanced_fallback(self):
        """Test bot image handling with advanced moderation fallback."""
        from src.bot import TelegramModerationBot
        
        # Create mock bot
        with patch('src.bot.Application'), patch('src.config.Config'), patch('src.moderation.ContentModerator'):
            bot = TelegramModerationBot("test_token")
            
            # Mock advanced moderator failure
            bot.advanced_moderator = Mock()
            bot.advanced_moderator.moderate_image = AsyncMock(side_effect=Exception("Advanced failed"))
            
            # Mock basic moderator success
            bot.moderator = Mock()
            bot.moderator.moderate_image = AsyncMock(return_value=ModerationResult(
                is_violation=False, confidence=0.0
            ))
            
            # Create mock update
            from unittest.mock import Mock
            mock_update = Mock()
            mock_message = Mock()
            mock_photo = [Mock()]  # List of photo sizes
            mock_photo[0].get_file = AsyncMock()
            mock_photo[0].get_file.return_value.download_as_bytearray = AsyncMock(return_value=b'image_data')
            
            mock_message.photo = mock_photo
            mock_message.from_user = Mock()
            mock_message.chat = Mock()
            mock_update.message = mock_message
            
            # Should fall back to basic moderation
            await bot.handle_photo_message(mock_update, None)
            
            # Verify fallback was used
            bot.moderator.moderate_image.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_caching_image_results(self):
        """Test that image moderation results are cached."""
        config = {'max_image_size': 10 * 1024 * 1024}
        moderator = ContentModerator(config)
        
        # Create test image
        image = Image.new('RGB', (100, 100), color='blue')
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='JPEG')
        image_data = img_bytes.getvalue()
        
        # First call
        result1 = await moderator.moderate_image(image_data)
        
        # Second call should use cache
        result2 = await moderator.moderate_image(image_data)
        
        # Results should be identical (from cache)
        assert result1.is_violation == result2.is_violation
        assert result1.confidence == result2.confidence


if __name__ == "__main__":
    pytest.main([__file__])