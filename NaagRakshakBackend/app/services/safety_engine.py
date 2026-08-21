from typing import Dict, Any
from app.db.schemas import SafetyLevelEnum, SafetySchema

class DeterministicSafetyEngine:
    @staticmethod
    def evaluate_safety(
        top_prediction: Dict[str, Any],
        identification_status: str
    ) -> SafetySchema:
        # Rule 1: Fail-Safe Mode for Uncertain / Unable to Identify Status
        if identification_status in ["UNABLE_TO_IDENTIFY", "NO_SNAKE_DETECTED"]:
            return SafetySchema(
                safety_level=SafetyLevelEnum.CAUTION,
                venomous=False,
                medically_significant=False,
                antivenom_recommended=False,
                safety_message="CAUTION: Species could not be identified with high visual certainty. Assume snake is potentially venomous. Maintain a safe standoff distance (15+ feet) and do not attempt to capture or touch."
            )

        medically_sig = top_prediction.get("medically_significant", False)
        is_venomous = top_prediction.get("venomous", False)
        common_name = top_prediction.get("common_name", "Unknown Species")
        scientific_name = top_prediction.get("scientific_name", "")

        # Rule 2: Medically Significant Species -> CRITICAL Priority
        if medically_sig:
            return SafetySchema(
                safety_level=SafetyLevelEnum.CRITICAL,
                venomous=True,
                medically_significant=True,
                antivenom_recommended=True,
                safety_message=f"CRITICAL WARNING: Highly venomous species ({common_name} / {scientific_name}). High neurotoxic or hemotoxic envenomation risk. Step back 15+ feet immediately. Seek emergency medical care instantly if bitten."
            )

        # Rule 3: Venomous (Mild/Moderate) -> HIGH Priority
        if is_venomous:
            return SafetySchema(
                safety_level=SafetyLevelEnum.HIGH,
                venomous=True,
                medically_significant=False,
                antivenom_recommended=False,
                safety_message=f"HIGH SAFETY ALERT: Venomous species ({common_name}). Standoff distance required. Mild to moderate envenomation risk (pain and swelling alert)."
            )

        # Rule 4: Harmless / Non-Venomous -> LOW Standoff
        return SafetySchema(
            safety_level=SafetyLevelEnum.LOW,
            venomous=False,
            medically_significant=False,
            antivenom_recommended=False,
            safety_message=f"LOW RISK: {common_name} is non-venomous and harmless to humans. Plays a crucial role in rodent control. Do not harm or kill."
        )
