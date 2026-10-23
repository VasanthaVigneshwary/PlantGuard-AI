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
        session = ort.InferenceSession(
            str(ONNX_MODEL_PATH),
            sess_options=opts,
            providers=["CPUExecutionProvider"]
        )
        validate_inference_signature(session)
        _session = session
    return _session


def validate_inference_signature(session: ort.InferenceSession) -> None:
    """Fail early when a deployed ONNX artifact is incompatible with this pipeline."""
    inputs = session.get_inputs()
    outputs = session.get_outputs()
    if len(inputs) != 1 or inputs[0].type != "tensor(float)":
        raise RuntimeError("Model must expose one float32 image input")
    input_shape = inputs[0].shape
    if len(input_shape) != 4 or input_shape[1:] != [3, 224, 224]:
        raise RuntimeError(f"Model input must have shape [batch, 3, 224, 224]; found {input_shape}")
    if len(outputs) != 1 or outputs[0].type != "tensor(float)":
        raise RuntimeError("Model must expose one float32 logits output")
    output_shape = outputs[0].shape
    if len(output_shape) != 2 or output_shape[-1] != 38:
        raise RuntimeError(f"Model output must have shape [batch, 38]; found {output_shape}")


def get_class_names() -> List[str]:
    """Load labels and reject disagreement between the indexed and text lists."""
    global _class_names
    if not _class_names:
        json_classes = None
        if CLASSES_JSON_PATH.exists():
            with open(CLASSES_JSON_PATH, "r", encoding="utf-8") as f:
                meta = json.load(f)
                json_classes = meta.get("classes")
        text_classes = None
        if CLASS_NAMES_TXT_PATH.exists():
            with open(CLASS_NAMES_TXT_PATH, "r", encoding="utf-8") as f:
                parsed = []
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    index, separator, label = line.partition(": ")
                    if not separator or not index.isdigit() or int(index) != len(parsed) or not label:
                        raise RuntimeError("Invalid indexed class label in class_names.txt")
                    parsed.append(label)
                text_classes = parsed
        if json_classes is not None and text_classes is not None and json_classes != text_classes:
            raise RuntimeError("classes.json and class_names.txt disagree on output class order")
        _class_names = json_classes if json_classes is not None else (text_classes or [])
        if (not isinstance(_class_names, list) or not _class_names
                or not all(isinstance(label, str) and label for label in _class_names)
                or len(_class_names) != len(set(_class_names))):
            raise RuntimeError("Failed to load class names list.")
    return _class_names


def preprocess_image(image: Image.Image) -> np.ndarray:
    """Apply the upstream model-card preprocessing and return a float32 NCHW batch."""
    rgb = image.convert("RGB").resize((224, 224), Image.Resampling.BILINEAR)
    arr = np.asarray(rgb, dtype=np.float32) / 255.0
    arr = (arr - IMAGENET_MEAN) / IMAGENET_STD
    return np.expand_dims(np.transpose(arr, (2, 0, 1)), axis=0).astype(np.float32)


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

        tensor = preprocess_image(rgb_image)

    # 5. Run ONNX model inference
    session = get_inference_session()
    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: tensor})
    if not outputs or np.asarray(outputs[0]).ndim != 2 or outputs[0].shape[0] != 1:
        raise RuntimeError("Model returned an unexpected output shape")
    logits = np.asarray(outputs[0][0], dtype=np.float32)
    classes = get_class_names()
    if len(classes) != 38:
        raise RuntimeError(f"Expected 38 model labels; found {len(classes)}")
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
