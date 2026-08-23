from typing import Dict, Any
from app.db.schemas import SafetyLevelEnum, SafetySchema

class DeterministicSafetyEngine:
    DANGEROUS_GENERA = ["echis", "daboia", "naja", "bungarus", "ophiophagus", "hypnale", "trimeresurus", "ovophis", "protobothrops", "gloydius"]

    @classmethod
    def evaluate_safety(
        cls,
        top_prediction: Dict[str, Any],
        identification_status: str,
        intent: str = "SNAKE_ENCOUNTER"
    ) -> SafetySchema:
        intent_upper = str(intent).upper()
        is_bite_intent = "BITE" in intent_upper

        # Rule 1: Fail-Safe Mode for Uncertain / Unable to Identify Status
        if identification_status == "NO_SNAKE_DETECTED" and not is_bite_intent:
            return SafetySchema(
                safety_level=SafetyLevelEnum.SAFE,
                venomous=False,
                medically_significant=False,
                antivenom_recommended=False,
                safety_message="NO SNAKE DETECTED (YOU ARE SAFE): No snake was detected in the uploaded image. Disclaimer: If a snake is hidden in foliage or you require expert verification, please upload a clearer photo or contact a certified local rescuer."
            )

        if identification_status in ["UNABLE_TO_IDENTIFY", "NO_SNAKE_DETECTED"]:
            return SafetySchema(
                safety_level=SafetyLevelEnum.CAUTION if not is_bite_intent else SafetyLevelEnum.CRITICAL,
                venomous=False,
                medically_significant=False,
                antivenom_recommended=is_bite_intent,
                safety_message="SNAKE BITE EMERGENCY ALERT: Species could not be visually confirmed with 100% certainty. Keep patient completely still and rush immediately to the nearest ASV Hospital." if is_bite_intent else "CAUTION: Species could not be identified with high visual certainty. Maintain a safe standoff distance (15+ feet) and do not attempt to capture or touch."
            )

        common_name = top_prediction.get("common_name", "Unknown Species")
        scientific_name = top_prediction.get("scientific_name", "")
        sc_lower = scientific_name.lower()
        cn_lower = common_name.lower()

        # Hardcode Big Four & Dangerous Genus Mandatory Venom Rule
        is_dangerous_genus = any(gen in sc_lower for gen in cls.DANGEROUS_GENERA) or \
                             any(kw in cn_lower for kw in ["viper", "cobra", "krait"])

        medically_sig = top_prediction.get("medically_significant", False) or is_dangerous_genus
        is_venomous = top_prediction.get("venomous", False) or is_dangerous_genus

        # Rule 2: Medically Significant / Dangerous Genus -> CRITICAL Priority
        if medically_sig:
            return SafetySchema(
                safety_level=SafetyLevelEnum.CRITICAL,
                venomous=True,
                medically_significant=True,
                antivenom_recommended=True,
                safety_message=f"CRITICAL WARNING: Highly venomous species ({common_name} / {scientific_name}). High neurotoxic or hemotoxic envenomation risk. Step back 15+ feet immediately. Seek emergency medical care instantly if bitten." if not is_bite_intent else f"SNAKE BITE EMERGENCY: Patient bitten by highly venomous species ({common_name}). Keep limb immobilized. Do NOT cut or apply tourniquets. Rush to nearest ASV hospital immediately!"
            )

        # Rule 3: Venomous (Mild/Moderate) -> HIGH Priority
        if is_venomous:
            return SafetySchema(
                safety_level=SafetyLevelEnum.HIGH,
                venomous=True,
                medically_significant=False,
                antivenom_recommended=is_bite_intent,
                safety_message=f"HIGH SAFETY ALERT: Venomous species ({common_name}). Standoff distance required. Mild to moderate envenomation risk (pain and swelling alert)." if not is_bite_intent else f"SNAKE BITE EMERGENCY: Bitten by venomous species ({common_name}). Keep patient calm and immobilized. Seek urgent medical evaluation at nearest ASV hospital."
            )

        # Rule 4: Harmless / Non-Venomous with Bite Intent Override
        if is_bite_intent:
            return SafetySchema(
                safety_level=SafetyLevelEnum.CAUTION,
                venomous=False,
                medically_significant=False,
                antivenom_recommended=False,
                safety_message=f"SNAKE BITE MEDICAL ALERT: Bite reported for non-venomous species ({common_name}). Clean wound with soap/water. Seek medical evaluation to prevent bacterial infection or secondary complications."
            )

        # Rule 5: Harmless / Non-Venomous -> LOW Risk
        return SafetySchema(
            safety_level=SafetyLevelEnum.LOW,
            venomous=False,
            medically_significant=False,
            antivenom_recommended=False,
            safety_message=f"LOW RISK: {common_name} is non-venomous and harmless to humans. Plays a crucial role in rodent control. Do not harm or kill."
        )
