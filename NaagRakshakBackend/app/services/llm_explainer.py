import os
import logging
import asyncio
import re
from typing import Dict, Any, Optional, Tuple, Union
from google import genai
from google.genai import types
from app.config import settings

logger = logging.getLogger("naagrakshak.llm_explainer")

# Recognized Scenarios
SCENARIO_NO_SNAKE = "NO_SNAKE"
SCENARIO_LOW_CONFIDENCE = "LOW_CONFIDENCE"
SCENARIO_NON_VENOMOUS = "NON_VENOMOUS"
SCENARIO_VENOMOUS = "VENOMOUS"
SCENARIO_VENOMOUS_HIGH = "VENOMOUS_HIGH"
SCENARIO_CRITICAL_DANGER = "CRITICAL_DANGER"


def normalize_confidence(confidence: Union[float, int]) -> int:
    """Normalizes confidence float (0.91) or int/float (91.4) into clean integer percentage (91)."""
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
    """Categorizes the backend situation into an authoritative scenario."""
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
    """Formats distance in natural spoken words."""
    rounded = round(distance_km, 1)
    if rounded == int(rounded):
        val = int(rounded)
        if val == 1:
            return "one kilometer"
        elif val == 2:
            return "two kilometers"
        elif val == 3:
            return "three kilometers"
        elif val == 4:
            return "four kilometers"
        elif val == 5:
            return "five kilometers"
        else:
            return f"{val} kilometers"
    return f"{rounded} kilometers"


def get_deterministic_fallback(
    scenario: str,
    snake_species: str,
    confidence: Union[float, int],
    venomous: bool,
    nearest_hospital_name: Optional[str] = None,
    nearest_hospital_distance_km: Optional[float] = None
) -> str:
    """Generates a high-quality, situation-tailored fallback spoken alert from backend facts."""
    conf_int = normalize_confidence(confidence)
    species_name = snake_species.strip() if snake_species else "unknown snake"

    hosp_str = ""
    if nearest_hospital_name and nearest_hospital_distance_km is not None:
        dist_str = format_hospital_distance(nearest_hospital_distance_km)
        hosp_str = f" The nearest hospital is {nearest_hospital_name}, about {dist_str} away."

    if scenario == SCENARIO_NO_SNAKE:
        return "No snake was detected in the uploaded photo. Please ensure the specimen is centered under good lighting."

    if scenario == SCENARIO_LOW_CONFIDENCE:
        venom_clause = "It may be venomous, so please keep your distance and treat it with caution." if venomous else "Keep a safe distance and avoid disturbing it."
        return f"This may be a {species_name}, with about {conf_int} percent confidence. {venom_clause} If anyone has been bitten, seek emergency medical care immediately.{hosp_str}"

    if scenario == SCENARIO_NON_VENOMOUS:
        return f"This appears to be a {species_name}, with about {conf_int} percent confidence. It is non-venomous, but please keep a safe distance and avoid handling or disturbing it.{hosp_str}"

    # VENOMOUS / VENOMOUS_HIGH / CRITICAL_DANGER
    return f"This looks like a {species_name}, with about {conf_int} percent confidence. It is venomous, so please stay well away and do not try to handle or approach it. If anyone has been bitten, get emergency medical care immediately.{hosp_str}"


