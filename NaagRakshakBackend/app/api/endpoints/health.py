import time
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db, active_db_type
from app.services.inference import ml_engine
from app.db.schemas import HealthResponse

router = APIRouter()
start_time = time.time()

@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    db_connected = False
    try:
        await db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    uptime = float(round(time.time() - start_time, 2))

    return HealthResponse(
        status="HEALTHY" if (db_connected and ml_engine.is_loaded) else "DEGRADED",
        database_connected=db_connected,
        active_db_engine=active_db_type,
        model_loaded=ml_engine.is_loaded,
        class_count=len(ml_engine.idx_to_class),
        uptime_seconds=uptime
    )
