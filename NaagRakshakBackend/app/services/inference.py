import os
import sys
import logging
from typing import Dict, Any, List, Optional
from PIL import Image
import numpy as np

logger = logging.getLogger("naagrakshak.inference")

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    import torch
    import torch.nn as nn
    from torchvision import models, transforms
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch or torchvision is not installed yet.")

from app.services.species_info import SNAKE_SPECIES_DB

IMAGE_SIZE = 224
NORM_MEAN = [0.485, 0.456, 0.406]
NORM_STD = [0.229, 0.224, 0.225]

# ImageNet-1k snake and reptile class indices
SNAKE_IMAGENET_INDICES = set(range(52, 69))   # 52 to 68 are snake species in ImageNet
REPTILE_IMAGENET_INDICES = set(range(33, 69))  # 33 to 68 are reptiles

def get_inference_transforms():
    if not TORCH_AVAILABLE:
        return None
    return transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=NORM_MEAN, std=NORM_STD)
    ])

def build_model(arch: str = "convnext_small", num_classes: int = 22, pretrained: bool = False):
    if not TORCH_AVAILABLE:
        return None
    arch = arch.lower()
    if "convnext" in arch:
        weights = models.ConvNeXt_Small_Weights.DEFAULT if pretrained else None
        model = models.convnext_small(weights=weights)
        in_features = model.classifier[2].in_features
        model.classifier[2] = nn.Sequential(
            nn.Dropout(p=0.4),
            nn.Linear(in_features, num_classes)
        )
    elif "mobilenet" in arch:
        weights = models.MobileNet_V3_Large_Weights.DEFAULT if pretrained else None
        model = models.mobilenet_v3_large(weights=weights)
        in_features = model.classifier[3].in_features
        model.classifier[3] = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_features, num_classes)
        )
    elif "resnet" in arch:
        weights = models.ResNet50_Weights.DEFAULT if pretrained else None
        model = models.resnet50(weights=weights)
        in_features = model.fc.in_features
        model.fc = nn.Sequential(
            nn.Dropout(p=0.4),
            nn.Linear(in_features, num_classes)
        )
    else:
        weights = models.ConvNeXt_Small_Weights.DEFAULT if pretrained else None
        model = models.convnext_small(weights=weights)
        in_features = model.classifier[2].in_features
        model.classifier[2] = nn.Sequential(
            nn.Dropout(p=0.4),
            nn.Linear(in_features, num_classes)
        )
    return model


