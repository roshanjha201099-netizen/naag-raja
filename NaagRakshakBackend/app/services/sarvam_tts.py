import logging
import httpx
from typing import Optional
from app.config import settings

logger = logging.getLogger("naagrakshak.sarvam_tts")

VALID_SARVAM_LANGUAGES = {
    "hi-IN": "Hindi",
    "bn-IN": "Bengali",
    "ta-IN": "Tamil",
    "mr-IN": "Marathi",
    "kn-IN": "Kannada",
    "ml-IN": "Malayalam",
    "te-IN": "Telugu",
    "gu-IN": "Gujarati",
    "pa-IN": "Punjabi",
    "en-IN": "English"
}

class SarvamTTSService:
    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        self.tts_url = settings.SARVAM_TTS_URL

    async def generate_speech_audio(
        self,
        text_script: str,
        language_code: str = "hi-IN"
    ) -> Optional[str]:
        if not self.api_key:
            logger.warning("SARVAM_API_KEY is missing. Skipping TTS generation.")
            return None

        clean_lang = language_code if language_code in VALID_SARVAM_LANGUAGES else "hi-IN"

        # Limit text length to 450 characters for crisp TTS speech
        truncated_text = text_script[:450] if len(text_script) > 450 else text_script

        payload = {
            "inputs": [truncated_text],
            "target_language_code": clean_lang,
            "speaker": "anushka",
            "pitch": 0,
            "pace": 1.05,
            "loudness": 1.5,
            "speech_sample_rate": 22050,
            "enable_preprocessing": True,
            "model": "bulbul:v2"
        }

        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json"
        }

        try:
            logger.info(f"Sending Sarvam AI TTS request in '{clean_lang}'...")
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(self.tts_url, json=payload, headers=headers)
                if response.status_code == 200:
                    res_json = response.json()
                    audios = res_json.get("audios", [])
                    if audios and len(audios) > 0:
                        logger.info(f"Sarvam AI TTS audio generated successfully ({len(audios[0])} Base64 chars).")
                        return audios[0]
                else:
                    logger.warning(f"Sarvam AI TTS failed ({response.status_code}): {response.text}")
                    return None
        except Exception as e:
            logger.warning(f"Sarvam AI TTS API request exception: {e}")
            return None

sarvam_tts = SarvamTTSService()
