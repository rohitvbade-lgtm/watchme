import logging
import asyncio
from typing import Optional, Dict, Any
import firebase_admin
from firebase_admin import credentials, messaging
from pathlib import Path
from app.services.push.base import PushNotificationProvider
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class FCMPushProvider(PushNotificationProvider):
    def __init__(self):
        self._initialized = False
        self._has_credentials = False

    @staticmethod
    def _resolve_credentials_path(raw_path: str) -> Optional[str]:
        if not raw_path:
            return None
        p = Path(raw_path)
        if p.exists() and p.is_file():
            return str(p.resolve())

        clean_name = raw_path.lstrip("/\\")
        this_file = Path(__file__).resolve()
        candidates = [
            Path.cwd() / raw_path,
            Path.cwd() / clean_name,
            this_file.parents[3] / clean_name,  # backend root
            this_file.parents[4] / clean_name,  # workspace root
            Path.cwd().parent / clean_name,
        ]
        for c in candidates:
            if c.exists() and c.is_file():
                return str(c.resolve())
        return str(p)

    def _init_firebase(self):
        if self._initialized:
            return

        if not settings.fcm_credentials_path:
            logger.warning("FCM credentials not configured — push notifications disabled.")
            self._initialized = True
            self._has_credentials = False
            return

        try:
            if not firebase_admin._apps:
                resolved_path = self._resolve_credentials_path(settings.fcm_credentials_path)
                cred = credentials.Certificate(resolved_path)
                firebase_admin.initialize_app(cred)
            self._initialized = True
            self._has_credentials = True
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
            self._initialized = True
            self._has_credentials = False

    async def send(
        self,
        push_token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        image_url: Optional[str] = None
    ) -> bool:
        self._init_firebase()

        if push_token.startswith("simulated_") or push_token == "simulated":
            # Log what would have been sent (useful for dev)
            logger.info(f"[FCM-SIMULATED] To: {push_token} | {title}: {body} | Image: {image_url}")
            return True

        if not self._has_credentials:
            logger.warning(f"FCM credentials not available — cannot send to {push_token}")
            return False

        # FCM requires all data values to be strings
        str_data = {k: str(v) for k, v in (data or {}).items()}
        if image_url:
            str_data["imageUrl"] = str(image_url)
        if title:
            str_data["itemTitle"] = str(title)

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                    image=image_url if image_url else None
                ),
                data=str_data,
                token=push_token,
            )
            # firebase_admin.messaging.send() is synchronous — run in thread
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: messaging.send(message))
            logger.info(f"FCM sent successfully: {response}")
            return True
        except Exception as e:
            logger.error(f"FCM send failed for token {push_token[:12]}...: {e}")
            return False
