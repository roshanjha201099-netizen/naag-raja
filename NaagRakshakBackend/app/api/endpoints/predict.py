import time
import uuid
import logging
from typing import Optional, List
from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.db.models import PredictionLog
from app.db.schemas import PredictResponse, IntentEnum
from app.services.validation import ImageValidationService
from app.services.quality import ImageQualityAnalyzer
from app.services.inference import ml_engine
from app.services.geo_ranking import LocationAwareRankingService
from app.services.safety_engine import DeterministicSafetyEngine
from app.services.response_composer import ResponseComposerService
from app.services.stream_worker import process_ai_enrichment_stream

logger = logging.getLogger("naagrakshak.predict")
router = APIRouter()

@router.post("/predict", response_model=PredictResponse)
async def predict_snake(
    background_tasks: BackgroundTasks,
    image: Optional[UploadFile] = File(None, description="Single snake specimen field image file (JPEG, PNG, WEBP)"),
    image_base64: Optional[str] = Form(None, description="Base64 encoded image string"),
    intent: Optional[str] = Form("SNAKE_ENCOUNTER", description="User field intent enum"),
    state: Optional[str] = Form(None, description="Indian state or region name"),
    language_code: Optional[str] = Form("hi-IN", description="Regional language code"),
    description: Optional[str] = Form(None, description="Optional specimen description/context for LLM"),
    user_lat: Optional[float] = Form(None, description="User latitude"),
    user_lng: Optional[float] = Form(None, description="User longitude"),
    latitude: Optional[float] = Form(None, description="Alternative alias for user latitude"),
    longitude: Optional[float] = Form(None, description="Alternative alias for user longitude"),
    user_accuracy: Optional[float] = Form(None, description="GPS Accuracy in meters"),
    location_source: Optional[str] = Form(None, description="Source of location data"),
    location_status: Optional[str] = Form(None, description="Status of location services"),
    session_id: Optional[str] = Form(None, description="Client session tracking token for WebSocket streaming"),
    is_bite: Optional[bool] = Form(False, description="Emergency bite incident flag"),
    db: AsyncSession = Depends(get_db)
):
    start_time = time.time()

    req_id = str(uuid.uuid4())
    active_session_id = session_id or req_id
    lang_clean = language_code if language_code else "hi-IN"

    # Consolidate location coordinates
    lat_val = user_lat if user_lat is not None else latitude
    lng_val = user_lng if user_lng is not None else longitude

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
    if is_bite:
        raw_intent_key = "SNAKE_BITE_EMERGENCY"

    intent_clean = INTENT_ALIAS_MAP.get(raw_intent_key, "SNAKE_ENCOUNTER")
    try:
        intent_enum = IntentEnum(intent_clean)
    except ValueError:
        intent_enum = IntentEnum.SNAKE_ENCOUNTER

    # Print Request Log
    has_image = "Yes (Binary stream)" if image else ("Yes (Base64)" if image_base64 else "No")
    print("\n" + "="*75)
    print(f">> [DECOUPLED PREDICT REQUEST] POST /api/v1/predict (Session ID: {active_session_id})")
    print("="*75)
    print(f"  * User Intent:         '{intent}' -> Parsed as: {intent_enum.value}")
    print(f"  * Indian State/Region: '{state}'")
    print(f"  * Language Code:       '{language_code}' (TTS Language: {lang_clean})")
    if description:
        print(f"  * Description (LLM):   '{description}'")
    print(f"  * GPS Latitude:        {lat_val if lat_val is not None else 'None (Manual Location)'}")
    print(f"  * GPS Longitude:       {lng_val if lng_val is not None else 'None (Manual Location)'}")
    print(f"  * Specimen Image:      {has_image}")
    print("="*75 + "\n")

    # 1. Read & Validate Binary Stream or Base64 String
    pil_img = None
    if image:
        try:
            file_bytes = await image.read()
            pil_img = ImageValidationService.validate_image_stream(file_bytes)
        except Exception as e:
            logger.warning(f"Could not parse single image file: {e}")

    if not pil_img and image_base64:
        pil_img = ImageValidationService.validate_image_stream(image_base64)

    if not pil_img:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid image file (or image_base64) must be provided."
        )

    # 2 & 3. Synchronous Fast-path ML Inference (~150-300ms)
    quality_score = ImageQualityAnalyzer.analyze_quality(pil_img)
    ml_result = ml_engine.predict(pil_img, quality_score)

    # 4. Location-Aware Bayesian Ranking
    top_k_candidates = ml_result.get("top_k", [])
    ranked_candidates = LocationAwareRankingService.rerank_predictions(top_k_candidates, state=state)

    top_1 = ranked_candidates[0] if ranked_candidates else {
        "species_id": 1,
        "scientific_name": "Unknown",
        "common_name": "Unknown Species",
        "venomous": False,
        "medically_significant": False
    }

    is_snake = ml_result.get("snake_detected", False)
    det_conf = ml_result.get("detection_confidence", 0.0)

    # 5. Deterministic Safety Engine Evaluation & Facility Lookups
    safety_payload = DeterministicSafetyEngine.evaluate_safety(
        top_prediction=top_1,
        identification_status=ml_result.get("identification_status", "HIGH_CONFIDENCE"),
        intent=intent_enum.value
    )

    nearest_hosp_name = None
    nearest_hosp_dist = None
    nearest_hosp_obj = None
    try:
        from app.api.endpoints.medical import get_medical_facilities
        hospitals = await get_medical_facilities(
            state=state,
            district=None,
            asv_only=True,
            user_lat=lat_val,
            user_lng=lng_val,
            user_accuracy=user_accuracy,
            db=db
        )
        if hospitals and len(hospitals) > 0:
            nearest_hosp_obj = hospitals[0]
            nearest_hosp_name = hospitals[0].name
            nearest_hosp_dist = hospitals[0].distance_km
    except Exception as ex:
        logger.warning(f"Could not query nearest hospital: {ex}")

    rescue_helpline_str = "Forest Emergency Helpline 1926"
    rescue_facilities_list = []
    try:
        from app.api.endpoints.rescue import get_rescue_facilities
        rescue_facilities_list = await get_rescue_facilities(state=state, user_lat=lat_val, user_lng=lng_val, db=db)
        if rescue_facilities_list and len(rescue_facilities_list) > 0:
            rescue_helpline_str = f"{rescue_facilities_list[0].name} ({rescue_facilities_list[0].phone})"
    except Exception as ex:
        logger.warning(f"Could not query rescue facilities: {ex}")

    # 6. Push LLM explanation & Sarvam AI TTS audio to Background Task (Asynchronous Stream)
    background_tasks.add_task(
        process_ai_enrichment_stream,
        session_id=active_session_id,
        species_facts=top_1,
        is_bite=(intent_enum == IntentEnum.SNAKE_BITE_EMERGENCY or is_bite),
        user_description=description,
        state=state,
        user_lat=lat_val,
        user_lng=lng_val,
        language_code=lang_clean,
        nearest_hospital_name=nearest_hosp_name,
        nearest_hospital_distance_km=nearest_hosp_dist,
        rescue_helpline=rescue_helpline_str,
        is_snake_detected=is_snake
    )
    logger.info(f"Background task added for session {active_session_id} AI enrichment stream.")

    proc_time_ms = float(round((time.time() - start_time) * 1000, 2))

    # 7. Compose & Return Immediate Synchronous Response (<300ms)
    res_obj = ResponseComposerService.compose_response(
        request_id=req_id,
        ml_result=ml_result,
        ranked_predictions=ranked_candidates,
        safety=safety_payload,
        intent=intent_enum,
        state=state,
        quality_score=quality_score,
        processing_time_ms=proc_time_ms,
        llm_explanation=None,  # Streamed via WebSocket
        audio_base64=None,     # Streamed via WebSocket
        language_code=lang_clean
    )
    
    res_obj.session_id = active_session_id

    computed_source = location_source or ("MANUAL_GEOCODED" if lat_val is not None and user_accuracy is None else "GPS")
    if user_accuracy is not None and user_accuracy <= 5000:
        computed_status = "ACCURATE"
    elif computed_source == "MANUAL_GEOCODED":
        computed_status = "MANUAL"
    elif lat_val is not None:
        computed_status = "LOW_ACCURACY"
    else:
        computed_status = "LOW_ACCURACY"

    from app.db.schemas import LocationPayloadSchema
    loc_disp = f"{state}, India" if state else "India"
    res_obj.location = LocationPayloadSchema(
        latitude=lat_val,
        longitude=lng_val,
        accuracy_meters=user_accuracy,
        display_name=loc_disp,
        district=None,
        state=state,
        country="India",
        region=state,
        source=computed_source,
        status=computed_status
    )

    res_obj.nearest_hospital = nearest_hosp_obj
    if res_obj.medical:
        res_obj.medical.nearest_facility = nearest_hosp_obj
    if res_obj.rescue:
        res_obj.rescue.contacts = rescue_facilities_list[:3]

    print(f">> [FAST-PATH RESPONSE RETURNED] Session ID: {active_session_id} | Response Time: {proc_time_ms}ms")
    return res_obj
