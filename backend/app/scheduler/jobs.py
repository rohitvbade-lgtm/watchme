import logging
from datetime import datetime, timezone
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.device import Device
from app.models.notification_event import NotificationEvent
from app.services.notifications.candidate_service import NotificationCandidateService
from app.services.notifications.ai_generator import AINotificationGenerator
from app.services.notifications.template_generator import TemplateNotificationGenerator
from app.services.push.fcm import FCMPushProvider
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

candidate_service = NotificationCandidateService()
push_provider = FCMPushProvider()
ai_generator = AINotificationGenerator()
template_generator = TemplateNotificationGenerator()

async def generate_and_send_notifications():
    logger.info("Starting scheduled notification job...")
    
    async with AsyncSessionLocal() as db:
        # Fetch all registered devices with push tokens
        result = await db.execute(select(Device).where(Device.push_token.isnot(None)))
        devices = result.scalars().all()
        
        if not devices:
            logger.info("No registered devices with push tokens found. Skipping cycle.")
            return

        logger.info(f"Processing notifications for {len(devices)} device(s)...")
        for device in devices:
            try:
                candidate = await candidate_service.select_candidate(db, device.device_id)
                if not candidate:
                    logger.info(f"No eligible candidate found for device {device.device_id} (empty watchlist or already notified in last 24h).")
                    continue
                    
                item_title = candidate.media_item.title
                poster_path = candidate.media_item.poster_path
                image_url = None
                if poster_path:
                    image_url = poster_path if poster_path.startswith("http") else f"{settings.tmdb_image_base_url}{poster_path}"

                media_item_dict = {
                    "title": item_title,
                    "overview": candidate.media_item.overview,
                    "media_type": candidate.media_item.media_type,
                    "genres": candidate.media_item.genres_json or []
                }
                
                try:
                    text, method = await ai_generator.generate(media_item_dict)
                except Exception as e:
                    logger.warning(f"AI generation failed, falling back to template: {e}")
                    text, method = await template_generator.generate(media_item_dict)
                
                logger.info(f"Generated notification ({method}) for '{item_title}': \"{text}\"")

                success = await push_provider.send(
                    push_token=device.push_token,
                    title=item_title,
                    body=text,
                    image_url=image_url,
                    data={
                        "url": f"/item/{candidate.id}",
                        "itemTitle": item_title,
                        "imageUrl": image_url or ""
                    }
                )
                
                event = NotificationEvent(
                    device_id=device.device_id,
                    watchlist_item_id=candidate.id,
                    item_title=item_title,
                    item_image_url=image_url,
                    text=text,
                    generation_method=method,
                    status="SENT" if success else "FAILED",
                    sent_at=datetime.now(timezone.utc) if success else None
                )
                db.add(event)
                await db.commit()
                logger.info(f"Notification saved for '{item_title}' (status={'SENT' if success else 'FAILED'}).")
                
            except Exception as e:
                logger.error(f"Failed to process notifications for device {device.device_id}: {e}")
                await db.rollback()
                
    logger.info("Finished scheduled notification job.")
