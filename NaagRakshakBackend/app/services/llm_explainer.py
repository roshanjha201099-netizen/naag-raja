import os
import logging
import re
from typing import Dict, Any, Optional, Tuple, Union, AsyncGenerator
from google import genai
from google.genai import types
from app.config import settings
from app.core.languages import resolve_language

logger = logging.getLogger("naagrakshak.llm_explainer")

SCENARIO_NO_SNAKE = "NO_SNAKE"
SCENARIO_LOW_CONFIDENCE = "LOW_CONFIDENCE"
SCENARIO_NON_VENOMOUS = "NON_VENOMOUS"
SCENARIO_VENOMOUS = "VENOMOUS"
SCENARIO_VENOMOUS_HIGH = "VENOMOUS_HIGH"

def normalize_confidence(confidence: Union[float, int]) -> int:
    try:
        conf_float = float(confidence)
        if conf_float <= 1.0:
            conf_float *= 100.0
        return max(0, min(100, int(round(conf_float))))
    except Exception:
        return 75

def determine_scenario(
    is_snake_detected: bool,
    confidence: Union[float, int],
    venomous: bool,
    danger_level: str
) -> str:
    if not is_snake_detected:
        return SCENARIO_NO_SNAKE
    conf_pct = normalize_confidence(confidence)
    danger_upper = str(danger_level).upper()
    if conf_pct < 70:
        return SCENARIO_LOW_CONFIDENCE
    if not venomous:
        return SCENARIO_NON_VENOMOUS
    if danger_upper in ["HIGH", "CRITICAL", "EXTREME"]:
        return SCENARIO_VENOMOUS_HIGH
    return SCENARIO_VENOMOUS

def format_hospital_distance(distance_km: float) -> str:
    rounded = round(distance_km, 1)
    if rounded == int(rounded):
        val = int(rounded)
        return "one kilometer" if val == 1 else f"{val} kilometers"
    return f"{rounded} kilometers"

def get_deterministic_fallback(
    scenario: str,
    snake_species: str,
    confidence: Union[float, int],
    venomous: bool,
    nearest_hospital_name: Optional[str] = None,
    nearest_hospital_distance_km: Optional[float] = None,
    language_code: str = "hi-IN"
) -> str:
    conf_int = normalize_confidence(confidence)
    species_name = snake_species.strip() if snake_species else "unknown snake"

    hosp_str = ""
    if nearest_hospital_name and nearest_hospital_distance_km is not None:
        dist_str = format_hospital_distance(nearest_hospital_distance_km)
        hosp_str = f" The nearest hospital with antivenom is {nearest_hospital_name}, about {dist_str} away."

    if scenario == SCENARIO_NO_SNAKE:
        return "No snake was detected in the photo. Please keep a safe distance and capture a clearer image."
    if scenario == SCENARIO_LOW_CONFIDENCE:
        venom_clause = "It may be venomous, so please keep your distance." if venomous else "Avoid disturbing it."
        return f"This may be a {species_name}, with about {conf_int} percent confidence. {venom_clause} Seek immediate medical care if bitten.{hosp_str}"
    if scenario == SCENARIO_NON_VENOMOUS:
        return f"This appears to be a {species_name}, with about {conf_int} percent confidence. It is non-venomous, but avoid handling it.{hosp_str}"

    return f"This looks like a {species_name}, with about {conf_int} percent confidence. It is venomous. Stay well away and seek emergency medical care immediately if bitten.{hosp_str}"

def validate_explanation(
    text: str,
    snake_species: str,
    venomous: bool,
    nearest_hospital_name: Optional[str] = None
) -> Tuple[bool, str]:
    if not text or not text.strip():
        return False, "Empty output"
    clean_text = text.strip()
    words = clean_text.split()
    if len(words) < 5:
        return False, "Too short"
    if len(words) > 85:
        return False, "Too long"
    return True, "VALID"

