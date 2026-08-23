from typing import Dict, Any, List, Optional
from app.db.schemas import (
    PredictResponse, BoundingBoxSchema, SpeciesPredictionSchema,
    SafetySchema, ContextualGuidanceSchema, ProtocolSchema, ModelMetaSchema,
    IntentEnum, IdentificationStatusEnum, LocationPayloadSchema, IdentificationPayloadSchema,
    AlternativeSpeciesSchema, SafetyPayloadSchema, RescuePayloadSchema, MedicalPayloadSchema,
    VoiceAlertPayloadSchema
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

        bbox = BoundingBoxSchema(**ml_result.get("bounding_box", {"x_min": 0, "y_min": 0, "x_max": 224, "y_max": 224})) if ml_result.get("bounding_box") else None
        
        det_conf = float(ml_result.get("detection_confidence", 0.0))
        top_prob = float(pred_schemas[0].calibrated_confidence) if pred_schemas else 0.0
        overall_conf = float(round(det_conf * top_prob, 4)) if pred_schemas else 0.0

        top_prediction_schema = pred_schemas[0] if pred_schemas else None

        # Build Clean Field-First Emergency Payload Structures
        loc_payload = LocationPayloadSchema(region=state or "Bihar")
        
        alternatives_list = [
            AlternativeSpeciesSchema(
                name=f"{p['common_name']} ({p['scientific_name']})",
                probability_percent=int(round(p['calibrated_confidence'] * 100))
            )
            for p in ranked_predictions[1:5]
        ] if len(ranked_predictions) > 1 else []

        id_status_str = str(ml_result.get("identification_status", "HIGH_CONFIDENCE"))
        snake_detected_bool = ml_result.get("snake_detected", True)

        if not snake_detected_bool or id_status_str == "NO_SNAKE_DETECTED":
            common_name_val = "No Snake Detected"
            local_name_val = "कोई सांप नहीं मिला"
            sci_name_val = "Non-Snake Image"
            req_expert = True
            safe_msg_val = "NO SNAKE DETECTED (YOU ARE SAFE): No snake was detected in the uploaded image. Disclaimer: If a snake is hidden in foliage or you require expert verification, please upload a clearer high-resolution photo or consult a certified local rescuer."
        else:
            top_rec = ranked_predictions[0] if ranked_predictions else {}
            sci_name_val = top_rec.get("scientific_name", "Unknown Species")
            c_name = top_rec.get("common_name")
            if not c_name or c_name == "Unknown Species" or c_name == sci_name_val:
                c_name = sci_name_val.replace("_", " ").title()
            common_name_val = c_name
            local_name_val = top_rec.get("hindi_name") or c_name
            req_expert = id_status_str in ["UNABLE_TO_IDENTIFY", "MODERATE_CONFIDENCE"] or top_prob < 0.80
            safe_msg_val = safety.safety_message

        ident_payload = IdentificationPayloadSchema(
            common_name=common_name_val,
            local_name=local_name_val,
            scientific_name=sci_name_val,
            confidence_percent=int(round(top_prob * 100)) if snake_detected_bool else 0,
            status=id_status_str,
            requires_expert_verification=req_expert,
            snake_detection_confidence=int(round(det_conf * 100)),
            alternatives=alternatives_list
        )

        if intent == IntentEnum.SNAKE_BITE_EMERGENCY:
            field_actions = [
                "Keep victim calm and keep bitten limb completely still at heart level.",
                "Do NOT apply tourniquets, ropes, tight bands, or cut/suck the bite wound.",
                "Transport immediately to nearest ASV hospital."
            ]
        elif not snake_detected_bool or id_status_str == "NO_SNAKE_DETECTED":
            field_actions = [
                "Verify Surroundings: If you suspect a snake is hidden nearby in brush or tall grass, remain cautious.",
                "Upload Clear Specimen Photo: Ensure the image clearly shows the snake's head or scale patterns for AI classification.",
                "Request Expert Verification: Contact your local Wildlife Rescue Cell if uncertain about the encounter location."
            ]
        else:
            field_actions = [
                "Maintain a safe standoff distance of 15+ feet.",
                "Do NOT touch, hit, corner, or attempt to capture the snake.",
                "Keep eyes on snake location and contact an authorized rescuer or Forest Department."
            ]

        safe_payload = SafetyPayloadSchema(
            level=safety.safety_level.value if snake_detected_bool else "SAFE",
            assume_potentially_venomous=False if not snake_detected_bool else (safety.venomous or req_expert),
            message=safe_msg_val,
            actions=field_actions
        )

        v_alert = VoiceAlertPayloadSchema(
            language=language_code,
            text=llm_explanation,
            audio_base64=audio_base64
        )

        return PredictResponse(
            request_id=request_id,
            snake_detected=ml_result.get("snake_detected", True),
            detection_confidence=det_conf,
            snake_detection_confidence=det_conf,
            species_classification_probability=top_prob,
            overall_identification_confidence=overall_conf,
            bounding_box=bbox,
            identification_status=IdentificationStatusEnum(ml_result.get("identification_status", "HIGH_CONFIDENCE")),
            prediction=top_prediction_schema,
            predictions_list=pred_schemas,
            predictions=pred_schemas,
            safety=safety,
            contextual_guidance=contextual,
            model_meta=meta,
            location=loc_payload,
            identification=ident_payload,
            safety_payload=safe_payload,
            intent=intent.value if hasattr(intent, 'value') else str(intent),
            rescue=RescuePayloadSchema(contacts=[]),
            medical=MedicalPayloadSchema(nearest_facility=None),
            voice_alert=v_alert
        )
