"""Print reproducible, privacy-conscious diagnostics for uploaded leaf images.

Example:
    python backend/diagnose_predictions.py image1.jpg image2.jpg ...

The report includes each input's content hash, dimensions, actual model tensor
and logits, top predictions, and the matching disease record when PostgreSQL is
available. It never prints image paths or persists the uploaded images.
"""

import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from ml import predict as prediction  # noqa: E402
from services.database_service import get_disease_details_by_prediction  # noqa: E402


def diagnose(image_path: Path, include_database: bool = True) -> dict:
    image_bytes = image_path.read_bytes()
    with Image.open(BytesIO(image_bytes)) as image:
        dimensions = list(image.size)
        tensor = prediction.preprocess_image(image)

    session = prediction.get_inference_session()
    outputs = session.run(None, {session.get_inputs()[0].name: tensor})
    logits = np.asarray(outputs[0][0], dtype=np.float32)
    classes = prediction.get_class_names()
    if logits.shape != (len(classes),) or not np.isfinite(logits).all():
        raise RuntimeError("Model output does not match the finite class-label vector")

    shifted_logits = logits - logits.max()
    exp_logits = np.exp(shifted_logits)
    scores = exp_logits / exp_logits.sum()
    top_indices = np.argsort(scores)[::-1][:5]
    predicted_label = classes[int(top_indices[0])]

    record = None
    database_status = "skipped"
    if include_database:
        try:
            details = get_disease_details_by_prediction(predicted_label)
            database_status = "matched" if details else "no_matching_record"
            if details:
                disease = details["disease"]
                record = {"id": disease[0], "name": disease[1], "crop": disease[2]}
        except Exception as exc:
            # Error class helps diagnose availability without exposing DSNs or
            # other connection details that may include credentials.
            database_status = f"unavailable ({type(exc).__name__})"

    return {
        "image_sha256": sha256(image_bytes).hexdigest(),
        "image_dimensions": dimensions,
        "model_input": {
            "shape": list(tensor.shape),
            "dtype": str(tensor.dtype),
            "minimum": float(tensor.min()),
            "maximum": float(tensor.max()),
        },
        "raw_logits": logits.tolist(),
        "top_predictions": [
            {
                "index": int(index),
                "label": classes[int(index)],
                "raw_logit": float(logits[index]),
                "softmax_score_uncalibrated_percent": float(scores[index] * 100),
            }
            for index in top_indices
        ],
        "mapped_label": predicted_label,
        "database_status": database_status,
        "database_disease_record": record,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+", type=Path, help="Image files to analyze")
    parser.add_argument(
        "--skip-database", action="store_true",
        help="Skip the read-only disease-record lookup",
    )
    args = parser.parse_args()

    reports = []
    try:
        for image_path in args.images:
            reports.append(diagnose(image_path, include_database=not args.skip_database))
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(f"diagnostic failed: {exc}")
    print(json.dumps(reports, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
