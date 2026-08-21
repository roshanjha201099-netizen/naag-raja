from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

class IntentEnum(str, Enum):
    SNAKE_ENCOUNTER = "SNAKE_ENCOUNTER"
    SNAKE_BITE_EMERGENCY = "SNAKE_BITE_EMERGENCY"
    STUDY_RESEARCH = "STUDY_RESEARCH"
    WILDLIFE_PHOTOGRAPHY = "WILDLIFE_PHOTOGRAPHY"

class SafetyLevelEnum(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    CAUTION = "CAUTION"
    LOW = "LOW"
    NONE = "NONE"

class IdentificationStatusEnum(str, Enum):
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
    MODERATE_CONFIDENCE = "MODERATE_CONFIDENCE"
    UNABLE_TO_IDENTIFY = "UNABLE_TO_IDENTIFY"
    NO_SNAKE_DETECTED = "NO_SNAKE_DETECTED"

class BoundingBoxSchema(BaseModel):
    x_min: int = 0
    y_min: int = 0
    x_max: int = 224
    y_max: int = 224

class SpeciesPredictionSchema(BaseModel):
    species_id: int
    scientific_name: str
    common_name: str
    family: str
    raw_probability: float
    calibrated_confidence: float
    regional_presence: str = "COMMON"

class SafetySchema(BaseModel):
    safety_level: SafetyLevelEnum
    venomous: bool
    medically_significant: bool
    antivenom_recommended: bool
    safety_message: str

class ProtocolSchema(BaseModel):
    immediate_action: str
    strict_prohibitions: List[str]
    medical_disclaimer: str = "Do not delay medical care while waiting for or relying on AI identification."

class ContextualGuidanceSchema(BaseModel):
    intent: IntentEnum
    protocol: ProtocolSchema
    nearby_facilities_endpoint: Optional[str] = None
    llm_explanation: Optional[str] = None
    audio_base64: Optional[str] = None
    language_code: Optional[str] = "hi-IN"

class ModelMetaSchema(BaseModel):
    detector_version: str = "yolov8m-snake-v1.0"
    classifier_version: str = "convnext_tiny-naagml-phase1-98c"
    image_quality_score: float
    processing_time_ms: float

class PredictResponse(BaseModel):
    request_id: str
    snake_detected: bool
    detection_confidence: float
    bounding_box: Optional[BoundingBoxSchema] = None
    identification_status: IdentificationStatusEnum
    predictions: List[SpeciesPredictionSchema]
    safety: SafetySchema
    contextual_guidance: ContextualGuidanceSchema
    model_meta: ModelMetaSchema

class RegionalNameSchema(BaseModel):
    hindi: Optional[str] = None
    bengali: Optional[str] = None
    tamil: Optional[str] = None
    marathi: Optional[str] = None
    kannada: Optional[str] = None
    malayalam: Optional[str] = None
    telugu: Optional[str] = None

class SpeciesDetailResponse(BaseModel):
    id: int
    scientific_name: str
    common_name: str
    hindi_name: Optional[str] = None
    family: str
    genus: Optional[str] = None
    venomous: bool
    medically_significant: bool
    safety_level: str
    habitat: Optional[str] = None
    distribution: Optional[str] = None
    average_length_cm: Optional[float] = None
    maximum_length_cm: Optional[float] = None
    diet: Optional[str] = None
    activity_pattern: Optional[str] = None
    behaviour: Optional[str] = None
    description: Optional[str] = None
    safety_message: Optional[str] = None
    regional_names: Optional[Dict[str, str]] = None
    lookalikes: List[Dict[str, str]] = []

    class Config:
        from_attributes = True

class MedicalFacilitySchema(BaseModel):
    id: str
    name: str
    type: str
    state: str
    district: str
    address: str
    phone: str
    asv_available: bool
    icu_facility: bool
    ventilator_count: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        from_attributes = True

class RescueFacilitySchema(BaseModel):
    id: str
    name: str
    organization: str
    state: str
    district: Optional[str] = None
    phone: str
    response_hours: str

    class Config:
        from_attributes = True

class HealthResponse(BaseModel):
    status: str = "HEALTHY"
    database_connected: bool
    active_db_engine: str
    model_loaded: bool
    class_count: int
    uptime_seconds: float
