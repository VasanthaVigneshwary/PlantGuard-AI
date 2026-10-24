"""Train and one-shot evaluate a PlantDoc-only 16-class CPU candidate.

This experiment intentionally does not modify the production ONNX model. It
trains a MobileNetV3-Small from random initialization, using only PlantDoc's
original train split and a stratified validation split drawn from that train
split. The original test split is read only after training/model selection.

Command (from repository root, after installing torch/torchvision):
  python backend/train_plantdoc_candidate.py datasets/plantdoc

All artifacts/reports are written under datasets/plantdoc/candidate/ (ignored
by Git). Test images with exact SHA-256 matches in train are excluded from both
training and final metrics. Conflicting exact duplicates inside train are also
excluded in full. This narrower candidate is not a drop-in replacement for the
38-class production model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))
from ml.predict import get_class_names  # noqa: E402
from plantdoc_dataset import COMPATIBLE_LABELS  # noqa: E402

SEED = 20261024
VAL_FRACTION = 0.15
EPOCHS = 20
PATIENCE = 5
BATCH_SIZE = 32
IMAGE_SIZE = 224
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def read_manifest(dataset_root: Path) -> list[dict]:
    path = dataset_root / "manifest.jsonl"
    if not path.is_file():
        raise FileNotFoundError(f"Missing dataset manifest: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def make_data_splits(rows: list[dict], seed: int = SEED) -> dict:
    """Return stable train/validation/final-test lists and leakage exclusions."""
    test_rows = [r for r in rows if r["split"] == "test"]
    test_hashes = {r["sha256"] for r in test_rows}
    mapped_test_labels = {
        COMPATIBLE_LABELS[r["ground_truth_label"]][0]
        for r in test_rows if r["ground_truth_label"] in COMPATIBLE_LABELS
        and r["sha256"] not in test_hashes.intersection(
            {x["sha256"] for x in rows if x["split"] == "train"}
        )
    }
    # Restrict this experiment to supported classes that actually occur in the
    # final test split, so the model's label space is explicit and evaluable.
    classes = sorted(mapped_test_labels)
    class_set = set(classes)
    train_candidates = [
        r for r in rows
        if r["split"] == "train" and r["ground_truth_label"] in COMPATIBLE_LABELS
        and r["sha256"] not in test_hashes
        and not r["loading_error"]
    ]

    hash_groups: dict[str, list[dict]] = defaultdict(list)
    for row in train_candidates:
        hash_groups[row["sha256"]].append(row)
    duplicate_conflicts = []
    deduplicated = []
    duplicate_train_extra_count = 0
    for digest, group in hash_groups.items():
        labels = {COMPATIBLE_LABELS[r["ground_truth_label"]][0] for r in group}
        if len(labels) > 1:
            duplicate_conflicts.append({
                "sha256": digest,
                "image_paths": sorted(r["image_path"] for r in group),
                "mapped_labels": sorted(labels),
                "action": "excluded all copies due to conflicting labels",
            })
            continue
        group.sort(key=lambda r: r["image_path"])
        deduplicated.append(group[0])
        duplicate_train_extra_count += len(group) - 1

    by_class: dict[str, list[dict]] = defaultdict(list)
    for row in deduplicated:
        label = COMPATIBLE_LABELS[row["ground_truth_label"]][0]
        if label in class_set:
            by_class[label].append(row)
    rng = random.Random(seed)
    train, validation = [], []
    for label in classes:
        class_rows = sorted(by_class[label], key=lambda r: (r["sha256"], r["image_path"]))
        if len(class_rows) < 3:
            raise ValueError(f"Not enough unique training images for {label}: {len(class_rows)}")
        rng.shuffle(class_rows)
        val_count = max(1, round(len(class_rows) * VAL_FRACTION))
        val_count = min(val_count, len(class_rows) - 1)
        validation.extend(class_rows[:val_count])
        train.extend(class_rows[val_count:])

    # Images from ambiguous/unsupported labels aren't relabeled or admitted.
    evaluation_rows = [
        r for r in test_rows if r["ground_truth_label"] in COMPATIBLE_LABELS
        and COMPATIBLE_LABELS[r["ground_truth_label"]][0] in class_set
        and r["sha256"] not in test_hashes.intersection(
            {x["sha256"] for x in rows if x["split"] == "train"}
        )
        and not r["loading_error"]
    ]
    if not evaluation_rows:
        raise ValueError("No leakage-free, compatible PlantDoc test images are available")
    train_hashes = {r["sha256"] for r in train}
    validation_hashes = {r["sha256"] for r in validation}
    eval_hashes = {r["sha256"] for r in evaluation_rows}
    if train_hashes & validation_hashes or train_hashes & eval_hashes or validation_hashes & eval_hashes:
        raise AssertionError("Dataset split leakage detected")
    return {
        "classes": classes,
        "train": train,
        "validation": validation,
        "test": evaluation_rows,
        "duplicate_conflicts": duplicate_conflicts,
        "duplicate_train_extra_count": duplicate_train_extra_count,
        "train_test_overlap_excluded_count": sum(
            r["split"] == "train" and r["sha256"] in test_hashes for r in rows
        ),
    }


def classification_metrics(truth: list[int], predicted: list[int], class_names: list[str]) -> dict:
    matrix = [[0 for _ in class_names] for _ in class_names]
    for actual, guess in zip(truth, predicted):
        matrix[actual][guess] += 1
    per_class = {}
    for i, name in enumerate(class_names):
        tp = matrix[i][i]
        support = sum(matrix[i])
        predicted_count = sum(row[i] for row in matrix)
        precision = tp / predicted_count if predicted_count else 0.0
        recall = tp / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[name] = {
            "support": support,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    return {
        "sample_count": len(truth),
        "accuracy": sum(matrix[i][i] for i in range(len(class_names))) / len(truth) if truth else None,
        "macro_precision": float(np.mean([v["precision"] for v in per_class.values()])) if truth else None,
        "macro_recall": float(np.mean([v["recall"] for v in per_class.values()])) if truth else None,
        "macro_f1": float(np.mean([v["f1"] for v in per_class.values()])) if truth else None,
        "per_class": per_class,
        "confusion_matrix": {"labels": class_names, "counts": matrix},
    }


def train_and_evaluate(dataset_root: Path, epochs: int = EPOCHS) -> dict:
    import torch
    from torch import nn
    from torch.utils.data import DataLoader, Dataset
    from torchvision import transforms
    from torchvision.models import mobilenet_v3_small

    splits = make_data_splits(read_manifest(dataset_root))
    classes = splits["classes"]
    model_classes = get_class_names()
    if any(label not in model_classes for label in classes):
        raise ValueError("PlantDoc target mapping includes a class outside the deployed model taxonomy")
    class_index = {label: i for i, label in enumerate(classes)}

    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.68, 1.0), interpolation=transforms.InterpolationMode.BILINEAR),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.22, contrast=0.22, saturation=0.22, hue=0.04),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    eval_transform = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE), interpolation=transforms.InterpolationMode.BILINEAR),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])

    class ImageRows(Dataset):
        def __init__(self, items: list[dict], transform):
            self.items = items
            self.transform = transform

        def __len__(self):
            return len(self.items)

        def __getitem__(self, index):
            row = self.items[index]
            path = dataset_root / Path(row["image_path"])
            with Image.open(path) as image:
                image = image.convert("RGB")
                tensor = self.transform(image)
            label = COMPATIBLE_LABELS[row["ground_truth_label"]][0]
            return tensor, class_index[label]

    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    torch.set_num_threads(min(8, torch.get_num_threads()))
    device = torch.device("cpu")
    generator = torch.Generator().manual_seed(SEED)
    train_loader = DataLoader(
        ImageRows(splits["train"], train_transform), batch_size=BATCH_SIZE,
        shuffle=True, num_workers=0, generator=generator,
    )
    validation_loader = DataLoader(
        ImageRows(splits["validation"], eval_transform), batch_size=BATCH_SIZE,
        shuffle=False, num_workers=0,
    )
    test_loader = DataLoader(
        ImageRows(splits["test"], eval_transform), batch_size=BATCH_SIZE,
        shuffle=False, num_workers=0,
    )

    model = mobilenet_v3_small(weights=None, num_classes=len(classes)).to(device)
    class_counts = Counter(COMPATIBLE_LABELS[r["ground_truth_label"]][0] for r in splits["train"])
    weights = torch.tensor([
        (len(splits["train"]) / max(1, len(classes) * class_counts[label])) ** 0.5
        for label in classes
    ], dtype=torch.float32)
    criterion = nn.CrossEntropyLoss(weight=weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-4, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    artifact_dir = dataset_root / "candidate"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    model_path = artifact_dir / "mobilenet_v3_small_plantdoc.pt"
    best_macro_f1 = -1.0
    best_epoch = 0
    stale_epochs = 0
    epoch_history = []

    def predict_loader(loader, do_train: bool = False):
        truths, predictions = [], []
        total_loss = 0.0
        model.train(do_train)
        context = torch.enable_grad() if do_train else torch.inference_mode()
        with context:
            for images, targets in loader:
                images, targets = images.to(device), targets.to(device)
                if do_train:
                    optimizer.zero_grad(set_to_none=True)
                outputs = model(images)
                loss = criterion(outputs, targets)
                if do_train:
                    loss.backward()
                    optimizer.step()
                total_loss += float(loss.item()) * len(targets)
                truths.extend(targets.cpu().tolist())
                predictions.extend(outputs.argmax(dim=1).cpu().tolist())
        return truths, predictions, total_loss / max(1, len(loader.dataset))

    for epoch in range(1, epochs + 1):
        train_truth, train_pred, train_loss = predict_loader(train_loader, do_train=True)
        val_truth, val_pred, val_loss = predict_loader(validation_loader)
        validation_metrics = classification_metrics(val_truth, val_pred, classes)
        scheduler.step()
        epoch_history.append({
            "epoch": epoch, "train_loss": train_loss, "validation_loss": val_loss,
            "validation_accuracy": validation_metrics["accuracy"],
            "validation_macro_f1": validation_metrics["macro_f1"],
        })
        print(
            f"epoch {epoch:02d}/{epochs} train_loss={train_loss:.4f} "
            f"val_loss={val_loss:.4f} val_macro_f1={validation_metrics['macro_f1']:.4f}",
            flush=True,
        )
        if validation_metrics["macro_f1"] > best_macro_f1:
            best_macro_f1 = validation_metrics["macro_f1"]
            best_epoch = epoch
            stale_epochs = 0
            torch.save({"state_dict": model.state_dict(), "classes": classes}, model_path)
        else:
            stale_epochs += 1
            if stale_epochs >= PATIENCE:
                break

    checkpoint = torch.load(model_path, map_location=device, weights_only=True)
    if checkpoint["classes"] != classes:
        raise RuntimeError("Candidate checkpoint class list changed unexpectedly")
    model.load_state_dict(checkpoint["state_dict"])
    test_truth, test_pred, _ = predict_loader(test_loader)
    candidate_metrics = classification_metrics(test_truth, test_pred, classes)

    # Compare on precisely the same leakage-free, compatible test images using
    # the production ONNX results recorded before model training. No test result
    # feeds training or checkpoint selection.
    baseline_path = dataset_root / "plantdoc-evaluation.json"
    baseline_report = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline_rows = {
        row["image_path"]: row for row in baseline_report["predictions"]
        if row.get("label_mapping_status") == "compatible"
    }
    expected_paths = [r["image_path"] for r in splits["test"]]
    if set(expected_paths) != set(baseline_rows):
        raise ValueError(
            "Production baseline report does not match this candidate test subset; "
            "rerun the pinned PlantDoc production evaluation before training."
        )
    outside_label = "OUTSIDE_CANDIDATE_LABELS"
    comparison_labels = classes + [outside_label]
    baseline_matrix = [[0 for _ in comparison_labels] for _ in classes]
    baseline_truth, baseline_prediction = [], []
    for row in splits["test"]:
        truth_name = COMPATIBLE_LABELS[row["ground_truth_label"]][0]
        baseline_name = baseline_rows[row["image_path"]]["predicted_model_class"]
        true_idx = class_index[truth_name]
        pred_idx = class_index.get(baseline_name, len(classes))
        baseline_matrix[true_idx][pred_idx] += 1
        baseline_truth.append(true_idx)
        baseline_prediction.append(pred_idx)
    baseline_metrics = _metrics_with_outside_column(baseline_matrix, classes, comparison_labels)

    train_test_overlap_paths = [
        r["image_path"] for r in read_manifest(dataset_root)
        if r["split"] == "test" and r["sha256"] in {
            t["sha256"] for t in read_manifest(dataset_root) if t["split"] == "train"
        }
    ]
    report = {
        "candidate": "torchvision MobileNetV3-Small trained from random initialization",
        "candidate_scope": "16 PlantDoc-compatible diseases represented in the leakage-free test split; not a 38-class replacement",
        "dataset_source": baseline_report.get("dataset_source"),
        "dataset_source_revision": baseline_report.get("dataset_source_revision"),
        "training_device": str(device),
        "pretrained_weights": None,
        "class_order": classes,
        "split_counts": {"train": len(splits["train"]), "validation": len(splits["validation"]), "test": len(splits["test"])},
        "test_images_with_hashes_in_train_excluded": len(train_test_overlap_paths),
        "duplicate_conflicts_excluded_from_training": splits["duplicate_conflicts"],
        "extra_exact_duplicate_training_files_excluded": splits["duplicate_train_extra_count"],
        "training_config": {
            "seed": SEED, "max_epochs": epochs, "early_stopping_patience": PATIENCE,
            "batch_size": BATCH_SIZE, "optimizer": "AdamW", "initial_learning_rate": 5e-4,
            "weight_decay": 1e-4, "selection_metric": "validation macro F1",
            "validation_fraction_per_class": VAL_FRACTION,
            "augmentation": ["random resized crop", "horizontal flip", "rotation ±15 degrees", "color jitter"],
            "normalization": {"mean": IMAGENET_MEAN, "std": IMAGENET_STD},
            "evaluation_resize": "RGB bilinear resize to 224x224, then ImageNet normalization",
        },
        "selected_epoch": best_epoch,
        "epoch_history": epoch_history,
        "current_production_model": {
            "name": "EfficientNetV2-S ONNX, 38 outputs",
            **baseline_metrics,
        },
        "candidate_test_metrics": candidate_metrics,
        "candidate_artifact": str(model_path.resolve()),
        "limitations": [
            "Candidate has only 16 output classes represented in this test set and cannot replace the deployed 38-class model.",
            "Small PlantDoc training sample sizes and exact-source overlap with the production model's PlantVillage training data are not independently audited.",
            "Test set was not used for training or checkpoint/threshold selection.",
            "No unsupported-plant/non-leaf negative dataset was available to validate an OOD detector.",
        ],
    }
    report_path = artifact_dir / "evaluation.json"
    report["report_path"] = str(report_path.resolve())
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _metrics_with_outside_column(matrix: list[list[int]], classes: list[str], columns: list[str]) -> dict:
    totals = sum(sum(row) for row in matrix)
    per_class = {}
    for i, label in enumerate(classes):
        tp = matrix[i][i]
        support = sum(matrix[i])
        predicted_count = sum(matrix[row][i] for row in range(len(classes)))
        precision = tp / predicted_count if predicted_count else 0.0
        recall = tp / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {"support": support, "precision": precision, "recall": recall, "f1": f1}
    return {
        "sample_count": totals,
        "accuracy": sum(matrix[i][i] for i in range(len(classes))) / totals if totals else None,
        "macro_precision": float(np.mean([x["precision"] for x in per_class.values()])) if totals else None,
        "macro_recall": float(np.mean([x["recall"] for x in per_class.values()])) if totals else None,
        "macro_f1": float(np.mean([x["f1"] for x in per_class.values()])) if totals else None,
        "per_class": per_class,
        "confusion_matrix": {"labels": columns, "counts": matrix},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    args = parser.parse_args()
    if args.epochs < 1:
        parser.error("--epochs must be positive")
    report = train_and_evaluate(args.dataset_root, epochs=args.epochs)
    print(json.dumps({key: value for key, value in report.items() if key != "epoch_history"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
