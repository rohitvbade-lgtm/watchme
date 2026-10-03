from typing import Dict, Any, Tuple
from app.services.notifications.generator import NotificationGenerator
from app.config import get_settings
from groq import AsyncGroq
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

class AINotificationGenerator(NotificationGenerator):
    def __init__(self):
        self.api_key = settings.groq_api_key
        self.model = settings.groq_model
        self.client = AsyncGroq(api_key=self.api_key) if self.api_key else None

    async def generate(self, media_item: Dict[str, Any]) -> Tuple[str, str]:
        if not self.client:
            raise ValueError("Groq API key not configured")
            
        title = media_item.get("title", "Unknown")
        overview = media_item.get("overview", "")
        media_type = media_item.get("media_type", "media")
        
        prompt = (
            f"Write a short, catchy, consumption-oriented push notification (1-2 sentences, max 120 chars) "
            f"to entice a user to watch the {media_type} '{title}'.\n"
            f"Overview: {overview}\n"
            f"Do NOT invent facts. Do NOT say '{title} is in your watchlist'. "
            f"Make it feel like an editorial hook."
        )
        
        try:
            chat_completion = await self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a creative copywriter for a streaming app. Reply ONLY with the notification text, no quotes, no extra conversational text."
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model,
                max_tokens=50,
                temperature=0.7,
            )
            text = chat_completion.choices[0].message.content.strip().strip('"\'')
            if len(text) > 200:
                text = text[:197] + "..."
            return text, "ai"
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