class PyTorchSnakeClassifier:
    """
    2-Stage PyTorch Snake Inference Engine (new_stuff ConvNeXt-Small Architecture).
    Stage 1: Foundation check (Is it a snake or non-snake object like human, vehicle, furniture).
    Stage 2: Fine-tuned species classifier (22 species classes + regional knowledge DB).
    """

    def __init__(self, model_path: str = "app/models/snake_classifier.pth", class_file: str = "app/models/class_names.txt"):
        self.model_path = model_path
        self.class_file = class_file
        self.class_names = []
        self.model = None
        self.general_model = None
        self.imagenet_categories = []
        self.is_loaded = False
        self.device = "cuda" if TORCH_AVAILABLE and torch.cuda.is_available() else "cpu"

        if TORCH_AVAILABLE:
            self.transform = get_inference_transforms()
            self.load_classes()
            self.load_models()

    def load_classes(self):
        if os.path.exists(self.class_file):
            with open(self.class_file, "r", encoding="utf-8") as f:
                self.class_names = [line.strip() for line in f if line.strip()]
        
        if not self.class_names:
            self.class_names = [
                "black", "black_headed_royal_snake_non_venoumous", "boa", "cat_snake",
                "cobra_venoumous", "common", "common_krait", "common_krait_venomous",
                "common_trinket_non_venoumous", "indian_boa_non_venoumous", "indian_cat_ven",
                "indian_cobra", "keelback", "keelback_non_venomous", "kukri_snake",
                "pit_viper", "python", "racer_snake", "rat_snake", "russells_viper",
                "saw_scaled_viper", "wolf_snake"
            ]

    def load_models(self):
        if not TORCH_AVAILABLE:
            return

        try:
            # 1. Load ImageNet Foundation Model for Stage 1 non-snake detection
            self.general_weights = models.MobileNet_V3_Large_Weights.DEFAULT
            self.general_model = models.mobilenet_v3_large(weights=self.general_weights).to(self.device)
            self.general_model.eval()
            self.imagenet_categories = self.general_weights.meta["categories"]

            # 2. Check & Reassemble split PyTorch Model Checkpoint if missing
            if not os.path.exists(self.model_path):
                part1_path = os.path.join(os.path.dirname(self.model_path), "snake_classifier_part1.bin")
                part2_path = os.path.join(os.path.dirname(self.model_path), "snake_classifier_part2.bin")
                
                if os.path.exists(part1_path) and os.path.exists(part2_path):
                    logger.info(f"Model checkpoint missing at '{self.model_path}'. Reassembling from split binary chunks...")
                    try:
                        with open(self.model_path, "wb") as f_out:
                            with open(part1_path, "rb") as f1:
                                f_out.write(f1.read())
                            with open(part2_path, "rb") as f2:
                                f_out.write(f2.read())
                        logger.info("✅ PyTorch model checkpoint reassembled successfully.")
                    except Exception as merge_err:
                        logger.error(f"Failed to reassemble split model checkpoint parts: {merge_err}")

            if os.path.exists(self.model_path):
                checkpoint = torch.load(self.model_path, map_location=self.device)


                
                arch = "convnext_small"
                if isinstance(checkpoint, dict):
                    arch = checkpoint.get("arch", "convnext_small")
                    if "class_names" in checkpoint:
                        self.class_names = checkpoint["class_names"]

                num_classes = len(self.class_names)
                
                # Attempt building convnext_small first, fallback to mobilenet if mismatch
                try:
                    self.model = build_model(arch=arch, num_classes=num_classes, pretrained=False)
                    state_dict = checkpoint.get("state_dict", checkpoint) if isinstance(checkpoint, dict) else checkpoint
                    self.model.load_state_dict(state_dict)
                except Exception as ex1:
                    logger.warning(f"Fallback convnext_small architecture mismatch: {ex1}. Trying mobilenet_v3_large...")
                    self.model = build_model(arch="mobilenet_v3_large", num_classes=num_classes, pretrained=False)
                    state_dict = checkpoint.get("state_dict", checkpoint) if isinstance(checkpoint, dict) else checkpoint
                    self.model.load_state_dict(state_dict)

                self.model.to(self.device)
                self.model.eval()
                self.is_loaded = True
                logger.info(f"✅ [PyTorch ML Engine] Loaded new_stuff model checkpoint from {self.model_path} ({len(self.class_names)} species classes).")
            else:
                logger.error(f"Model checkpoint not found at {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to initialize PyTorch ML Engine: {e}")

    def check_is_snake(self, tensor) -> Dict[str, Any]:
        """Stage 1: Foundation model check to determine if image contains a reptile/snake."""
        if not TORCH_AVAILABLE or self.general_model is None:
            return {"is_snake": True, "detected_general_object": "Reptile/Object", "top_general_labels": []}

        with torch.no_grad():
            outputs = self.general_model(tensor)
            probs = torch.softmax(outputs, dim=1)[0]

        top_probs, top_indices = torch.topk(probs, k=5)
        top_indices_list = [idx.item() for idx in top_indices]
        top_labels = [self.imagenet_categories[idx] for idx in top_indices_list]

        snake_prob_mass = sum(probs[idx].item() for idx in SNAKE_IMAGENET_INDICES)
        reptile_prob_mass = sum(probs[idx].item() for idx in REPTILE_IMAGENET_INDICES)

        is_top_snake = any(idx in SNAKE_IMAGENET_INDICES for idx in top_indices_list[:3])
        is_top_reptile = any(idx in REPTILE_IMAGENET_INDICES for idx in top_indices_list[:3])

        detected_subject = top_labels[0].replace("_", " ").title()
        is_snake = is_top_snake or snake_prob_mass > 0.08 or (is_top_reptile and reptile_prob_mass > 0.15)

        return {
            "is_snake": is_snake,
            "detected_general_object": detected_subject,
            "top_general_labels": [lbl.replace("_", " ").title() for lbl in top_labels[:3]],
            "snake_confidence": round(snake_prob_mass * 100, 2)
        }

    def predict(self, pil_image: Image.Image, quality_score: float = 1.0) -> Dict[str, Any]:
        if not TORCH_AVAILABLE or not self.is_loaded or self.model is None:
            logger.warning("PyTorch Model not ready or PyTorch not loaded.")
            return {
                "snake_detected": False,
                "detection_confidence": 0.0,
                "identification_status": "MODEL_NOT_READY",
                "top_k": []
            }

        try:
            # Ensure RGB Image
            image = pil_image.convert("RGB")
            tensor = self.transform(image).unsqueeze(0).to(self.device)

            # Stage 1: Verification (Is it a snake?)
            verification = self.check_is_snake(tensor)

            if not verification["is_snake"]:
                logger.info(f"🚫 [STAGE 1 GATE] Non-snake object detected: {verification['detected_general_object']}")
                return {
                    "snake_detected": False,
                    "detection_confidence": 0.05,
                    "detected_object": verification["detected_general_object"],
                    "top_detected_labels": verification["top_general_labels"],
                    "identification_status": "NO_SNAKE_DETECTED",
                    "top_k": []
                }

            # Stage 2: Fine-grained species classification
            with torch.no_grad():
                outputs = self.model(tensor)
                probs = torch.softmax(outputs, dim=1)[0]

            top_k_count = min(5, len(self.class_names))
            top_probs, top_indices = torch.topk(probs, k=top_k_count)

            top_k_candidates = []
            for idx, (prob, class_idx) in enumerate(zip(top_probs, top_indices), 1):
                class_key = self.class_names[class_idx.item()]
                prob_val = float(prob.item())

                # Query species knowledge base metadata
                meta = SNAKE_SPECIES_DB.get(class_key, {})
                comm_name = meta.get("common_name", class_key.replace("_", " ").title())
                sci_name = meta.get("scientific_name", class_key.replace("_", " ").title())
                
                # Venomous check: explicit metadata flag or keyword match in class name
                if "is_venomous" in meta:
                    is_venomous = meta["is_venomous"]
                else:
                    ck_lower = class_key.lower()
                    is_venomous = any(k in ck_lower for k in ["venou", "venom", "cobra", "krait", "viper", "_ven"]) and ("non_ven" not in ck_lower and "non_venou" not in ck_lower and "non_venom" not in ck_lower)

                danger_level = meta.get("danger_level", "EXTREME" if is_venomous else "LOW")


                top_k_candidates.append({
                    "species_id": class_idx.item() + 1,
                    "class_key": class_key,
                    "common_name": comm_name,
                    "scientific_name": sci_name,
                    "hindi_name": meta.get("hindi_name", None),
                    "family": meta.get("family", "Reptilia (Serpentes)"),
                    "probability": round(prob_val, 4),
                    "raw_probability": round(prob_val, 4),
                    "calibrated_confidence": round(prob_val, 4),
                    "confidence_pct": round(prob_val * 100, 2),
                    "venomous": is_venomous,
                    "medically_significant": is_venomous,
                    "regional_presence": "COMMON",
                    "danger_level": danger_level,
                    "key_traits": meta.get("key_traits", ""),
                    "first_aid": meta.get("first_aid", "")
                })


            top_1 = top_k_candidates[0] if top_k_candidates else {}

            return {
                "snake_detected": True,
                "detection_confidence": round(top_1.get("probability", 0.95), 3),
                "identification_status": "HIGH_CONFIDENCE",
                "top_1": top_1,
                "top_k": top_k_candidates
            }

        except Exception as e:
            logger.error(f"Prediction failed in PyTorch ML Engine: {e}")
            return {
                "snake_detected": False,
                "detection_confidence": 0.0,
                "identification_status": "ERROR",
                "top_k": []
            }


# Global ML Engine Instance
ml_engine = PyTorchSnakeClassifier()
