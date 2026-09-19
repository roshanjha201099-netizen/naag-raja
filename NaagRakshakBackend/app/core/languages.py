from typing import Dict, Any

SUPPORTED_LANGUAGES: Dict[str, Dict[str, Any]] = {
    "hi-IN": {"name": "Hindi", "native": "हिन्दी", "sarvam_code": "hi-IN", "default_speaker": "ritu"},
    "bn-IN": {"name": "Bengali", "native": "বাংলা", "sarvam_code": "bn-IN", "default_speaker": "ritu"},
    "te-IN": {"name": "Telugu", "native": "తెలుగు", "sarvam_code": "te-IN", "default_speaker": "ritu"},
    "ta-IN": {"name": "Tamil", "native": "தமிழ்", "sarvam_code": "ta-IN", "default_speaker": "ritu"},
    "mr-IN": {"name": "Marathi", "native": "मराठी", "sarvam_code": "mr-IN", "default_speaker": "ritu"},
    "gu-IN": {"name": "Gujarati", "native": "ગુજરાતી", "sarvam_code": "gu-IN", "default_speaker": "ritu"},
    "kn-IN": {"name": "Kannada", "native": "ಕನ್ನಡ", "sarvam_code": "kn-IN", "default_speaker": "ritu"},
    "ml-IN": {"name": "Malayalam", "native": "മലയാളം", "sarvam_code": "ml-IN", "default_speaker": "ritu"},
    "pa-IN": {"name": "Punjabi", "native": "ਪੰਜਾਬੀ", "sarvam_code": "pa-IN", "default_speaker": "ritu"},
    "od-IN": {"name": "Odia", "native": "ଓଡ଼ିଆ", "sarvam_code": "od-IN", "default_speaker": "ritu"},
    "en-IN": {"name": "Indian English", "native": "English", "sarvam_code": "en-IN", "default_speaker": "ritu"}
}

def resolve_language(code: str = None) -> Dict[str, Any]:
    if not code:
        return SUPPORTED_LANGUAGES["hi-IN"]
    code_clean = code.strip()
    if code_clean in SUPPORTED_LANGUAGES:
        return SUPPORTED_LANGUAGES[code_clean]
    # Match short prefix (e.g. 'ta' -> 'ta-IN')
    prefix = code_clean.split("-")[0].lower()
    for key, val in SUPPORTED_LANGUAGES.items():
        if key.startswith(prefix):
            return val
    return SUPPORTED_LANGUAGES["hi-IN"]
