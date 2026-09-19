from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.database import get_db
from app.db.models import Species, SpeciesDistribution

import httpx

router = APIRouter()

# Authoritative Curated Mapping for Indian Species with iNaturalist Open Data S3 photo mirrors
SPECIES_ASSETS = {
    "naja_naja": {
        "common_name": "Indian Spectacled Cobra",
        "scientific_name": "Naja naja",
        "hindi_name": "नाग / गेहुंअन",
        "venomous": True,
        "danger_level": "EXTREME",
        "family": "Elapidae",
        "image_url": "https://inaturalist-open-data.s3.amazonaws.com/photos/736873884/medium.jpg",
        "description": "One of India's Big Four deadliest snakes. Features a distinctive spectacle mark on the rear of its hood."
    },
    "daboia_russelii": {
        "common_name": "Russell's Viper",
        "scientific_name": "Daboia russelii",
        "hindi_name": "दबोइया / कोरिवाला",
        "venomous": True,
        "danger_level": "EXTREME",
        "family": "Viperidae",
        "image_url": "https://inaturalist-open-data.s3.amazonaws.com/photos/736745737/medium.jpg",
        "description": "Responsible for the majority of severe snakebite envenomations in South Asia. Emits a loud pressure-cooker hiss when threatened."
    },
    "bungarus_caeruleus": {
        "common_name": "Common Krait",
        "scientific_name": "Bungarus caeruleus",
        "hindi_name": "करैत",
        "venomous": True,
        "danger_level": "EXTREME",
        "family": "Elapidae",
        "image_url": "https://inaturalist-open-data.s3.amazonaws.com/photos/735970528/medium.jpg",
        "description": "Highly neurotoxic species active primarily at night. Features narrow paired white crossbands along dorsal."
    },
    "echis_carinatus": {
        "common_name": "Saw-scaled Viper",
        "scientific_name": "Echis carinatus",
        "hindi_name": "फुर्सा",
        "venomous": True,
        "danger_level": "HIGH",
        "family": "Viperidae",
        "image_url": "https://inaturalist-open-data.s3.amazonaws.com/photos/736866527/medium.jpg",
        "description": "Small, irritable viper that rubs serrated flank scales together to make a sizzling warning sound."
    },
    "ptyas_mucosa": {
        "common_name": "Indian Rat Snake (Dhaman)",
        "scientific_name": "Ptyas mucosa",
        "hindi_name": "धामन",
        "venomous": False,
        "danger_level": "HARMLESS",
        "family": "Colubridae",
        "image_url": "https://static.inaturalist.org/photos/736855001/medium.jpg",
        "description": "Large, fast-moving harmless colubrid beneficial for controlling agricultural rodent populations."
    },
    "ophiophagus_hannah": {
        "common_name": "King Cobra",
        "scientific_name": "Ophiophagus hannah",
        "hindi_name": "राजनाग",
        "venomous": True,
        "danger_level": "EXTREME",
        "family": "Elapidae",
        "image_url": "https://inaturalist-open-data.s3.amazonaws.com/photos/736412086/medium.jpg",
        "description": "World's longest venomous snake, feeding predominantly on other snakes."
    },
    "eryx_conicus": {
        "common_name": "Rough-scaled Sand Boa",
        "scientific_name": "Eryx conicus",
        "hindi_name": "दोमुंहा / बालू बोआ",
        "venomous": False,
        "danger_level": "HARMLESS",
        "family": "Boidae",
        "image_url": "https://inaturalist-open-data.s3.amazonaws.com/photos/733588796/medium.jpg",
        "description": "Docile non-venomous burrowing constrictor with rough keeled scales."
    },
    "eryx_johnii": {
        "common_name": "Red Sand Boa",
        "scientific_name": "Eryx johnii",
        "hindi_name": "लाल दोमुंहा",
        "venomous": False,
        "danger_level": "HARMLESS",
        "family": "Boidae",
        "image_url": "https://inaturalist-open-data.s3.amazonaws.com/photos/735008672/medium.jpg",
        "description": "Stout non-venomous sand boa with blunt tail, often misidentified in folklore as two-headed."
    },
    "lycodon_aulicus": {
        "common_name": "Common Wolf Snake",
        "scientific_name": "Lycodon aulicus",
        "hindi_name": "भेड़िया सांप",
        "venomous": False,
        "danger_level": "HARMLESS",
        "family": "Colubridae",
        "image_url": "https://inaturalist-open-data.s3.amazonaws.com/photos/736719244/medium.jpg",
        "description": "Completely harmless non-venomous house snake that Batesian-mimics the Common Krait."
    },
    "python_molurus": {
        "common_name": "Indian Rock Python",
        "scientific_name": "Python molurus",
        "hindi_name": "अजगर",
        "venomous": False,
        "danger_level": "HARMLESS",
        "family": "Pythonidae",
        "image_url": "https://static.inaturalist.org/photos/736494544/medium.jpg",
        "description": "Large non-venomous constrictor species native to India."
    }
}


