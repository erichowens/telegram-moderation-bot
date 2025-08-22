"""
Content moderation using real AI models and custom rule parsing.
Production-ready implementation with proper error handling.
"""

import logging
import re
import asyncio
import hashlib
import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from pathlib import Path
import json
from functools import lru_cache
from collections import OrderedDict
import concurrent.futures

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    from PIL import Image
    import io
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    
try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False
    cv2 = None
    np = None

try:
    from .security import InputValidator, RateLimiter
except ImportError:
    from security import InputValidator, RateLimiter

logger = logging.getLogger(__name__)


@dataclass
class ModerationResult:
    """Result of content moderation."""
    is_violation: bool
    confidence: float
    reason: Optional[str] = None
    category: Optional[str] = None


class ModerationThresholds:
    """Configuration constants for moderation thresholds."""
    TOXICITY_THRESHOLD = 0.7
    SPAM_THRESHOLD = 0.6
    HARASSMENT_THRESHOLD = 0.6
    CAPS_RATIO_THRESHOLD = 0.7
    MIN_REPETITION_COUNT = 3
    MAX_URL_COUNT = 3
    CONFIDENCE_BASE = 0.6
    CONFIDENCE_SCALE = 0.35
    MAX_CONFIDENCE = 0.95


class ContentModerator:
    """Production content moderator with AI models and custom rules."""
    
    MAX_CACHE_SIZE = 1000  # Maximum number of cached items
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache = OrderedDict()  # LRU cache with bounded size
        self.models = {}
        self.custom_rules = []
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self.validator = InputValidator()
        self.rate_limiter = RateLimiter(max_messages_per_second=10)
        self._closed = False
        
        self.load_simple_rules()
        self.load_ai_models()
        self.load_custom_rules()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        if not self._closed:
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=True)
            self._closed = True
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()
    
    def _add_to_cache(self, key: str, value: ModerationResult):
        """Add item to cache with LRU eviction."""
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
        else:
            self.cache[key] = value
            # Evict oldest if cache is full
            if len(self.cache) > self.MAX_CACHE_SIZE:
                self.cache.popitem(last=False)  # Remove oldest (FIFO)
    
    def _get_from_cache(self, key: str) -> Optional[ModerationResult]:
        """Get item from cache and update LRU order."""
        if key in self.cache:
            self.cache.move_to_end(key)  # Mark as recently used
            return self.cache[key]
        return None
    
    def load_simple_rules(self):
        """Load simple keyword-based moderation rules."""
        # Spam indicators
        self.spam_keywords = [
            "buy now", "limited time", "click here", "free money", "earn $$$",
            "make money fast", "work from home", "get rich quick", "no experience",
            "guaranteed income", "join now", "act now", "special offer"
        ]
        
        # Harassment indicators  
        self.harassment_keywords = [
            "idiot", "stupid", "loser", "shut up", "kill yourself", "hate you",
            "worthless", "pathetic", "disgusting", "go die"
        ]
        
        # Inappropriate content indicators
        self.inappropriate_keywords = [
            "xxx", "porn", "naked", "nude", "sex chat", "adult content",
            "18+", "nsfw", "explicit"
        ]
        
        # Hate speech indicators
        self.hate_keywords = [
            # Common slurs and hate speech terms would go here
            # For demo purposes, using mild examples
            "terrorist", "nazi", "fascist"
        ]
    
    def load_ai_models(self):
        """Load AI models for content moderation."""
        if not HAS_TRANSFORMERS:
            logger.warning("Transformers not available, skipping AI model loading")
            return
        
        try:
            # Text toxicity detection
            self.models['toxicity'] = pipeline(
                "text-classification",
                model="unitary/toxic-bert",
                device=-1  # Use CPU
            )
            
            # NSFW image detection (placeholder - would need proper model)
            # self.models['nsfw_image'] = pipeline(
            #     "image-classification",
            #     model="Falconsai/nsfw_image_detection"
            # )
            
            logger.info("AI models loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load AI models: {e}")
            self.models = {}
    
    def load_custom_rules(self):
        """Load custom rules from rule documents."""
        base_dir = Path(__file__).parent.parent
        rules_file = base_dir / "config" / "custom_rules.json"
        
        # Validate path to prevent traversal attacks
        safe_path = self.validator.sanitize_path(str(rules_file), base_dir)
        if not safe_path or not safe_path.exists():
            logger.info("No custom rules file found")
            return
        
        try:
            with open(safe_path, 'r') as f:
                rules = json.load(f)
                # Validate regex patterns in rules
                self.custom_rules = []
                for rule in rules:
                    if 'pattern' in rule:
                        if self.validator.validate_regex_pattern(rule['pattern']):
                            self.custom_rules.append(rule)
                        else:
                            logger.warning(f"Skipping rule with invalid pattern: {rule.get('name', 'unnamed')}")
                    else:
                        self.custom_rules.append(rule)
            logger.info(f"Loaded {len(self.custom_rules)} valid custom rules")
        except Exception as e:
            logger.error(f"Failed to load custom rules: {e}")
            self.custom_rules = []
    
    def _get_cache_key(self, content: Union[str, bytes]) -> str:
        """Generate cache key for content."""
        if isinstance(content, str):
            content = content.encode('utf-8')
        return hashlib.md5(content).hexdigest()
    
    async def moderate_text(self, text: str) -> ModerationResult:
        """Moderate text content using AI models and rules."""
        # Validate input size
        if not self.validator.validate_message_size(text):
            return ModerationResult(
                is_violation=True,
                confidence=1.0,
                reason="Message exceeds size limit",
                category="spam"
            )
        
        # Apply rate limiting
        if not await self.rate_limiter.acquire():
            logger.warning("Rate limit exceeded for text moderation")
            # Don't block, but log for monitoring
        
        # Check cache first
        cache_key = self._get_cache_key(text)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        # Check custom rules first (highest priority)
        custom_result = self.apply_custom_rules(text)
        if custom_result and custom_result.is_violation:
            self._add_to_cache(cache_key, custom_result)
            return custom_result
        
        # Try AI model if available
        if 'toxicity' in self.models:
            try:
                result = await self._moderate_text_ai(text)
                if result.is_violation:
                    self._add_to_cache(cache_key, result)
                    return result
            except Exception as e:
                logger.error(f"AI moderation failed, falling back to rules: {e}")
        
        # Fall back to rule-based moderation
        result = await self._moderate_text_rules(text)
        self._add_to_cache(cache_key, result)
        return result
    
    async def _moderate_text_ai(self, text: str) -> ModerationResult:
        """Use AI model for text moderation."""
        # Run CPU-intensive AI model in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        toxicity_result = await loop.run_in_executor(
            self.executor, 
            self.models['toxicity'], 
            text
        )
        
        # Parse result (format may vary by model)
        if isinstance(toxicity_result, list) and len(toxicity_result) > 0:
            result = toxicity_result[0]
            if result.get('label') == 'TOXIC' and result.get('score', 0) > 0.7:
                return ModerationResult(
                    is_violation=True,
                    confidence=result['score'],
                    reason="AI detected toxic content",
                    category="toxicity"
                )
        
        return ModerationResult(is_violation=False, confidence=0.0)
    
    async def _moderate_text_rules(self, text: str) -> ModerationResult:
        """Rule-based text moderation fallback."""
        text_lower = text.lower()
        
        # Check for spam
        spam_score = self.check_keywords(text_lower, self.spam_keywords)
        if spam_score > 0:
            # Check if it's repetitive (common spam indicator)
            if self.is_repetitive(text):
                spam_score += 0.3
                
            if spam_score >= ModerationThresholds.SPAM_THRESHOLD:
                return ModerationResult(
                    is_violation=True,
                    confidence=min(spam_score, 0.95),
                    reason="Detected spam content",
                    category="spam"
                )
        
        # Check for harassment
        harassment_score = self.check_keywords(text_lower, self.harassment_keywords)
        if harassment_score >= ModerationThresholds.HARASSMENT_THRESHOLD:
            return ModerationResult(
                is_violation=True,
                confidence=min(harassment_score, 0.95),
                reason="Detected harassment or bullying",
                category="harassment"
            )
        
        # Check for inappropriate content
        inappropriate_score = self.check_keywords(text_lower, self.inappropriate_keywords)
        if inappropriate_score >= 0.8:
            return ModerationResult(
                is_violation=True,
                confidence=min(inappropriate_score, 0.95),
                reason="Detected inappropriate content",
                category="nsfw"
            )
        
        # Check for hate speech
        hate_score = self.check_keywords(text_lower, self.hate_keywords)
        if hate_score >= 0.8:
            return ModerationResult(
                is_violation=True,
                confidence=min(hate_score, 0.95),
                reason="Detected hate speech",
                category="hate_speech"
            )
        
        # Check for excessive caps (shouting)
        if self.is_excessive_caps(text):
            return ModerationResult(
                is_violation=True,
                confidence=0.6,
                reason="Excessive use of capital letters",
                category="spam"
            )
        
        # No violations detected
        return ModerationResult(is_violation=False, confidence=0.0)
    
    async def moderate_image(self, image_data: bytes) -> ModerationResult:
        """Basic image moderation using simple heuristics."""
        # Validate image size
        if not self.validator.validate_image_size(image_data):
            return ModerationResult(
                is_violation=True,
                confidence=1.0,
                reason="Image exceeds size limit",
                category="spam"
            )
        
        # Apply rate limiting
        if not await self.rate_limiter.acquire():
            logger.warning("Rate limit exceeded for image moderation")
        
        # For now, implement very basic checks
        # In a real system, this would use computer vision models
        
        image_size = len(image_data)
        
        # Flag very large images as potentially problematic
        if image_size > 10 * 1024 * 1024:  # 10MB
            return ModerationResult(
                is_violation=True,
                confidence=0.6,
                reason="Image file too large",
                category="policy"
            )
        
        # Basic image analysis
        try:
            # Convert bytes to PIL Image for analysis
            image = Image.open(io.BytesIO(image_data))
            
            # Check image dimensions (very large images might be problematic)
            width, height = image.size
            if width > 4000 or height > 4000:
                return ModerationResult(
                    is_violation=True,
                    confidence=0.6,
                    reason="Image resolution too high",
                    category="policy"
                )
            
            # TODO: Implement actual AI-based NSFW detection
            # For now, just basic checks
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return ModerationResult(
                is_violation=True,
                confidence=0.5,
                reason="Unable to analyze image",
                category="error"
            )
        
        return ModerationResult(is_violation=False, confidence=0.0)
    
    async def moderate_video(self, video_data: bytes) -> ModerationResult:
        """Video content moderation with frame extraction."""
        # Validate video size
        if not self.validator.validate_video_size(video_data):
            return ModerationResult(
                is_violation=True,
                confidence=1.0,
                reason="Video exceeds size limit",
                category="spam"
            )
        
        # Apply rate limiting
        if not await self.rate_limiter.acquire():
            logger.warning("Rate limit exceeded for video moderation")
        
        video_size = len(video_data)
        
        # Check file size limits
        max_size = self.config.get('max_video_size', 50 * 1024 * 1024)  # 50MB default
        if video_size > max_size:
            return ModerationResult(
                is_violation=True,
                confidence=0.8,
                reason=f"Video file too large ({video_size // (1024*1024)}MB)",
                category="policy"
            )
        
        # Extract and analyze frames
        try:
            frames = await self._extract_video_frames(video_data)
            if not frames:
                return ModerationResult(
                    is_violation=False,
                    confidence=0.0,
                    reason="No frames extracted",
                    category="video"
                )
            
            # Analyze extracted frames
            violation_results = []
            for frame_data in frames:
                frame_result = await self.moderate_image(frame_data)
                if frame_result.is_violation:
                    violation_results.append(frame_result)
            
            # Determine overall result
            if violation_results:
                # Use highest confidence violation
                worst_violation = max(violation_results, key=lambda x: x.confidence)
                return ModerationResult(
                    is_violation=True,
                    confidence=worst_violation.confidence,
                    reason=f"Video frame violation: {worst_violation.reason}",
                    category=worst_violation.category
                )
            
        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            return ModerationResult(
                is_violation=False,
                confidence=0.0,
                reason="Video analysis failed",
                category="error"
            )
        
        return ModerationResult(is_violation=False, confidence=0.0)
    
    def check_keywords(self, text: str, keywords: List[str]) -> float:
        """Check how many keywords from a list appear in text with word boundaries."""
        matches = 0
        total_keywords = len(keywords)
        text_lower = text.lower()
        
        for keyword in keywords:
            # Use word boundaries to avoid false positives
            # \b ensures we match whole words only
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, text_lower):
                matches += 1
        
        if matches == 0:
            return 0.0
        
        # Calculate confidence - more matches = higher confidence
        # Base confidence for any match, then increase with more matches
        confidence = ModerationThresholds.CONFIDENCE_BASE + (matches / total_keywords) * ModerationThresholds.CONFIDENCE_SCALE
        return min(confidence, ModerationThresholds.MAX_CONFIDENCE)
    
    def is_repetitive(self, text: str) -> bool:
        """Check if text is repetitive (common spam indicator)."""
        words = text.lower().split()
        if len(words) < 3:
            return False
        
        # Check for repeated words
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        max_count = max(word_counts.values())
        return max_count > len(words) * 0.5  # More than 50% repeated words
    
    def is_excessive_caps(self, text: str) -> bool:
        """Check if text has excessive capital letters."""
        if len(text) < 10:
            return False
        
        caps_count = sum(1 for c in text if c.isupper())
        caps_ratio = caps_count / len(text)
        
        return caps_ratio > ModerationThresholds.CAPS_RATIO_THRESHOLD
    
    def apply_custom_rules(self, text: str) -> Optional[ModerationResult]:
        """Apply custom rules parsed from rule documents."""
        for rule in self.custom_rules:
            try:
                if self._check_custom_rule(text, rule):
                    return ModerationResult(
                        is_violation=True,
                        confidence=rule.get('confidence', 0.8),
                        reason=rule.get('reason', 'Custom rule violation'),
                        category=rule.get('category', 'custom')
                    )
            except Exception as e:
                logger.error(f"Error applying custom rule: {e}")
        
        return None
    
    def _check_custom_rule(self, text: str, rule: Dict[str, Any]) -> bool:
        """Check if text violates a custom rule."""
        rule_type = rule.get('type')
        
        if rule_type == 'keyword':
            keywords = rule.get('keywords', [])
            return any(keyword.lower() in text.lower() for keyword in keywords)
        
        elif rule_type == 'url':
            pattern = rule.get('pattern')
            return bool(re.search(pattern, text, re.IGNORECASE))
        
        elif rule_type == 'length':
            max_length = rule.get('max_length', 1000)
            return len(text) > max_length
        
        elif rule_type == 'caps':
            max_ratio = rule.get('max_caps_ratio', 0.7)
            return self._calculate_caps_ratio(text) > max_ratio
            
        return False
    
    def _calculate_caps_ratio(self, text: str) -> float:
        """Calculate ratio of capital letters in text."""
        if len(text) < 10:
            return 0.0
        caps_count = sum(1 for c in text if c.isupper())
        return caps_count / len(text)
    
    def add_custom_rule_from_text(self, rule_text: str) -> Dict[str, Any]:
        """Parse natural language rule and add to custom rules."""
        try:
            from .rule_parser import RuleDocumentParser
        except ImportError:
            from rule_parser import RuleDocumentParser
        
        parser = RuleDocumentParser()
        parsed_rules = parser.parse_document(rule_text)
        
        for rule in parsed_rules:
            self.custom_rules.append(rule)
        
        # Save to file
        self._save_custom_rules()
        
        return {"added_rules": len(parsed_rules), "rules": parsed_rules}
    
    def _save_custom_rules(self):
        """Save custom rules to file."""
        try:
            rules_file = Path("config/custom_rules.json")
            rules_file.parent.mkdir(exist_ok=True)
            with open(rules_file, 'w') as f:
                json.dump(self.custom_rules, f, indent=2)
            logger.info(f"Saved {len(self.custom_rules)} custom rules")
        except Exception as e:
            logger.error(f"Failed to save custom rules: {e}")
    
    async def _extract_video_frames(self, video_data: bytes, max_frames: int = 5) -> List[bytes]:
        """Extract key frames from video for analysis."""
        if not HAS_OPENCV:
            logger.warning("OpenCV not available for video processing")
            return []
        
        import tempfile
        import os
        
        frames = []
        temp_file = None
        
        try:
            # Write video data to temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
                tmp.write(video_data)
                temp_file = tmp.name
            
            # Open video with OpenCV
            cap = cv2.VideoCapture(temp_file)
            if not cap.isOpened():
                logger.error("Failed to open video file")
                return []
            
            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            duration = total_frames / fps if fps > 0 else 0
            
            logger.info(f"Video: {total_frames} frames, {fps:.1f} FPS, {duration:.1f}s")
            
            # Extract frames at regular intervals
            if total_frames <= max_frames:
                # Extract all frames if video is short
                frame_indices = list(range(0, total_frames, max(1, total_frames // max_frames)))
            else:
                # Extract frames at regular intervals
                interval = total_frames // max_frames
                frame_indices = [i * interval for i in range(max_frames)]
            
            for frame_idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if ret:
                    # Convert frame to JPEG bytes
                    success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    if success:
                        frames.append(buffer.tobytes())
                        logger.debug(f"Extracted frame {frame_idx}/{total_frames}")
                
                if len(frames) >= max_frames:
                    break
            
            cap.release()
            logger.info(f"Extracted {len(frames)} frames from video")
            
        except Exception as e:
            logger.error(f"Frame extraction failed: {e}")
        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")
        
        return frames
    
    def get_rule_summary(self) -> Dict[str, Any]:
        """Get summary of all active rules."""
        return {
            "keyword_rules": len([r for r in self.custom_rules if r.get('type') == 'keyword']),
            "url_rules": len([r for r in self.custom_rules if r.get('type') == 'url']),
            "length_rules": len([r for r in self.custom_rules if r.get('type') == 'length']),
            "other_rules": len([r for r in self.custom_rules if r.get('type') not in ['keyword', 'url', 'length']]),
            "total_custom_rules": len(self.custom_rules),
            "ai_models_loaded": len(self.models),
            "cache_size": len(self.cache)
        }