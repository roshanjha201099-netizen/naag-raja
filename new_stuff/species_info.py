"""
Species Knowledge Base and Metadata for Snake Classification.
Provides details on venomous status, danger levels, distribution, and first aid tips.
"""

SNAKE_SPECIES_DB = {
    "common_krait": {
        "common_name": "Common Krait",
        "scientific_name": "Bungarus caeruleus",
        "family": "Elapidae (Cobras & Kraits)",
        "danger_level": "EXTREME",
        "is_venomous": True,
        "key_traits": "Glossy steel-black or dark blue-black body; narrow paired white crossbands along dorsal; enlarged hexagonal vertebral scales down the spine; smooth shiny scales; sub-cylindrical body with no distinct neck.",
        "habitat": "Fields, low scrub, farmlands, and near village houses in South Asia (primarily nocturnal)",
        "description": "One of India's 'Big Four' deadliest snakes. Neurotoxic venom is 15x more potent than cobra venom. Bites often occur at night and are deceptive because they cause minimal pain/swelling initially.",
        "first_aid": "🚨 CRITICAL MEDICAL EMERGENCY: Immobilize limb completely with pressure bandage. Do NOT let patient walk. Rush to hospital with ICU/ventilator support immediately — respiratory failure can onset within hours."
    },
    "king_cobra": {
        "common_name": "King Cobra",
        "scientific_name": "Ophiophagus hannah",
        "family": "Elapidae (Cobras & Kraits)",
        "danger_level": "EXTREME",
        "is_venomous": True,
        "key_traits": "Olive-green to dark brown/black with pale chevron bands; large occipital head shields; expandable narrow hood with forward-facing threat display; large size (3–5+ meters).",
        "habitat": "Dense forests, bamboo thickets, and wetlands across South & Southeast Asia",
        "description": "The world's longest venomous snake. Preys predominantly on other snakes. Injects massive venom volume per bite.",
        "first_aid": "🚨 MEDICAL EMERGENCY: Call emergency services immediately. Apply broad pressure immobilization bandage. Keep patient calm and completely still. Administer specific antivenom at nearest hospital."
    },
    "indian_cobra": {
        "common_name": "Indian Spectacled Cobra",
        "scientific_name": "Naja naja",
        "family": "Elapidae (Cobras & Kraits)",
        "danger_level": "EXTREME",
        "is_venomous": True,
        "key_traits": "Prominent dilatable neck hood with distinct spectacle/mono-ocellate marking on back; smooth scales; raised upright defensive posture with audible hissing.",
        "habitat": "Plains, agricultural fields, open forests, and residential peripheries throughout India",
        "description": "A member of the 'Big Four'. Neurotoxic and cardiotoxic venom. Easily provoked when cornered.",
        "first_aid": "🚨 IMMEDIATE HOSPITALIZATION: Apply pressure-immobilization bandage from digits up the limb. Keep patient still and transport immediately to a hospital for polyvalent antivenom."
    },
    "russells_viper": {
        "common_name": "Russell's Viper",
        "scientific_name": "Daboia russelii",
        "family": "Viperidae (True Vipers)",
        "danger_level": "EXTREME",
        "is_venomous": True,
        "key_traits": "Triangular flat head clearly distinct from thin neck; heavily keeled, rough scales; 3 distinct longitudinal chains of dark brown oval spots with black and white borders; loud pressure-cooker hiss.",
        "habitat": "Open grasslands, farmland edges, and scrub forests in South Asia",
        "description": "Responsible for the majority of severe snakebite envenomations in South Asia. Causes severe hemotoxicity, acute renal failure, and tissue damage.",
        "first_aid": "🚨 CRITICAL EMERGENCY: Keep bitten limb immobilized BELOW heart level. Do NOT use tight tourniquets or ice. Rush to hospital emergency room for antivenom."
    },
    "saw_scaled_viper": {
        "common_name": "Saw-scaled Viper",
        "scientific_name": "Echis carinatus",
        "family": "Viperidae (True Vipers)",
        "danger_level": "HIGH",
        "is_venomous": True,
        "key_traits": "Small, stout body (30–60 cm); prominent white 'bird-foot' or cross marking on top of head; heavily keeled serrated flank scales rubbed together to produce a sizzling warning sound; undulating movement.",
        "habitat": "Dry, sandy, and rocky soils, scrubland, and semi-arid terrain across India & Middle East",
        "description": "Highly irritable and quick to strike when stepped on. Potent hemotoxic venom causing continuous bleeding.",
        "first_aid": "🚨 MEDICAL EMERGENCY: Immobilize limb and rush to hospital. Requires urgent antivenom and coagulation monitoring."
    },
    "banded_krait": {
        "common_name": "Banded Krait",
        "scientific_name": "Bungarus fasciatus",
        "family": "Elapidae (Cobras & Kraits)",
        "danger_level": "EXTREME",
        "is_venomous": True,
        "key_traits": "Unmistakable broad, alternating bright yellow and jet-black bands of equal width; prominent triangular body cross-section with sharp dorsal ridge; blunt rounded tail tip.",
        "habitat": "Agricultural fields, lowlands, and water margins in Northeast India and Southeast Asia",
        "description": "Shy and mostly active by night, but possesses lethal neurotoxic venom. Feeds on other snakes and small vertebrates.",
        "first_aid": "🚨 CRITICAL EMERGENCY: Apply pressure bandage and rush immediately to emergency medical care for antivenom."
    },
    "common_wolf_snake": {
        "common_name": "Common Wolf Snake (Krait Mimic)",
        "scientific_name": "Lycodon aulicus",
        "family": "Colubridae (Non-Venomous / Harmless)",
        "danger_level": "LOW",
        "is_venomous": False,
        "key_traits": "Brown/grey body with white/pale yellow crossbars that are broadest on the sides and narrow or break on the spine; dorsal scales are smooth without enlarged vertebral scales; neck is distinct from head.",
        "habitat": "Human homes, stone crevices, wall cracks, and gardens across South Asia",
        "description": "Completely harmless non-venomous snake that Batesian-mimics the Common Krait. Often found climbing house walls chasing geckos.",
        "first_aid": "✅ HARMLESS / NON-VENOMOUS: Wash bite with antiseptic soap and water. Clean superficial scratches."
    },
    "rat_snake": {
        "common_name": "Indian Rat Snake (Dhaman)",
        "scientific_name": "Ptyas mucosa",
        "family": "Colubridae (Harmless)",
        "danger_level": "LOW",
        "is_venomous": False,
        "key_traits": "Large, slender, active snake (up to 2.5 meters); large eyes with round pupils; black vertical stripes between upper lip scales; dark mesh/crossband pattern near rear body; fast moving.",
        "habitat": "Farmlands, forests, roofs, and suburban areas throughout South Asia",
        "description": "Beneficial non-venomous snake that keeps rodent populations under control. Often mistaken for a cobra when fleeing.",
        "first_aid": "✅ NON-VENOMOUS: Disinfect surface bite punctures with soap and water."
    },
    "green_mamba": {
        "common_name": "Eastern Green Mamba",
        "scientific_name": "Dendroaspis angusticeps",
        "danger_level": "HIGH",
        "is_venomous": True,
        "habitat": "Coastal forests and woodlands of East/Southern Africa",
        "description": "Arboreal snake with vivid emerald-green scales. Highly agile and shy, but possesses potent neurotoxins.",
        "first_aid": "🚨 URGENT: Apply pressure bandage and transport immediately to a hospital with antivenom."
    },
    "copperhead": {
        "common_name": "Eastern Copperhead",
        "scientific_name": "Agkistrodon contortrix",
        "danger_level": "MODERATE",
        "is_venomous": True,
        "habitat": "Deciduous forests and rocky outcrops in North America",
        "description": "Distinctive hourglass-shaped bands along its copper-colored body. Bites are painful with hemotoxic venom, rarely fatal with care.",
        "first_aid": "⚠️ MEDICAL ATTENTION REQUIRED: Remove rings/watches before swelling occurs. Clean wound and get to an emergency medical center."
    },
    "cottonmouth": {
        "common_name": "Cottonmouth / Water Moccasin",
        "scientific_name": "Agkistrodon piscivorus",
        "danger_level": "HIGH",
        "is_venomous": True,
        "habitat": "Swamps, marshes, rivers, and lakes in Southeastern USA",
        "description": "Semi-aquatic viper that flashes the white interior lining of its mouth in a defensive posture.",
        "first_aid": "🚨 MEDICAL EMERGENCY: Keep patient still, limb elevated slightly or neutral, do not apply ice. Seek emergency room antivenom treatment."
    },
    "rattlesnake": {
        "common_name": "Timber / Diamondback Rattlesnake",
        "scientific_name": "Crotalus species",
        "danger_level": "HIGH",
        "is_venomous": True,
        "habitat": "Deserts, grasslands, and forests across North and South America",
        "description": "Famous for the keratin rattle at the tip of its tail that buzzes when agitated. Pit viper with heat-sensing organs.",
        "first_aid": "🚨 MEDICAL EMERGENCY: Do NOT use snakebite suction kits. Keep limb level, avoid physical exertion, and go directly to emergency department."
    },
    "ball_python": {
        "common_name": "Ball Python / Royal Python",
        "scientific_name": "Python regius",
        "danger_level": "LOW",
        "is_venomous": False,
        "habitat": "Grasslands and open forests of Central and Western Africa",
        "description": "Gentle, non-venomous constrictor known for curling into a tight defensive ball. Popular pet reptile.",
        "first_aid": "✅ NON-VENOMOUS: Wash bite area thoroughly with warm water and soap. Apply antiseptic to prevent bacterial infection."
    },
    "burmese_python": {
        "common_name": "Burmese Python",
        "scientific_name": "Python bivittatus",
        "danger_level": "MODERATE",
        "is_venomous": False,
        "habitat": "Tropical rainforests and marshes in Southeast Asia",
        "description": "One of the largest snakes in the world. Powerful constrictor with dark brown blotches resembling giraffe patterns.",
        "first_aid": "⚠️ NON-VENOMOUS CONSTRICTOR: Clean bite with soap and water. If an exceptionally large specimen constricts, seek assistance to uncoil from the tail end."
    },
    "corn_snake": {
        "common_name": "Corn Snake / Red Rat Snake",
        "scientific_name": "Pantherophis guttatus",
        "danger_level": "LOW",
        "is_venomous": False,
        "habitat": "Fields, pinelands, and barns across Southeastern USA",
        "description": "Docile non-venomous colubrid with orange/red saddle patterns. Beneficial rodent controller.",
        "first_aid": "✅ HARMLESS: Wash with antiseptic soap and water. Clean surface scratches."
    },
    "garter_snake": {
        "common_name": "Common Garter Snake",
        "scientific_name": "Thamnophis sirtalis",
        "danger_level": "LOW",
        "is_venomous": False,
        "habitat": "Wetlands, woodlands, and gardens throughout North America",
        "description": "Small, slender snake with distinctive yellowish longitudinal stripes along a dark body. Completely harmless to humans.",
        "first_aid": "✅ HARMLESS: Mild soap and water wash. May release a musky scent when handled."
    },
    "rat_snake": {
        "common_name": "Indian Rat Snake (Dhaman)",
        "scientific_name": "Ptyas mucosa",
        "danger_level": "LOW",
        "is_venomous": False,
        "habitat": "Forests, open fields, agricultural lands, and urban peripheries in South/Southeast Asia",
        "description": "Large, fast-moving non-venomous snake often confused with cobras. Beneficial for controlling agricultural rodent pests.",
        "first_aid": "✅ NON-VENOMOUS: Disinfect bite area. Seek medical check if tetanus shot is outdated."
    },
    "green_tree_python": {
        "common_name": "Green Tree Python",
        "scientific_name": "Morelia viridis",
        "danger_level": "LOW",
        "is_venomous": False,
        "habitat": "Rainforests of New Guinea, eastern Indonesia, and Cape York, Australia",
        "description": "Bright lime green arboreal constrictor that rests draped horizontally in loops over tree branches.",
        "first_aid": "✅ NON-VENOMOUS: Clean the puncture wound with antiseptic soap and water."
    }
}