async def fetch_inaturalist_photos(query_name: str, max_photos: int = 8) -> List[Dict[str, Any]]:
    """
    Fetches research-grade observation photos for a given species name from iNaturalist API v1.
    """
    url = "https://api.inaturalist.org/v1/observations"
    params = {
        "q": query_name,
        "has[]": "photos",
        "quality_grade": "research",
        "per_page": max_photos
    }
    photos = []
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                for obs in data.get("results", []):
                    for photo in obs.get("photos", []):
                        raw_url = photo.get("url", "")
                        if not raw_url:
                            continue
                        medium_url = raw_url.replace("/square.", "/medium.").replace("square.jpg", "medium.jpg")
                        large_url = raw_url.replace("/square.", "/large.").replace("square.jpg", "large.jpg")
                        photos.append({
                            "id": photo.get("id"),
                            "url": medium_url,
                            "large_url": large_url,
                            "attribution": photo.get("attribution", "(c) iNaturalist Contributor"),
                            "license_code": photo.get("license_code", "cc-by-nc"),
                            "observer": obs.get("user", {}).get("login", "Researcher"),
                            "location": obs.get("place_guess", "India")
                        })
    except Exception as err:
        print(f"[iNaturalist Service] Error fetching photos for '{query_name}': {err}")
    return photos[:max_photos]


@router.get("/species")
async def list_species(
    category: Optional[str] = Query("all", description="all, big4, venomous, non-venomous"),
    venomousFilter: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    results = []
    
    # Determine active venomous filter mode
    v_filter = venomousFilter or category

    for key, data in SPECIES_ASSETS.items():
        sci_name = data.get("scientific_name") or key.replace("_", " ").title()
        is_venomous = data["venomous"]
        
        # Category / Venomous Filtering
        if v_filter == "venomous" and not is_venomous:
            continue
        if (v_filter == "non_venomous" or v_filter == "non-venomous") and is_venomous:
            continue
        if v_filter == "big4" and key not in ["naja_naja", "daboia_russelii", "bungarus_caeruleus", "echis_carinatus"]:
            continue
            
        # Search Filtering
        if search:
            s = search.lower()
            if (s not in data["common_name"].lower() and 
                s not in sci_name.lower() and 
                s not in data["hindi_name"].lower()):
                continue

        results.append({
            "id": key,
            "species_id": key,
            "scientific_name": sci_name,
            "common_name": data["common_name"],
            "hindi_name": data["hindi_name"],
            "family": data["family"],
            "is_venomous": is_venomous,
            "venomous": is_venomous,
            "danger_level": data["danger_level"],
            "image_url": data["image_url"],
            "imageUrl": data["image_url"],
            "description": data.get("description", "")
        })

    return results


@router.get("/species/photos/search")
async def search_species_photos(
    q: str = Query(..., description="Species common or scientific name (e.g., 'Python molurus' or 'King Cobra')"),
    limit: int = Query(8, ge=1, le=20)
):
    """
    Search live research-grade iNaturalist observation photos for any species.
    """
    photos = await fetch_inaturalist_photos(query_name=q, max_photos=limit)
    return {
        "query": q,
        "count": len(photos),
        "photos": photos
    }


@router.get("/species/{species_id}")
async def get_species_by_id(
    species_id: str,
    include_gallery: bool = Query(True, description="Fetch dynamic iNaturalist photo gallery"),
    db: AsyncSession = Depends(get_db)
):
    clean_id = str(species_id).lower().replace(" ", "_").replace("-", "_")
    
    # Check in SPECIES_ASSETS
    if clean_id in SPECIES_ASSETS:
        data = SPECIES_ASSETS[clean_id]
        sci_name = data.get("scientific_name") or clean_id.replace("_", " ").title()
        
        gallery = []
        if include_gallery:
            gallery = await fetch_inaturalist_photos(query_name=sci_name, max_photos=6)
            
        return {
            "id": clean_id,
            "species_id": clean_id,
            "scientific_name": sci_name,
            "common_name": data["common_name"],
            "hindi_name": data["hindi_name"],
            "family": data["family"],
            "is_venomous": data["venomous"],
            "venomous": data["venomous"],
            "danger_level": data["danger_level"],
            "image_url": data["image_url"],
            "imageUrl": data["image_url"],
            "description": data.get("description", ""),
            "gallery": gallery
        }

    # Query from database if present
    query = select(Species).where(or_(Species.id == species_id, Species.scientific_name.ilike(f"%{species_id}%")))
    res = await db.execute(query)
    sp = res.scalars().first()

    if sp:
        gallery = []
        if include_gallery:
            gallery = await fetch_inaturalist_photos(query_name=sp.scientific_name or sp.common_name, max_photos=6)

        return {
            "id": sp.id,
            "species_id": sp.id,
            "scientific_name": sp.scientific_name,
            "common_name": sp.common_name,
            "hindi_name": sp.hindi_name or "",
            "family": sp.family,
            "is_venomous": sp.venomous,
            "venomous": sp.venomous,
            "danger_level": sp.safety_level,
            "image_url": "https://inaturalist-open-data.s3.amazonaws.com/photos/176962383/medium.jpg",
            "imageUrl": "https://inaturalist-open-data.s3.amazonaws.com/photos/176962383/medium.jpg",
            "description": sp.description or "",
            "gallery": gallery
        }

    # Default fallback
    first_key = list(SPECIES_ASSETS.keys())[0]
    data = SPECIES_ASSETS[first_key]
    sci_name = data.get("scientific_name") or first_key.replace("_", " ").title()
    gallery = []
    if include_gallery:
        gallery = await fetch_inaturalist_photos(query_name=sci_name, max_photos=6)

    return {
        "id": first_key,
        "species_id": first_key,
        "scientific_name": sci_name,
        "common_name": data["common_name"],
        "hindi_name": data["hindi_name"],
        "family": data["family"],
        "is_venomous": data["venomous"],
        "venomous": data["venomous"],
        "danger_level": data["danger_level"],
        "image_url": data["image_url"],
        "imageUrl": data["image_url"],
        "description": data.get("description", ""),
        "gallery": gallery
    }
