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

from ml.predict import get_class_names, parse_class_label, predict_disease  # noqa: E402

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def health_status_metrics(samples: list[dict]) -> dict:
    """Summarize healthy/diseased predictions, retaining uncertain results as abstentions."""
    true_labels = ("healthy", "diseased")
    predicted_labels = ("healthy", "diseased", "uncertain")

    def summarize(rows: list[dict]) -> dict:
        matrix = [[0 for _ in predicted_labels] for _ in true_labels]
        for sample in rows:
            true_index = true_labels.index(sample["truth"])
            predicted_index = predicted_labels.index(sample["prediction"])
            matrix[true_index][predicted_index] += 1

        total = sum(sum(row) for row in matrix)
        resolved = sum(matrix[truth][pred] for truth in range(2) for pred in range(2))
        correct = matrix[0][0] + matrix[1][1]
        per_class = {}
        for index, label in enumerate(true_labels):
            tp = matrix[index][index]
            predicted_count = sum(matrix[row][index] for row in range(2))
            support = sum(matrix[index])
            fn = support - tp  # Includes abstentions as misses for recall.
            precision = tp / predicted_count if predicted_count else 0.0
            recall = tp / support if support else 0.0
            f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
            per_class[label] = {
                "support": support,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "abstentions": matrix[index][2],
                "false_negatives_including_abstentions": fn,
            }

        return {
            "sample_count": total,
            "accuracy": correct / total if total else 0.0,
            "macro_f1": sum(item["f1"] for item in per_class.values()) / 2,
            "coverage": resolved / total if total else 0.0,
            "selective_accuracy": correct / resolved if resolved else 0.0,
            "per_class": per_class,
            "confusion_matrix": {
                "true_labels": list(true_labels),
                "predicted_labels": list(predicted_labels),
                "counts": matrix,
            },
        }

    summary = summarize(samples)
    crops = sorted({sample["crop"] for sample in samples})
    summary["per_crop"] = {
        crop: summarize([sample for sample in samples if sample["crop"] == crop])
        for crop in crops
    }
    return summary


def evaluate(dataset_root: Path, source: str) -> dict:
    classes = get_class_names()
    class_index = {label: index for index, label in enumerate(classes)}
    confusion = [[0 for _ in classes] for _ in classes]
    samples = []
    health_samples = []
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
                crop, _, true_healthy = parse_class_label(class_dir.name)
                _, _, predicted_healthy_from_label = parse_class_label(result["disease"])
                is_uncertain = bool(result.get("is_uncertain", False))
                predicted_healthy = bool(result.get("is_healthy", predicted_healthy_from_label))
                health_samples.append({
                    "crop": crop,
                    "truth": "healthy" if true_healthy else "diseased",
                    "prediction": "uncertain" if is_uncertain else (
                        "healthy" if predicted_healthy else "diseased"
                    ),
                })
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
            "f1": (
                2 * tp / (predicted_count + support)
                if predicted_count + support else 0.0
            ),
        }
    correct = sum(confusion[index][index] for index in range(len(classes)))
    supported_f1 = [item["f1"] for item in per_class.values() if item["support"]]
    macro_f1 = sum(supported_f1) / len(supported_f1)
    return {
        "dataset_source": source,
        "dataset_root": str(dataset_root.resolve()),
        "sample_count": len(samples),
        "accuracy": correct / len(samples),
        "macro_f1": macro_f1,
        "per_class": per_class,
        "confusion_matrix": {"labels": classes, "counts": confusion},
        "health_status": health_status_metrics(health_samples),
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
