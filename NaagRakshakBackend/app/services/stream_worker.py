import logging
from typing import Optional, Dict, Any
from app.services.llm_explainer import llm_explainer
from app.services.sarvam_tts import sarvam_tts
from app.services.connection_manager import ws_manager

logger = logging.getLogger("naagrakshak.stream_worker")

async def process_ai_enrichment_stream(
    session_id: str,
    species_facts: Dict[str, Any],
    is_bite: bool = False,
    user_description: Optional[str] = None,
    state: Optional[str] = None,
    user_lat: Optional[float] = None,
    user_lng: Optional[float] = None,
    language_code: str = "hi-IN",
    nearest_hospital_name: Optional[str] = None,
    nearest_hospital_distance_km: Optional[float] = None,
    rescue_helpline: Optional[str] = None,
    is_snake_detected: bool = True
):
    """
    Asynchronously generates Gemini LLM explanation, streams text chunks over WebSocket,
    synthesizes Sarvam AI TTS audio, and pushes AUDIO_READY event to client.
    """
    logger.info(f"Starting AI enrichment stream worker for session_id: {session_id}")

    snake_name = species_facts.get("common_name", species_facts.get("scientific_name", "Unknown Snake"))
    confidence = species_facts.get("confidence_score", species_facts.get("probability", 0.90))
    venomous = species_facts.get("is_venomous", species_facts.get("venomous", False))
    danger_level = species_facts.get("danger_level", "HIGH" if venomous else "LOW")

    # Step 1: Generate Gemini LLM explanation & stream text
    accumulated_text = []
    full_script = ""
    try:
        explanation = await llm_explainer.generate_explanation(
            snake_species=snake_name,
            confidence=confidence if confidence <= 1.0 else confidence / 100.0,
            venomous=venomous,
            danger_level=danger_level,
            user_description=user_description,
            state=state,
            user_lat=user_lat,
            user_lng=user_lng,
            nearest_hospital_name=nearest_hospital_name,
            nearest_hospital_distance_km=nearest_hospital_distance_km,
            rescue_helpline=rescue_helpline,
            is_snake_detected=is_snake_detected
        )
        
        full_script = explanation or ""
        
        # Stream chunks to WebSocket client
        chunk_size = 30
        for i in range(0, len(full_script), chunk_size):
            chunk = full_script[i:i + chunk_size]
            accumulated_text.append(chunk)
            await ws_manager.send_json(session_id, {
                "type": "LLM_TEXT_CHUNK",
                "event": "LLM_TEXT_CHUNK",
                "chunk": chunk
            })

        await ws_manager.send_json(session_id, {
            "type": "LLM_COMPLETED",
            "event": "LLM_COMPLETED",
            "full_script": full_script
        })
        logger.info(f"LLM explanation stream completed for session {session_id}")
    except Exception as e:
        logger.error(f"Error in LLM stream for session {session_id}: {e}")
        await ws_manager.send_json(session_id, {
            "type": "LLM_ERROR",
            "error": str(e)
        })

    # Step 2: Generate Sarvam AI / gTTS TTS Audio
    if full_script:
        try:
            audio_base64 = await sarvam_tts.generate_speech_audio(
                text_script=full_script,
                language_code=language_code
            )
            
            await ws_manager.send_json(session_id, {
                "type": "AUDIO_READY",
                "event": "AUDIO_READY",
                "audio_base64": audio_base64,
                "audio_format": "audio/wav"
            })
            logger.info(f"AUDIO_READY event dispatched for session {session_id}")
        except Exception as e:
            logger.error(f"Error generating TTS audio for session {session_id}: {e}")
            await ws_manager.send_json(session_id, {
                "type": "AUDIO_ERROR",
                "error": str(e)
            })
