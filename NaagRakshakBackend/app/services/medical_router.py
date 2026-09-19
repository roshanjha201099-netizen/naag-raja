import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("naagrakshak.medical_router")

class EmergencyMedicalRouter:
    @staticmethod
    async def get_nearest_facilities(
        user_lat: float,
        user_lng: float,
        db: AsyncSession,
        state: Optional[str] = None,
        max_results: int = 3
    ) -> List[Dict[str, Any]]:
        """Calculates nearest ASV medical facilities directly via database spatial search and OpenStreetMap fallback."""
        try:
            from app.api.endpoints.medical import get_medical_facilities
            facilities = await get_medical_facilities(
                user_lat=user_lat,
                user_lng=user_lng,
                state=state,
                db=db
            )
            result = []
            for f in facilities[:max_results]:
                if hasattr(f, "dict"):
                    result.append(f.dict())
                elif isinstance(f, dict):
                    result.append(f)
                else:
                    result.append({
                        "name": getattr(f, "name", "Hospital"),
                        "address": getattr(f, "address", ""),
                        "phone_number": getattr(f, "phone_number", getattr(f, "phone", None)),
                        "distance_km": getattr(f, "distance_km", None),
                        "has_antivenom": getattr(f, "has_antivenom", True),
                        "latitude": getattr(f, "latitude", None),
                        "longitude": getattr(f, "longitude", None)
                    })
            return result
        except Exception as e:
            logger.error(f"Failed to fetch nearest facilities in EmergencyMedicalRouter: {e}")
            return []
