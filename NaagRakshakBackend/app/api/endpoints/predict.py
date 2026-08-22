import time
import uuid
import logging
from typing import Optional, List
from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.db.models import PredictionLog
from app.db.schemas import PredictResponse, IntentEnum
from app.services.validation import ImageValidationService
from app.services.quality import ImageQualityAnalyzer
from app.services.inference import ml_engine
from app.services.geo_ranking import LocationAwareRankingService
from app.services.safety_engine import DeterministicSafetyEngine
from app.services.llm_explainer import llm_explainer
from app.services.sarvam_tts import sarvam_tts
from app.services.response_composer import ResponseComposerService

logger = logging.getLogger("naagrakshak.predict")
router = APIRouter()

@router.post("/predict", response_model=PredictResponse)
async def predict_snake(
    images: Optional[List[UploadFile]] = File(None, description="Multiple snake specimen field image files (up to 5)"),
    image: Optional[UploadFile] = File(None, description="Single snake specimen field image file (JPEG, PNG, WEBP)"),
    image_base64: Optional[str] = Form(None, description="Base64 encoded image string"),
    intent: Optional[str] = Form("SNAKE_ENCOUNTER", description="User field intent enum"),
    state: Optional[str] = Form(None, description="Indian state or region name"),
    language_code: Optional[str] = Form("hi-IN", description="Regional language code"),
    user_lat: Optional[float] = Form(None, description="User latitude"),
    user_lng: Optional[float] = Form(None, description="User longitude"),
    db: AsyncSession = Depends(get_db)
):
    start_time = time.time()
    req_id = str(uuid.uuid4())
    lang_clean = language_code if language_code else "hi-IN"

    # Parse Intent Enum
    INTENT_ALIAS_MAP = {
        "BITE": "SNAKE_BITE_EMERGENCY",
        "SNAKE_BITE": "SNAKE_BITE_EMERGENCY",
        "SNAKE_BITE_EMERGENCY": "SNAKE_BITE_EMERGENCY",
        "ENCOUNTER": "SNAKE_ENCOUNTER",
        "SNAKE_ENCOUNTER": "SNAKE_ENCOUNTER",
        "STUDY": "STUDY_RESEARCH",
        "STUDY_RESEARCH": "STUDY_RESEARCH",
        "PHOTOGRAPHY": "WILDLIFE_PHOTOGRAPHY",
        "WILDLIFE_PHOTOGRAPHY": "WILDLIFE_PHOTOGRAPHY"
    }
    raw_intent_key = intent.upper().strip() if intent else "SNAKE_ENCOUNTER"
    intent_clean = INTENT_ALIAS_MAP.get(raw_intent_key, "SNAKE_ENCOUNTER")
    try:
        intent_enum = IntentEnum(intent_clean)
    except ValueError:
        intent_enum = IntentEnum.SNAKE_ENCOUNTER

    # 1. Read & Validate Binary Stream(s) or Base64 String (Up to 5 images)
    images_to_process = []
    if images and len(images) > 0:
        for img_file in images[:5]:
            try:
                b = await img_file.read()
                if b and len(b) > 0:
                    pil_img = ImageValidationService.validate_image_stream(b)
                    images_to_process.append(pil_img)
            except Exception as e:
                logger.warning(f"Could not parse image file in multi-upload: {e}")
    
    if not images_to_process and image:
        try:
            file_bytes = await image.read()
            pil_img = ImageValidationService.validate_image_stream(file_bytes)
            images_to_process.append(pil_img)
        except Exception as e:
            logger.warning(f"Could not parse single image file: {e}")

    if not images_to_process and image_base64:
        pil_img = ImageValidationService.validate_image_stream(image_base64)
        images_to_process.append(pil_img)

    if not images_to_process:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one valid image file (or 'images' array up to 5) must be provided."
        )

    # 2 & 3. Process Multi-Image Inference Pipeline (Multi-View Ensemble)
    results = []
    for pil_img in images_to_process:
        q_score = ImageQualityAnalyzer.analyze_quality(pil_img)
        res = ml_engine.predict(pil_img, q_score)
        results.append((res, q_score))

    # Rank results by quality & detection confidence to pick top visual specimen
    results.sort(key=lambda x: (x[0].get("detection_confidence", 0.95) * x[1]), reverse=True)
    ml_result = results[0][0]
    quality_score = results[0][1]

    # 4. Location-Aware Bayesian Ranking
    top_k_candidates = ml_result.get("top_k", [])
    ranked_candidates = LocationAwareRankingService.rerank_predictions(top_k_candidates, state=state)

    # Top-1 candidate after geo re-ranking
    top_1 = ranked_candidates[0] if ranked_candidates else {
        "species_id": 1,
        "scientific_name": "Unknown",
        "common_name": "Unknown Species",
        "venomous": False,
        "medically_significant": False
    }

    # 5. Deterministic Safety Engine Evaluation (Intent-aware)
    safety_payload = DeterministicSafetyEngine.evaluate_safety(
        top_prediction=top_1,
        identification_status=ml_result.get("identification_status", "HIGH_CONFIDENCE"),
        intent=intent_enum.value
    )

    # 6. Nearest ASV Hospital Lookup for Voice Script Integration
    nearest_hosp_name = None
    nearest_hosp_dist = None
    try:
        from app.api.endpoints.medical import get_medical_facilities
        hospitals = await get_medical_facilities(
            state=state,
            district=None,
            asv_only=True,
            user_lat=user_lat,
            user_lng=user_lng,
            db=db
        )
        if hospitals and len(hospitals) > 0:
            nearest_hosp_name = hospitals[0].name
            nearest_hosp_dist = hospitals[0].distance_km if hospitals[0].distance_km is not None else 5.0
    except Exception as ex:
        logger.warning(f"Could not query nearest hospital for explainer: {ex}")

    # 7. OpenAI LLM Regional Language Script Synthesis
    regional_explanation = await llm_explainer.generate_explanation(
        common_name=top_1.get("common_name", "Unknown Species"),
        hindi_name=top_1.get("hindi_name", None),
        safety_level=safety_payload.safety_level.value,
        intent=intent_enum.value,
        location=state,
        language_code=lang_clean,
        nearest_hospital_name=nearest_hosp_name,
        nearest_hospital_distance_km=nearest_hosp_dist
    )

    # 7. Sarvam AI Text-to-Speech (TTS) Voice Audio Generation
    audio_base64 = None
    if regional_explanation:
        audio_base64 = await sarvam_tts.generate_speech_audio(
            text_script=regional_explanation,
            language_code=lang_clean
        )

    proc_time_ms = float(round((time.time() - start_time) * 1000, 2))

    # 8. Persist Prediction Log to DB
    try:
        log_entry = PredictionLog(
            request_id=req_id,
            image_quality_score=quality_score,
            snake_detected=ml_result.get("snake_detected", True),
            detection_confidence=ml_result.get("detection_confidence", 0.95),
            top_species_id=top_1.get("species_id", 1),
            calibrated_confidence=ml_result.get("identification_status", "HIGH_CONFIDENCE"),
            safety_level=safety_payload.safety_level.value,
            processing_time_ms=proc_time_ms
        )
        db.add(log_entry)
        await db.commit()
    except Exception as e:
        logger.warning(f"Failed to record prediction log to DB: {e}")

    # 9. Compose Intent-Driven Response
    return ResponseComposerService.compose_response(
        request_id=req_id,
        ml_result=ml_result,
        ranked_predictions=ranked_candidates,
        safety=safety_payload,
        intent=intent_enum,
        state=state,
        quality_score=quality_score,
        processing_time_ms=proc_time_ms,
        llm_explanation=regional_explanation,
        audio_base64=audio_base64,
        language_code=lang_clean
    )
