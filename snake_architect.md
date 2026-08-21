# NaagRakshak — End-to-End Master System Architecture Specification

Comprehensive technical specification document detailing the entire **NaagRakshak** system architecture across the **Presentation Layer (React Frontend)**, **Machine Learning Training Pipeline (PyTorch / ONNX)**, and **Production API Gateway Engine (FastAPI & PostgreSQL)**.

---

## 📑 Table of Contents
1. [Master System Architecture Diagram](#1-master-system-architecture-diagram)
2. [Core Architectural Principles](#2-core-architectural-principles)
3. [Presentation Layer (React + Vite Frontend)](#3-presentation-layer-react--vite-frontend)
4. [Machine Learning Training Pipeline & Datasets](#4-machine-learning-training-pipeline--datasets)
5. [Production Backend Engine (FastAPI & Services)](#5-production-backend-engine-fastapi--services)
6. [Database Schema & Data Models](#6-database-schema--data-models)
7. [Suggested Architectural Improvements & Next Steps](#7-suggested-architectural-improvements--next-steps)

---

## 1. Master System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     PRESENTATION LAYER (REACT 18 + VITE + TAILWIND)                              │
│                                                                                                                  │
│   ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────────┐   │
│   │  Landing Page (/)   │    │ Scanner (/identify) │    │  Dashboard (/result)│    │ Catalog (/explore)      │   │
│   │ 4 Intent Cards      │    │ WebRTC / Camera     │    │ Safety Banner       │    │ 98 Taxa Search          │   │
│   │ 3-Step Visual Guide │    │ Drag-and-Drop       │    │ Confidence Meter    │    │ Venom & State Filters   │   │
│   └─────────────────────┘    └─────────────────────┘    └─────────────────────┘    └─────────────────────────┘   │
│                                         │                                                                        │
│                      Global Contexts:   ├─ LocationContext (Geocoding & GPS)                                    │
│                                         └─ LanguageContext (10 Regional Indian Languages)                        │
└─────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────┘
                                          │  POST /api/v1/predict (Image, Intent, State, Language Code)
                                          ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    PRODUCTION BACKEND API ENGINE (FASTAPI)                                       │
│                                                                                                                  │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ 1. Ingestion Defense & Validation (Magic Byte Header Check, 15MB Size Cap, Decompression Bomb Guard)     │   │
│   └────────────────────────────────────┬─────────────────────────────────────────────────────────────────────┘   │
│                                        ▼                                                                         │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ 2. OpenCV Image Quality Analyzer (Laplacian Variance Blur Score Var(∇²I), Exposure, Contrast Metric Q)   │   │
│   └────────────────────────────────────┬─────────────────────────────────────────────────────────────────────┘   │
│                                        ▼                                                                         │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ 3. ML Inference Engine (PyTorch / ONNX Runtime forward pass over 98 classes, Temperature Scaling T=1.15) │   │
│   │    Uncertainty & Abstention Gate (If P₁ < 0.50 or ΔP < 0.15 or Q < 0.30 ➔ UNABLE_TO_IDENTIFY)               │   │
│   └────────────────────────────────────┬─────────────────────────────────────────────────────────────────────┘   │
│                                        ▼                                                                         │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ 4. Location-Aware Geo-Ranking (GBIF / ZSI State Occurrence Priors, Safety Override Rule for >0.85 P₁)     │   │
│   └────────────────────────────────────┬─────────────────────────────────────────────────────────────────────┘   │
│                                        ▼                                                                         │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ 5. Deterministic Safety Engine (Zero LLM Truth Table: Medically Significant ➔ CRITICAL, Venomous ➔ HIGH) │   │
│   └────────────────────────────────────┬─────────────────────────────────────────────────────────────────────┘   │
│                                        ▼                                                                         │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ 6. OpenAI LLM Regional Script Synthesis & Sarvam AI Text-to-Speech (bulbul:v2 Base64 Audio Generation)    │   │
│   └────────────────────────────────────┬─────────────────────────────────────────────────────────────────────┘   │
│                                        ▼                                                                         │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ 7. Async PostgreSQL Logging & OpenAPI JSON Response Composition                                           │   │
│   └──────────────────────────────────────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Architectural Principles

1. **Decoupling Probabilistic AI from Deterministic Safety**:
   - Probabilistic AI models (Neural Networks, LLMs) are inherently prone to uncertainty and hallucinations.
   - Therefore, **AI NEVER assigns safety levels (`CRITICAL`, `HIGH`, `CAUTION`, `LOW`) or medical antivenom recommendations**. Safety levels are determined 100% by a deterministic rulebook matching verified database attributes.
2. **Abstention Gate over False Certainty**:
   - If image quality is low ($Q < 0.30$) or visual confidence is low ($P_1 < 50\%$ or margin $\Delta < 0.15$), the system triggers **Abstention Mode** (`UNABLE_TO_IDENTIFY`) and defaults to `CAUTION` safety advice (*Assume potentially venomous until verified*).
3. **Zero-Manual Accessibility**:
   - High-contrast visual design, regional language voice audio alerts (Sarvam AI), and micro-location auto-detection ensure that users in urgent, low-literacy, or panic conditions do not need to read complex documentation.

---

## 3. Presentation Layer (React + Vite Frontend)

* **Location**: `NaagRakshakFrontend/`
* **Tech Stack**: React 18, Vite 6, Tailwind CSS, Lucide React Icons, Axios.

### Pages & Routes
- `/` (**Landing Page**): 4 Intent cards, 3-step visual scanner guide, Indian Big Four species strip.
- `/identify` (**Scanner Page**): Live WebRTC camera viewfinder (`getUserMedia`), drag-and-drop file upload, 1-click test preset photos (Cobra, Krait, Wolf Snake, Rat Snake), intent selector, micro-location indicator.
- `/result` (**Prediction Dashboard**): High-visibility safety banner (Red/Orange/Yellow/Green), calibrated confidence gauge, Top-K candidates list, **Sarvam AI Voice Alert Player** (play/pause base64 WAV stream), nearby ASV hospital finder.
- `/explore` (**Species Catalog**): Searchable 98-taxa catalog with venomous/non-venomous and state filters.
- `/species/:id` (**Species Profile**): Detailed taxonomy, 7 regional language names (Hindi, Bengali, Tamil, Marathi, Malayalam, Kannada, Telugu), lookalike comparison matrix, distribution map.
- `/emergency` (**Bite Emergency**): WHO/National "Do No Harm" first-aid guidelines, emergency hotline speed dials (112, 1800-112-211, 1926), state ASV hospital locator.

### Global React Contexts
- `LocationContext.jsx`: Geolocation API auto-detect + Nominatim reverse geocoding to extract `Village/Town, District, State`.
- `LanguageContext.jsx`: Manages user regional language selection (`hi-IN`, `bn-IN`, `ta-IN`, `mr-IN`, `te-IN`, `kn-IN`, `ml-IN`, `gu-IN`, `pa-IN`, `en-IN`).

---

## 4. Machine Learning Training Pipeline & Datasets

* **Location**: `Naag_ml/`
* **Framework**: PyTorch 2.1, `timm` (PyTorch Image Models), OpenCV, ONNX Runtime.

### Dataset Structure
- **Scope**: 98 Indian snake species across Elapidae, Viperidae, Colubridae, Typhlopidae, Boidae, Homalopsidae.
- **Image Downloader** (`download_phase1_subset.py`): Multi-threaded S3 downloader pulling iNaturalist research-grade Indian snake images.
- **Dataset Preprocessing & Augmentation** (`preprocessing/dataset.py`):
  - RandomResizedCrop (224x224)
  - RandomHorizontalFlip ($p=0.5$)
  - ColorJitter (Brightness=0.2, Contrast=0.2, Saturation=0.2)
  - ImageNet Normalization ($\mu = [0.485, 0.456, 0.406]$, $\sigma = [0.229, 0.224, 0.225]$)

### Model Training Loop (`training/train.py`)
- **Backbone**: `timm` ConvNeXt-Tiny / EfficientNet-B0 fine-tuned on 98 Indian snake taxa.
- **Loss Function**: CrossEntropyLoss with Label Smoothing ($0.1$) to prevent overconfident logits.
- **Optimizer**: AdamW ($lr=1e-3, wd=1e-2$).
- **Scheduler**: CosineAnnealingLR.
- **Export Formats**: PyTorch checkpoint (`snake_model_phase1_best.pth`) & ONNX model (`models/snake_model.onnx`).

---

## 5. Production Backend Engine (FastAPI & Services)

* **Location**: `NaagRakshakBackend/`
* **Tech Stack**: FastAPI, Uvicorn, Async SQLAlchemy 2.0, PostgreSQL 16 (`asyncpg`), OpenCV, ONNX Runtime, OpenAI API, Sarvam AI API.

### Service Modules
1. **Validation Service** (`app/services/validation.py`):
   - Magic Byte verification (`JPEG`, `PNG`, `WEBP`).
   - 15MB Payload size cap enforcement.
   - PIL Decompression Bomb Guard (`MAX_IMAGE_PIXELS = 89,478,485`).
   - $\ge 224 \times 224$ minimum resolution check.
   - Dual Input Support (Raw binary stream or Base64 string payload).
2. **Quality Analyzer** (`app/services/quality.py`):
   - OpenCV Laplacian Variance blur score $V_{\text{Laplacian}} = \text{Var}(\nabla^2(I_{\text{gray}}))$.
   - Exposure and contrast distribution metrics.
   - Composite quality score $Q \in [0.0, 1.0]$.
3. **ML Inference & Calibration Engine** (`app/services/inference.py`):
   - Bounding box snake spatial detection check.
   - ONNX Runtime execution provider forward pass over 98 classes.
   - Temperature scaling calibration ($T=1.15$).
   - Uncertainty & Abstention Gate (`HIGH_CONFIDENCE`, `MODERATE_CONFIDENCE`, `UNABLE_TO_IDENTIFY`).
4. **Geo-Ranking Service** (`app/services/geo_ranking.py`):
   - Damped Bayesian prior re-weighting using state occurrence records.
   - Safety override rule: High visual certainty ($> 0.85$) of medically significant species cannot be suppressed by location priors.
5. **Deterministic Safety Engine** (`app/services/safety_engine.py`):
   - Priority cascading truth table for safety assignment.
6. **OpenAI Regional Explainer** (`app/services/llm_explainer.py`):
   - GPT-4o-mini prompt engine generating 2-sentence regional alert scripts using local common names (e.g. *Spectacled Cobra / नाग गेहुंअन*).
   - Intent-aware protocol customization (`SNAKE_BITE_EMERGENCY` vs `SNAKE_ENCOUNTER`).
7. **Sarvam AI Text-to-Speech Service** (`app/services/sarvam_tts.py`):
   - Calls `https://api.sarvam.ai/text-to-speech` (`bulbul:v2` model, speaker `anushka`).
   - Generates Base64 WAV voice audio stream in the selected regional language.

---

## 6. Database Schema & Data Models

* **Database Engine**: PostgreSQL 16 (on `localhost:5432` with password `7044`, DB: `naagrakshak`).

### Key Entities & Relations
```sql
-- 1. Species Taxonomy Master Table
CREATE TABLE species (
    id SERIAL PRIMARY KEY,
    scientific_name VARCHAR(128) UNIQUE NOT NULL,
    common_name VARCHAR(128) NOT NULL,
    hindi_name VARCHAR(128),
    family VARCHAR(64) NOT NULL,
    genus VARCHAR(64),
    venomous BOOLEAN DEFAULT FALSE NOT NULL,
    medically_significant BOOLEAN DEFAULT FALSE NOT NULL,
    safety_level VARCHAR(32) DEFAULT 'LOW' NOT NULL,
    habitat TEXT,
    distribution TEXT,
    average_length_cm FLOAT,
    maximum_length_cm FLOAT,
    diet TEXT,
    activity_pattern VARCHAR(64),
    behaviour TEXT,
    description TEXT,
    safety_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Regional Distribution Records
CREATE TABLE species_distribution (
    id SERIAL PRIMARY KEY,
    species_id INTEGER REFERENCES species(id) ON DELETE CASCADE,
    country VARCHAR(64) DEFAULT 'India' NOT NULL,
    state_province VARCHAR(64) NOT NULL,
    occurrence_status VARCHAR(32) DEFAULT 'PRESENT_COMMON' NOT NULL,
    gbif_taxon_key INTEGER
);

-- 3. ASV Medical Facilities Directory
CREATE TABLE medical_facilities (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(256) NOT NULL,
    type VARCHAR(64) DEFAULT 'Govt Medical College' NOT NULL,
    state VARCHAR(64) NOT NULL,
    district VARCHAR(64) NOT NULL,
    address TEXT NOT NULL,
    phone VARCHAR(64) NOT NULL,
    asv_available BOOLEAN DEFAULT TRUE NOT NULL,
    icu_facility BOOLEAN DEFAULT TRUE NOT NULL,
    ventilator_count INTEGER DEFAULT 10 NOT NULL,
    latitude FLOAT,
    longitude FLOAT
);

-- 4. Wildlife Rescue Dispatch Helplines
CREATE TABLE rescue_facilities (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(256) NOT NULL,
    organization VARCHAR(128) DEFAULT 'Forest Department' NOT NULL,
    state VARCHAR(64) NOT NULL,
    district VARCHAR(64),
    phone VARCHAR(64) NOT NULL,
    response_hours VARCHAR(64) DEFAULT '24/7 Emergency Dispatch' NOT NULL
);

-- 5. Prediction Audit Logs
CREATE TABLE prediction_logs (
    request_id VARCHAR(64) PRIMARY KEY,
    image_quality_score FLOAT NOT NULL,
    snake_detected BOOLEAN NOT NULL,
    detection_confidence FLOAT NOT NULL,
    top_species_id INTEGER,
    calibrated_confidence VARCHAR(64) NOT NULL,
    safety_level VARCHAR(32) NOT NULL,
    processing_time_ms FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 7. Suggested Architectural Improvements & Next Steps

Here are high-impact architectural enhancements you can implement to further elevate performance and capabilities:

### 💡 1. Fine-Tune YOLOv8 Bounding Box Detector
- **Current State**: Stage 1 uses spatial image heuristic boundaries.
- **Improvement**: Train a dedicated YOLOv8-Nano / YOLOv8-Small snake detection model (`yolov8n-snake.onnx`) to crop background clutter (grass, rocks, hands) before passing the cropped snake specimen box to the 98-class classifier. This will increase classification accuracy on complex field photos by $+6-10\%$.

### 💡 2. Vector Similarity Search for Lookalike Verification (Pgvector / FAISS)
- **Improvement**: Store feature embeddings of verified museum & field specimens using a fine-tuned ConvNeXt backbone into PostgreSQL using `pgvector`.
- When an uncertain photo is uploaded, run a Cosine Similarity Search against reference embeddings to return visually similar reference images (e.g. *Common Krait* vs *Common Wolf Snake* scale pattern comparison).

### 3. PWA Offline Vision Model Execution (ONNX WebAssembly)
- **Improvement**: Load a quantized `snake_model_quantized.onnx` (12MB) into the browser via **ONNX Runtime WebAssembly (Wasm)**.
- If a user in a deep forest / rural area has zero internet connectivity, the React PWA can perform local offline species identification directly inside the browser!

### 💡 4. Geo-Spatial Hospital Distance Calculation (PostGIS Query)
- **Current State**: Hospitals are filtered by state/district name.
- **Improvement**: Enable `PostGIS` extension in PostgreSQL. Use Haversine / PostGIS spatial distance queries (`ST_DistanceSphere`) to sort ASV hospitals by exact distance (in kilometers) from the user's GPS coordinates (`latitude`, `longitude`).
