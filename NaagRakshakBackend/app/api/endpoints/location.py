import httpx
import logging
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from app.db.schemas import LocationPayloadSchema

logger = logging.getLogger("naagrakshak.location")
router = APIRouter()

@router.get("/geocode", response_model=LocationPayloadSchema)
async def geocode_manual_location(
    query: str = Query(..., description="Manual location string e.g. 'Lohna, Madhubani, Bihar'")
):
    """
    Geocodes a manual user-entered location query 
    using live OpenStreetMap Nominatim GIS API and returns authoritative Lat/Lng & location components.
    """
    logger.info(f">> [LOCATION API] Geocoding Manual Query: '{query}'")
    
    clean_query = query.strip()
    if not clean_query:
        raise HTTPException(status_code=400, detail="Location query string cannot be empty.")

    nominatim_url = f"https://nominatim.openstreetmap.org/search?q={clean_query}&format=json&addressdetails=1&limit=1"
    headers = {
        "User-Agent": "NaagRakshak/1.0 (India Emergency Snakebite App; geocode@naagrakshak.org)"
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(nominatim_url, headers=headers)
            if res.status_code == 200:
                results = res.json()
                if results and len(results) > 0:
                    item = results[0]
                    lat = float(item["lat"])
                    lng = float(item["lon"])
                    display_name = item.get("display_name", clean_query)
                    addr = item.get("address", {})
                    logger.info(f"📍 ADDRESS DATA: {addr}")

                    state = addr.get("state") or addr.get("region") or clean_query
                    district = addr.get("state_district") or addr.get("county") or addr.get("subdistrict") or addr.get("city") or "Local District"
                    country = addr.get("country", "India")

                    logger.info(f"✅ [LOCATION API] Geocoded '{clean_query}' -> Lat={lat}, Lng={lng}, Location='{display_name}'")

                    return LocationPayloadSchema(
                        latitude=lat,
                        longitude=lng,
                        accuracy_meters=None,
                        display_name=display_name,
                        district=district,
                        state=state,
                        country=country,
                        region=state,
                        source="MANUAL_GEOCODED",
                        status="MANUAL"
                    )
    except Exception as ex:
        logger.warning(f"⚠️ [LOCATION API] Live Nominatim geocoding failed or timed out: {ex}")

    raise HTTPException(status_code=404, detail=f"Could not geocode location query '{clean_query}'. Please check location name.")
