from typing import List, Dict, Any, Optional

OCCURRENCE_MULTIPLIERS = {
    "PRESENT_ABUNDANT": 1.00,
    "PRESENT_COMMON": 0.85,
    "PRESENT_RARE": 0.50,
    "UNRECORDED": 0.15
}

class LocationAwareRankingService:
    @staticmethod
    def rerank_predictions(
        predictions: List[Dict[str, Any]],
        state: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if not state or state == "All Regions / Nationwide":
            for p in predictions:
                p["regional_presence"] = "COMMON"
            return predictions

        adjusted_list = []
        alpha = 1.0
        beta = 0.25

        for p in predictions:
            raw_p = p["raw_probability"]
            is_medically_significant = p.get("medically_significant", False)

            # Look up regional frequency (Defaulting to COMMON for known species)
            freq_str = "PRESENT_COMMON"
            if "Bihar" in state and p["scientific_name"] in ["Daboia russelii", "Echis carinatus"]:
                freq_str = "PRESENT_RARE"
            elif "Bihar" in state and p["scientific_name"] in ["Bungarus caeruleus", "Naja naja"]:
                freq_str = "PRESENT_ABUNDANT"

            prior_multiplier = OCCURRENCE_MULTIPLIERS.get(freq_str, 0.85)

            # Apply Damped Bayesian Shift
            adjusted_score = (raw_p ** alpha) * (prior_multiplier ** beta)

            # SAFETY OVERRIDE RULE: High visual certainty (> 0.85) of medically significant species CANNOT be suppressed
            if is_medically_significant and raw_p >= 0.85:
                adjusted_score = max(adjusted_score, raw_p)

            p_copy = dict(p)
            p_copy["calibrated_confidence"] = float(round(adjusted_score, 4))
            p_copy["regional_presence"] = freq_str.replace("PRESENT_", "")
            adjusted_list.append(p_copy)

        # Normalize probabilities to sum to 1.0
        total_score = sum(p["calibrated_confidence"] for p in adjusted_list)
        if total_score > 0:
            for p in adjusted_list:
                p["calibrated_confidence"] = float(round(p["calibrated_confidence"] / total_score, 4))

        # Re-sort descending by calibrated confidence
        adjusted_list.sort(key=lambda x: x["calibrated_confidence"], reverse=True)
        return adjusted_list
