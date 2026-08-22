import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.db.models import SnakeSighting
from app.db.schemas import SnakeSightingCreateSchema, SnakeSightingResponseSchema

logger = logging.getLogger("naagrakshak.sighting")
router = APIRouter()

@router.post("/sightings", response_model=SnakeSightingResponseSchema)
async def report_sighting(
    sighting: SnakeSightingCreateSchema,
    db: AsyncSession = Depends(get_db)
):
    sighting_id = str(uuid.uuid4())
    new_sighting = SnakeSighting(
        id=sighting_id,
        species_name=sighting.species_name,
        scientific_name=sighting.scientific_name,
        safety_level=sighting.safety_level,
        latitude=sighting.latitude,
        longitude=sighting.longitude,
        state=sighting.state,
        district=sighting.district,
        notes=sighting.notes,
        image_reference=sighting.image_reference,
        verified=False,
        created_at=datetime.utcnow()
    )
    db.add(new_sighting)
    await db.commit()
    await db.refresh(new_sighting)

    logger.info(f"Snake sighting reported: {sighting_id} ({sighting.species_name} in {sighting.state})")

    return SnakeSightingResponseSchema(
        id=new_sighting.id,
        species_name=new_sighting.species_name,
        scientific_name=new_sighting.scientific_name,
        safety_level=new_sighting.safety_level,
        latitude=new_sighting.latitude,
        longitude=new_sighting.longitude,
        state=new_sighting.state,
        district=new_sighting.district,
        notes=new_sighting.notes,
        verified=new_sighting.verified,
        created_at=str(new_sighting.created_at)
    )
