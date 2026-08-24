import httpx
import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.db.models import RescueFacility
from app.db.schemas import RescueFacilitySchema

logger = logging.getLogger("naagrakshak.rescue")
router = APIRouter()

async def fetch_realtime_gis_rescuers(lat: float, lon: float, state_name: Optional[str] = None) -> List[RescueFacilitySchema]:
    """
    Disabled external OpenStreetMap network calls for fast local execution.
    """
    return []


@router.get("/rescue", response_model=List[RescueFacilitySchema])
async def get_rescue_facilities(
    state: Optional[str] = Query(None, description="State filter"),
    user_lat: Optional[float] = Query(None, description="User GPS Latitude"),
    user_lng: Optional[float] = Query(None, description="User GPS Longitude"),
    db: AsyncSession = Depends(get_db)
):
    print(f">> [FRONTEND REQUEST] GET /api/v1/rescue (State: '{state}', GPS: Lat={user_lat}, Lng={user_lng})")
    query = select(RescueFacility)
    if state and state != "All Regions / Nationwide":
        query = query.where(RescueFacility.state == state)

    res = await db.execute(query)
    rescue_teams = [RescueFacilitySchema.model_validate(r) for r in res.scalars().all()]

    # Fetch live GIS forest & wildlife rescue squads around user GPS coordinates
    if user_lat is not None and user_lng is not None:
        live_rescuers = await fetch_realtime_gis_rescuers(user_lat, user_lng, state)
        for live_r in live_rescuers:
            if not any(live_r.name.lower()[:12] in r.name.lower() for r in rescue_teams):
                rescue_teams.append(live_r)

    # Always ensure National Emergency 1926 Helpline is present
    if not any("1926" in r.phone for r in rescue_teams):
        rescue_teams.insert(0, RescueFacilitySchema(
            id="resc_nat_1926",
            name="National Forest Emergency Helpline",
            organization="Ministry of Environment, Forest & Climate Change",
            state="All Regions / Nationwide",
            district="All Districts",
            phone="1926",
            response_hours="24/7 Emergency Wildlife Helpline (Toll-Free)"
        ))

    # Print formatted ASCII block of rescue contacts being sent to frontend
    print("\n" + "="*75)
    print(f">> [BACKEND RESPONSE] GET /api/v1/rescue -> Returning {len(rescue_teams)} Rescue Helpline(s):")
    print("="*75)
    for idx, r in enumerate(rescue_teams, 1):
        print(f"  {idx}. {r.name}")
        print(f"     * Org:    '{r.organization}'")
        print(f"     * Phone:  '{r.phone}'")
        print(f"     * Region: '{r.state}' ({r.district})")
    print("="*75 + "\n")

    return rescue_teams
