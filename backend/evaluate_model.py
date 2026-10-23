"""Evaluate ONNX predictions against an independently labeled folder dataset.

Dataset layout: ROOT/<exact model class label>/<image files>. The evaluator
requires an explicit source citation and an operator assertion that the set is
independent of training data. It never treats smoke fixtures as evaluation data.
"""

import argparse
import json
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from ml.predict import get_class_names, predict_disease  # noqa: E402

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def evaluate(dataset_root: Path, source: str) -> dict:
    classes = get_class_names()
    class_index = {label: index for index, label in enumerate(classes)}
    confusion = [[0 for _ in classes] for _ in classes]
    samples = []
    for class_dir in sorted(path for path in dataset_root.iterdir() if path.is_dir()):
        if class_dir.name not in class_index:
            raise ValueError(f"Unknown ground-truth class directory: {class_dir.name}")
        for path in sorted(class_dir.rglob("*")):
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
                result = predict_disease(path, top_k=1)
                truth = class_index[class_dir.name]
                predicted = class_index[result["disease"]]
                confusion[truth][predicted] += 1
                samples.append((truth, predicted))
    if not samples:
        raise ValueError("No labeled images found in the dataset directory")

    per_class = {}
    for index, label in enumerate(classes):
        tp = confusion[index][index]
        support = sum(confusion[index])
        predicted_count = sum(row[index] for row in confusion)
        per_class[label] = {
            "support": support,
            "precision": tp / predicted_count if predicted_count else 0.0,
            "recall": tp / support if support else 0.0,
        }
    correct = sum(confusion[index][index] for index in range(len(classes)))
    return {
        "dataset_source": source,
        "dataset_root": str(dataset_root.resolve()),
        "sample_count": len(samples),
        "accuracy": correct / len(samples),
        "per_class": per_class,
        "confusion_matrix": {"labels": classes, "counts": confusion},
        "independence": "Operator asserted independent of model training data; not independently audited.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--source", required=True, help="Dataset name and source URL/citation")
    parser.add_argument(
        "--independent-of-training", action="store_true",
        help="Confirm the dataset has no overlap with the model's training data",
    )
    args = parser.parse_args()
    if not args.independent_of_training:
        parser.error("refusing metrics without --independent-of-training confirmation")
    if not args.dataset_root.is_dir():
        parser.error(f"dataset directory does not exist: {args.dataset_root}")
    try:
        print(json.dumps(evaluate(args.dataset_root, args.source), indent=2))
    except (OSError, ValueError, RuntimeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
