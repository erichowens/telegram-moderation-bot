"""
Moderation logic using simple rules and basic AI models.
Designed to be easy to understand and modify for non-technical users.
"""

import logging
import re
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ModerationResult:
    """Result of content moderation."""
    is_violation: bool
    confidence: float
    reason: Optional[str] = None
    category: Optional[str] = None


class ContentModerator:
    """Handles content moderation using simple rules and basic AI."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.load_simple_rules()
    
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
    
    async def moderate_text(self, text: str) -> ModerationResult:
        """Moderate text content using simple keyword matching."""
        text_lower = text.lower()
        
        # Check for spam
        spam_score = self.check_keywords(text_lower, self.spam_keywords)
        if spam_score > 0:
            # Check if it's repetitive (common spam indicator)
            if self.is_repetitive(text):
                spam_score += 0.3
                
            if spam_score >= 0.6:
                return ModerationResult(
                    is_violation=True,
                    confidence=min(spam_score, 0.95),
                    reason="Detected spam content",
                    category="spam"
                )
        
        # Check for harassment
        harassment_score = self.check_keywords(text_lower, self.harassment_keywords)
        if harassment_score >= 0.7:
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
        
        # For demo purposes, randomly flag 5% of images
        # In reality, you'd use image analysis models
        import random
        if random.random() < 0.05:
            return ModerationResult(
                is_violation=True,
                confidence=0.7,
                reason="Potentially inappropriate image content",
                category="nsfw"
            )
        
        return ModerationResult(is_violation=False, confidence=0.0)
    
    async def moderate_video(self, video_data: bytes) -> ModerationResult:
        """Basic video moderation."""
        # Simple size-based check for demo
        video_size = len(video_data)
        
        # Flag very large videos
        if video_size > 100 * 1024 * 1024:  # 100MB
            return ModerationResult(
                is_violation=True,
                confidence=0.7,
                reason="Video file too large",
                category="policy"
            )
        
        return ModerationResult(is_violation=False, confidence=0.0)
    
    def check_keywords(self, text: str, keywords: List[str]) -> float:
        """Check how many keywords from a list appear in text."""
        matches = 0
        total_keywords = len(keywords)
        
        for keyword in keywords:
            if keyword in text:
                matches += 1
        
        if matches == 0:
            return 0.0
        
        # Calculate confidence based on keyword density
        confidence = (matches / total_keywords) * 0.8 + 0.2
        return min(confidence, 0.95)
    
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
        
        return caps_ratio > 0.7  # More than 70% caps