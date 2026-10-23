import os
import json
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
from PIL import Image
import onnxruntime as ort

# Base directory resolution
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
ONNX_MODEL_PATH = MODELS_DIR / "efficientnet_v2_s_best.onnx"
CLASSES_JSON_PATH = MODELS_DIR / "classes.json"
CLASS_NAMES_TXT_PATH = MODELS_DIR / "class_names.txt"

# ImageNet normalization parameters for EfficientNetV2
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

_session = None
_class_names = []


def get_inference_session() -> ort.InferenceSession:
    """Load and cache ONNX runtime session (singleton)."""
    global _session
    if _session is None:
        if not ONNX_MODEL_PATH.exists():
            raise FileNotFoundError(f"Model file not found at {ONNX_MODEL_PATH}")
        # Configure session options for fast CPU execution
        opts = ort.SessionOptions()
        opts.inter_op_num_threads = 2
        opts.intra_op_num_threads = 2
        _session = ort.InferenceSession(
            str(ONNX_MODEL_PATH),
            sess_options=opts,
            providers=["CPUExecutionProvider"]
        )
    return _session


def get_class_names() -> List[str]:
    """Load class names from classes.json or fallback class_names.txt."""
    global _class_names
    if not _class_names:
        if CLASSES_JSON_PATH.exists():
            with open(CLASSES_JSON_PATH, "r", encoding="utf-8") as f:
                meta = json.load(f)
                _class_names = meta.get("classes", [])
        elif CLASS_NAMES_TXT_PATH.exists():
            with open(CLASS_NAMES_TXT_PATH, "r", encoding="utf-8") as f:
                _class_names = [
                    line.strip().split(": ", 1)[1]
                    for line in f
                    if line.strip() and ": " in line
                ]
        if not _class_names:
            raise RuntimeError("Failed to load class names list.")
    return _class_names


def parse_class_label(class_name: str) -> tuple[str, str, bool]:
    """Split class label into crop, condition, and healthy flag."""
    if "___" in class_name:
        parts = class_name.split("___", 1)
        crop = parts[0].replace("_", " ").strip()
        condition = parts[1].replace("_", " ").strip()
    else:
        crop = "Plant"
        condition = class_name.replace("_", " ").strip()

    is_healthy = condition.lower() == "healthy"
    return crop, condition, is_healthy


def predict_disease(image_path: str | Path, top_k: int = 5) -> Dict[str, Any]:
    """
    Predict plant disease using the EfficientNetV2-S ONNX model.
    Applies ImageNet normalization and returns a raw softmax score.

    The returned score is not a calibrated probability and is not evidence that
    the image belongs to one of the model's supported classes.
    """
    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    path_obj = Path(image_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Image not found at {image_path}")

    # 1. Open and validate image format
    with Image.open(path_obj) as img:
        rgb_image = img.convert("RGB")
        # Check image dimensions
        width, height = rgb_image.size
        if width < 10 or height < 10:
            raise ValueError("Image dimensions are too small to analyze.")

        # Check for near-blank or monochromatic images
        img_np = np.array(rgb_image, dtype=np.float32)
        pixel_std = float(np.std(img_np))

        # 2. Preprocess: Resize to 224x224 (Bilinear)
        resized = rgb_image.resize((224, 224), Image.Resampling.BILINEAR)

    # 3. Normalize: Scale to [0, 1] then apply standard ImageNet mean & std
    arr = np.array(resized, dtype=np.float32) / 255.0
    arr = (arr - IMAGENET_MEAN) / IMAGENET_STD

    # 4. Transpose to CHW and add batch dimension -> (1, 3, 224, 224)
    arr = np.transpose(arr, (2, 0, 1))
    tensor = np.expand_dims(arr, axis=0).astype(np.float32)

    # 5. Run ONNX model inference
    session = get_inference_session()
    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: tensor})
    if not outputs or np.asarray(outputs[0]).ndim != 2 or outputs[0].shape[0] != 1:
        raise RuntimeError("Model returned an unexpected output shape")
    logits = np.asarray(outputs[0][0], dtype=np.float32)
    classes = get_class_names()
    if logits.ndim != 1 or logits.size != len(classes):
        raise RuntimeError("Model output count does not match the class label list")
    if not np.isfinite(logits).all():
        raise RuntimeError("Model returned non-finite output scores")

    # 6. Compute softmax probabilities
    shifted_logits = logits - np.max(logits)
    exp_logits = np.exp(shifted_logits)
    probs = exp_logits / np.sum(exp_logits)

    # 7. Shannon entropy for uncertainty detection
    entropy = float(-np.sum(probs * np.log(probs + 1e-12)))

    # 8. Top predictions
    sorted_indices = np.argsort(probs)[::-1]
    top_index = int(sorted_indices[0])
    top_confidence = float(probs[top_index])
    confidence_percentage = round(top_confidence * 100, 2)
    predicted_class = classes[top_index]

    crop_name, condition_name, is_healthy = parse_class_label(predicted_class)

    top_predictions = []
    for idx in sorted_indices[:top_k]:
        c_name, cond, _ = parse_class_label(classes[idx])
        top_predictions.append({
            "class": classes[idx],
            "crop": c_name,
            "condition": cond,
            "confidence": round(float(probs[idx]) * 100, 2),
            "probability": float(probs[idx]),
        })

    # A softmax score is not calibrated and cannot establish in-domain input.
    status = "Uncalibrated model score"
    uncertainty_warning = (
        "This model score is not a calibrated probability, and unsupported images "
        "may still receive a class prediction. Treat the result as a candidate and "
        "verify it using plant symptoms or qualified agricultural guidance."
    )
    if pixel_std < 12.0:
        uncertainty_warning = (
            "The image has little visual contrast or leaf detail. Please provide a "
            "clear, well-lit photo of a plant leaf. The model score is not calibrated."
        )

    return {
        "disease": predicted_class,
        "crop": crop_name,
        "condition": condition_name,
        "is_healthy": is_healthy,
        "confidence": confidence_percentage,
        "status": status,
        "uncertainty_warning": uncertainty_warning,
        "entropy": round(entropy, 3),
        "top_predictions": top_predictions,
    }
