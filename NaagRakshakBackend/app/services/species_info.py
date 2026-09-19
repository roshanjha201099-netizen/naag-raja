import os
import csv

"""
Authoritative Species Knowledge Base for Indian & South Asian Snakes.
Aligned strictly with the target species classes of the ConvNeXt classifier.
"""

SNAKE_SPECIES_DB = {
    "common_krait": {
        "common_name": "Common Krait",
        "scientific_name": "Bungarus caeruleus",
        "family": "Elapidae",
        "danger_level": "EXTREME",
        "is_venomous": True,
        "key_traits": "Glossy steel-black body; narrow paired white crossbands along dorsal; enlarged hexagonal vertebral scales.",
        "habitat": "Fields, low scrub, farmlands, and near village houses across South Asia (primarily nocturnal).",
        "description": "One of India's 'Big Four' deadliest snakes. Highly potent neurotoxic venom.",
        "first_aid": "CRITICAL EMERGENCY: Apply pressure immobilization bandage. Rush to hospital with ICU/ventilator support immediately."
    },
    "indian_cobra": {
        "common_name": "Indian Spectacled Cobra",
        "scientific_name": "Naja naja",
        "family": "Elapidae",
        "danger_level": "EXTREME",
        "is_venomous": True,
        "key_traits": "Prominent dilatable neck hood with distinct spectacle mark; upright defensive posture.",
        "habitat": "Plains, agricultural fields, open forests, and residential peripheries throughout India.",
        "description": "A member of the 'Big Four'. Neurotoxic and cardiotoxic venom.",
        "first_aid": "IMMEDIATE HOSPITALIZATION: Keep patient completely still. Transport immediately to a hospital for polyvalent antivenom."
    },
    "russells_viper": {
        "common_name": "Russell's Viper",
        "scientific_name": "Daboia russelii",
        "family": "Viperidae",
        "danger_level": "EXTREME",
        "is_venomous": True,
        "key_traits": "Triangular flat head clearly distinct from thin neck; 3 distinct longitudinal chains of dark brown oval spots.",
        "habitat": "Open grasslands, farmland edges, and scrub forests in South Asia.",
        "description": "Responsible for the majority of severe snakebite envenomations in South Asia. Severe hemotoxicity.",
        "first_aid": "CRITICAL EMERGENCY: Keep bitten limb immobilized BELOW heart level. Do NOT use tight tourniquets or cut the wound."
    },
    "saw_scaled_viper": {
        "common_name": "Saw-scaled Viper",
        "scientific_name": "Echis carinatus",
        "family": "Viperidae",
        "danger_level": "HIGH",
        "is_venomous": True,
        "key_traits": "Small, stout body; white bird-foot marking on head; heavily keeled serrated flank scales.",
        "habitat": "Dry, sandy, and rocky soils, scrubland, and semi-arid terrain across India.",
        "description": "Irritable and quick to strike when stepped on. Potent hemotoxic venom.",
        "first_aid": "MEDICAL EMERGENCY: Immobilize limb and rush to hospital for antivenom and coagulation monitoring."
    },
    "king_cobra": {
        "common_name": "King Cobra",
        "scientific_name": "Ophiophagus hannah",
        "family": "Elapidae",
        "danger_level": "EXTREME",
        "is_venomous": True,
        "key_traits": "Olive-green to dark brown with pale chevron bands; expandable narrow hood; large size (3-5+ meters).",
        "habitat": "Dense forests, bamboo thickets, and wetlands across South & Southeast Asia.",
        "description": "The world's longest venomous snake. Preys predominantly on other snakes.",
        "first_aid": "CRITICAL EMERGENCY: Apply broad pressure immobilization. Keep patient calm and transport immediately."
    },
    "banded_krait": {
        "common_name": "Banded Krait",
        "scientific_name": "Bungarus fasciatus",
        "family": "Elapidae",
        "danger_level": "EXTREME",
        "is_venomous": True,
        "key_traits": "Broad alternating bright yellow and jet-black bands of equal width; triangular body cross-section.",
        "habitat": "Agricultural fields, lowlands, and water margins in Northeast and East India.",
        "description": "Shy and mostly nocturnal, but possesses lethal neurotoxic venom.",
        "first_aid": "CRITICAL EMERGENCY: Apply pressure bandage and rush immediately to emergency medical care for antivenom."
    },
    "common_wolf_snake": {
        "common_name": "Common Wolf Snake (Krait Mimic)",
        "scientific_name": "Lycodon aulicus",
        "family": "Colubridae",
        "danger_level": "LOW",
        "is_venomous": False,
        "key_traits": "Brown/grey body with white crossbars that narrow on spine; smooth scales; distinct neck.",
        "habitat": "Human homes, stone crevices, wall cracks, and gardens across South Asia.",
        "description": "Harmless non-venomous snake that Batesian-mimics the Common Krait.",
        "first_aid": "NON-VENOMOUS: Wash bite thoroughly with soap and clean water."
    },
    "rat_snake": {
        "common_name": "Indian Rat Snake (Dhaman)",
        "scientific_name": "Ptyas mucosa",
        "family": "Colubridae",
        "danger_level": "LOW",
        "is_venomous": False,
        "key_traits": "Large, slender, active snake (up to 2.5m); large eyes with round pupils; vertical lip stripes.",
        "habitat": "Farmlands, forests, roofs, and suburban areas throughout South Asia.",
        "description": "Beneficial non-venomous snake that keeps rodent populations under control.",
        "first_aid": "NON-VENOMOUS: Wash punctures with antiseptic soap and water."
    },
    "indian_rock_python": {
        "common_name": "Indian Rock Python",
        "scientific_name": "Python molurus",
        "family": "Pythonidae",
        "danger_level": "LOW",
        "is_venomous": False,
        "key_traits": "Large non-venomous constrictor; yellowish-brown pattern with dark irregular blotches.",
        "habitat": "Marshes, grasslands, open forests, and rocky river banks across India.",
        "description": "Large non-venomous constrictor, protected species in India.",
        "first_aid": "NON-VENOMOUS: Disinfect surface bite punctures with soap and water."
    },
    "checkered_keelback": {
        "common_name": "Checkered Keelback",
        "scientific_name": "Fowlea piscator",
        "family": "Colubridae",
        "danger_level": "LOW",
        "is_venomous": False,
        "key_traits": "Quincuncial checkered black spots on olive-grey body; active swimmer.",
        "habitat": "Freshwater lakes, paddy fields, rivers, and ponds across India.",
        "description": "Common non-venomous water snake, aggressive when cornered but non-venomous.",
        "first_aid": "NON-VENOMOUS: Wash with clean water and apply antiseptic cream."
    }
}

