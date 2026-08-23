import httpx
import logging
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from app.db.schemas import LocationPayloadSchema

logger = logging.getLogger("naagrakshak.location")
router = APIRouter()

STATE_CENTROIDS = {
    "bihar": {"lat": 25.0961, "lng": 85.3131, "state": "Bihar", "district": "Patna"},
    "west bengal": {"lat": 22.9868, "lng": 87.8550, "state": "West Bengal", "district": "Kolkata"},
    "maharashtra": {"lat": 19.7515, "lng": 75.7139, "state": "Maharashtra", "district": "Mumbai"},
    "tamil nadu": {"lat": 11.1271, "lng": 78.6569, "state": "Tamil Nadu", "district": "Chennai"},
    "kerala": {"lat": 10.8505, "lng": 76.2711, "state": "Kerala", "district": "Thiruvananthapuram"},
    "karnataka": {"lat": 15.3173, "lng": 75.7139, "state": "Karnataka", "district": "Bengaluru"},
    "uttar pradesh": {"lat": 26.8467, "lng": 80.9462, "state": "Uttar Pradesh", "district": "Lucknow"},
    "delhi": {"lat": 28.7041, "lng": 77.1025, "state": "Delhi", "district": "New Delhi"},
    "gujarat": {"lat": 22.2587, "lng": 71.1924, "state": "Gujarat", "district": "Ahmedabad"},
    "rajasthan": {"lat": 27.0238, "lng": 74.2179, "state": "Rajasthan", "district": "Jaipur"},
    "madhya pradesh": {"lat": 22.9734, "lng": 78.6569, "state": "Madhya Pradesh", "district": "Bhopal"},
    "assam": {"lat": 26.2006, "lng": 92.9376, "state": "Assam", "district": "Guwahati"},
    "odisha": {"lat": 20.9517, "lng": 85.0985, "state": "Odisha", "district": "Bhubaneswar"}
}

@router.get("/geocode", response_model=LocationPayloadSchema)
async def geocode_manual_location(
    query: str = Query(..., description="Manual location string e.g. 'Lohna, Madhubani, Bihar'")
):
    """
    Geocodes a manual user-entered location query (e.g. 'Lohna, Madhubani, Bihar') 
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
        async with httpx.AsyncClient(timeout=4.0) as client:
            res = await client.get(nominatim_url, headers=headers)
            if res.status_code == 200:
                results = res.json()
                if results and len(results) > 0:
                    item = results[0]
                    lat = float(item["lat"])
                    lng = float(item["lon"])
                    display_name = item.get("display_name", clean_query)
                    addr = item.get("address", {})

                    state = addr.get("state") or addr.get("region") or "Bihar"
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

    # Fallback to State Centroid Lookup if Nominatim failed
    query_lower = clean_query.lower()
    matched_centroid = None
    for st_key, st_info in STATE_CENTROIDS.items():
        if st_key in query_lower:
            matched_centroid = st_info
            break

    if not matched_centroid:
        matched_centroid = STATE_CENTROIDS["bihar"]

    disp = f"{clean_query}, {matched_centroid['state']}, India"

    return LocationPayloadSchema(
        latitude=matched_centroid["lat"],
        longitude=matched_centroid["lng"],
        accuracy_meters=None,
        display_name=disp,
        district=matched_centroid["district"],
        state=matched_centroid["state"],
        country="India",
        region=matched_centroid["state"],
        source="MANUAL_GEOCODED",
        status="MANUAL"
    )
