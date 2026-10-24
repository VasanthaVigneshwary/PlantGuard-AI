"""Prepare and evaluate the official PlantDoc archive without altering its labels.

Run preparation with:
  python backend/plantdoc_dataset.py prepare datasets/plantdoc-source.zip datasets/plantdoc
Run evaluation with:
  python backend/plantdoc_dataset.py evaluate datasets/plantdoc

The archive's train/test folders remain separate. Filename changes are limited to
Windows-incompatible/colliding names and are traced back in manifest.jsonl.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

from PIL import Image, UnidentifiedImageError

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))
from ml.predict import get_class_names, predict_disease  # noqa: E402

SOURCE_URL = "https://github.com/pratikkayal/PlantDoc-Dataset"
REPO_LICENSE = "CC BY 4.0"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
ARCHIVE_ROOT = "PlantDoc-Dataset-master"

# A mapping exists only for crop/disease labels that have a direct equivalent in
# the active model. Generic leaf labels are deliberately not called healthy.
COMPATIBLE_LABELS = {
    "Apple Scab Leaf": ("Apple___Apple_scab", "Apple scab"),
    "Apple rust leaf": ("Apple___Cedar_apple_rust", "Apple cedar apple rust"),
    "Bell_pepper leaf spot": ("Pepper,_bell___Bacterial_spot", "Bell pepper bacterial spot"),
    "Corn Gray leaf spot": ("Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot", "Corn gray leaf spot"),
    "Corn rust leaf": ("Corn_(maize)___Common_rust_", "Corn common rust"),
    "Potato leaf early blight": ("Potato___Early_blight", "Potato early blight"),
    "Potato leaf late blight": ("Potato___Late_blight", "Potato late blight"),
    "Squash Powdery mildew leaf": ("Squash___Powdery_mildew", "Squash powdery mildew"),
    "Tomato Early blight leaf": ("Tomato___Early_blight", "Tomato early blight"),
    "Tomato Septoria leaf spot": ("Tomato___Septoria_leaf_spot", "Tomato Septoria leaf spot"),
    "Tomato leaf bacterial spot": ("Tomato___Bacterial_spot", "Tomato bacterial spot"),
    "Tomato leaf late blight": ("Tomato___Late_blight", "Tomato late blight"),
    "Tomato leaf mosaic virus": ("Tomato___Tomato_mosaic_virus", "Tomato mosaic virus"),
    "Tomato leaf yellow virus": ("Tomato___Tomato_Yellow_Leaf_Curl_Virus", "Tomato yellow leaf curl virus"),
    "Tomato mold leaf": ("Tomato___Leaf_Mold", "Tomato leaf mold"),
    "Tomato two spotted spider mites leaf": (
        "Tomato___Spider_mites Two-spotted_spider_mite", "Tomato two-spotted spider mites"
    ),
    "grape leaf black rot": ("Grape___Black_rot", "Grape black rot"),
}
AMBIGUOUS_LABELS = {
    "Apple leaf": "Disease/healthy status is not specified.",
    "Bell_pepper leaf": "Disease/healthy status is not specified.",
    "Blueberry leaf": "Disease/healthy status is not specified.",
    "Cherry leaf": "Disease/healthy status is not specified.",
    "Corn leaf blight": "The label does not identify which corn blight; multiple conditions are possible.",
    "Peach leaf": "Disease/healthy status is not specified.",
    "Raspberry leaf": "Disease/healthy status is not specified.",
    "Soyabean leaf": "Disease/healthy status is not specified.",
    "Strawberry leaf": "Disease/healthy status is not specified.",
    "Tomato leaf": "Disease/healthy status is not specified.",
    "grape leaf": "Disease/healthy status is not specified.",
}


def _portable_component(value: str) -> str:
    # Encode forbidden Windows characters byte-wise; retain ordinary Unicode.
    forbidden = set('<>:"/\\|?*')
    return "".join(f"%{ord(char):02X}" if char in forbidden or ord(char) < 32 else char for char in value)


def _portable_path(parts: tuple[str, ...]) -> PurePosixPath:
    safe_parts = [_portable_component(part) for part in parts]
    # Stay comfortably below legacy Windows MAX_PATH even for deeply nested
    # absolute workspace paths. Manifest retains the untouched source path.
    for i in range(len(safe_parts) - 1, 0, -1):
        part = safe_parts[i]
        if len(part) > 100:
            digest = hashlib.sha1("/".join(parts).encode("utf-8")).hexdigest()[:12]
            suffix = Path(part).suffix
            safe_parts[i] = f"{part[:24]}~{digest}{suffix}"
    return PurePosixPath(*safe_parts)


def _entry_relative(name: str) -> PurePosixPath | None:
    path = PurePosixPath(name)
    if len(path.parts) < 2 or path.parts[0] != ARCHIVE_ROOT:
        return None
    rel = PurePosixPath(*path.parts[1:])
    if rel.is_absolute() or any(part in {"", ".", ".."} for part in rel.parts):
        raise ValueError(f"Unsafe archive path: {name}")
    return rel


def prepare(zip_path: Path, destination: Path) -> dict:
    if not zip_path.is_file():
        raise FileNotFoundError(zip_path)
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"Refusing to overwrite non-empty dataset directory: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"ZIP CRC check failed at {bad}")
        file_infos = []
        for info in archive.infolist():
            rel = _entry_relative(info.filename)
            if rel is None or info.is_dir():
                continue
            if rel.parts[0] not in {"train", "test"}:
                # Keep official README, license, and citation at dataset root.
                if len(rel.parts) == 1:
                    file_infos.append((info, rel, None))
                continue
            safe = _portable_path(rel.parts)
            file_infos.append((info, rel, safe))

        # Windows paths that differ only by case cannot coexist. Disambiguate
        # every member of a collision group deterministically using source path.
        groups: dict[str, list[int]] = {}
        for i, (_, _, safe) in enumerate(file_infos):
            if safe is not None:
                groups.setdefault(str(safe).casefold(), []).append(i)
        adjusted: dict[int, PurePosixPath] = {}
        for indexes in groups.values():
            if len(indexes) > 1:
                for i in indexes:
                    _, original, safe = file_infos[i]
                    digest = hashlib.sha1(str(original).encode("utf-8")).hexdigest()[:8]
                    adjusted[i] = safe.with_name(f"{safe.stem}~{digest}{safe.suffix}")

        rows = []
        extracted = 0
        for i, (info, original, safe) in enumerate(file_infos):
            if safe is None:
                safe = PurePosixPath(_portable_component(original.name))
            else:
                safe = adjusted.get(i, safe)
            out = destination.joinpath(*safe.parts)
            out.parent.mkdir(parents=True, exist_ok=True)
            payload = archive.read(info)
            out.write_bytes(payload)
            extracted += 1
            if safe.parts[0] not in {"train", "test"}:
                continue
            split = safe.parts[0]
            label = original.parts[1]
            width = height = None
            error = None
            digest = hashlib.sha256(payload).hexdigest()
            try:
                with Image.open(out) as im:
                    im.verify()
                with Image.open(out) as im:
                    width, height = im.size
                    im.load()
            except (OSError, ValueError, UnidentifiedImageError) as exc:
                error = f"{type(exc).__name__}: {exc}"
            rows.append({
                "image_path": safe.as_posix(),
                "source_archive_path": info.filename,
                "ground_truth_label": label,
                "source": SOURCE_URL,
                "split": split,
                "width": width,
                "height": height,
                "sha256": digest,
                "loading_error": error,
                "filename_adjusted_for_windows": str(safe) != str(original),
            })

    manifest = destination / "manifest.jsonl"
    with manifest.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    attribution = destination / "ATTRIBUTION.txt"
    attribution.write_text(
        "PlantDoc Dataset by Davinder Singh, Naman Jain, Pranjali Jain, Pratik Kayal, "
        "Sudhakar Kumawat, and Nipun Batra\n"
        f"Source: {SOURCE_URL}\nLicense: {REPO_LICENSE} (https://creativecommons.org/licenses/by/4.0/)\n"
        "This local copy retains the repository's train/test folders and class-folder labels. "
        "Image contents are unchanged. Some filenames were percent-encoded or suffixed to "
        "avoid Windows-invalid names and case-insensitive collisions; manifest.jsonl records "
        "the original archive path and this adjustment.\n"
        "Please retain creator attribution, the license link, and notice of modifications.\n",
        encoding="utf-8",
    )
    split_counts = Counter(row["split"] for row in rows)
    loading_errors = sum(row["loading_error"] is not None for row in rows)
    return {
        "dataset_root": str(destination.resolve()),
        "image_count": len(rows),
        "split_counts": dict(split_counts),
        "non_image_files_extracted": extracted - len(rows),
        "loading_errors": loading_errors,
        "manifest": str(manifest.resolve()),
        "license": REPO_LICENSE,
    }


def label_audit(labels: list[str], model_classes: list[str]) -> dict:
    audit = {"exact": [], "compatible": [], "ambiguous": [], "unsupported": []}
    for label in labels:
        if label in model_classes:
            audit["exact"].append({"plantdoc_label": label, "model_class": label})
        elif label in COMPATIBLE_LABELS:
            model_class, rationale = COMPATIBLE_LABELS[label]
            if model_class not in model_classes:
                audit["unsupported"].append({"plantdoc_label": label, "reason": "Mapped model class absent"})
            else:
                audit["compatible"].append({
                    "plantdoc_label": label, "model_class": model_class, "rationale": rationale,
                })
        elif label in AMBIGUOUS_LABELS:
            audit["ambiguous"].append({"plantdoc_label": label, "reason": AMBIGUOUS_LABELS[label]})
        else:
            audit["unsupported"].append({
                "plantdoc_label": label,
                "reason": "No direct crop-and-condition equivalent defined in the 38 model classes.",
            })
    return audit


def evaluate(dataset_root: Path) -> dict:
    manifest_path = dataset_root / "manifest.jsonl"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing manifest: {manifest_path}; run prepare first")
    rows = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    classes = get_class_names()
    class_index = {name: i for i, name in enumerate(classes)}
    labels = sorted({row["ground_truth_label"] for row in rows})
    audit = label_audit(labels, classes)
    mapping = {item["plantdoc_label"]: item["model_class"] for item in audit["exact"] + audit["compatible"]}
    covered_model_classes = sorted(set(mapping.values()))
    test_rows = [r for r in rows if r["split"] == "test"]
    train_hashes = {r["sha256"] for r in rows if r["split"] == "train"}
    overlap_test_rows = [r for r in test_rows if r["sha256"] in train_hashes]
    confusion = [[0 for _ in classes] for _ in classes]
    failures = []
    predictions = []
    metric_count = 0
    metric_correct = 0
    for row in test_rows:
        path = dataset_root / Path(row["image_path"])
        has_compatible_label = row["ground_truth_label"] in mapping
        truth = mapping.get(row["ground_truth_label"])
        if row["loading_error"]:
            failures.append({"image_path": row["image_path"], "ground_truth_label": row["ground_truth_label"], "error": row["loading_error"]})
            continue
        try:
            result = predict_disease(path, top_k=5)
            predicted = result["disease"]
            if predicted not in class_index:
                raise RuntimeError(f"Pipeline returned unknown class: {predicted}")
            overlaps_training = row["sha256"] in train_hashes
            if has_compatible_label and not overlaps_training:
                confusion[class_index[truth]][class_index[predicted]] += 1
                metric_count += 1
                metric_correct += int(truth == predicted)
            predictions.append({
                "image_path": row["image_path"], "ground_truth_label": row["ground_truth_label"],
                "ground_truth_model_class": truth,
                "label_mapping_status": "compatible" if has_compatible_label and not overlaps_training else "excluded",
                "metric_exclusion_reason": "duplicate image hash in train split" if overlaps_training else (
                    None if has_compatible_label else "ambiguous or unsupported PlantDoc label"
                ),
                "predicted_model_class": predicted,
                "top_predictions": result.get("top_predictions", []),
                "uncalibrated_score_percent": result.get("confidence"),
            })
        except Exception as exc:  # record per-image failures and finish the complete set
            failures.append({
                "image_path": row["image_path"], "ground_truth": truth,
                "error": f"{type(exc).__name__}: {exc}",
            })
    per_class = {}
    supported_truth = {
        mapping[r["ground_truth_label"]] for r in test_rows
        if r["ground_truth_label"] in mapping and r["sha256"] not in train_hashes
    }
    for i, label in enumerate(classes):
        support = sum(confusion[i])
        predicted_count = sum(row[i] for row in confusion)
        if label in supported_truth:
            per_class[label] = {
                "support": support,
                "precision": confusion[i][i] / predicted_count if predicted_count else 0.0,
                "recall": confusion[i][i] / support if support else 0.0,
            }
    split_paths = {split: {r["sha256"] for r in rows if r["split"] == split} for split in ("train", "test")}
    overlap = sorted(split_paths["train"] & split_paths["test"])
    excluded = Counter(r["ground_truth_label"] for r in test_rows if r["ground_truth_label"] not in mapping)
    report = {
        "dataset_source": SOURCE_URL,
        "dataset_root": str(dataset_root.resolve()),
        "evaluation_split": "test only; original train images were not evaluated or used for training/tuning",
        "test_image_count": len(test_rows),
        "test_images_with_compatible_labels": sum(r["ground_truth_label"] in mapping for r in test_rows),
        "usable_test_images_inferred": len(predictions),
        "usable_images_in_compatible_metric_subset": metric_count,
        "test_images_with_hashes_also_in_train": len(overlap_test_rows),
        "test_images_excluded_for_train_overlap": len(overlap_test_rows),
        "evaluation_failures": failures,
        "accuracy": metric_correct / metric_count if metric_count else None,
        "per_class_precision_recall": per_class,
        "confusion_matrix": {"labels": classes, "counts": confusion},
        "label_coverage": audit,
        "model_classes_covered_by_plantdoc_labels": covered_model_classes,
        "model_classes_without_compatible_plantdoc_label": sorted(set(classes) - set(covered_model_classes)),
        "excluded_test_images_by_label": dict(excluded),
        "train_test_sha256_overlap_count": len(overlap),
        "train_test_sha256_overlap": overlap,
        "predictions": predictions,
        "limitations": [
            "Metrics cover only the explicitly compatible PlantDoc test labels, not all 38 model classes or all diseases.",
            "The existing model card identifies PlantVillage training data; PlantDoc is a distinct source, but exact training-image overlap has not been independently audited.",
            "Raw scores are uncalibrated and do not establish that an image is supported or a prediction is reliable.",
        ],
    }
    (dataset_root / "plantdoc-evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p_prepare = sub.add_parser("prepare", help="extract and verify the official ZIP, then write manifest")
    p_prepare.add_argument("zip_path", type=Path)
    p_prepare.add_argument("destination", type=Path)
    p_evaluate = sub.add_parser("evaluate", help="evaluate the original test split on mapped disease labels")
    p_evaluate.add_argument("dataset_root", type=Path)
    args = parser.parse_args()
    try:
        result = prepare(args.zip_path, args.destination) if args.command == "prepare" else evaluate(args.dataset_root)
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
        parser.error(str(exc))
    if args.command == "evaluate":
        summary = {key: value for key, value in result.items() if key != "predictions" and key != "confusion_matrix"}
        summary["report_file"] = str((args.dataset_root / "plantdoc-evaluation.json").resolve())
        print(json.dumps(summary, indent=2))
    else:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
