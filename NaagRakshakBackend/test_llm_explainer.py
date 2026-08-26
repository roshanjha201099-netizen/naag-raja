"""
Independent Test Harness and Prototype for NaagRakshak LLM Explainer.
Can be run directly via CLI without running the frontend, model, database, or server.

Usage:
  python test_llm_explainer.py               # Run all 14 test scenarios with Gemini/Vertex AI (or fallback if offline)
  python test_llm_explainer.py --mock        # Run in offline mock mode (0 API credits used)
  python test_llm_explainer.py --scenario venomous --runs 5
"""

import sys
import os
import argparse
import asyncio
from typing import List, Dict, Any

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.llm_explainer import (
    LLMExplainerService,
    determine_scenario,
    normalize_confidence,
    get_deterministic_fallback,
    validate_explanation,
    SCENARIO_NO_SNAKE,
    SCENARIO_LOW_CONFIDENCE,
    SCENARIO_NON_VENOMOUS,
    SCENARIO_VENOMOUS,
    SCENARIO_VENOMOUS_HIGH
)

TEST_SCENARIOS: List[Dict[str, Any]] = [
    {
        "id": "scenario_1_cobra_high",
        "name": "1. Indian Cobra (91%, Venomous, HIGH, With Hospital)",
        "inputs": {
            "snake_species": "Indian Cobra",
            "confidence": 91,
            "venomous": True,
            "danger_level": "HIGH",
            "user_description": "Snake found near house entrance",
            "state": "Bihar",
            "nearest_hospital_name": "AIIMS Patna Hospital",
            "nearest_hospital_distance_km": 4.2,
            "rescue_helpline": "Forest Rescue 1926",
            "is_snake_detected": True
        }
    },
    {
        "id": "scenario_2_krait_critical",
        "name": "2. Common Krait (94%, Venomous, CRITICAL, With Hospital)",
        "inputs": {
            "snake_species": "Common Krait",
            "confidence": 0.94,
            "venomous": True,
            "danger_level": "CRITICAL",
            "user_description": "Hiding under porch tiles",
            "state": "Maharashtra",
            "nearest_hospital_name": "District Civil Hospital",
            "nearest_hospital_distance_km": 2.0,
            "rescue_helpline": "WildLife Helpline 98220",
            "is_snake_detected": True
        }
    },
    {
        "id": "scenario_3_rat_snake",
        "name": "3. Indian Rat Snake (88%, Non-Venomous, LOW)",
        "inputs": {
            "snake_species": "Indian Rat Snake",
            "confidence": 88,
            "venomous": False,
            "danger_level": "LOW",
            "user_description": "Crawling along garden boundary wall",
            "state": "Karnataka",
            "nearest_hospital_name": "City General Hospital",
            "nearest_hospital_distance_km": 5.5,
            "rescue_helpline": "BBMP Wildlife Helpline",
            "is_snake_detected": True
        }
    },
    {
        "id": "scenario_4_python",
        "name": "4. Indian Rock Python (79%, Non-Venomous)",
        "inputs": {
            "snake_species": "Indian Rock Python",
            "confidence": 0.79,
            "venomous": False,
            "danger_level": "CAUTION",
            "user_description": "Resting under large banyan tree",
            "state": "Gujarat",
            "nearest_hospital_name": "Civil Hospital",
            "nearest_hospital_distance_km": 8.1,
            "rescue_helpline": "Forest Department 1926",
            "is_snake_detected": True
        }
    },
    {
        "id": "scenario_5_low_conf_cobra",
        "name": "5. Indian Cobra (61%, Venomous, Low Confidence / Uncertainty)",
        "inputs": {
            "snake_species": "Indian Cobra",
            "confidence": 61,
            "venomous": True,
            "danger_level": "HIGH",
            "user_description": "Partially obscured by thick grass",
            "state": "Uttar Pradesh",
            "nearest_hospital_name": "SGM Hospital",
            "nearest_hospital_distance_km": 3.0,
            "rescue_helpline": "1926",
            "is_snake_detected": True
        }
    },
    {
        "id": "scenario_6_no_snake",
        "name": "6. No Snake Detected",
        "inputs": {
            "snake_species": "Unknown",
            "confidence": 0.05,
            "venomous": False,
            "danger_level": "SAFE",
            "user_description": "Took photo of brown stick in garden",
            "state": "Delhi",
            "nearest_hospital_name": None,
            "nearest_hospital_distance_km": None,
            "rescue_helpline": None,
            "is_snake_detected": False
        }
    },
    {
        "id": "scenario_7_russell_hospital",
        "name": "7. Russell's Viper (89%, Venomous, With Hospital Info)",
        "inputs": {
            "snake_species": "Russell's Viper",
            "confidence": 89,
            "venomous": True,
            "danger_level": "CRITICAL",
            "user_description": "Found near paddy field edge",
            "state": "Tamil Nadu",
            "nearest_hospital_name": "Government Medical College Hospital",
            "nearest_hospital_distance_km": 1.5,
            "rescue_helpline": "1926",
            "is_snake_detected": True
        }
    },
    {
        "id": "scenario_8_saw_scaled_no_hospital",
        "name": "8. Saw-scaled Viper (92%, Venomous, Without Hospital Info)",
        "inputs": {
            "snake_species": "Saw-scaled Viper",
            "confidence": 0.92,
            "venomous": True,
            "danger_level": "HIGH",
            "user_description": "Spotted in rocky dry riverbed",
            "state": "Rajasthan",
            "nearest_hospital_name": None,
            "nearest_hospital_distance_km": None,
            "rescue_helpline": "Desert Wildlife Rescue",
            "is_snake_detected": True
        }
    },
    {
        "id": "scenario_9_missing_hospital",
        "name": "9. Banded Krait (95%, Venomous, Missing Hospital)",
        "inputs": {
            "snake_species": "Banded Krait",
            "confidence": 95,
            "venomous": True,
            "danger_level": "EXTREME",
            "user_description": "Yellow and black striped snake near stream",
            "state": "Assam",
            "nearest_hospital_name": None,
            "nearest_hospital_distance_km": None,
            "rescue_helpline": "Forest Helpline",
            "is_snake_detected": True
        }
    },
    {
        "id": "scenario_10_missing_helpline",
        "name": "10. Common Trinket Snake (85%, Non-Venomous, Missing Helpline)",
        "inputs": {
            "snake_species": "Common Trinket Snake",
            "confidence": 0.85,
            "venomous": False,
            "danger_level": "LOW",
            "user_description": "Found inside kitchen store room",
            "state": "Kerala",
            "nearest_hospital_name": "Taluk Hospital",
            "nearest_hospital_distance_km": 3.4,
            "rescue_helpline": None,
            "is_snake_detected": True
        }
    },
    {
        "id": "scenario_11_float_confidence",
        "name": "11. Confidence Supplied as Float (0.91)",
        "inputs": {
            "snake_species": "Indian Cobra",
            "confidence": 0.91,
            "venomous": True,
            "danger_level": "HIGH",
            "user_description": "Near backyard drain",
            "state": "Bihar",
            "nearest_hospital_name": " सदर अस्पताल",
            "nearest_hospital_distance_km": 4.0,
            "rescue_helpline": "1926",
            "is_snake_detected": True
        }
    },
    {
        "id": "scenario_12_int_confidence",
        "name": "12. Confidence Supplied as Integer (91)",
        "inputs": {
            "snake_species": "Indian Cobra",
            "confidence": 91,
            "venomous": True,
            "danger_level": "HIGH",
            "user_description": "Near backyard drain",
            "state": "Bihar",
            "nearest_hospital_name": "District Hospital",
            "nearest_hospital_distance_km": 4.0,
            "rescue_helpline": "1926",
            "is_snake_detected": True
        }
    },
    {
        "id": "scenario_13_very_low_conf",
        "name": "13. Very Low Confidence (45%)",
        "inputs": {
            "snake_species": "Common Wolf Snake",
            "confidence": 45,
            "venomous": False,
            "danger_level": "LOW",
            "user_description": "Blurry night photo of snake tail",
            "state": "West Bengal",
            "nearest_hospital_name": "Rural Health Centre",
            "nearest_hospital_distance_km": 6.2,
            "rescue_helpline": "1926",
            "is_snake_detected": True
        }
    },
    {
        "id": "scenario_14_noisy_description",
        "name": "14. User Description with Irrelevant Noise",
        "inputs": {
            "snake_species": "Indian Cobra",
            "confidence": 93,
            "venomous": True,
            "danger_level": "HIGH",
            "user_description": "My dog barking at snake near blue plastic bucket behind bicycle near gate",
            "state": "Madhya Pradesh",
            "nearest_hospital_name": "District Hospital",
            "nearest_hospital_distance_km": 2.5,
            "rescue_helpline": "1926",
            "is_snake_detected": True
        }
    }
]


