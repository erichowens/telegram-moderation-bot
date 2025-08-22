"""
Advanced Moderation with Vision-Language Models and Pattern Detection
Implements real image/video analysis and coordinated attack detection
"""

import logging
import asyncio
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, deque
import hashlib
import io

try:
    from transformers import (
        AutoProcessor, 
        AutoModelForImageClassification,
        BlipProcessor, 
        BlipForConditionalGeneration,
        pipeline,
        AutoTokenizer,
        AutoModelForSequenceClassification
    )
    from PIL import Image
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    print("Warning: transformers not installed. Advanced moderation features disabled.")

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False
    cv2 = None
    print("Warning: opencv-python not installed. Video processing disabled.")

logger = logging.getLogger(__name__)


@dataclass
class ImageAnalysisResult:
    """Result of image content analysis."""
    is_nsfw: bool
    nsfw_confidence: float
    content_description: str
    detected_objects: List[str]
    safety_scores: Dict[str, float]
    
    
@dataclass
class ThreatPattern:
    """Detected threat pattern."""
    pattern_type: str  # 'coordinated_spam', 'raid', 'link_farm'
    confidence: float
    affected_users: List[str]
    time_window: timedelta
    evidence: List[Dict[str, Any]]


class VisionModerator:
    """Advanced image/video moderation using Vision-Language Models."""
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.models_loaded = False
        self.nsfw_detector = None
        self.blip_processor = None
        self.blip_model = None
        
    def load_models(self):
        """Load vision models for content analysis."""
        if not HAS_TRANSFORMERS:
            logger.error("Transformers library not installed")
            return False
            
        try:
            # Load NSFW detector (Vision Transformer)
            logger.info("Loading NSFW detection model...")
            self.nsfw_detector = pipeline(
                "image-classification",
                model="AdamCodd/vit-base-nsfw-detector",
                device=0 if self.device == "cuda" else -1
            )
            
            # Load BLIP for image understanding
            logger.info("Loading BLIP vision-language model...")
            self.blip_processor = BlipProcessor.from_pretrained(
                "Salesforce/blip-image-captioning-base"
            )
            self.blip_model = BlipForConditionalGeneration.from_pretrained(
                "Salesforce/blip-image-captioning-base"
            ).to(self.device)
            
            self.models_loaded = True
            logger.info("Vision models loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load vision models: {e}")
            return False
    
    async def analyze_image(self, image_data: bytes) -> ImageAnalysisResult:
        """Analyze image content for moderation."""
        if not self.models_loaded:
            self.load_models()
            
        if not self.models_loaded:
            # Fallback to basic checks
            return ImageAnalysisResult(
                is_nsfw=False,
                nsfw_confidence=0.0,
                content_description="Model not loaded",
                detected_objects=[],
                safety_scores={}
            )
        
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # NSFW Detection
            nsfw_results = await self._detect_nsfw(image)
            
            # Content Understanding with BLIP
            description = await self._generate_caption(image)
            
            # Analyze caption for problematic content
            safety_scores = self._analyze_caption_safety(description)
            
            # Determine if NSFW based on multiple signals
            is_nsfw = (
                nsfw_results['confidence'] > 0.7 or
                safety_scores.get('sexual', 0) > 0.5 or
                safety_scores.get('violence', 0) > 0.7
            )
            
            return ImageAnalysisResult(
                is_nsfw=is_nsfw,
                nsfw_confidence=nsfw_results['confidence'],
                content_description=description,
                detected_objects=self._extract_objects(description),
                safety_scores=safety_scores
            )
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return ImageAnalysisResult(
                is_nsfw=False,
                nsfw_confidence=0.0,
                content_description=f"Analysis error: {str(e)}",
                detected_objects=[],
                safety_scores={}
            )
    
    async def _detect_nsfw(self, image: Image) -> Dict[str, Any]:
        """Detect NSFW content in image."""
        try:
            results = self.nsfw_detector(image)
            
            # Parse results (model returns 'safe' or 'nsfw' labels)
            nsfw_score = 0.0
            for result in results:
                if result['label'].lower() in ['nsfw', 'porn', 'explicit']:
                    nsfw_score = max(nsfw_score, result['score'])
            
            return {
                'is_nsfw': nsfw_score > 0.5,
                'confidence': nsfw_score,
                'raw_results': results
            }
        except Exception as e:
            logger.error(f"NSFW detection failed: {e}")
            return {'is_nsfw': False, 'confidence': 0.0}
    
    async def _generate_caption(self, image: Image) -> str:
        """Generate description of image content."""
        try:
            inputs = self.blip_processor(image, return_tensors="pt").to(self.device)
            
            # Generate caption
            out = self.blip_model.generate(**inputs, max_length=50)
            caption = self.blip_processor.decode(out[0], skip_special_tokens=True)
            
            return caption
        except Exception as e:
            logger.error(f"Caption generation failed: {e}")
            return "Unable to generate description"
    
    def _analyze_caption_safety(self, caption: str) -> Dict[str, float]:
        """Analyze caption for safety concerns."""
        # Keywords that might indicate problematic content
        safety_keywords = {
            'sexual': ['nude', 'naked', 'explicit', 'sexual', 'intimate'],
            'violence': ['blood', 'gore', 'violence', 'weapon', 'fight'],
            'drugs': ['drug', 'pills', 'needle', 'substance'],
            'hate': ['hate', 'racist', 'discriminate'],
        }
        
        scores = {}
        caption_lower = caption.lower()
        
        for category, keywords in safety_keywords.items():
            score = 0.0
            for keyword in keywords:
                if keyword in caption_lower:
                    score = 1.0
                    break
            scores[category] = score
        
        return scores
    
    def _extract_objects(self, caption: str) -> List[str]:
        """Extract detected objects from caption."""
        # Simple extraction - in production, use NER or proper parsing
        common_objects = [
            'person', 'people', 'man', 'woman', 'child',
            'car', 'building', 'animal', 'food', 'text'
        ]
        
        detected = []
        caption_lower = caption.lower()
        for obj in common_objects:
            if obj in caption_lower:
                detected.append(obj)
        
        return detected


