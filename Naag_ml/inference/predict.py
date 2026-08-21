import os
import cv2
import numpy as np
import onnxruntime as ort
import pandas as pd

# Load class mappings & species knowledge
class_map_df = pd.read_csv("models/class_mapping.csv")
idx_to_class = dict(zip(class_map_df["class_id"], class_map_df["class_name"]))

snakes_df = pd.read_csv("models/indian_snakes.csv")
snake_info = snakes_df.set_index("scientific_name").to_dict(orient="index")

# Initialize ONNX inference session (optimized for CPU)
session = ort.InferenceSession("models/snake_model.onnx", providers=["CPUExecutionProvider"])
input_name = session.get_inputs()[0].name

def preprocess_image(image_path):
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (224, 224))
    
    # Standard normalization
    img = img.astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    img = (img - mean) / std
    
    # NHWC to NCHW
    img = np.transpose(img, (2, 0, 1))
    return np.expand_dims(img, axis=0)

def softmax(x):
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=1, keepdims=True)

def predict_snake(image_path):
    tensor = preprocess_image(image_path)
    outputs = session.run(None, {input_name: tensor})[0]
    probs = softmax(outputs)[0]

    top_idx = int(np.argmax(probs))
    species_name = idx_to_class.get(top_idx, "Unknown")
    confidence = float(probs[top_idx])

    meta = snake_info.get(species_name, {})
    
    return {
        "scientific_name": species_name,
        "common_name": meta.get("common_name", "N/A"),
        "venomous_status": meta.get("venomous_status", "unknown"),
        "family": meta.get("family", "N/A"),
        "confidence": round(confidence * 100, 2),
        "is_emergency": meta.get("venomous_status", "").lower() in ["venomous", "highly venomous"]
    }

if __name__ == "__main__":
    # Test on any sample snake image
    print("Inference engine ready.")