async def run_scenario(
    scenario_data: Dict[str, Any],
    explainer: LLMExplainerService,
    mock_mode: bool = False
):
    inp = scenario_data["inputs"]
    name = scenario_data["name"]

    conf_pct = normalize_confidence(inp["confidence"])
    scenario = determine_scenario(
        inp["is_snake_detected"],
        conf_pct,
        inp["venomous"],
        inp["danger_level"]
    )

    if mock_mode:
        provider_name = "Mock Engine (Deterministic Fallback)"
        response_text = get_deterministic_fallback(
            scenario=scenario,
            snake_species=inp["snake_species"],
            confidence=conf_pct,
            venomous=inp["venomous"],
            nearest_hospital_name=inp.get("nearest_hospital_name"),
            nearest_hospital_distance_km=inp.get("nearest_hospital_distance_km")
        )
    else:
        provider_name = explainer.provider or "Deterministic Fallback"
        response_text = await explainer.generate_explanation(
            snake_species=inp["snake_species"],
            confidence=inp["confidence"],
            venomous=inp["venomous"],
            danger_level=inp["danger_level"],
            user_description=inp.get("user_description"),
            state=inp.get("state"),
            nearest_hospital_name=inp.get("nearest_hospital_name"),
            nearest_hospital_distance_km=inp.get("nearest_hospital_distance_km"),
            rescue_helpline=inp.get("rescue_helpline"),
            is_snake_detected=inp.get("is_snake_detected", True)
        )

    is_valid, validation_msg = validate_explanation(
        text=response_text,
        snake_species=inp["snake_species"],
        venomous=inp["venomous"],
        nearest_hospital_name=inp.get("nearest_hospital_name")
    )

    raw_hosp = inp.get('nearest_hospital_name')
    hosp_disp = raw_hosp.encode('ascii', errors='ignore').decode('ascii').strip() if raw_hosp else ""
    if not hosp_disp and raw_hosp:
        hosp_disp = "Local Hospital"
    hosp_str = f"{hosp_disp} ({inp.get('nearest_hospital_distance_km')} km)" if raw_hosp else "None"

    resp_disp = response_text.encode('ascii', errors='ignore').decode('ascii').strip()
    if not resp_disp:
        resp_disp = response_text

    print("=" * 80)
    print(f"SCENARIO: {name}")
    print("-" * 80)
    print(f"INPUT FACTS  : Species: {inp['snake_species']} | Conf: {conf_pct}% | Venomous: {inp['venomous']} | Danger: {inp['danger_level']}")
    print(f"EXTRA DATA   : Hospital: {hosp_str} | Helpline: {inp.get('rescue_helpline') or 'None'}")
    print("-" * 80)
    print("GENERATED RESPONSE:")
    print(f'"{resp_disp}"')
    print("-" * 80)
    print(f"METADATA     : Provider: {provider_name} | Scenario: {scenario} | Validation: {'PASS' if is_valid else 'FAIL (' + validation_msg + ')'}")
    print("=" * 80 + "\n")




