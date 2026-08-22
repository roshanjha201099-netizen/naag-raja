import logging
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from app.config import settings
from app.services.sarvam_tts import VALID_SARVAM_LANGUAGES

logger = logging.getLogger("naagrakshak.llm_explainer")

class LLMExplainerService:
    def __init__(self):
        self.client = None
        if settings.OPENAI_API_KEY:
            try:
                self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI LLM Explainer initialized.")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")

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
        if not self.client:
            return None

        target_language = VALID_SARVAM_LANGUAGES.get(language_code, "Hindi")
        local_name_str = f"{common_name}" + (f" ({hindi_name})" if hindi_name else "")

        intent_upper = intent.upper()
        hosp_info_str = ""
        if nearest_hospital_name and nearest_hospital_distance_km is not None:
            hosp_info_str = f" Nearest ASV Hospital: {nearest_hospital_name} ({nearest_hospital_distance_km} km away)."

        if "BITE" in intent_upper:
            intent_action_instruction = f"SNAKE BITE EMERGENCY! You MUST start with snake local name: '{local_name_str} ने काटा है! मरीज को शांत रखें, काटे स्थान को हिलाएं नहीं और तुरंत नजदीकी एंटी-वेनम अस्पताल जाएं।'{hosp_info_str} MUST state the snake local name AND nearest hospital name and distance!"
        else:
            intent_action_instruction = f"SNAKE ENCOUNTER ALERT! Instruct immediately: '{local_name_str} का सामना हुआ है। 15 फीट दूर रहें और तुरंत सुरक्षित स्थान पर जाएं।'"

        prompt = f"""
You are NaagRakshak Field Safety Voice Assistant for India.
Generate a VERY CONCISE 2-sentence emergency field alert script strictly written in the **{target_language}** language script.

FACTS:
- Snake Common/Local Name: {local_name_str}
- Assigned Safety Level: {safety_level}
- Situation Intent: {intent} ({intent_action_instruction})
- Region: {location or 'India'}
- Nearest ASV Medical Facility: {nearest_hospital_name or 'District Hospital'} ({nearest_hospital_distance_km if nearest_hospital_distance_km is not None else ''} km)

CRITICAL RULES FOR TTS VOICE:
1. Write the ENTIRE output strictly in **{target_language}** script (e.g. Devanagari script for Hindi/Marathi, Bengali script for Bengali, Tamil script for Tamil, etc.).
2. Do NOT use Latin binomial scientific names like "Naja naja" or "Bungarus caeruleus". Use ONLY common local names (e.g. "गेहुंअन / नाग", "फूड़सा", "करैत", "दबोइया").
3. For SNAKE_BITE_EMERGENCY intent, MUST start with snake local name (e.g. "{local_name_str} ने काटा है!"), instruct patient to keep calm & still, AND state nearest hospital name and distance (e.g. "नजदीकी अस्पताल {nearest_hospital_name or 'Sadar Hospital'} {nearest_hospital_distance_km or ''} km दूर है।")! Do NOT say 15 feet standoff or "सामना हुआ है" when bitten.
4. Keep it under 35 words total so it sounds natural when spoken aloud.
5. Do NOT include markdown formatting or quotes.
"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"You are a field herpetology safety assistant producing spoken audio scripts in {target_language}."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.3
            )
            script = response.choices[0].message.content.strip()
            # Strip quotes if any
            script = script.strip('"\'')
            return script
        except Exception as e:
            logger.warning(f"LLM regional explanation generation failed: {e}")
            return None

llm_explainer = LLMExplainerService()
