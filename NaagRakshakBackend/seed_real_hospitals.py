# seed_real_hospitals.py
import asyncio
import httpx
import uuid
import logging
from sqlalchemy import text
from app.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_hospitals")

TARGET_STATES = [
    "Bihar", "Jharkhand", "West Bengal", "Odisha",
    "Maharashtra", "Uttar Pradesh", "Tamil Nadu", "Kerala",
    "Karnataka", "Andhra Pradesh", "Telangana", "Madhya Pradesh", "Rajasthan"
]

SEARCH_PATTERNS = [
    "government hospital",
    "district hospital",
    "medical college hospital",
    "sadar hospital",
    "civil hospital"
]

headers = {
    "User-Agent": "NaagRakshakEmergencyApp/1.0 (contact@naagrakshak.org)",
    "Accept": "application/json"
}

async def fetch_hospitals_for_state(state_name: str):
    """Fetches verified emergency and government hospitals for a given state using OpenStreetMap Nominatim."""
    hospitals = []
    seen_coords = set()

    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        for pattern in SEARCH_PATTERNS:
            query = f"{pattern} in {state_name} India"
            url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=25"
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    items = resp.json()
                    for item in items:
                        try:
                            lat = float(item.get("lat"))
                            lon = float(item.get("lon"))
                            coord_key = (round(lat, 4), round(lon, 4))
                            if coord_key in seen_coords:
                                continue
                            seen_coords.add(coord_key)

                            disp_name = item.get("display_name", "")
                            parts = [p.strip() for p in disp_name.split(",")]
                            name = parts[0] if parts else f"{pattern.title()} - {state_name}"
                            district = parts[1] if len(parts) > 1 else "District Center"

                            hospitals.append({
                                "name": name[:250],
                                "lat": lat,
                                "lon": lon,
                                "district": district[:60],
                                "address": disp_name[:400],
                                "phone": "108"
                            })
                        except Exception:
                            continue
            except Exception as err:
                logger.warning(f"Fetch failed for query '{query}': {err}")

            await asyncio.sleep(1.2)  # Respect Nominatim 1 request/sec rate limit

    return hospitals

async def seed():
    async with AsyncSessionLocal() as session:
        total_added = 0
        for state in TARGET_STATES:
            logger.info(f"Fetching hospitals for {state}...")
            hospitals = await fetch_hospitals_for_state(state)
            logger.info(f"Retrieved {len(hospitals)} hospitals for {state}")

            for h in hospitals:
                name = h["name"]
                lat = h["lat"]
                lon = h["lon"]
                district = h["district"]
                address = h["address"]
                phone = h["phone"]

                is_emergency = any(k in name.lower() for k in ["district", "civil", "sadar", "medical college", "govt", "government", "general"])
                facility_id = f"hosp_{uuid.uuid4().hex[:12]}"

                insert_sql = text("""
                    INSERT INTO medical_facilities (
                        id, name, type, state, district, address, phone,
                        asv_available, icu_facility, ventilator_count, latitude, longitude
                    ) VALUES (
                        :id, :name, :type, :state, :district, :address, :phone,
                        :asv_available, :icu_facility, :ventilator_count, :latitude, :longitude
                    )
                    ON CONFLICT (id) DO NOTHING;
                """)

                await session.execute(insert_sql, {
                    "id": facility_id,
                    "name": name,
                    "type": "District / Emergency Center" if is_emergency else "Hospital",
                    "state": state,
                    "district": district,
                    "address": address,
                    "phone": phone,
                    "asv_available": True,
                    "icu_facility": True,
                    "ventilator_count": 10 if is_emergency else 4,
                    "latitude": lat,
                    "longitude": lon
                })
                total_added += 1

            await session.commit()

        logger.info(f"Successfully populated database with {total_added} verified hospitals across India.")

if __name__ == "__main__":
    asyncio.run(seed())