def load_dynamic_species_catalog(csv_path: str = "models/indian_snakes.csv"):
    """Dynamically loads and enriches species metadata from authoritative database CSV files."""
    if not os.path.exists(csv_path):
        return

    try:
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sci_name = row.get("scientific_name", "").strip()
                if not sci_name:
                    continue

                norm_key = sci_name.lower().replace(" ", "_")
                venomous_str = str(row.get("venomous_status", "")).lower()
                is_venomous = "non" not in venomous_str and ("venom" in venomous_str or "poison" in venomous_str)
                family = row.get("family", "Reptilia (Serpentes)").strip()

                if norm_key not in SNAKE_SPECIES_DB:
                    SNAKE_SPECIES_DB[norm_key] = {
                        "common_name": sci_name,
                        "scientific_name": sci_name,
                        "family": family,
                        "danger_level": "EXTREME" if is_venomous else "LOW",
                        "is_venomous": is_venomous,
                        "key_traits": f"Species of family {family}.",
                        "habitat": "Records documented across Indian regional habitats.",
                        "description": f"Authoritative record for {sci_name} ({family}). Venomous status: {venomous_str}.",
                        "first_aid": "IMMEDIATE MEDICAL CARE: Keep calm, immobilize limb, and go to hospital." if is_venomous else "Wash area with soap and water."
                    }
    except Exception:
        pass

# Automatically load dynamic catalog on import
load_dynamic_species_catalog()


def normalize_key(name: str) -> str:
    """Normalize class or common name to match database keys."""
    cleaned = name.lower().replace(" ", "_").replace("-", "_").strip()
    if cleaned in SNAKE_SPECIES_DB:
        return cleaned
    for key, info in SNAKE_SPECIES_DB.items():
        if key in cleaned or cleaned in key:
            return key
        if cleaned in info.get("common_name", "").lower().replace(" ", "_"):
            return key
        if cleaned in info.get("scientific_name", "").lower().replace(" ", "_"):
            return key
    return cleaned


def get_species_info(species_name: str) -> dict:
    """Retrieve detailed species info dictionary for a given prediction."""
    key = normalize_key(species_name)
    if key in SNAKE_SPECIES_DB:
        return SNAKE_SPECIES_DB[key]
    
    is_venomous = any(w in species_name.lower() for w in ["cobra", "viper", "krait"])
    return {
        "common_name": species_name.replace("_", " ").title(),
        "scientific_name": "Species classification result",
        "danger_level": "HIGH" if is_venomous else "LOW",
        "is_venomous": is_venomous,
        "first_aid": "If bitten, stay calm, immobilize limb below heart level, and proceed immediately to the nearest hospital."
    }