def validate_explanation(
    text: str,
    snake_species: str,
    venomous: bool,
    nearest_hospital_name: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Validates LLM-generated script against strict safety, fact integrity, and TTS rules.
    Returns (is_valid, reason_message).
    """
    if not text or not text.strip():
        return False, "Empty or whitespace output"

    clean_text = text.strip()
    words = clean_text.split()

    if len(words) < 8:
        return False, f"Too short ({len(words)} words)"
    if len(words) > 65:
        return False, f"Too long for TTS ({len(words)} words)"

    # Sentence Closure Check
    if not clean_text.endswith(('.', '!', '?', '"', "'")):
        return False, "Truncated sentence (does not end with proper punctuation)"

    # Check for Markdown, Emojis, JSON, Quotes, or URLs

    forbidden_patterns = [
        (r'[`#*_\[\]\{\}]', "Contains markdown or bracket formatting"),
        (r'https?://|www\.', "Contains URL"),
        (r'^\s*["\'].*["\']\s*$', "Contains surrounding quotes"),
        (r'[\u4e00-\u9fff\u1100-\u11ff]', "Contains unsupported script chars")
    ]
    for pattern, reason in forbidden_patterns:
        if re.search(pattern, clean_text):
            return False, reason

    # Check for AI / Technical Meta-language
    meta_jargon = [
        r"\baccording to\b", r"\bprovided information\b", r"\bbased on the analysis\b", r"\bthe model\b",
        r"\bconvnext\b", r"\bood\b", r"\blogits\b", r"\bsoftmax\b", r"\bprobability distribution\b",
        r"\bconfidence score\b", r"\bdataset\b", r"\bbackend\b", r"\banalysis indicates\b"
    ]
    text_lower = clean_text.lower()
    for jargon_pattern in meta_jargon:
        if re.search(jargon_pattern, text_lower):
            term = jargon_pattern.replace(r"\b", "")
            return False, f"Contains technical/meta jargon: '{term}'"


    # Fact Integrity Check: Venomous Status
    if venomous:
        if "non-venomous" in text_lower or "harmless" in text_lower or "not venomous" in text_lower:
            return False, "CONTRADICTION: Backend says venomous, but text claimed non-venomous/harmless"
    else:
        if "is venomous" in text_lower or "highly venomous" in text_lower or "deadly venom" in text_lower:
            return False, "CONTRADICTION: Backend says non-venomous, but text claimed venomous"

    # Fact Integrity Check: Hospital Hallucination
    if not nearest_hospital_name:
        hospital_triggers = ["nearest hospital is", "hospital named", "medical center", "hospital, about"]
        for trigger in hospital_triggers:
            if trigger in text_lower:
                return False, f"HALLUCINATION: LLM invented hospital ('{trigger}') when none provided by backend"

    return True, "VALID"


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

    def build_prompt_for_scenario(
        self,
        scenario: str,
        snake_species: str,
        confidence_pct: int,
        venomous: bool,
        danger_level: str,
        nearest_hospital_name: Optional[str] = None,
        nearest_hospital_distance_km: Optional[float] = None,
        rescue_helpline: Optional[str] = None
    ) -> str:
        """Constructs a situation-adapted Gemini prompt focusing strictly on TTS output."""
        
        hospital_info_clause = ""
        if nearest_hospital_name and nearest_hospital_distance_km is not None:
            dist_str = format_hospital_distance(nearest_hospital_distance_km)
            hospital_info_clause = f"- Nearest Hospital: {nearest_hospital_name} (Distance: {dist_str})"

        scenario_instructions = ""
        if scenario == SCENARIO_LOW_CONFIDENCE:
            scenario_instructions = (
                "SITUATION: The species identification has low confidence. "
                f"State clearly that it 'may be' or 'could be' a {snake_species} with about {confidence_pct} percent confidence. "
                "Urge caution and recommend keeping distance. If anyone may have been bitten, advise emergency medical care immediately."
            )
        elif scenario == SCENARIO_NON_VENOMOUS:
            scenario_instructions = (
                "SITUATION: The identified snake is NON-VENOMOUS. "
                f"State that this looks like a {snake_species} with about {confidence_pct} percent confidence, and that it is non-venomous. "
                "Keep the tone calm and reassuring, but briefly advise avoiding handling or disturbing it."
            )
        else: # VENOMOUS / VENOMOUS_HIGH
            scenario_instructions = (
                "SITUATION: The identified snake is VENOMOUS and potentially dangerous. "
                f"State that this looks like a {snake_species} with about {confidence_pct} percent confidence, and clearly warn that it is venomous. "
                "Prioritize safety: advise staying well away and not trying to approach or handle it. "
                "If anyone has been bitten, urge seeking emergency medical care immediately."
            )

        prompt = f"""You are a calm, experienced Indian wildlife safety assistant speaking to someone who has just taken a photo of a snake.

YOUR BACKEND FACTS (DO NOT ALTER OR CONTRADICT):
- Species Name: {snake_species}
- Confidence Percentage: {confidence_pct}%
- Venomous Status: {"VENOMOUS" if venomous else "NON-VENOMOUS"}
- Danger Level: {danger_level}
{hospital_info_clause}

{scenario_instructions}

STRICT SPOKEN TTS RULES:
1. Speak directly, naturally, and warmly in 2 to 3 simple spoken sentences (25 to 40 words).
2. DO NOT use artificial AI phrasing like "According to the model", "Based on the analysis", "The provided information indicates", or "Confidence score".
3. DO NOT repeat the species name or confidence percentage multiple times.
4. DO NOT invent fake hospital names or helplines. Only mention the hospital if listed above.
5. Plain text ONLY: NO markdown (*, #), NO quotes around string, NO emojis, NO bullet points. Use simple commas and periods for natural speech pauses.

Return ONLY the plain spoken text."""
        return prompt

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
        is_snake_detected: bool = True
    ) -> str:
        """
        Main pipeline entry point:
        1. Categorizes scenario.
        2. If NO_SNAKE -> Returns deterministic backend message directly.
        3. Prepares authoritative facts & prompt.
        4. Calls LLM with situation adaptation.
        5. Validates LLM output against backend facts.
        6. Falls back gracefully to deterministic fallback on failure/rate-limit.
        """
        # 1. Normalize confidence & Determine scenario
        conf_pct = normalize_confidence(confidence)
        scenario = determine_scenario(is_snake_detected, conf_pct, venomous, danger_level)

        # 2. Handle NO_SNAKE deterministically without calling LLM
        if scenario == SCENARIO_NO_SNAKE:
            return get_deterministic_fallback(scenario, snake_species, conf_pct, venomous)

        # Prepare deterministic fallback for validation failure or API error
        fallback_text = get_deterministic_fallback(
            scenario,
            snake_species,
            conf_pct,
            venomous,
            nearest_hospital_name,
            nearest_hospital_distance_km
        )

        if not self.client:
            logger.info("LLM Client unavailable. Using deterministic fallback message.")
            return fallback_text

        # 3. Build adapted prompt
        prompt = self.build_prompt_for_scenario(
            scenario=scenario,
            snake_species=snake_species,
            confidence_pct=conf_pct,
            venomous=venomous,
            danger_level=danger_level,
            nearest_hospital_name=nearest_hospital_name,
            nearest_hospital_distance_km=nearest_hospital_distance_km,
            rescue_helpline=rescue_helpline
        )

        # 4. Call Gemini / Vertex LLM
        try:
            def _gen_content():
                res = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.25,
                        max_output_tokens=600
                    )

                )
                return res.text.strip() if res.text else ""

            raw_script = await asyncio.to_thread(_gen_content)
            clean_script = raw_script.strip('"\'`')

            # 5. Validate Output against backend facts
            is_valid, validation_reason = validate_explanation(
                text=clean_script,
                snake_species=snake_species,
                venomous=venomous,
                nearest_hospital_name=nearest_hospital_name
            )

            if is_valid:
                logger.info(f"✅ Voice alert script generated successfully via {self.provider} [{scenario}]: '{clean_script}'")
                return clean_script
            else:
                logger.warning(f"⚠️ LLM Validation Failed ({validation_reason}). Using deterministic fallback.")
                return fallback_text

        except Exception as e:
            logger.warning(f"Vertex/Gemini AI API exception ({e}). Using deterministic fallback.")
            return fallback_text


llm_explainer = LLMExplainerService()
