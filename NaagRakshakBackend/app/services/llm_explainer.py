import logging
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from app.config import settings

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
        species_name: str,
        safety_level: str,
        intent: str,
        location: Optional[str] = None
    ) -> Optional[str]:
        if not self.client:
            return None

        prompt = f"""
You are NaagRakshak AI, an expert herpetological safety explainer in India.
Provide a concise, 2-3 sentence field safety note based ONLY on the following verified facts:

- Detected Species: {species_name}
- Assigned Safety Level: {safety_level}
- User Situation / Intent: {intent}
- Location: {location or 'India'}

STRICT RULES:
1. Do NOT re-identify or contradict the species name ({species_name}) or safety level ({safety_level}).
2. Do NOT provide medical anti-venom dosage or medical diagnoses.
3. Be professional, urgent, clear, and focused on safety in Indian field conditions.
"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a field herpetology safety assistant for India."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"LLM explanation generation failed: {e}")
            return None

llm_explainer = LLMExplainerService()
