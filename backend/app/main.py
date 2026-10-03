from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
import logging

from app.config import get_settings
from app.api import search, watchlist, devices, notifications
from app.scheduler.jobs import generate_and_send_notifications

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up...")
    scheduler.add_job(
        generate_and_send_notifications,
        'interval',
        seconds=settings.notification_interval_seconds,
        id='notification_job'
    )
    scheduler.start()
    yield
    # Shutdown
    logger.info("Shutting down...")
    scheduler.shutdown()

app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(devices.router, prefix="/api/devices", tags=["devices"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
