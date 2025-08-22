"""
Test video moderation with frame extraction.
"""

import pytest
import asyncio
import os
import sys
import tempfile
import numpy as np
from unittest.mock import Mock, patch, AsyncMock, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.moderation import ContentModerator, ModerationResult
from src.advanced_moderation import AdvancedModerationSystem


class TestVideoFrameExtraction:
    """Test video frame extraction functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        return {
            'max_video_size': 50 * 1024 * 1024,
            'moderation': {
                'thresholds': {
                    'spam': 0.7,
                    'toxicity': 0.8
                }
            }
        }
    
    @pytest.fixture
    def moderator(self, mock_config):
        """Create content moderator instance."""
        return ContentModerator(mock_config)
    
    @pytest.fixture
    def advanced_moderator(self):
        """Create advanced moderation system."""
        return AdvancedModerationSystem()
    
    def create_mock_video_data(self, size_mb=1):
        """Create mock video data of specified size."""
        return b'FAKE_VIDEO_DATA' * (size_mb * 1024 * 1024 // 15)
    
    @pytest.mark.asyncio
    async def test_video_size_validation(self, moderator):
        """Test video size validation."""
        # Test normal size video
        normal_video = self.create_mock_video_data(1)  # 1MB
        result = await moderator.moderate_video(normal_video)
        assert isinstance(result, ModerationResult)
        
        # Test oversized video
        large_video = self.create_mock_video_data(100)  # 100MB
        result = await moderator.moderate_video(large_video)
        assert result.is_violation
        assert result.category == "spam"  # Size limit violations are categorized as spam
        assert "size limit" in result.reason.lower()
    
    @pytest.mark.asyncio
    async def test_frame_extraction_success(self, moderator):
        """Test successful frame extraction."""
        with patch('src.moderation.HAS_OPENCV', True):
            with patch('src.moderation.cv2') as mock_cv2:
                # Mock OpenCV video capture
                mock_cap = MagicMock()
                mock_cap.isOpened.return_value = True
                mock_cap.get.side_effect = lambda prop: {
                    mock_cv2.CAP_PROP_FRAME_COUNT: 100,
                    mock_cv2.CAP_PROP_FPS: 30
                }.get(prop, 0)
                mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
                mock_cv2.VideoCapture.return_value = mock_cap
                mock_cv2.imencode.return_value = (True, np.array([1, 2, 3, 4, 5]))
                
                # Mock moderate_image to avoid violations
                moderator.moderate_image = AsyncMock(return_value=ModerationResult(
                    is_violation=False, confidence=0.0
                ))
                
                video_data = self.create_mock_video_data(1)
                frames = await moderator._extract_video_frames(video_data, max_frames=3)
                
                assert len(frames) <= 3
                mock_cap.set.assert_called()
                mock_cap.read.assert_called()
    
    @pytest.mark.asyncio
    @patch('src.moderation.HAS_OPENCV', False)
    async def test_frame_extraction_no_opencv(self, moderator):
        """Test frame extraction when OpenCV is not available."""
        video_data = self.create_mock_video_data(1)
        frames = await moderator._extract_video_frames(video_data)
        
        assert frames == []
    
    @pytest.mark.asyncio
    async def test_frame_extraction_video_open_failure(self, moderator):
        """Test frame extraction when video cannot be opened."""
        with patch('src.moderation.HAS_OPENCV', True):
            with patch('src.moderation.cv2') as mock_cv2:
                mock_cap = MagicMock()
                mock_cap.isOpened.return_value = False
                mock_cv2.VideoCapture.return_value = mock_cap
                
                video_data = self.create_mock_video_data(1)
                frames = await moderator._extract_video_frames(video_data)
                
                assert frames == []
    
    @pytest.mark.asyncio
    async def test_video_moderation_with_violations(self, moderator):
        """Test video moderation that detects violations in frames."""
        with patch('src.moderation.HAS_OPENCV', True):
            with patch('src.moderation.cv2') as mock_cv2:
                # Mock frame extraction
                mock_cap = MagicMock()
                mock_cap.isOpened.return_value = True
                mock_cap.get.side_effect = lambda prop: {
                    mock_cv2.CAP_PROP_FRAME_COUNT: 50,
                    mock_cv2.CAP_PROP_FPS: 25
                }.get(prop, 0)
                mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
                mock_cv2.VideoCapture.return_value = mock_cap
                mock_cv2.imencode.return_value = (True, np.array([1, 2, 3]))
                
                # Mock image moderation to return violation
                moderator.moderate_image = AsyncMock(return_value=ModerationResult(
                    is_violation=True, 
                    confidence=0.9,
                    reason="NSFW content detected",
                    category="nsfw"
                ))
                
                video_data = self.create_mock_video_data(1)
                result = await moderator.moderate_video(video_data)
                
                assert result.is_violation
                assert result.confidence == 0.9
                assert "frame violation" in result.reason.lower()
    
    @pytest.mark.asyncio
    async def test_video_moderation_no_violations(self, moderator):
        """Test video moderation with clean content."""
        with patch('src.moderation.HAS_OPENCV', True):
            with patch('src.moderation.cv2') as mock_cv2:
                # Mock frame extraction
                mock_cap = MagicMock()
                mock_cap.isOpened.return_value = True
                mock_cap.get.side_effect = lambda prop: {
                    mock_cv2.CAP_PROP_FRAME_COUNT: 30,
                    mock_cv2.CAP_PROP_FPS: 30
                }.get(prop, 0)
                mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
                mock_cv2.VideoCapture.return_value = mock_cap
                mock_cv2.imencode.return_value = (True, np.array([1, 2, 3]))
                
                # Mock image moderation to return no violation
                moderator.moderate_image = AsyncMock(return_value=ModerationResult(
                    is_violation=False, confidence=0.0
                ))
                
                video_data = self.create_mock_video_data(1)
                result = await moderator.moderate_video(video_data)
                
                assert not result.is_violation
                assert result.confidence == 0.0


class TestAdvancedVideoModeration:
    """Test advanced video moderation system."""
    
    @pytest.fixture
    def advanced_moderator(self):
        """Create advanced moderation system."""
        return AdvancedModerationSystem()
    
    @pytest.mark.asyncio
    async def test_advanced_frame_extraction_strategy(self, advanced_moderator):
        """Test advanced frame extraction with smart strategy."""
        # Mock video with various durations
        test_cases = [
            (30, 25, 5),   # Short video: 5 seconds, 30 frames, expect more frames
            (900, 30, 2),  # Medium video: 30 seconds, 900 frames, expect medium frames  
            (1800, 30, 1), # Long video: 60 seconds, 1800 frames, expect fewer frames
        ]
        
        with patch('src.advanced_moderation.HAS_OPENCV', True):
            with patch('src.advanced_moderation.cv2') as mock_cv2:
                for total_frames, fps, expected_frame_ratio in test_cases:
                    mock_cap = MagicMock()
                    mock_cap.isOpened.return_value = True
                    mock_cap.get.side_effect = lambda prop: {
                        mock_cv2.CAP_PROP_FRAME_COUNT: total_frames,
                        mock_cv2.CAP_PROP_FPS: fps
                    }.get(prop, 0)
                    mock_cap.read.return_value = (True, np.zeros((720, 1280, 3), dtype=np.uint8))
                    mock_cv2.VideoCapture.return_value = mock_cap
                    mock_cv2.imencode.return_value = (True, np.array([1, 2, 3, 4]))
                    mock_cv2.resize.return_value = np.zeros((512, 910, 3), dtype=np.uint8)
                    
                    video_data = b'FAKE_VIDEO' * 1000
                    frames = await advanced_moderator._extract_video_frames(video_data, max_frames=8)
                    
                    # Verify frame extraction calls
                    assert mock_cap.set.called
                    assert mock_cap.read.called
    
    @pytest.mark.asyncio
    async def test_advanced_video_moderation_integration(self, advanced_moderator):
        """Test complete advanced video moderation workflow."""
        # Mock the vision moderator
        mock_vision_result = Mock()
        mock_vision_result.is_nsfw = True
        mock_vision_result.nsfw_confidence = 0.85
        mock_vision_result.content_description = "Inappropriate content detected"
        mock_vision_result.safety_scores = {"adult": 0.9, "violence": 0.1}
        
        advanced_moderator.vision_moderator = Mock()
        advanced_moderator.vision_moderator.analyze_image = AsyncMock(return_value=mock_vision_result)
        advanced_moderator.initialized = True
        
        # Mock frame extraction
        with patch.object(advanced_moderator, '_extract_video_frames') as mock_extract:
            mock_extract.return_value = [b'frame1', b'frame2', b'frame3']
            
            video_data = b'FAKE_VIDEO_DATA' * 1000
            result = await advanced_moderator.moderate_video(video_data)
            
            assert result['is_violation']
            assert result['confidence'] == 0.85
            assert result['frames_analyzed'] == 3
            assert result['violation_count'] == 3  # All frames flagged
            assert result['action'] == 'delete'
    
    @pytest.mark.asyncio
    async def test_advanced_video_moderation_clean_content(self, advanced_moderator):
        """Test advanced video moderation with clean content."""
        # Mock clean vision results
        mock_vision_result = Mock()
        mock_vision_result.is_nsfw = False
        mock_vision_result.nsfw_confidence = 0.1
        mock_vision_result.content_description = "Safe content"
        mock_vision_result.safety_scores = {"adult": 0.05, "violence": 0.02}
        
        advanced_moderator.vision_moderator = Mock()
        advanced_moderator.vision_moderator.analyze_image = AsyncMock(return_value=mock_vision_result)
        advanced_moderator.initialized = True
        
        # Mock frame extraction
        with patch.object(advanced_moderator, '_extract_video_frames') as mock_extract:
            mock_extract.return_value = [b'frame1', b'frame2']
            
            video_data = b'CLEAN_VIDEO_DATA' * 1000
            result = await advanced_moderator.moderate_video(video_data)
            
            assert not result['is_violation']
            assert result['confidence'] == 0.0
            assert result['frames_analyzed'] == 2
            assert result['violation_count'] == 0
            assert result['action'] == 'allow'
    
    @pytest.mark.asyncio
    async def test_advanced_video_no_frames_extracted(self, advanced_moderator):
        """Test advanced video moderation when no frames can be extracted."""
        advanced_moderator.initialized = True
        
        # Mock frame extraction to return empty list
        with patch.object(advanced_moderator, '_extract_video_frames') as mock_extract:
            mock_extract.return_value = []
            
            video_data = b'CORRUPTED_VIDEO_DATA'
            result = await advanced_moderator.moderate_video(video_data)
            
            assert not result['is_violation']
            assert result['confidence'] == 0.0
            assert result['frames_analyzed'] == 0
            assert "No frames could be extracted" in result['description']


class TestVideoModerationPerformance:
    """Test video moderation performance and resource management."""
    
    @pytest.fixture
    def moderator(self):
        """Create moderator with performance settings."""
        config = {
            'max_video_size': 10 * 1024 * 1024,  # 10MB for faster tests
        }
        return ContentModerator(config)
    
    @pytest.mark.asyncio
    async def test_video_size_limits_respected(self, moderator):
        """Test that video size limits are properly enforced."""
        # Test with input validation
        oversized_video = b'X' * (60 * 1024 * 1024)  # 60MB
        
        result = await moderator.moderate_video(oversized_video)
        assert result.is_violation
        assert "size limit" in result.reason.lower()
    
    @pytest.mark.asyncio
    async def test_frame_limit_respected(self, moderator):
        """Test that frame extraction respects max_frames limit."""
        with patch('src.moderation.HAS_OPENCV', True):
            with patch('src.moderation.cv2') as mock_cv2:
                # Mock large video
                mock_cap = MagicMock()
                mock_cap.isOpened.return_value = True
                mock_cap.get.side_effect = lambda prop: {
                    mock_cv2.CAP_PROP_FRAME_COUNT: 1000,  # Large video
                    mock_cv2.CAP_PROP_FPS: 30
                }.get(prop, 0)
                mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
                mock_cv2.VideoCapture.return_value = mock_cap
                mock_cv2.imencode.return_value = (True, np.array([1, 2, 3]))
                
                video_data = b'LARGE_VIDEO' * 1000
                frames = await moderator._extract_video_frames(video_data, max_frames=3)
                
                assert len(frames) <= 3
    
    @pytest.mark.asyncio
    async def test_cleanup_temp_files(self, moderator):
        """Test that temporary files are properly cleaned up."""
        with patch('src.moderation.HAS_OPENCV', True):
            with patch('src.moderation.cv2') as mock_cv2:
                with patch('tempfile.NamedTemporaryFile') as mock_temp:
                    with patch('os.path.exists', return_value=True):
                        with patch('os.unlink') as mock_unlink:
                            # Mock file operations
                            mock_temp_file = Mock()
                            mock_temp_file.name = "/tmp/test_video.mp4"
                            mock_temp.__enter__ = Mock(return_value=mock_temp_file)
                            mock_temp.__exit__ = Mock(return_value=None)
                            
                            # Mock failed video opening to trigger cleanup
                            mock_cap = MagicMock()
                            mock_cap.isOpened.return_value = False
                            mock_cv2.VideoCapture.return_value = mock_cap
                            
                            video_data = b'TEST_VIDEO'
                            await moderator._extract_video_frames(video_data)
                            
                            # Verify cleanup was attempted
                            mock_unlink.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])