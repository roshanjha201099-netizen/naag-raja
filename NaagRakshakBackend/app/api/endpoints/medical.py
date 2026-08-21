from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.database import get_db
from app.db.models import MedicalFacility
from app.db.schemas import MedicalFacilitySchema

router = APIRouter()

@router.get("/medical-facilities", response_model=List[MedicalFacilitySchema])
async def get_medical_facilities(
    state: Optional[str] = Query(None, description="State / UT filter"),
    district: Optional[str] = Query(None, description="District filter"),
    asv_only: bool = Query(True, description="Only return facilities with ASV in stock"),
    db: AsyncSession = Depends(get_db)
):
    query = select(MedicalFacility)
    if asv_only:
        query = query.where(MedicalFacility.asv_available == True)

    if state and state != "All Regions / Nationwide":
        query = query.where(
            or_(
                MedicalFacility.state.ilike(f"%{state}%"),
                MedicalFacility.address.ilike(f"%{state}%")
            )
        )

    if district:
        query = query.where(MedicalFacility.district.ilike(f"%{district}%"))

    res = await db.execute(query)
    facilities = res.scalars().all()
    return facilities
