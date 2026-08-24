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
    image: Optional[UploadFile] = File(None, description="Single snake specimen field image file (JPEG, PNG, WEBP)"),
    image_base64: Optional[str] = Form(None, description="Base64 encoded image string"),
    intent: Optional[str] = Form("SNAKE_ENCOUNTER", description="User field intent enum"),
    state: Optional[str] = Form(None, description="Indian state or region name"),
    language_code: Optional[str] = Form("hi-IN", description="Regional language code"),
    user_lat: Optional[float] = Form(None, description="User latitude"),
    user_lng: Optional[float] = Form(None, description="User longitude"),
    user_accuracy: Optional[float] = Form(None, description="GPS Accuracy in meters"),
    location_source: Optional[str] = Form(None, description="Source of location data"),
    location_status: Optional[str] = Form(None, description="Status of location services"),
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

    # Print Formatted Incoming Frontend Request Payload
    has_image = "Yes (Binary stream)" if image else ("Yes (Base64)" if image_base64 else "No")
    print("\n" + "="*75)
    print(f">> [FRONTEND REQUEST RECEIVED] POST /api/v1/predict (Request ID: {req_id})")
    print("="*75)
    print(f"  * User Intent:         '{intent}' -> Parsed as: {intent_enum.value}")
    print(f"  * Indian State/Region: '{state}'")
    print(f"  * Language Code:       '{language_code}' (TTS Language: {lang_clean})")
    print(f"  * GPS Latitude:        {user_lat if user_lat is not None else 'None (Manual Location)'}")
    print(f"  * GPS Longitude:       {user_lng if user_lng is not None else 'None (Manual Location)'}")
    print(f"  * GPS Accuracy:        {str(user_accuracy) + ' meters' if user_accuracy is not None else 'None'}")
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

    # 2 & 3. Process Single Image Inference Pipeline
    quality_score = ImageQualityAnalyzer.analyze_quality(pil_img)
    ml_result = ml_engine.predict(pil_img, quality_score)

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

    # --------------------------------------------------------------------------
    # BOLD MODEL PREDICTION TERMINAL OUTPUT LOGGING
    # --------------------------------------------------------------------------
    is_snake = ml_result.get("snake_detected", True)
    det_conf = ml_result.get("detection_confidence", 0.0)

    print("\n" + "🐍 "*35)
    print(" [MODEL PREDICTION TERMINAL OUTPUT]")
    print("="*70)
    print(f"  * Snake Detected:     {'YES ✅' if is_snake else 'NO ❌'} (Confidence: {det_conf*100:.1f}%)")
    if is_snake and top_1:
        comm_name = top_1.get("common_name", "Unknown Species")
        sci_name = top_1.get("scientific_name", "Unknown")
        hin_name = top_1.get("hindi_name", "N/A")
        prob_val = top_1.get("probability", 0.94)
        prob_pct = (prob_val * 100) if prob_val <= 1.0 else prob_val
        is_venom = top_1.get("venomous", False)
        print(f"  * Species Identified: {comm_name} ({sci_name})")
        print(f"  * Local/Hindi Name:   {hin_name}")
        print(f"  * Model Confidence:   {prob_pct:.1f}% Match")
        print(f"  * Venom Status:       {'⚠️ VENOMOUS (HIGH DANGER)' if is_venom else '🟢 NON-VENOMOUS (HARMLESS)'}")
    else:
        print("  * Model Status:       No snake specimen detected in uploaded image.")
    print("="*70)
    print("🐍 "*35 + "\n")

    logger.info(f"📍 MODEL PREDICTION: Is Snake={is_snake} | Species={top_1.get('common_name')} ({top_1.get('scientific_name')}) | Conf={top_1.get('probability', 0.94)*100:.1f}% | Venomous={top_1.get('venomous')}")

    # 5. Deterministic Safety Engine Evaluation (Intent-aware)
    safety_payload = DeterministicSafetyEngine.evaluate_safety(
        top_prediction=top_1,
        identification_status=ml_result.get("identification_status", "HIGH_CONFIDENCE"),
        intent=intent_enum.value
    )


    # 6. Bypass external LLM and TTS calls for pure fast ML model prediction
    regional_explanation = None
    audio_base64 = None
    nearest_hosp_name = None
    nearest_hosp_dist = None

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

    # 6.5 Query Verified Rescue Helplines & Facilities
    rescue_facilities_list = []
    try:
        from app.api.endpoints.rescue import get_rescue_facilities
        rescue_facilities_list = await get_rescue_facilities(state=state, user_lat=user_lat, user_lng=user_lng, db=db)
    except Exception as ex:
        logger.warning(f"Could not query rescue facilities: {ex}")

    nearest_hosp_obj = None


    # 9. Compose Intent-Driven Response
    res_obj = ResponseComposerService.compose_response(
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
    
    # Dynamic Location Payload Contract
    computed_source = location_source or ("MANUAL_GEOCODED" if user_lat is not None and user_accuracy is None else "GPS")
    if user_accuracy is not None and user_accuracy <= 5000:
        computed_status = "ACCURATE"
    elif computed_source == "MANUAL_GEOCODED":
        computed_status = "MANUAL"
    elif user_lat is not None:
        computed_status = "LOW_ACCURACY"
    else:
        computed_status = "LOW_ACCURACY"

    from app.db.schemas import LocationPayloadSchema
    loc_disp = f"{state}, India" if state else "India"
    res_obj.location = LocationPayloadSchema(
        latitude=user_lat,
        longitude=user_lng,
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
    return res_obj
