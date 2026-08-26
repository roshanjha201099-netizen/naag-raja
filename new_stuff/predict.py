"""
Snake Classifier Inference Utility.
Supports loading custom fine-tuned checkpoints (MobileNetV3 / ResNet50)
or pretrained weights with class mapping.
"""

import os
import sys
import json

# Ensure UTF-8 output handling on Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import numpy as np


# Standard ImageNet normalization parameters
IMAGE_SIZE = 224
NORM_MEAN = [0.485, 0.456, 0.406]
NORM_STD = [0.229, 0.224, 0.225]


def get_inference_transforms():
    """Preprocessing transformations for evaluation and inference."""
    return transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=NORM_MEAN, std=NORM_STD)
    ])


def build_model(arch: str = "mobilenet_v3_large", num_classes: int = 10, pretrained: bool = True):
    """Instantiate model backbone with appropriate head matching train.py."""
    arch = arch.lower()
    if "mobilenet" in arch:
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
    elif "convnext" in arch:
        weights = models.ConvNeXt_Small_Weights.DEFAULT if pretrained else None
        model = models.convnext_small(weights=weights)
        in_features = model.classifier[2].in_features
        model.classifier[2] = nn.Sequential(
            nn.Dropout(p=0.4),
            nn.Linear(in_features, num_classes)
        )
    else:
        raise ValueError(f"Unsupported architecture: {arch}. Choose convnext_small, resnet50, mobilenet_v3_large, or efficientnet_b0.")
        
    return model


# ImageNet-1k snake and reptile class indices
SNAKE_IMAGENET_INDICES = set(range(52, 69))  # 52 to 68 are all snake species in ImageNet
REPTILE_IMAGENET_INDICES = set(range(33, 69)) # lizards, turtles, snakes


