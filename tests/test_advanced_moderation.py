"""
Tests for advanced moderation features including vision models and pattern detection.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from advanced_moderation import (
    VisionModerator,
    ThreatPatternDetector,
    AdvancedModerationSystem,
    ImageAnalysisResult,
    ThreatPattern
)


class TestVisionModerator:
    """Test vision-based moderation capabilities."""
    
    @pytest.fixture
    def vision_moderator(self):
        """Create a vision moderator instance."""
        return VisionModerator()
    
    def test_init(self, vision_moderator):
        """Test vision moderator initialization."""
        assert vision_moderator.models_loaded == False
        assert vision_moderator.nsfw_detector is None
        assert vision_moderator.blip_processor is None
        assert vision_moderator.blip_model is None
    
    @patch('advanced_moderation.HAS_TRANSFORMERS', False)
    def test_load_models_without_transformers(self, vision_moderator):
        """Test model loading when transformers is not available."""
        result = vision_moderator.load_models()
        assert result == False
        assert vision_moderator.models_loaded == False
    
    @patch('advanced_moderation.pipeline')
    @patch('advanced_moderation.BlipProcessor')
    @patch('advanced_moderation.BlipForConditionalGeneration')
    @patch('advanced_moderation.HAS_TRANSFORMERS', True)
    def test_load_models_success(self, mock_blip_model, mock_blip_processor, 
                                 mock_pipeline, vision_moderator):
        """Test successful model loading."""
        mock_pipeline.return_value = Mock()
        mock_blip_processor.from_pretrained.return_value = Mock()
        mock_blip_model.from_pretrained.return_value = Mock()
        
        result = vision_moderator.load_models()
        
        assert result == True
        assert vision_moderator.models_loaded == True
        assert vision_moderator.nsfw_detector is not None
    
    @pytest.mark.asyncio
    async def test_analyze_image_without_models(self, vision_moderator):
        """Test image analysis when models are not loaded."""
        image_data = b"fake_image_data"
        
        result = await vision_moderator.analyze_image(image_data)
        
        assert isinstance(result, ImageAnalysisResult)
        assert result.is_nsfw == False
        assert result.nsfw_confidence == 0.0
        # Description will be an error message since fake data isn't a valid image
        assert "error" in result.content_description.lower() or result.content_description == "Model not loaded"
    
    @pytest.mark.asyncio
    @patch('advanced_moderation.Image')
    async def test_analyze_image_with_models(self, mock_image, vision_moderator):
        """Test image analysis with loaded models."""
        vision_moderator.models_loaded = True
        vision_moderator.nsfw_detector = Mock(return_value=[
            {'label': 'nsfw', 'score': 0.8}
        ])
        
        # Mock the async methods
        vision_moderator._detect_nsfw = AsyncMock(return_value={
            'is_nsfw': True,
            'confidence': 0.8
        })
        vision_moderator._generate_caption = AsyncMock(
            return_value="Person in inappropriate pose"
        )
        
        image_data = b"fake_image_data"
        result = await vision_moderator.analyze_image(image_data)
        
        assert isinstance(result, ImageAnalysisResult)
        assert result.is_nsfw == True
        assert result.nsfw_confidence == 0.8
        assert "Person" in result.content_description
    
    def test_analyze_caption_safety(self, vision_moderator):
        """Test caption safety analysis."""
        caption = "A nude person standing"
        scores = vision_moderator._analyze_caption_safety(caption)
        
        assert 'sexual' in scores
        assert scores['sexual'] == 1.0
        
        caption = "A cat sitting on a chair"
        scores = vision_moderator._analyze_caption_safety(caption)
        assert scores['sexual'] == 0.0
    
    def test_extract_objects(self, vision_moderator):
        """Test object extraction from captions."""
        caption = "A person and a car near a building"
        objects = vision_moderator._extract_objects(caption)
        
        assert 'person' in objects
        assert 'car' in objects
        assert 'building' in objects


class TestThreatPatternDetector:
    """Test threat pattern detection capabilities."""
    
    @pytest.fixture
    def detector(self):
        """Create a threat pattern detector instance."""
        return ThreatPatternDetector(window_minutes=5)
    
    def test_init(self, detector):
        """Test detector initialization."""
        assert detector.window_minutes == 5
        assert detector.similarity_threshold == 0.8
        assert len(detector.message_history) == 0
        assert len(detector.user_activity) == 0
    
    def test_add_message(self, detector):
        """Test adding messages to history."""
        detector.add_message(
            user_id="user1",
            group_id="group1",
            message="Test message",
            timestamp=datetime.now()
        )
        
        assert len(detector.message_history["group1"]) == 1
        assert len(detector.user_activity["user1"]) == 1
        
        msg_data = detector.message_history["group1"][0]
        assert msg_data['user_id'] == "user1"
        assert msg_data['message'] == "Test message"
    
    def test_calculate_similarity(self, detector):
        """Test text similarity calculation."""
        text1 = "Buy crypto now"
        text2 = "Buy crypto now"
        similarity = detector._calculate_similarity(text1, text2)
        assert similarity == 1.0
        
        text1 = "Buy crypto now"
        text2 = "Sell stocks later"
        similarity = detector._calculate_similarity(text1, text2)
        assert similarity < 0.5
        
        text1 = "Buy crypto now cheap"
        text2 = "Buy crypto now"
        similarity = detector._calculate_similarity(text1, text2)
        assert 0.5 < similarity < 1.0
    
    def test_hash_message(self, detector):
        """Test message hashing."""
        msg1 = "Hello world"
        msg2 = "world Hello"  # Different order, same words
        
        hash1 = detector._hash_message(msg1)
        hash2 = detector._hash_message(msg2)
        
        assert hash1 == hash2  # Should be same after normalization
        assert len(hash1) == 8
    
    def test_detect_coordinated_spam(self, detector):
        """Test coordinated spam detection."""
        now = datetime.now()
        
        # Add similar messages from different users
        detector.add_message("user1", "group1", "Buy crypto now!", now)
        detector.add_message("user2", "group1", "Buy crypto now!", now)
        detector.add_message("user3", "group1", "Buy crypto now!", now)
        
        patterns = detector.detect_patterns("group1")
        
        assert len(patterns) > 0
        spam_pattern = patterns[0]
        assert spam_pattern.pattern_type == 'coordinated_spam'
        assert len(spam_pattern.affected_users) >= 3
    
    def test_detect_raid_pattern(self, detector):
        """Test raid detection."""
        now = datetime.now()
        
        # Simulate a raid with many messages from new users
        for i in range(60):  # 60 messages
            detector.add_message(f"user{i}", "group1", f"Message {i}", now)
        
        patterns = detector.detect_patterns("group1")
        
        # Should detect raid pattern
        raid_patterns = [p for p in patterns if p.pattern_type == 'raid']
        assert len(raid_patterns) > 0
    
    def test_detect_link_farming(self, detector):
        """Test link farming detection."""
        now = datetime.now()
        
        # Add many messages with links
        for i in range(15):
            detector.add_message(
                f"user{i % 3}",  # 3 users posting links
                "group1",
                f"Check out https://scam.com/link{i % 2}",  # Low link diversity
                now
            )
        
        patterns = detector.detect_patterns("group1")
        
        # Should detect link farming
        link_patterns = [p for p in patterns if p.pattern_type == 'link_farming']
        assert len(link_patterns) > 0
    
    def test_no_patterns_with_normal_activity(self, detector):
        """Test that normal activity doesn't trigger patterns."""
        now = datetime.now()
        
        # Add normal varied messages
        detector.add_message("user1", "group1", "Hello everyone", now)
        detector.add_message("user2", "group1", "How are you?", now)
        detector.add_message("user3", "group1", "I'm good thanks", now)
        
        patterns = detector.detect_patterns("group1")
        
        assert len(patterns) == 0


