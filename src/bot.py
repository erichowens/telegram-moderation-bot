"""
Telegram moderation bot main module.
"""

import logging
import asyncio
from datetime import datetime
from typing import Optional, Callable, Dict, Any
from telegram import Update, Message
from telegram.ext import Application, MessageHandler, filters, ContextTypes

from .moderation import ContentModerator, ModerationResult
from .config import Config

logger = logging.getLogger(__name__)


class TelegramModerationBot:
    """Main bot class for handling Telegram moderation."""
    
    def __init__(self, token: str, violation_callback: Optional[Callable] = None):
        self.token = token
        self.violation_callback = violation_callback
        self.application = Application.builder().token(token).build()
        self.moderator = None
        self.stats = {
            "messages_checked": 0,
            "violations_found": 0,
            "actions_taken": 0
        }
        self._setup_handlers()
        self._load_moderator()
    
    def _load_moderator(self):
        """Load content moderator with default settings."""
        try:
            config = Config()
            self.moderator = ContentModerator(config)
        except:
            # Use simple fallback moderator if config fails
            self.moderator = ContentModerator({})
    
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
        
        try:
            # Get the largest photo
            photo = message.photo[-1]
            photo_file = await photo.get_file()
            photo_data = await photo_file.download_as_bytearray()
            
            # Moderate the image content
            result = await self.moderator.moderate_image(bytes(photo_data))
            
            if result.is_violation:
                await self.handle_violation(message, result, "image")
                
        except Exception as e:
            logger.error(f"Error moderating photo message: {e}")
    
    async def handle_video_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming video messages for moderation."""
        message = update.message
        if not message or not message.video:
            return
        
        self.stats["messages_checked"] += 1
        
        try:
            video_file = await message.video.get_file()
            # For demo, we'll skip actual video download due to size
            # In production, you might download and analyze key frames
            
            # Simple policy: flag videos over certain size or duration
            if message.video.duration > 300:  # 5 minutes
                result = ModerationResult(
                    is_violation=True,
                    confidence=0.6,
                    reason="Video too long",
                    category="policy"
                )
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
    
    def run(self):
        """Start the bot."""
        logger.info("Starting Telegram moderation bot...")
        self.application.run_polling()
    
    def stop(self):
        """Stop the bot."""
        if self.application:
            self.application.stop_running()


if __name__ == "__main__":
    bot = TelegramModerationBot("YOUR_BOT_TOKEN")
    bot.run()