class LLMExplainerService:
    def __init__(self):
        self.client = None
        self.provider = None
        if settings.GEMINI_API_KEY:
            try:
                # Strictly bind to standard Google GenAI API key
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
                self.provider = "Gemini API"
                logger.info("Gemini API Client initialized successfully.")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini API client: {e}")

    def build_prompt(
        self,
        snake_species: str,
        confidence_pct: int,
        venomous: bool,
        danger_level: str,
        language_code: str,
        nearest_hospital_name: Optional[str],
        nearest_hospital_distance_km: Optional[float],
        rescue_helpline: Optional[str]
    ) -> str:
        lang_meta = resolve_language(language_code)
        target_lang = lang_meta["name"]
        native_name = lang_meta["native"]

        hospital_clause = ""
        if nearest_hospital_name and nearest_hospital_distance_km is not None:
            dist_str = format_hospital_distance(nearest_hospital_distance_km)
            hospital_clause = f"- Nearest Hospital with Antivenom: {nearest_hospital_name} ({dist_str})"

        return f"""You are an emergency wildlife first-aid assistant speaking to a person who found a snake in India.

TARGET LANGUAGE: {target_lang} ({native_name}). Write ONLY in the native script of {target_lang}.

BACKEND FACTS (DO NOT CONTRADICT):
- Specimen: {snake_species} ({confidence_pct}% confidence)
- Venomous: {"YES (VENOMOUS)" if venomous else "NO (NON-VENOMOUS)"}
- Danger: {danger_level}
{hospital_clause}
- Helpline: {rescue_helpline or "1926"}

INSTRUCTIONS:
1. Generate 2 to 3 concise, calm emergency guidance sentences directly in {target_lang}.
2. If venomous: instruct them to remain calm and still, immobilize any bitten limb, do NOT apply a tourniquet, do NOT cut the wound, and go immediately to the hospital.
3. No Markdown symbols (*, #), no emojis, no AI meta-phrases. Plain conversational text suitable for audio synthesis."""

    async def generate_explanation(
        self,
        snake_species: str,
        confidence: Union[float, int],
        venomous: bool,
        danger_level: str,
        user_description: Optional[str] = None,
        state: Optional[str] = None,
        user_lat: Optional[float] = None,
        user_lng: Optional[float] = None,
        nearest_hospital_name: Optional[str] = None,
        nearest_hospital_distance_km: Optional[float] = None,
        rescue_helpline: Optional[str] = None,
        is_snake_detected: bool = True,
        language_code: str = "hi-IN"
    ) -> str:
        conf_pct = normalize_confidence(confidence)
        scenario = determine_scenario(is_snake_detected, conf_pct, venomous, danger_level)

        if scenario == SCENARIO_NO_SNAKE or not self.client:
            return get_deterministic_fallback(
                scenario, snake_species, conf_pct, venomous,
                nearest_hospital_name, nearest_hospital_distance_km, language_code
            )

        prompt = self.build_prompt(
            snake_species=snake_species,
            confidence_pct=conf_pct,
            venomous=venomous,
            danger_level=danger_level,
            language_code=language_code,
            nearest_hospital_name=nearest_hospital_name,
            nearest_hospital_distance_km=nearest_hospital_distance_km,
            rescue_helpline=rescue_helpline
        )

        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.25,
                    max_output_tokens=600
                )
            )
            raw_script = response.text.strip() if response.text else ""
            clean_script = raw_script.strip('"\'`')

            is_valid, _ = validate_explanation(
                text=clean_script,
                snake_species=snake_species,
                venomous=venomous,
                nearest_hospital_name=nearest_hospital_name
            )

            if is_valid:
                return clean_script
            return get_deterministic_fallback(scenario, snake_species, conf_pct, venomous, nearest_hospital_name, nearest_hospital_distance_km, language_code)
        except Exception as e:
            logger.warning(f"Gemini API exception ({e}). Using fallback.")
            return get_deterministic_fallback(scenario, snake_species, conf_pct, venomous, nearest_hospital_name, nearest_hospital_distance_km, language_code)

    async def generate_explanation_stream(
        self,
        species_facts: dict,
        is_bite: bool = False,
        language_code: str = "hi-IN",
        user_description: Optional[str] = None,
        state: Optional[str] = None,
        hospital_name: Optional[str] = None,
        hospital_dist: Optional[float] = None,
        rescue_helpline: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        snake_species = species_facts.get('common_name', species_facts.get('scientific_name', 'Snake'))
        confidence = species_facts.get('confidence_score', species_facts.get('probability', 90))
        venomous = species_facts.get('is_venomous', species_facts.get('venomous', False))
        danger_level = species_facts.get('danger_level', 'HIGH' if venomous else 'LOW')
        conf_pct = normalize_confidence(confidence)

        scenario = determine_scenario(True, conf_pct, venomous, danger_level)

        if not self.client:
            yield get_deterministic_fallback(scenario, snake_species, conf_pct, venomous, hospital_name, hospital_dist, language_code)
            return

        prompt = self.build_prompt(
            snake_species=snake_species,
            confidence_pct=conf_pct,
            venomous=venomous,
            danger_level=danger_level,
            language_code=language_code,
            nearest_hospital_name=hospital_name,
            nearest_hospital_distance_km=hospital_dist,
            rescue_helpline=rescue_helpline
        )

        try:
            response = await self.client.aio.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=prompt
            )
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.warning(f"Gemini streaming exception: {e}. Yielding fallback.")
            yield get_deterministic_fallback(scenario, snake_species, conf_pct, venomous, hospital_name, hospital_dist, language_code)

llm_explainer = LLMExplainerService()
