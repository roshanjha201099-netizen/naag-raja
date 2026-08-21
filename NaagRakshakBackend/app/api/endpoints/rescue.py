from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.db.models import RescueFacility
from app.db.schemas import RescueFacilitySchema

router = APIRouter()

@router.get("/rescue", response_model=List[RescueFacilitySchema])
async def get_rescue_facilities(
    state: Optional[str] = Query(None, description="State filter"),
    db: AsyncSession = Depends(get_db)
):
    query = select(RescueFacility)
    if state and state != "All Regions / Nationwide":
        query = query.where(RescueFacility.state == state)

    res = await db.execute(query)
    rescue_teams = res.scalars().all()
    return rescue_teams
