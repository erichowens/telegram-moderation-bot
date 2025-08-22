"""
Telegram moderation bot main module.
"""

import logging
import asyncio
import os
import time
from datetime import datetime
from typing import Optional, Callable, Dict, Any
from telegram import Update, Message
from telegram.ext import Application, MessageHandler, filters, ContextTypes

try:
    from .moderation import ContentModerator, ModerationResult
    from .config import Config
    from .advanced_moderation import AdvancedModerationSystem
    HAS_ADVANCED = True
except ImportError:
    try:
        from moderation import ContentModerator, ModerationResult
        from config import Config
        from advanced_moderation import AdvancedModerationSystem
        HAS_ADVANCED = True
    except ImportError:
        from moderation import ContentModerator, ModerationResult
        from config import Config
        HAS_ADVANCED = False
        logger.warning("Advanced moderation not available")

logger = logging.getLogger(__name__)


class TelegramModerationBot:
    """Main bot class for handling Telegram moderation."""
    
    def __init__(self, token: str, violation_callback: Optional[Callable] = None):
        self.token = token
        self.violation_callback = violation_callback
        self.application = Application.builder().token(token).build()
        self.moderator = None
        self.advanced_moderator = None
        self.start_time = time.time()
        self.stats = {
            "messages_checked": 0,
            "violations_found": 0,
            "actions_taken": 0,
            "images_analyzed": 0,
            "patterns_detected": 0
        }
        self._setup_handlers()
        self._load_moderator()
        self._load_advanced_moderator()
    
    def _load_moderator(self):
        """Load content moderator with default settings."""
        try:
            config = Config()
            self.moderator = ContentModerator(config)
        except FileNotFoundError as e:
            logger.critical(f"Configuration file not found: {e}")
            raise
        except Exception as e:
            logger.critical(f"Failed to load moderator configuration: {e}")
            raise RuntimeError(f"Cannot initialize bot without valid configuration: {e}")
    
    def _load_advanced_moderator(self):
        """Load advanced moderation system if available."""
        if HAS_ADVANCED:
            try:
                self.advanced_moderator = AdvancedModerationSystem()
                asyncio.create_task(self.advanced_moderator.initialize())
                logger.info("Advanced moderation system loaded")
            except Exception as e:
                logger.warning(f"Failed to load advanced moderation: {e}")
                self.advanced_moderator = None
        else:
            logger.info("Advanced moderation not available")
    
    def _setup_handlers(self):
        """Set up message handlers."""
        # Handle text messages
        text_handler = MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handle_text_message
        )
        self.application.add_handler(text_handler)
        
        # Handle photo messages
        photo_handler = MessageHandler(
            filters.PHOTO,
            self.handle_photo_message
        )
        self.application.add_handler(photo_handler)
        
        # Handle video messages
        video_handler = MessageHandler(
            filters.VIDEO,
            self.handle_video_message
        )
        self.application.add_handler(video_handler)
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages for moderation."""
        message = update.message
        if not message or not message.text:
            return
        
        self.stats["messages_checked"] += 1
        
        try:
            # Track message for pattern detection if advanced moderation is available
            if self.advanced_moderator and message.from_user and message.chat:
                self.advanced_moderator.track_message(
                    user_id=str(message.from_user.id),
                    group_id=str(message.chat.id),
                    message=message.text
                )
                
                # Check for threat patterns
                patterns = self.advanced_moderator.check_threat_patterns(str(message.chat.id))
                if patterns:
                    self.stats["patterns_detected"] += len(patterns)
                    for pattern in patterns:
                        if pattern['confidence'] > 0.8:
                            logger.warning(f"Threat pattern detected: {pattern['type']} - {pattern['affected_users']}")
                            # Could trigger automatic actions based on pattern type
            
            # Moderate the text content
            result = await self.moderator.moderate_text(message.text)
            
            if result.is_violation:
                await self.handle_violation(message, result, "text")
                
        except Exception as e:
            logger.error(f"Error moderating text message: {e}")
    
    async def handle_photo_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming photo messages for moderation."""
        message = update.message
        if not message or not message.photo:
            return
        
        self.stats["messages_checked"] += 1
        self.stats["images_analyzed"] += 1
        
        try:
            # Get the largest photo
            photo = message.photo[-1]
            photo_file = await photo.get_file()
            photo_data = await photo_file.download_as_bytearray()
            
            # Use advanced moderation if available
            if self.advanced_moderator:
                try:
                    advanced_result = await self.advanced_moderator.moderate_image(bytes(photo_data))
                    
                    if advanced_result['is_violation']:
                        result = ModerationResult(
                            is_violation=True,
                            confidence=advanced_result['confidence'],
                            reason=f"Image contains: {advanced_result['description']}",
                            category="nsfw_content"
                        )
                        await self.handle_violation(message, result, "image")
                        return
                except Exception as e:
                    logger.warning(f"Advanced image moderation failed: {e}")
            
            # Fallback to basic moderation
            result = await self.moderator.moderate_image(bytes(photo_data))
            
            if result.is_violation:
                await self.handle_violation(message, result, "image")
                
        except Exception as e:
            logger.error(f"Error moderating photo message: {e}")
    
    async def handle_video_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming video messages for moderation with frame extraction."""
        message = update.message
        if not message or not message.video:
            return
        
        self.stats["messages_checked"] += 1
        
        try:
            # Quick policy checks first
            if message.video.duration > 600:  # 10 minutes
                result = ModerationResult(
                    is_violation=True,
                    confidence=0.8,
                    reason="Video too long (over 10 minutes)",
                    category="policy"
                )
                await self.handle_violation(message, result, "video")
                return
            
            # Download and analyze video content
            video_file = await message.video.get_file()
            video_data = await video_file.download_as_bytearray()
            
            # Use advanced moderation if available
            if self.advanced_moderator:
                try:
                    advanced_result = await self.advanced_moderator.moderate_video(bytes(video_data))
                    
                    if advanced_result['is_violation']:
                        result = ModerationResult(
                            is_violation=True,
                            confidence=advanced_result['confidence'],
                            reason=f"Video content violation: {advanced_result['description']}",
                            category="nsfw_content"
                        )
                        await self.handle_violation(message, result, "video")
                        logger.info(f"Video analysis: {advanced_result['frames_analyzed']} frames, {advanced_result['violation_count']} violations")
                        return
                except Exception as e:
                    logger.warning(f"Advanced video moderation failed: {e}")
            
            # Fallback to basic video moderation
            result = await self.moderator.moderate_video(bytes(video_data))
            
            if result.is_violation:
                await self.handle_violation(message, result, "video")
                
        except Exception as e:
            logger.error(f"Error moderating video message: {e}")
    
    async def handle_violation(self, message: Message, result: ModerationResult, content_type: str):
        """Handle a detected violation."""
        self.stats["violations_found"] += 1
        
        violation_data = {
            "timestamp": datetime.now().isoformat(),
            "chat_id": message.chat_id,
            "chat_title": getattr(message.chat, 'title', 'Private'),
            "user_id": message.from_user.id if message.from_user else None,
            "username": message.from_user.username if message.from_user else None,
            "content_type": content_type,
            "violation_type": result.category or "unknown",
            "confidence": result.confidence,
            "reason": result.reason,
            "action_taken": None
        }
        
        # Take action based on configuration
        action_taken = await self.take_action(message, result)
        violation_data["action_taken"] = action_taken
        
        if action_taken:
            self.stats["actions_taken"] += 1
        
        # Notify GUI if callback is set
        if self.violation_callback:
            try:
                self.violation_callback(violation_data)
            except Exception as e:
                logger.error(f"Error in violation callback: {e}")
        
        logger.info(f"Violation detected: {result.category} (confidence: {result.confidence:.2f})")
    
    async def take_action(self, message: Message, result: ModerationResult) -> Optional[str]:
        """Take appropriate action based on the violation."""
        try:
            # For high confidence violations, delete the message
            if result.confidence > 0.8:
                await message.delete()
                return "deleted"
            
            # For medium confidence violations, warn the user
            elif result.confidence > 0.6:
                warning_text = f"⚠️ Your message may violate community guidelines: {result.reason}"
                await message.reply_text(warning_text)
                return "warned"
            
            # For low confidence violations, just log
            else:
                return "logged"
                
        except Exception as e:
            logger.error(f"Error taking action: {e}")
            return "error"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current bot statistics."""
        return self.stats.copy()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check and return system status."""
        try:
            uptime = time.time() - self.start_time
            
            # Check moderator status
            moderator_status = "healthy"
            models_loaded = 0
            cache_size = 0
            
            if self.moderator:
                if hasattr(self.moderator, 'models'):
                    models_loaded = len(self.moderator.models)
                if hasattr(self.moderator, 'cache'):
                    cache_size = len(self.moderator.cache)
            
            # Check if bot is responsive
            try:
                bot_info = await self.application.bot.get_me()
                bot_responsive = bot_info is not None
            except:
                bot_responsive = False
                bot_info = None
            
            return {
                "status": "healthy" if bot_responsive else "degraded",
                "uptime_seconds": uptime,
                "bot_info": {
                    "username": bot_info.username if bot_info else None,
                    "responsive": bot_responsive
                },
                "moderator": {
                    "status": moderator_status,
                    "models_loaded": models_loaded,
                    "cache_size": cache_size,
                    "max_cache_size": getattr(self.moderator, 'MAX_CACHE_SIZE', 1000) if self.moderator else 1000
                },
                "statistics": self.stats,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def run(self):
        """Start the bot."""
        logger.info("Starting Telegram moderation bot...")
        self.application.run_polling()
    
    def stop(self):
        """Stop the bot and cleanup resources."""
        if self.application:
            self.application.stop_running()
        # Clean up moderator resources
        if self.moderator and hasattr(self.moderator, 'cleanup'):
            self.moderator.cleanup()


if __name__ == "__main__":
    # Get bot token from environment variable
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        print("Error: Please set the TELEGRAM_BOT_TOKEN environment variable")
        print("Example: export TELEGRAM_BOT_TOKEN='your-bot-token-here'")
        exit(1)
    
    bot = TelegramModerationBot(token)
    bot.run()