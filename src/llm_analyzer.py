import os
import logging
import json
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Try to import OpenAI, handle failure gracefully
try:
    from openai import AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

logger = logging.getLogger(__name__)

@dataclass
class SentimentResult:
    is_danger: bool
    category: str  # fud, shilling, scam, distress
    confidence: float
    explanation: str
    suggested_action: str

class LLMSentimentAnalyzer:
    """
    Advanced context-aware analysis using LLMs.
    Detects FUD, subtly malicious intent, and complex scams.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None
        if HAS_OPENAI and self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            logger.warning("OpenAI client not initialized. Sentiment Guard will be disabled.")

    async def analyze_text(self, text: str, context_messages: List[str] = []) -> SentimentResult:
        """
        Analyze text for complex threats (FUD, Competitor Shilling, etc).
        """
        if not self.client:
            return SentimentResult(False, "unknown", 0.0, "LLM not configured", "none")

        system_prompt = """
        You are a Security Analyst for a Telegram community. 
        Analyze the following message for subtle threats that regex misses.
        
        Categories to detect:
        1. FUD (Fear, Uncertainty, Doubt): Claims that the project is dead, devs are selling, or rug pull imminent.
        2. Competitor Shilling: Subtle promotion of other tokens/projects.
        3. Social Engineering: Attempts to trick admins or users (e.g., "I can't connect wallet, DM me").
        4. Distress: Genuine user needing help (not a threat, but distinct).
        
        Output JSON only:
        {
            "is_danger": boolean,
            "category": "fud" | "shilling" | "scam" | "distress" | "safe",
            "confidence": float (0.0-1.0),
            "explanation": "brief reason",
            "suggested_action": "delete" | "warn" | "alert_admin" | "none"
        }
        """
        
        user_prompt = f"Message: {text}\n"
        if context_messages:
            user_prompt += f"Context (last 3 msgs): {json.dumps(context_messages)}"

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview", # or gpt-3.5-turbo for speed/cost
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            data = json.loads(response.choices[0].message.content)
            
            return SentimentResult(
                is_danger=data.get("is_danger", False),
                category=data.get("category", "safe"),
                confidence=data.get("confidence", 0.0),
                explanation=data.get("explanation", ""),
                suggested_action=data.get("suggested_action", "none")
            )
            
        except Exception as e:
            logger.error(f"LLM Analysis failed: {e}")
            return SentimentResult(False, "error", 0.0, str(e), "none")

    async def analyze_batch(self, messages: List[str]) -> List[SentimentResult]:
        """Analyze a batch of messages (useful for historical scanning)."""
        # TODO: Implement batch processing
        pass
