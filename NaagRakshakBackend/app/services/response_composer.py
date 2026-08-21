from typing import Dict, Any, List, Optional
from app.db.schemas import (
    PredictResponse, BoundingBoxSchema, SpeciesPredictionSchema,
    SafetySchema, ContextualGuidanceSchema, ProtocolSchema, ModelMetaSchema,
    IntentEnum, IdentificationStatusEnum
)

class ResponseComposerService:
    @staticmethod
    def compose_response(
        request_id: str,
        ml_result: Dict[str, Any],
        ranked_predictions: List[Dict[str, Any]],
        safety: SafetySchema,
        intent: IntentEnum,
        state: Optional[str] = None,
        quality_score: float = 0.90,
        processing_time_ms: float = 120.0,
        llm_explanation: Optional[str] = None,
        audio_base64: Optional[str] = None,
        language_code: str = "hi-IN"
    ) -> PredictResponse:
        
        # Build predictions array
        pred_schemas = [
            SpeciesPredictionSchema(
                species_id=p["species_id"],
                scientific_name=p["scientific_name"],
                common_name=p["common_name"],
                family=p["family"],
                raw_probability=p["raw_probability"],
                calibrated_confidence=p["calibrated_confidence"],
                regional_presence=p.get("regional_presence", "COMMON")
            )
            for p in ranked_predictions
        ]

        # Build Protocol based on intent
        if intent == IntentEnum.SNAKE_BITE_EMERGENCY:
            protocol = ProtocolSchema(
                immediate_action="IMMOBILIZE PATIENT AT HEART LEVEL. Keep victim completely calm and still. Transport immediately to nearest ASV hospital.",
                strict_prohibitions=[
                    "DO NOT apply tourniquets, ropes, or tight bands (risk of tissue necrosis & amputation).",
                    "DO NOT cut, incise, or suck venom from the bite wound.",
                    "DO NOT apply ice, chemicals, or herbal pastes.",
                    "DO NOT delay medical transport while waiting for species confirmation."
                ]
            )
        elif intent == IntentEnum.SNAKE_ENCOUNTER:
            protocol = ProtocolSchema(
                immediate_action="STEP BACK 15 FEET MINIMUM. Keep eyes on snake location. Keep children and pets away.",
                strict_prohibitions=[
                    "DO NOT corner snake or hit with sticks.",
                    "DO NOT attempt to capture or pick up snake even if it appears dead.",
                    "DO NOT block snake's exit route."
                ]
            )
        else:
            protocol = ProtocolSchema(
                immediate_action="Observe from safe distance. Record morphological traits (hood mark, crossbands, scale texture).",
                strict_prohibitions=[
                    "DO NOT handle wild snakes without professional credentials.",
                    "DO NOT disturb natural micro-habitats."
                ]
            )

        facility_query = state if state else "All"
        nearby_endpoint = f"/api/v1/medical-facilities?state={facility_query.replace(' ', '+')}"

        contextual = ContextualGuidanceSchema(
            intent=intent,
            protocol=protocol,
            nearby_facilities_endpoint=nearby_endpoint,
            llm_explanation=llm_explanation,
            audio_base64=audio_base64,
            language_code=language_code
        )

        meta = ModelMetaSchema(
            detector_version="yolov8m-snake-v1.0",
            classifier_version="convnext_tiny-naagml-phase1-98c",
            image_quality_score=quality_score,
            processing_time_ms=processing_time_ms
        )

        bbox = BoundingBoxSchema(**ml_result.get("bounding_box", {"x_min": 0, "y_min": 0, "x_max": 224, "y_max": 224}))

        return PredictResponse(
            request_id=request_id,
            snake_detected=ml_result.get("snake_detected", True),
            detection_confidence=ml_result.get("detection_confidence", 0.95),
            bounding_box=bbox,
            identification_status=IdentificationStatusEnum(ml_result.get("identification_status", "HIGH_CONFIDENCE")),
            predictions=pred_schemas,
            safety=safety,
            contextual_guidance=contextual,
            model_meta=meta
        )