class ThreatPatternDetector:
    """Detect coordinated attacks and threat patterns."""
    
    def __init__(self, window_minutes: int = 5):
        self.window_minutes = window_minutes
        self.message_history = defaultdict(lambda: deque(maxlen=1000))
        self.user_activity = defaultdict(lambda: deque(maxlen=100))
        self.similarity_threshold = 0.8
        
    def add_message(self, user_id: str, group_id: str, message: str, timestamp: datetime):
        """Add message to tracking history."""
        message_data = {
            'user_id': user_id,
            'group_id': group_id,
            'message': message,
            'timestamp': timestamp,
            'hash': self._hash_message(message)
        }
        
        self.message_history[group_id].append(message_data)
        self.user_activity[user_id].append(message_data)
    
    def detect_patterns(self, group_id: str) -> List[ThreatPattern]:
        """Detect threat patterns in a group."""
        patterns = []
        
        # Check for coordinated spam
        spam_pattern = self._detect_coordinated_spam(group_id)
        if spam_pattern:
            patterns.append(spam_pattern)
        
        # Check for raid patterns
        raid_pattern = self._detect_raid_pattern(group_id)
        if raid_pattern:
            patterns.append(raid_pattern)
        
        # Check for link farming
        link_pattern = self._detect_link_farming(group_id)
        if link_pattern:
            patterns.append(link_pattern)
        
        return patterns
    
    def _detect_coordinated_spam(self, group_id: str) -> Optional[ThreatPattern]:
        """Detect multiple accounts posting similar content."""
        messages = list(self.message_history[group_id])
        if len(messages) < 3:
            return None
        
        # Group messages by similarity
        similar_groups = defaultdict(list)
        now = datetime.now()
        window_start = now - timedelta(minutes=self.window_minutes)
        
        # Only check recent messages
        recent_messages = [m for m in messages if m['timestamp'] > window_start]
        
        for i, msg1 in enumerate(recent_messages):
            for msg2 in recent_messages[i+1:]:
                if msg1['user_id'] != msg2['user_id']:
                    similarity = self._calculate_similarity(msg1['message'], msg2['message'])
                    if similarity > self.similarity_threshold:
                        key = msg1['hash']
                        similar_groups[key].append(msg1)
                        similar_groups[key].append(msg2)
        
        # Check if we have coordinated spam
        for hash_key, similar_msgs in similar_groups.items():
            unique_users = set(m['user_id'] for m in similar_msgs)
            if len(unique_users) >= 3:  # At least 3 different users
                return ThreatPattern(
                    pattern_type='coordinated_spam',
                    confidence=0.85,
                    affected_users=list(unique_users),
                    time_window=timedelta(minutes=self.window_minutes),
                    evidence=[{
                        'message_count': len(similar_msgs),
                        'unique_users': len(unique_users),
                        'sample_message': similar_msgs[0]['message'][:100]
                    }]
                )
        
        return None
    
    def _detect_raid_pattern(self, group_id: str) -> Optional[ThreatPattern]:
        """Detect mass join or message flood patterns."""
        messages = list(self.message_history[group_id])
        now = datetime.now()
        
        # Check message rate in 1-minute windows
        one_minute_ago = now - timedelta(minutes=1)
        recent_burst = [m for m in messages if m['timestamp'] > one_minute_ago]
        
        if len(recent_burst) > 50:  # More than 50 messages in 1 minute
            unique_users = set(m['user_id'] for m in recent_burst)
            
            # Check if these are new users (simplified check)
            new_users = []
            for user in unique_users:
                user_history = list(self.user_activity[user])
                if len(user_history) < 5:  # User has less than 5 total messages
                    new_users.append(user)
            
            if len(new_users) > 10:  # More than 10 new users
                return ThreatPattern(
                    pattern_type='raid',
                    confidence=0.9,
                    affected_users=new_users,
                    time_window=timedelta(minutes=1),
                    evidence=[{
                        'message_count': len(recent_burst),
                        'new_users': len(new_users),
                        'total_users': len(unique_users)
                    }]
                )
        
        return None
    
    def _detect_link_farming(self, group_id: str) -> Optional[ThreatPattern]:
        """Detect excessive link posting."""
        import re
        
        messages = list(self.message_history[group_id])
        now = datetime.now()
        window_start = now - timedelta(minutes=self.window_minutes)
        
        link_pattern = re.compile(r'https?://|www\.|t\.me/|@\w+')
        
        link_messages = []
        for msg in messages:
            if msg['timestamp'] > window_start:
                if link_pattern.search(msg['message']):
                    link_messages.append(msg)
        
        if len(link_messages) > 10:  # More than 10 links in window
            unique_users = set(m['user_id'] for m in link_messages)
            
            # Check link diversity
            unique_links = set()
            for msg in link_messages:
                links = link_pattern.findall(msg['message'])
                unique_links.update(links)
            
            # High link count but low diversity = likely spam
            if len(unique_links) < len(link_messages) / 2:
                return ThreatPattern(
                    pattern_type='link_farming',
                    confidence=0.75,
                    affected_users=list(unique_users),
                    time_window=timedelta(minutes=self.window_minutes),
                    evidence=[{
                        'link_count': len(link_messages),
                        'unique_links': len(unique_links),
                        'users_involved': len(unique_users)
                    }]
                )
        
        return None
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        # Simple approach: normalized edit distance
        # In production, use better algorithms like cosine similarity
        if text1 == text2:
            return 1.0
        
        # Jaccard similarity on words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _hash_message(self, message: str) -> str:
        """Generate hash for message similarity grouping."""
        # Normalize and hash
        normalized = ' '.join(sorted(message.lower().split()))
        return hashlib.md5(normalized.encode()).hexdigest()[:8]