def normalize_key(name: str) -> str:
    """Normalize class or common name to match database keys."""
    cleaned = name.lower().replace(" ", "_").replace("-", "_").strip()
    # Check direct match
    if cleaned in SNAKE_SPECIES_DB:
        return cleaned
    
    # Fuzzy match by substrings
    for key, info in SNAKE_SPECIES_DB.items():
        if key in cleaned or cleaned in key:
            return key
        if cleaned in info["common_name"].lower().replace(" ", "_"):
            return key
        if cleaned in info["scientific_name"].lower().replace(" ", "_"):
            return key
            
    return cleaned


def get_species_info(species_name: str) -> dict:
    """Retrieve detailed species info dictionary for a given prediction."""
    key = normalize_key(species_name)
    if key in SNAKE_SPECIES_DB:
        return SNAKE_SPECIES_DB[key]
    
    # Generic fallback
    is_likely_venomous = any(w in species_name.lower() for w in ["cobra", "viper", "mamba", "krait", "taipan", "rattlesnake", "cottonmouth", "copperhead"])
    return {
        "common_name": species_name.replace("_", " ").title(),
        "scientific_name": "Species classification result",
        "danger_level": "HIGH" if is_likely_venomous else "MODERATE / UNVERIFIED",
        "is_venomous": is_likely_venomous,
        "habitat": "Habitat information available in extended catalog.",
        "description": f"Classified as {species_name.replace('_', ' ').title()}. Always exercise caution when dealing with unidentified reptiles.",
        "first_aid": "🚨 CAUTION: Treat all wild snake encounters with extreme care. If bitten, stay calm, immobilize the limb, and consult a medical professional immediately."
    }
