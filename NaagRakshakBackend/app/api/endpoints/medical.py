import math
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.database import get_db
from app.db.models import MedicalFacility
from app.db.schemas import MedicalFacilitySchema

router = APIRouter()

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes exact Haversine great-circle distance between two GPS points in kilometers.
    """
    R = 6371.0  # Earth's mean radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return float(round(R * c, 2))

@router.get("/medical-facilities", response_model=List[MedicalFacilitySchema])
async def get_medical_facilities(
    state: Optional[str] = Query(None, description="State / UT filter"),
    district: Optional[str] = Query(None, description="District filter"),
    asv_only: bool = Query(True, description="Only return facilities with ASV in stock"),
    user_lat: Optional[float] = Query(None, description="User GPS Latitude"),
    user_lng: Optional[float] = Query(None, description="User GPS Longitude"),
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

    facility_schemas = []
    for f in facilities:
        schema = MedicalFacilitySchema.model_validate(f)
        if user_lat is not None and user_lng is not None and f.latitude is not None and f.longitude is not None:
            schema.distance_km = haversine_distance(user_lat, user_lng, f.latitude, f.longitude)
        else:
            schema.distance_km = None
        facility_schemas.append(schema)

    # Sort nearest-first if distance is calculated
    if user_lat is not None and user_lng is not None:
        facility_schemas.sort(key=lambda x: (x.distance_km if x.distance_km is not None else 99999.0))

    return facility_schemas
