import os
import logging
import httpx
from typing import Optional
from app.config import settings
from app.core.languages import resolve_language

logger = logging.getLogger("naagrakshak.sarvam_tts")

class SarvamTTSService:
    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        self.tts_url = settings.SARVAM_TTS_URL or "https://api.sarvam.ai/text-to-speech"

    async def generate_speech_audio(
        self,
        text_script: str,
        language_code: str = "hi-IN"
    ) -> Optional[str]:
        lang_meta = resolve_language(language_code)
        sarvam_lang = lang_meta["sarvam_code"]
        # Use resolved regional default speaker
        speaker = lang_meta.get("default_speaker", "ritu")

        truncated_text = text_script[:450] if len(text_script) > 450 else text_script

        if not self.api_key or self.api_key.startswith("your_") or self.api_key == "demo_key":
            logger.info(f"SARVAM_API_KEY not configured. Generating gTTS spoken audio fallback for language '{sarvam_lang}'...")
            return self._generate_gtts_fallback(truncated_text, sarvam_lang)

        payload = {
            "inputs": [truncated_text],
            "target_language_code": sarvam_lang,
            "speaker": speaker,
            "pitch": 0.0,
            "pace": 1.0,
            "loudness": 1.0,
            "speech_sample_rate": 22050,
            "enable_preprocessing": True,
            "model": "bulbul:v3"
        }

        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json"
        }

        try:
            logger.info(f"Sending Sarvam AI TTS request in '{sarvam_lang}' (Speaker: {speaker})...")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.tts_url, json=payload, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    audios = data.get("audios", [])
                    if audios and len(audios) > 0:
                        logger.info(f"Sarvam AI TTS audio generated successfully in '{sarvam_lang}' ({len(audios[0])} Base64 chars).")
                        return audios[0]
                else:
                    logger.warning(f"Sarvam API failed with status {response.status_code}: {response.text}. Falling back to gTTS...")
        except Exception as e:
            logger.warning(f"Sarvam TTS exception: {e}. Falling back to gTTS...")

        return self._generate_gtts_fallback(truncated_text, sarvam_lang)

    def _generate_gtts_fallback(self, text: str, sarvam_lang: str) -> Optional[str]:
        try:
            import io
            import base64
            from gtts import gTTS
            
            gtts_map = {
                "hi-IN": "hi", "bn-IN": "bn", "ta-IN": "ta", "te-IN": "te",
                "mr-IN": "mr", "gu-IN": "gu", "kn-IN": "kn", "ml-IN": "ml",
                "pa-IN": "pa", "od-IN": "or", "or-IN": "or", "en-IN": "en"
            }
            lang = gtts_map.get(sarvam_lang, "hi")

            fp = io.BytesIO()
            tts = gTTS(text=text[:350], lang=lang, slow=False)
            tts.write_to_fp(fp)
            fp.seek(0)
            b64_str = base64.b64encode(fp.read()).decode('utf-8')
            logger.info(f"gTTS Audio Fallback generated successfully in '{lang}' ({len(b64_str)} base64 chars).")
            return b64_str
        except Exception as ex:
            logger.error(f"gTTS fallback failed: {ex}")
            return None

sarvam_tts = SarvamTTSService()