class TestAdvancedModerationSystem:
    """Test the complete advanced moderation system."""
    
    @pytest.fixture
    def system(self):
        """Create an advanced moderation system instance."""
        return AdvancedModerationSystem()
    
    def test_init(self, system):
        """Test system initialization."""
        assert system.vision_moderator is not None
        assert system.pattern_detector is not None
        assert system.initialized == False
    
    @pytest.mark.asyncio
    @patch('advanced_moderation.HAS_TRANSFORMERS', True)
    async def test_initialize(self, system):
        """Test system initialization."""
        with patch.object(system.vision_moderator, 'load_models', return_value=True):
            await system.initialize()
            assert system.initialized == True
    
    @pytest.mark.asyncio
    async def test_moderate_image(self, system):
        """Test image moderation through the system."""
        system.initialized = True
        
        # Mock the vision moderator
        mock_result = ImageAnalysisResult(
            is_nsfw=True,
            nsfw_confidence=0.85,
            content_description="Inappropriate content",
            detected_objects=["person"],
            safety_scores={'sexual': 0.9}
        )
        
        with patch.object(system.vision_moderator, 'analyze_image', 
                         return_value=mock_result) as mock_analyze:
            result = await system.moderate_image(b"fake_image")
            
            assert result['is_violation'] == True
            assert result['confidence'] == 0.85
            assert result['action'] == 'delete'
            assert 'Inappropriate content' in result['description']
    
    def test_track_message(self, system):
        """Test message tracking."""
        system.track_message(
            user_id="user1",
            group_id="group1",
            message="Test message"
        )
        
        # Check that message was added to pattern detector
        assert len(system.pattern_detector.message_history["group1"]) == 1
    
    def test_check_threat_patterns(self, system):
        """Test threat pattern checking."""
        # Add some coordinated spam
        now = datetime.now()
        system.pattern_detector.add_message("user1", "group1", "Buy now!", now)
        system.pattern_detector.add_message("user2", "group1", "Buy now!", now)
        system.pattern_detector.add_message("user3", "group1", "Buy now!", now)
        
        results = system.check_threat_patterns("group1")
        
        assert len(results) > 0
        assert results[0]['type'] == 'coordinated_spam'
        assert results[0]['recommended_action'] == 'ban_users'
    
    def test_get_recommended_action(self, system):
        """Test recommended action for different pattern types."""
        raid_pattern = ThreatPattern(
            pattern_type='raid',
            confidence=0.9,
            affected_users=['user1'],
            time_window=timedelta(minutes=1),
            evidence=[]
        )
        assert system._get_recommended_action(raid_pattern) == 'enable_slow_mode'
        
        spam_pattern = ThreatPattern(
            pattern_type='coordinated_spam',
            confidence=0.85,
            affected_users=['user1', 'user2'],
            time_window=timedelta(minutes=5),
            evidence=[]
        )
        assert system._get_recommended_action(spam_pattern) == 'ban_users'
        
        link_pattern = ThreatPattern(
            pattern_type='link_farming',
            confidence=0.75,
            affected_users=['user1'],
            time_window=timedelta(minutes=5),
            evidence=[]
        )
        assert system._get_recommended_action(link_pattern) == 'restrict_links'


class TestIntegration:
    """Integration tests for the complete system."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test the complete moderation workflow."""
        system = AdvancedModerationSystem()
        
        # Track multiple messages
        system.track_message("user1", "group1", "Check out this link: http://scam.com")
        system.track_message("user2", "group1", "Check out this link: http://scam.com")
        system.track_message("user3", "group1", "Check out this link: http://scam.com")
        
        # Check for patterns
        patterns = system.check_threat_patterns("group1")
        
        assert len(patterns) > 0
        assert any(p['type'] == 'coordinated_spam' for p in patterns)
        
        # Test image moderation (without actual models)
        result = await system.moderate_image(b"fake_image_data")
        assert 'is_violation' in result
        assert 'confidence' in result
        assert 'action' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])