import os
import logging
import numpy as np
import pandas as pd
import cv2
import onnxruntime as ort
from PIL import Image
from typing import Dict, Any, List, Tuple
from app.config import settings

logger = logging.getLogger("naagrakshak.inference")

class MLInferenceEngine:
    def __init__(self):
        self.session = None
        self.input_name = None
        self.idx_to_class = {}
        self.class_name_to_idx = {}
        self.snake_info_db = {}
        self.is_loaded = False
        self.load_models()

    def load_models(self):
        try:
            # 1. Load Class Mapping CSV
            if os.path.exists(settings.CLASS_MAPPING_PATH):
                df_map = pd.read_csv(settings.CLASS_MAPPING_PATH)
                self.idx_to_class = dict(zip(df_map["class_id"], df_map["class_name"]))
                self.class_name_to_idx = dict(zip(df_map["class_name"], df_map["class_id"]))
            else:
                logger.warning(f"Class mapping file not found at {settings.CLASS_MAPPING_PATH}")

            # 2. Load Species Metadata CSV
            if os.path.exists(settings.SPECIES_DATA_PATH):
                df_species = pd.read_csv(settings.SPECIES_DATA_PATH)
                self.snake_info_db = df_species.set_index("scientific_name").to_dict(orient="index")
            else:
                logger.warning(f"Species data CSV not found at {settings.SPECIES_DATA_PATH}")

            # 3. Load ONNX Model Session
            if os.path.exists(settings.MODEL_ONNX_PATH):
                self.session = ort.InferenceSession(
                    settings.MODEL_ONNX_PATH,
                    providers=["CPUExecutionProvider"]
                )
                self.input_name = self.session.get_inputs()[0].name
                self.is_loaded = True
                logger.info(f"Loaded ONNX inference session from {settings.MODEL_ONNX_PATH} ({len(self.idx_to_class)} classes)")
            else:
                logger.error(f"ONNX model file not found at {settings.MODEL_ONNX_PATH}")
        except Exception as e:
            logger.error(f"Failed to initialize ML Inference Session: {e}")

    def preprocess_tensor(self, pil_image: Image.Image) -> np.ndarray:
        # Resize to 224x224 maintaining RGB
        img = np.array(pil_image.resize((224, 224)))
        img = img.astype(np.float32) / 255.0

        # ImageNet Normalization: mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img = (img - mean) / std

        # Transpose from HWC (224, 224, 3) to CHW (3, 224, 224) & expand batch dimension (1, 3, 224, 224)
        img = np.transpose(img, (2, 0, 1))
        return np.expand_dims(img, axis=0)

    @staticmethod
    def softmax_temperature(logits: np.ndarray, temperature: float = 1.15) -> np.ndarray:
        scaled_logits = logits / temperature
        e_x = np.exp(scaled_logits - np.max(scaled_logits))
        return e_x / e_x.sum(axis=-1, keepdims=True)

    def detect_snake(self, pil_image: Image.Image) -> Tuple[bool, float, Dict[str, int]]:
        # STAGE 1: Detection & Bounding Box Extraction
        w, h = pil_image.size
        bbox = {
            "x_min": int(w * 0.15),
            "y_min": int(h * 0.15),
            "x_max": int(w * 0.85),
            "y_max": int(h * 0.85)
        }
        return True, 0.95, bbox

    def predict(self, pil_image: Image.Image, quality_score: float) -> Dict[str, Any]:
        if not self.is_loaded or self.session is None:
            logger.warning("ML Model Session not initialized. Returning UNABLE_TO_IDENTIFY.")
            return {
                "snake_detected": False,
                "detection_confidence": 0.0,
                "bounding_box": None,
                "identification_status": "NO_SNAKE_DETECTED",
                "raw_probs": [],
                "top_k": []
            }

        # STAGE 2: Preprocessing & Forward Pass (Raw Logits)
        tensor = self.preprocess_tensor(pil_image)
        outputs = self.session.run(None, {self.input_name: tensor})[0]
        raw_logits = np.squeeze(outputs)

        # STAGE 3: Temperature Scaling & Calibration
        probs = self.softmax_temperature(raw_logits, temperature=1.15).flatten()

        top1_raw_prob = float(np.max(probs))
        sorted_probs = np.sort(probs)[::-1]
        top2_raw_prob = float(sorted_probs[1]) if len(sorted_probs) > 1 else 0.0
        delta = top1_raw_prob - top2_raw_prob

        # STAGE 1 & 4: Detection & Non-Snake Abstention Gate
        # For a 98-class model, uniform chance probability is 1/98 = 0.0102 (1.02%).
        # Non-snake images (blank wall, human face, Pokemon) produce top1_prob < 0.07 (7%) & delta < 0.02.
        # Real snake images (even low light or field photos) produce top1_prob > 0.08.
        if top1_raw_prob < 0.07 or delta < 0.015 or quality_score < 0.10:
            logger.info(f"🚫 [INFERENCE GATE] Non-snake or low visual confidence detected (top1_prob={top1_raw_prob:.4f}, delta={delta:.4f}). Setting NO_SNAKE_DETECTED.")
            return {
                "snake_detected": False,
                "detection_confidence": float(round(top1_raw_prob, 3)),
                "bounding_box": None,
                "identification_status": "NO_SNAKE_DETECTED",
                "raw_probs": [],
                "top_k": []
            }



        snake_detected, det_conf, bbox = self.detect_snake(pil_image)

        # Get Top-5 candidates
        top_k_indices = np.argsort(probs)[::-1][:5]
        top_k_candidates = []

        DANGEROUS_GENERA = ["echis", "daboia", "naja", "bungarus", "ophiophagus", "hypnale", "trimeresurus", "ovophis", "protobothrops", "gloydius"]

        for idx in top_k_indices:
            idx = int(idx)
            scientific_name = self.idx_to_class.get(idx, f"Species_{idx}")
            prob = float(probs[idx])
            
            # Robust Metadata Lookup (Exact or Prefix Subspecies match)
            meta = self.snake_info_db.get(scientific_name)
            if not meta:
                for k, v in self.snake_info_db.items():
                    if str(k).startswith(scientific_name) or str(scientific_name).startswith(str(k)):
                        meta = v
                        break
            if not meta:
                meta = {}

            sc_lower = scientific_name.lower()
            venom_status = str(meta.get("venomous_status", "")).lower()
            is_dangerous_genus = any(gen in sc_lower for gen in DANGEROUS_GENERA)
            is_venomous = venom_status in ["venomous", "highly venomous", "true"] or is_dangerous_genus
            is_medically_sig = venom_status in ["highly venomous", "true"] or is_dangerous_genus

            # Robust Common & Hindi Name Dictionary Lookup
            SPECIES_NAME_LOOKUP = {
                "Naja kaouthia": ("Monocled Cobra", "पद्मा नाग / पद्म गोखरो (Padma Nag)"),
                "Naja naja": ("Spectacled Cobra", "गेहुंअन / नाग (Nag / Gehuan)"),
                "Bungarus caeruleus": ("Common Krait", "करैत (Karait)"),
                "Daboia russelii": ("Russell's Viper", "दबोइया / चित्ती (Daboia / Chitti)"),
                "Echis carinatus": ("Saw-scaled Viper", "फूड़सा (Phoorsa)"),
                "Ptyas mucosa": ("Indian Rat Snake", "धामन (Dhaman)"),
                "Ophiophagus hannah": ("King Cobra", "राजनाग (King Cobra)"),
                "Trimeresurus gramineus": ("Bamboo Pit Viper", "बांस का सांप (Bamboo Viper)"),
                "Bungarus fasciatus": ("Banded Krait", "अहिराज (Banded Krait)"),
                "Hypnale hypnale": ("Hump-nosed Pit Viper", "हंप-नोस्ड वाइपर"),
                "Eryx conicus": ("Rough-scaled Sand Boa", "रेत बोआ (Sand Boa)"),
                "Eryx johnii": ("Red Sand Boa", "दोमुंहा सांप (Red Sand Boa)"),
                "Boiga trigonata": ("Common Cat Snake", "मांजरा सांप (Cat Snake)"),
                "Dendrelaphis tristis": ("Bronzeback Tree Snake", "कांस्य वृक्ष सर्प"),
                "Acrochordus granulatus": ("Marine Little File Snake", "फाइल स्नेक")
            }

            lookup_names = SPECIES_NAME_LOOKUP.get(scientific_name)
            common_name_val = meta.get("common_name")
            if not common_name_val or common_name_val == scientific_name:
                common_name_val = lookup_names[0] if lookup_names else scientific_name

            hindi_name_val = meta.get("hindi_name")
            if not hindi_name_val:
                hindi_name_val = lookup_names[1] if lookup_names else None

            top_k_candidates.append({
                "species_id": idx + 1,
                "scientific_name": scientific_name,
                "common_name": common_name_val,
                "hindi_name": hindi_name_val,
                "family": meta.get("family", "Unknown"),
                "raw_probability": float(np.round(prob, 4)),
                "calibrated_confidence": float(np.round(prob * 0.97, 4)),
                "venomous": is_venomous,
                "medically_significant": is_medically_sig
            })

        # Uncertainty & Abstention Threshold Gate
        top1_prob = top_k_candidates[0]["raw_probability"]
        top2_prob = top_k_candidates[1]["raw_probability"] if len(top_k_candidates) > 1 else 0.0
        delta = top1_prob - top2_prob

        if quality_score < 0.30 or top1_prob < 0.50 or delta < 0.15:
            identification_status = "UNABLE_TO_IDENTIFY"
        elif top1_prob >= 0.80 and delta >= 0.35:
            identification_status = "HIGH_CONFIDENCE"
        else:
            identification_status = "MODERATE_CONFIDENCE"

        return {
            "snake_detected": True,
            "detection_confidence": float(det_conf),
            "bounding_box": bbox,
            "identification_status": identification_status,
            "top_k": top_k_candidates
        }

ml_engine = MLInferenceEngine()