class AdvancedModerationSystem:
    """Complete advanced moderation system."""
    
    def __init__(self):
        self.vision_moderator = VisionModerator()
        self.pattern_detector = ThreatPatternDetector()
        self.initialized = False
        
    async def initialize(self):
        """Initialize all moderation systems."""
        logger.info("Initializing advanced moderation system...")
        
        # Load vision models
        if HAS_TRANSFORMERS:
            success = self.vision_moderator.load_models()
            if success:
                logger.info("Vision models loaded successfully")
            else:
                logger.warning("Vision models failed to load, using fallback")
        
        self.initialized = True
        logger.info("Advanced moderation system initialized")
    
    async def moderate_image(self, image_data: bytes) -> Dict[str, Any]:
        """Moderate image content."""
        if not self.initialized:
            await self.initialize()
        
        result = await self.vision_moderator.analyze_image(image_data)
        
        return {
            'is_violation': result.is_nsfw,
            'confidence': result.nsfw_confidence,
            'description': result.content_description,
            'detected_objects': result.detected_objects,
            'safety_scores': result.safety_scores,
            'action': 'delete' if result.is_nsfw else 'allow'
        }
    
    def track_message(self, user_id: str, group_id: str, message: str):
        """Track message for pattern detection."""
        self.pattern_detector.add_message(
            user_id=user_id,
            group_id=group_id,
            message=message,
            timestamp=datetime.now()
        )
    
    def check_threat_patterns(self, group_id: str) -> List[Dict[str, Any]]:
        """Check for threat patterns in group."""
        patterns = self.pattern_detector.detect_patterns(group_id)
        
        results = []
        for pattern in patterns:
            results.append({
                'type': pattern.pattern_type,
                'confidence': pattern.confidence,
                'affected_users': pattern.affected_users,
                'evidence': pattern.evidence,
                'recommended_action': self._get_recommended_action(pattern)
            })
        
        return results
    
    async def moderate_video(self, video_data: bytes) -> Dict[str, Any]:
        """Moderate video content using advanced frame analysis."""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Extract frames from video
            frames = await self._extract_video_frames(video_data)
            if not frames:
                return {
                    'is_violation': False,
                    'confidence': 0.0,
                    'description': 'No frames could be extracted',
                    'frames_analyzed': 0,
                    'action': 'allow'
                }
            
            # Analyze each frame
            violations = []
            all_descriptions = []
            max_confidence = 0.0
            
            for i, frame_data in enumerate(frames):
                try:
                    frame_result = await self.vision_moderator.analyze_image(frame_data)
                    all_descriptions.append(f"Frame {i+1}: {frame_result.content_description}")
                    
                    if frame_result.is_nsfw:
                        violations.append({
                            'frame_index': i,
                            'confidence': frame_result.nsfw_confidence,
                            'description': frame_result.content_description,
                            'safety_scores': frame_result.safety_scores
                        })
                        max_confidence = max(max_confidence, frame_result.nsfw_confidence)
                        
                except Exception as e:
                    logger.error(f"Failed to analyze frame {i}: {e}")
                    all_descriptions.append(f"Frame {i+1}: Analysis failed")
            
            # Determine overall result
            is_violation = len(violations) > 0
            
            return {
                'is_violation': is_violation,
                'confidence': max_confidence,
                'description': '; '.join(all_descriptions),
                'frames_analyzed': len(frames),
                'violation_frames': violations,
                'violation_count': len(violations),
                'action': 'delete' if is_violation else 'allow'
            }
            
        except Exception as e:
            logger.error(f"Video moderation failed: {e}")
            return {
                'is_violation': False,
                'confidence': 0.0,
                'description': f'Video analysis failed: {str(e)}',
                'frames_analyzed': 0,
                'action': 'allow'
            }
    
    async def _extract_video_frames(self, video_data: bytes, max_frames: int = 8) -> List[bytes]:
        """Extract frames from video for advanced analysis."""
        if not HAS_OPENCV:
            logger.warning("OpenCV not available for video frame extraction")
            return []
        
        import tempfile
        import os
        
        frames = []
        temp_file = None
        
        try:
            # Write video to temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
                tmp.write(video_data)
                temp_file = tmp.name
            
            # Open video with OpenCV
            cap = cv2.VideoCapture(temp_file)
            if not cap.isOpened():
                logger.error("Failed to open video file for frame extraction")
                return []
            
            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            duration = total_frames / fps if fps > 0 else 0
            
            logger.info(f"Video analysis: {total_frames} frames, {fps:.1f} FPS, {duration:.1f}s")
            
            # Smart frame extraction strategy
            if duration <= 10:  # Short video - extract more frames
                frame_count = min(max_frames, total_frames)
            elif duration <= 60:  # Medium video - balanced approach
                frame_count = max_frames // 2
            else:  # Long video - fewer frames
                frame_count = max_frames // 3
            
            # Extract frames at strategic points
            if total_frames <= frame_count:
                frame_indices = list(range(total_frames))
            else:
                # Include start, middle, and end frames for better coverage
                start_frames = [0, total_frames // 8]  # Early frames
                middle_frames = [total_frames // 2 - 1, total_frames // 2, total_frames // 2 + 1]  # Middle
                end_frames = [total_frames - total_frames // 8, total_frames - 1]  # Late frames
                
                # Additional random frames for comprehensive analysis
                remaining_count = frame_count - 7
                if remaining_count > 0:
                    step = total_frames // (remaining_count + 1)
                    additional_frames = [i * step for i in range(1, remaining_count + 1)]
                else:
                    additional_frames = []
                
                frame_indices = sorted(set(start_frames + middle_frames + end_frames + additional_frames))
                frame_indices = frame_indices[:frame_count]  # Limit to max_frames
            
            # Extract the frames
            for frame_idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if ret:
                    # Resize frame for faster processing while maintaining quality
                    height, width = frame.shape[:2]
                    if width > 1024 or height > 1024:
                        scale = min(1024/width, 1024/height)
                        new_width = int(width * scale)
                        new_height = int(height * scale)
                        frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
                    
                    # Convert to high-quality JPEG
                    success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                    if success:
                        frames.append(buffer.tobytes())
                        logger.debug(f"Extracted frame {frame_idx}/{total_frames} (timestamp: {frame_idx/fps:.1f}s)")
            
            cap.release()
            logger.info(f"Successfully extracted {len(frames)} frames for analysis")
            
        except Exception as e:
            logger.error(f"Frame extraction error: {e}")
        finally:
            # Clean up
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp video file: {e}")
        
        return frames
    
    def _get_recommended_action(self, pattern: ThreatPattern) -> str:
        """Get recommended action for threat pattern."""
        if pattern.pattern_type == 'raid':
            return 'enable_slow_mode'
        elif pattern.pattern_type == 'coordinated_spam':
            return 'ban_users'
        elif pattern.pattern_type == 'link_farming':
            return 'restrict_links'
        return 'monitor'


# Example usage
if __name__ == "__main__":
    async def test_moderation():
        system = AdvancedModerationSystem()
        await system.initialize()
        
        # Test image moderation
        with open("test_image.jpg", "rb") as f:
            image_data = f.read()
            result = await system.moderate_image(image_data)
            print(f"Image moderation result: {result}")
        
        # Test pattern detection
        system.track_message("user1", "group1", "Buy crypto now! t.me/scam")
        system.track_message("user2", "group1", "Buy crypto now! t.me/scam")
        system.track_message("user3", "group1", "Buy crypto now! t.me/scam")
        
        patterns = system.check_threat_patterns("group1")
        print(f"Detected patterns: {patterns}")
    
    asyncio.run(test_moderation())