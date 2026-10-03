from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.schemas.notification import DeviceRegisterRequest
from app.models.device import Device

router = APIRouter()

@router.post("/register")
async def register_device(request: DeviceRegisterRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(Device).where(Device.device_id == request.deviceId)
    result = await db.execute(stmt)
    device = result.scalar_one_or_none()
    
    if device:
        device.platform = request.platform
        device.push_token = request.pushToken
    else:
        device = Device(
            device_id=request.deviceId,
            platform=request.platform,
            push_token=request.pushToken
        )
        db.add(device)
        
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        
    return {"status": "ok"}