async def main():
    parser = argparse.ArgumentParser(description="Test Harness for NaagRakshak LLM Explainer")
    parser.add_argument("--mock", action="store_true", help="Run offline in mock mode (0 API calls)")
    parser.add_argument("--scenario", type=str, default=None, help="Filter scenario by keyword (e.g. cobra, krait, python, rat)")
    parser.add_argument("--runs", type=int, default=1, help="Number of test runs per scenario")
    args = parser.parse_args()

    explainer = LLMExplainerService()
    
    print("\n" + "=" * 70)
    print(" NAAGRAKSHAK LLM EXPLAINER TEST PROTOTYPE")
    print(f" Mode: {'OFFLINE MOCK (0 API Credits)' if args.mock else 'LIVE ENGINE (' + str(explainer.provider or 'Fallback') + ')'}")
    print("=" * 70 + "\n")


    scenarios_to_run = TEST_SCENARIOS
    if args.scenario:
        filter_kw = args.scenario.lower()
        scenarios_to_run = [s for s in TEST_SCENARIOS if filter_kw in s["name"].lower() or filter_kw in s["id"].lower()]

    for run_idx in range(1, args.runs + 1):
        if args.runs > 1:
            print(f"\n🔄 --- RUN ITERATION {run_idx} / {args.runs} ---")
        for sc in scenarios_to_run:
            await run_scenario(sc, explainer, mock_mode=args.mock)


if __name__ == "__main__":
    asyncio.run(main())
