import os
import logging
import asyncio
from typing import Dict, Any, Optional
from google import genai
from google.genai import types
from app.config import settings
from app.services.sarvam_tts import VALID_SARVAM_LANGUAGES

logger = logging.getLogger("naagrakshak.llm_explainer")

class LLMExplainerService:
    def __init__(self):
        self.client = None
        self.provider = None

        # 1. Primary: Try Vertex AI Service Account
        creds_path = os.path.abspath(settings.VERTEX_CREDENTIALS_PATH)
        if os.path.exists(creds_path):
            try:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
                self.client = genai.Client(vertexai=True, project="demos-others", location="us-central1")
                self.provider = "Vertex AI (demos-others)"
                logger.info("✅ Google Cloud Vertex AI Client initialized successfully (Project: demos-others).")
            except Exception as e:
                logger.warning(f"Failed to initialize Vertex AI client: {e}")

        # 2. Fallback: Try Gemini API Key
        if not self.client and settings.GEMINI_API_KEY:
            try:
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
                self.provider = "Gemini API"
                logger.info("✅ Google Gemini API Client initialized successfully.")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini API client: {e}")

    async def generate_explanation(
        self,
        common_name: str,
        hindi_name: Optional[str],
        safety_level: str,
        intent: str,
        location: Optional[str] = None,
        language_code: str = "hi-IN",
        nearest_hospital_name: Optional[str] = None,
        nearest_hospital_distance_km: Optional[float] = None
    ) -> Optional[str]:
        target_language = VALID_SARVAM_LANGUAGES.get(language_code, "Hindi")
        local_name_str = f"{common_name}" + (f" ({hindi_name})" if hindi_name else "")

        intent_upper = intent.upper()
        hosp_info_str = ""
        if nearest_hospital_name and nearest_hospital_distance_km is not None:
            hosp_info_str = f" Nearest ASV Hospital: {nearest_hospital_name} ({nearest_hospital_distance_km} km away)."

        if not self.client:
            h_str = f" नजदीकी अस्पताल {nearest_hospital_name} {nearest_hospital_distance_km} किमी दूर है।" if nearest_hospital_name else ""
            if "BITE" in intent_upper:
                return f"{local_name_str} ने काटा है! मरीज को शांत रखें, हिलाएं नहीं और तुरंत अस्पताल जाएं।{h_str}"
            else:
                return f"{local_name_str} का सामना हुआ है। कृपया 15 फीट दूर रहें और सुरक्षित स्थान पर जाएं।{h_str}"

        if "BITE" in intent_upper:
            intent_action_instruction = f"SNAKE BITE EMERGENCY! You MUST start with snake local name: '{local_name_str} ने काटा है! मरीज को शांत रखें, काटे स्थान को हिलाएं नहीं और तुरंत नजदीकी एंटी-वेनम अस्पताल जाएं।'{hosp_info_str} MUST state the snake local name AND nearest hospital name and distance!"
        else:
            intent_action_instruction = f"SNAKE ENCOUNTER ALERT! Instruct immediately: '{local_name_str} का सामना हुआ है। 15 फीट दूर रहें और तुरंत सुरक्षित स्थान पर जाएं।'"

        prompt = f"""You are NaagRakshak, an India-focused field safety voice assistant.

Generate a VERY CONCISE emergency voice alert in exactly 2 sentences, written entirely in the {target_language} script.

INPUT FACTS:
- Snake local/common name: {local_name_str}
- Safety level: {safety_level}
- Situation: {intent}
- Required action: {intent_action_instruction}
- Region: {location or 'India'}
- Nearest ASV medical facility: {nearest_hospital_name or 'District Hospital'}
- Hospital distance: {nearest_hospital_distance_km if nearest_hospital_distance_km is not None else 'unknown'} km

STRICT RULES:
1. Write ONLY in the requested {target_language} script. No English words or scientific names.
2. Use ONLY the local snake name "{local_name_str}".
3. If SNAKE_BITE_EMERGENCY, start with "{local_name_str} ने काटा है!" and mention nearest hospital.
4. Output EXACTLY 2 sentences and under 35 words. Return ONLY the 2 sentences text.
"""
        try:
            # Execute synchronous GenAI SDK call in threadpool
            def _gen_content():
                res = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        max_output_tokens=150
                    )
                )
                return res.text.strip()

            script = await asyncio.to_thread(_gen_content)
            script = script.strip('"\'')
            logger.info(f"✅ Voice alert script generated successfully via {self.provider}: '{script}'")
            return script
        except Exception as e:
            logger.warning(f"Vertex/Gemini AI explanation generation failed ({e}). Using dynamic emergency script for Sarvam AI TTS.")
            h_str = f" नजदीकी अस्पताल {nearest_hospital_name} {nearest_hospital_distance_km} किमी दूर है।" if nearest_hospital_name else ""
            if "BITE" in intent_upper:
                return f"{local_name_str} ने काटा है! मरीज को शांत रखें, हिलाएं नहीं और तुरंत अस्पताल जाएं।{h_str}"
            else:
                return f"{local_name_str} का सामना हुआ है। कृपया 15 फीट दूर रहें और सुरक्षित स्थान पर जाएं।{h_str}"

llm_explainer = LLMExplainerService()
