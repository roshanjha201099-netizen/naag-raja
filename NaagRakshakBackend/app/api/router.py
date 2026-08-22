from fastapi import APIRouter
from app.api.endpoints import predict, species, medical, rescue, health, sighting

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(predict.router, tags=["AI Prediction & Safety"])
api_router.include_router(species.router, tags=["Taxonomy & Species"])
api_router.include_router(medical.router, tags=["ASV Medical Facilities"])
api_router.include_router(rescue.router, tags=["Wildlife Rescue Dispatch"])
api_router.include_router(sighting.router, tags=["Snake Sighting Reports"])
