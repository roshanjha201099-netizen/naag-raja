import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base

class Species(Base):
    __tablename__ = "species"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scientific_name = Column(String(128), unique=True, nullable=False, index=True)
    common_name = Column(String(128), nullable=False, index=True)
    hindi_name = Column(String(128), nullable=True)
    family = Column(String(64), nullable=False, index=True)
    genus = Column(String(64), nullable=True)
    venomous = Column(Boolean, default=False, nullable=False, index=True)
    medically_significant = Column(Boolean, default=False, nullable=False, index=True)
    safety_level = Column(String(32), default="LOW", nullable=False)
    habitat = Column(Text, nullable=True)
    distribution = Column(Text, nullable=True)
    average_length_cm = Column(Float, nullable=True)
    maximum_length_cm = Column(Float, nullable=True)
    diet = Column(Text, nullable=True)
    activity_pattern = Column(String(64), nullable=True)
    behaviour = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    safety_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    distributions = relationship("SpeciesDistribution", back_populates="species", cascade="all, delete-orphan")
    sources = relationship("SpeciesSource", back_populates="species", cascade="all, delete-orphan")

class SpeciesDistribution(Base):
    __tablename__ = "species_distribution"

    id = Column(Integer, primary_key=True, autoincrement=True)
    species_id = Column(Integer, ForeignKey("species.id", ondelete="CASCADE"), nullable=False)
    country = Column(String(64), default="India", nullable=False, index=True)
    state_province = Column(String(64), nullable=False, index=True)
    occurrence_status = Column(String(32), default="PRESENT_COMMON", nullable=False) # ABUNDANT, COMMON, RARE, UNRECORDED
    gbif_taxon_key = Column(Integer, nullable=True)

    species = relationship("Species", back_populates="distributions")

class SpeciesSource(Base):
    __tablename__ = "species_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    species_id = Column(Integer, ForeignKey("species.id", ondelete="CASCADE"), nullable=False)
    citation = Column(Text, nullable=False)
    source_type = Column(String(64), default="Herpetological Reference", nullable=False)
    external_url = Column(String(512), nullable=True)

    species = relationship("Species", back_populates="sources")

class MedicalFacility(Base):
    __tablename__ = "medical_facilities"

    id = Column(String(64), primary_key=True)
    name = Column(String(256), nullable=False, index=True)
    type = Column(String(64), default="Govt Medical College", nullable=False)
    state = Column(String(64), nullable=False, index=True)
    district = Column(String(64), nullable=False, index=True)
    address = Column(Text, nullable=False)
    phone = Column(String(64), nullable=False)
    asv_available = Column(Boolean, default=True, nullable=False)
    icu_facility = Column(Boolean, default=True, nullable=False)
    ventilator_count = Column(Integer, default=10, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

class RescueFacility(Base):
    __tablename__ = "rescue_facilities"

    id = Column(String(64), primary_key=True)
    name = Column(String(256), nullable=False)
    organization = Column(String(128), default="Forest Department", nullable=False)
    state = Column(String(64), nullable=False, index=True)
    district = Column(String(64), nullable=True)
    phone = Column(String(64), nullable=False)
    response_hours = Column(String(64), default="24/7 Emergency Dispatch", nullable=False)

class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    request_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    image_quality_score = Column(Float, nullable=False)
    snake_detected = Column(Boolean, nullable=False)
    detection_confidence = Column(Float, nullable=False)
    top_species_id = Column(Integer, nullable=True)
    calibrated_confidence = Column(String(64), nullable=False)
    safety_level = Column(String(32), nullable=False)
    processing_time_ms = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class SnakeSighting(Base):
    __tablename__ = "snake_sightings"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    species_name = Column(String(256), nullable=True)
    scientific_name = Column(String(256), nullable=True)
    safety_level = Column(String(32), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    state = Column(String(64), nullable=True, index=True)
    district = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)
    image_reference = Column(String(512), nullable=True)
    verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
