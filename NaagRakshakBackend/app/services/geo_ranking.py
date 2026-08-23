from typing import List, Dict, Any, Optional

OCCURRENCE_MULTIPLIERS = {
    "PRESENT_ABUNDANT": 1.00,
    "PRESENT_COMMON": 1.00,
    "PRESENT_RARE": 0.85,
    "UNRECORDED": 0.50
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
                p["calibrated_confidence"] = float(round(p.get("raw_probability", 0.0), 4))
            return predictions

        adjusted_list = []

        for p in predictions:
            raw_p = float(p.get("raw_probability", 0.0))
            is_medically_significant = p.get("medically_significant", False)
            sci_name = p.get("scientific_name", "")

            # Default occurrence frequency for native Indian species
            freq_str = "PRESENT_COMMON"
            
            # Big Four venomous species are abundant/common across all Indian states
            BIG_FOUR = ["Naja naja", "Daboia russelii", "Bungarus caeruleus", "Echis carinatus"]
            if sci_name in BIG_FOUR:
                freq_str = "PRESENT_ABUNDANT"

            prior_multiplier = OCCURRENCE_MULTIPLIERS.get(freq_str, 1.0)
            adjusted_score = raw_p * prior_multiplier

            # Medically significant species keep their raw model probability
            if is_medically_significant:
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