class SnakeClassifier:
    """Inference engine with 2-stage verification (Is it a snake? -> What species?)."""
    
    def __init__(self, model_path: str = "models/snake_classifier.pth", class_file: str = "class_names.txt", arch: str = "mobilenet_v3_large", device: str = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.transform = get_inference_transforms()
        self.arch = arch
        self.class_names = []
        self.model = None
        self.is_custom_trained = False
        
        # Load general ImageNet model for out-of-distribution (OOD) & non-snake detection
        self.general_weights = models.MobileNet_V3_Large_Weights.DEFAULT
        self.general_model = models.mobilenet_v3_large(weights=self.general_weights).to(self.device)
        self.general_model.eval()
        self.imagenet_categories = self.general_weights.meta["categories"]
        
        self._load_classes(class_file)
        self._load_model(model_path)

    def _load_classes(self, class_file: str):
        """Load class labels from file or fall back to standard list."""
        if os.path.exists(class_file):
            with open(class_file, "r", encoding="utf-8") as f:
                self.class_names = [line.strip() for line in f if line.strip()]
        
        if not self.class_names:
            self.class_names = [
                "common_krait", "banded_krait", "common_wolf_snake",
                "indian_cobra", "king_cobra", "russells_viper",
                "saw_scaled_viper", "rat_snake", "ball_python",
                "burmese_python", "corn_snake", "green_tree_python",
                "black_mamba", "copperhead", "cottonmouth", "rattlesnake"
            ]

    def _load_model(self, model_path: str):
        """Load fine-tuned weights if available."""
        num_classes = len(self.class_names)
        
        if os.path.exists(model_path):
            try:
                checkpoint = torch.load(model_path, map_location=self.device)
                arch = checkpoint.get("arch", self.arch) if isinstance(checkpoint, dict) else self.arch
                self.arch = arch
                
                if isinstance(checkpoint, dict) and "class_names" in checkpoint:
                    self.class_names = checkpoint["class_names"]
                    num_classes = len(self.class_names)
                
                self.model = build_model(arch=self.arch, num_classes=num_classes, pretrained=False)
                state_dict = checkpoint.get("state_dict", checkpoint) if isinstance(checkpoint, dict) else checkpoint
                self.model.load_state_dict(state_dict)
                self.is_custom_trained = True
                print(f"[SnakeClassifier] Loaded fine-tuned weights from {model_path} ({self.arch}, {num_classes} classes).")
            except Exception as e:
                print(f"[SnakeClassifier] Notice: Custom checkpoint fallback: {e}")
                self.model = build_model(arch=self.arch, num_classes=num_classes, pretrained=True)
        else:
            self.model = build_model(arch=self.arch, num_classes=num_classes, pretrained=True)
            
        self.model.to(self.device)
        self.model.eval()

    def check_is_snake(self, tensor):
        """
        Stage 1: Verify whether the image actually contains a snake or reptile
        using ImageNet-1k 1000-class foundation features.
        """
        with torch.no_grad():
            general_outputs = self.general_model(tensor)
            general_probs = torch.softmax(general_outputs, dim=1)[0]
            
        top_probs, top_indices = torch.topk(general_probs, k=5)
        top_indices_list = [idx.item() for idx in top_indices]
        top_labels = [self.imagenet_categories[idx] for idx in top_indices_list]
        
        # Calculate total probability mass assigned to snakes / reptiles
        snake_prob_mass = sum(general_probs[idx].item() for idx in SNAKE_IMAGENET_INDICES)
        reptile_prob_mass = sum(general_probs[idx].item() for idx in REPTILE_IMAGENET_INDICES)
        
        # Check if any of the top 3 predictions are snakes/reptiles
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

    def predict(self, image_input, top_k: int = 3, min_confidence: float = 20.0):
        """
        Run 2-Stage inference:
        1. General Object / Snake Detector (filters out humans, cars, random objects)
        2. Fine-grained Snake Species Classifier
        """
        if isinstance(image_input, str):
            image = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, np.ndarray):
            image = Image.fromarray(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            image = image_input.convert("RGB")
        else:
            raise TypeError(f"Unsupported image type: {type(image_input)}")
            
        tensor = self.transform(image).unsqueeze(0).to(self.device)
        
        # Stage 1: Check if the input is actually a snake
        verification = self.check_is_snake(tensor)
        
        # If definitely NOT a snake (e.g. human face, glasses, dog, vehicle)
        if not verification["is_snake"]:
            return {
                "is_snake": False,
                "detected_object": verification["detected_general_object"],
                "top_detected_labels": verification["top_general_labels"],
                "message": f"No snake detected. Image appears to be: {verification['detected_general_object']}",
                "predictions": []
            }
            
        # Stage 2: Fine-grained species classification
        with torch.no_grad():
            outputs = self.model(tensor)
            probabilities = torch.softmax(outputs, dim=1)[0]
            
        top_k = min(top_k, len(self.class_names))
        top_probs, top_indices = torch.topk(probabilities, k=top_k)
        
        results = []
        for prob, idx in zip(top_probs, top_indices):
            idx_val = idx.item()
            class_name = self.class_names[idx_val] if idx_val < len(self.class_names) else f"class_{idx_val}"
            conf = prob.item()
            results.append({
                "class": class_name,
                "confidence": conf,
                "confidence_pct": round(conf * 100, 2)
            })
            
        return {
            "is_snake": True,
            "detected_object": "Snake / Reptile",
            "top_detected_labels": verification["top_general_labels"],
            "predictions": results
        }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test Snake Classification on an image.")
    parser.add_argument("--image", type=str, required=True, help="Path to input image file.")
    parser.add_argument("--model", type=str, default="models/snake_classifier.pth", help="Path to model weights.")
    parser.add_argument("--arch", type=str, default="mobilenet_v3_large", help="Model architecture.")
    parser.add_argument("--top_k", type=int, default=3, help="Top K predictions to return.")
    args = parser.parse_args()
    
    classifier = SnakeClassifier(model_path=args.model, arch=args.arch)
    preds = classifier.predict(args.image, top_k=args.top_k)
    print("\n--- Predictions ---")
    for i, p in enumerate(preds, 1):
        print(f"{i}. {p['class']} — {p['confidence_pct']}%")
