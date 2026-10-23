"""Smoke tests for the checked-in ONNX model and available image fixtures.

These checks validate loading, preprocessing/inference shape, finite scores, and
label alignment. They do not measure model accuracy because the fixtures do not
have independently verified ground-truth labels.
"""

from pathlib import Path
import sys

import numpy as np

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from ml.predict import get_class_names, get_inference_session, predict_disease  # noqa: E402


def main() -> None:
    fixtures = (
        PROJECT_ROOT / "test_images" / "sample_leaf.jpg",
        BACKEND_DIR / "uploads" / "leaf-spot-fungus-920x518.webp",
    )
    missing = [str(path) for path in fixtures if not path.is_file()]
    if missing:
        raise FileNotFoundError("Required model test image(s) are missing: " + ", ".join(missing))

    session = get_inference_session()
    classes = get_class_names()
    input_shape = session.get_inputs()[0].shape
    output_shape = session.get_outputs()[0].shape
    if input_shape[1:] != [3, 224, 224]:
        raise AssertionError(f"Unexpected model input shape: {input_shape}")
    if len(classes) != 38 or len(set(classes)) != len(classes):
        raise AssertionError(f"Expected 38 unique class labels; found {len(classes)}")
    if output_shape[-1] != len(classes):
        raise AssertionError(f"Model output/classes mismatch: {output_shape} vs {len(classes)} labels")

    for image_path in fixtures:
        result = predict_disease(image_path)
        if result["disease"] not in classes:
            raise AssertionError(f"Prediction has no class mapping: {result['disease']!r}")
        if not np.isfinite(result["confidence"]) or not 0 <= result["confidence"] <= 100:
            raise AssertionError(f"Invalid top score for {image_path.name}: {result['confidence']!r}")
        raw_scores = np.asarray([item["confidence"] for item in result["top_predictions"]])
        if raw_scores.size != 5 or not np.isfinite(raw_scores).all():
            raise AssertionError(f"Invalid top-five raw scores for {image_path.name}")
        if np.any(raw_scores < 0) or np.any(raw_scores > 100):
            raise AssertionError(f"Out-of-range raw score for {image_path.name}")
        print(f"{image_path.name}: {result['disease']} (raw model score {result['confidence']:.2f}%)")

    # The known 15-byte fixture must be rejected as an invalid image.
    corrupt_image = BACKEND_DIR / "uploads" / "leaf.jpg"
    try:
        predict_disease(corrupt_image)
    except (OSError, ValueError):
        pass
    else:
        raise AssertionError("Corrupted image fixture was accepted")

    absent_image = BACKEND_DIR / "uploads" / "does-not-exist.jpg"
    try:
        predict_disease(absent_image)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("Missing image was accepted")

    print(f"Model smoke checks passed for {len(fixtures)} images; accuracy was not evaluated.")


if __name__ == "__main__":
    main()
