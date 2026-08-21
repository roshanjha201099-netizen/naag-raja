import time
import uuid
import logging
from typing import Optional
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
from app.services.response_composer import ResponseComposerService

logger = logging.getLogger("naagrakshak.predict")
router = APIRouter()

@router.post("/predict", response_model=PredictResponse)
async def predict_snake(
    image: UploadFile = File(..., description="Snake specimen field image file (JPEG, PNG, WEBP)"),
    intent: Optional[str] = Form("SNAKE_ENCOUNTER", description="User field intent enum"),
    state: Optional[str] = Form(None, description="Indian state or region name"),
    db: AsyncSession = Depends(get_db)
):
    start_time = time.time()
    req_id = str(uuid.uuid4())

    # Parse Intent Enum
    intent_clean = intent.upper() if intent else "SNAKE_ENCOUNTER"
    try:
        intent_enum = IntentEnum(intent_clean)
    except ValueError:
        intent_enum = IntentEnum.SNAKE_ENCOUNTER

    # 1. Read & Validate Binary Stream
    file_bytes = await image.read()
    pil_image = ImageValidationService.validate_image_stream(file_bytes)

    # 2. Image Quality & Clarity Analysis (OpenCV Laplacian Blur Metric)
    quality_score = ImageQualityAnalyzer.analyze_quality(pil_image)

    # 3. Multi-Stage ML Inference Pipeline (Detection, Classification, Calibration)
    ml_result = ml_engine.predict(pil_image, quality_score)

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

    # 5. Deterministic Safety Engine Evaluation (Zero LLM Priority Cascade)
    safety_payload = DeterministicSafetyEngine.evaluate_safety(
        top_prediction=top_1,
        identification_status=ml_result.get("identification_status", "HIGH_CONFIDENCE")
    )

    # 6. Optional LLM Natural Language Explainer
    explanation = await llm_explainer.generate_explanation(
        species_name=top_1.get("common_name", top_1.get("scientific_name", "")),
        safety_level=safety_payload.safety_level.value,
        intent=intent_enum.value,
        location=state
    )

    proc_time_ms = float(round((time.time() - start_time) * 1000, 2))

    # 7. Persist Prediction Log to DB
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

    # 8. Compose Intent-Driven Response
    return ResponseComposerService.compose_response(
        request_id=req_id,
        ml_result=ml_result,
        ranked_predictions=ranked_candidates,
        safety=safety_payload,
        intent=intent_enum,
        state=state,
        quality_score=quality_score,
        processing_time_ms=proc_time_ms,
        llm_explanation=explanation
    )
