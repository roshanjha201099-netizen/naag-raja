from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.database import get_db
from app.db.models import Species, SpeciesDistribution
from app.db.schemas import SpeciesDetailResponse

router = APIRouter()

REGIONAL_NAMES_MAP = {
    "Naja naja": {
        "hindi": "नाग / गेहुंअन (Nag / Gehuan)",
        "bengali": "গোখরো (Gokhro)",
        "tamil": "நல்லபாம்பு (Nalla Pambu)",
        "marathi": "नाग (Nag)",
        "kannada": "ನಾಗರಹಾವು (Nagara Haavu)",
        "malayalam": "മൂർഖൻ (Moorkhan)",
        "telugu": "నాగుపాము (Nagu Pamu)"
    },
    "Bungarus caeruleus": {
        "hindi": "करैत (Karait)",
        "bengali": "কালাচ (Kalach)",
        "tamil": "கட்டுவிரியன் (Kattu Viriyan)",
        "marathi": "मण्यार (Manyar)",
        "kannada": "ಕಟ್ಟುಹಾವು (Kattu Haavu)",
        "malayalam": "വെള്ളിക്കെട്ടൻ (Vellikkettan)",
        "telugu": "కట్లపాము (Katla Pamu)"
    },
    "Daboia russelii": {
        "hindi": "दबोइया / चित्ती (Daboia / Chitti)",
        "bengali": "চন্দ্রবোড়া (Chandrobora)",
        "tamil": "கண்ணாடிவிரியன் (Kannadi Viriyan)",
        "marathi": "घोणस (Ghonas)",
        "kannada": "கொளகுமಂಡಲ (Kolaku Mandala)",
        "malayalam": "അണലി (Anali)",
        "telugu": "రక్తపింజరి (Rakta Pinjari)"
    },
    "Ptyas mucosa": {
        "hindi": "धामन (Dhaman)",
        "bengali": "দাঁড়াশ (Darash)",
        "tamil": "சாரைப்பாம்பு (Saarai Pambu)",
        "marathi": "धामण (Dhaman)",
        "kannada": "ಕೇರೆಹಾವು (Keere Haavu)",
        "malayalam": "ചേര (Chera)",
        "telugu": "జెర్రిపోతు (Jerri Pothu)"
    }
}

LOOKALIKES_MAP = {
    "Naja naja": [
        {"name": "Indian Rat Snake (Ptyas mucosa)", "difference": "Rat Snake does NOT have a spectacle mark or expandable hood. Scales around jaw have dark vertical stripes."},
        {"name": "King Cobra (Ophiophagus hannah)", "difference": "King Cobra is significantly larger (up to 5.5m), has chevron stripes, and chevron neck markings."}
    ],
    "Bungarus caeruleus": [
        {"name": "Common Wolf Snake (Lycodon aulicus)", "difference": "CRITICAL DANGER: Wolf snake bands start right behind head and are yellowish-white with brown spots. Wolf snake lacks enlarged hexagonal dorsal scales."}
    ],
    "Ptyas mucosa": [
        {"name": "Spectacled Cobra (Naja naja)", "difference": "Rat snake DOES NOT expand a hood and lacks spectacle dorsal markings. Rat snake has distinct black jaw stripes."}
    ]
}

@router.get("/species", response_model=List[SpeciesDetailResponse])
async def list_species(
    search: Optional[str] = Query(None, description="Search query by common or scientific name"),
    venomous: Optional[bool] = Query(None, description="Filter by venomous status"),
    medically_significant: Optional[bool] = Query(None, description="Filter by medical significance"),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    query = select(Species)
    if venomous is not None:
        query = query.where(Species.venomous == venomous)
    if medically_significant is not None:
        query = query.where(Species.medically_significant == medically_significant)
    if search:
        s = f"%{search}%"
        query = query.where(
            or_(
                Species.scientific_name.ilike(s),
                Species.common_name.ilike(s),
                Species.hindi_name.ilike(s)
            )
        )

    query = query.offset(skip).limit(limit)
    res = await db.execute(query)
    species_list = res.scalars().all()

    result = []
    for sp in species_list:
        d = SpeciesDetailResponse.model_validate(sp)
        d.regional_names = REGIONAL_NAMES_MAP.get(sp.scientific_name, {})
        d.lookalikes = LOOKALIKES_MAP.get(sp.scientific_name, [])
        result.append(d)

    return result

@router.get("/species/{species_id}", response_model=SpeciesDetailResponse)
async def get_species_by_id(
    species_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(Species).where(Species.id == species_id)
    res = await db.execute(query)
    sp = res.scalars().first()

    if not sp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Species record with ID {species_id} not found."
        )

    d = SpeciesDetailResponse.model_validate(sp)
    d.regional_names = REGIONAL_NAMES_MAP.get(sp.scientific_name, {})
    d.lookalikes = LOOKALIKES_MAP.get(sp.scientific_name, [])
    return d

@router.get("/species/{species_id}/distribution")
async def get_species_distribution(
    species_id: int,
    db: AsyncSession = Depends(get_db)
):
    query = select(SpeciesDistribution).where(SpeciesDistribution.species_id == species_id)
    res = await db.execute(query)
    records = res.scalars().all()

    return {
        "species_id": species_id,
        "distribution_records": [
            {
                "country": r.country,
                "state_province": r.state_province,
                "occurrence_status": r.occurrence_status,
                "gbif_taxon_key": r.gbif_taxon_key
            }
            for r in records
        ]
    }
