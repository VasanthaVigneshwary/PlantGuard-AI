r"""Validate traceable plant-image intake manifests without inferring labels.

Run from the project root with::

    python backend/dataset_manifest.py path\to\manifest.csv

The manifest is CSV; image paths are relative to the manifest file. The JSON
report is printed to stdout. Invalid rows remain in that report with reasons.
"""

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from ml.predict import get_class_names, parse_class_label


REQUIRED_COLUMNS = {
    "image_id", "image_path", "crop", "health_status", "disease_label",
    "label_source", "reviewer", "source_id", "source_url", "license",
    "attribution", "plant_id", "capture_group", "image_source",
    "label_confidence", "review_status", "duplicate_group_id",
}
RIGHTS_PERMISSION_FIELDS = (
    "training_permission",
    "original_image_redistribution",
    "model_weights_redistribution",
)
OPTIONAL_RIGHTS_COLUMNS = {
    *RIGHTS_PERMISSION_FIELDS,
    "rights_evidence",
    "rights_restrictions",
}
PERMISSION_STATUSES = {"allowed", "not_allowed", "unknown"}
HEALTH_STATES = {"healthy", "diseased", "unknown"}
IMAGE_SOURCES = {"controlled_dataset", "field_photograph"}
REVIEW_STATUSES = {"confirmed", "reviewed", "unreviewed", "unknown"}
CONFIDENCE_VALUES = {"high", "medium", "low", "unknown"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def _image_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _supported_labels() -> tuple[dict[str, set[str]], dict[str, tuple[str, bool]]]:
    labels = get_class_names()
    crop_labels: dict[str, set[str]] = defaultdict(set)
    parsed = {}
    for label in labels:
        crop, condition, healthy = parse_class_label(label)
        crop_labels[crop].add(label)
        parsed[label] = (crop, healthy)
    return crop_labels, parsed


def validate_manifest(manifest_path: Path) -> dict:
    """Return an actionable validation/readiness report for a CSV manifest."""
    manifest_path = manifest_path.resolve()
    report = {
        "manifest": str(manifest_path),
        "record_count": 0,
        "valid_count": 0,
        "invalid_count": 0,
        "manifest_issues": [],
        "records": [],
        "readiness": {},
    }
    if not manifest_path.is_file():
        report["manifest_issues"].append(f"Manifest does not exist: {manifest_path}")
        return report

    try:
        with manifest_path.open("r", newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            columns = set(reader.fieldnames or [])
            missing_columns = sorted(REQUIRED_COLUMNS - columns)
            if missing_columns:
                report["manifest_issues"].append(
                    "Missing required CSV columns: " + ", ".join(missing_columns)
                )
                return report
            rows = [
                row for row in reader
                if not ((row.get("image_id") or "").lstrip().startswith("#"))
            ]
    except (OSError, UnicodeError, csv.Error) as error:
        report["manifest_issues"].append(f"Cannot read CSV manifest: {error}")
        return report

    if not rows:
        report["manifest_issues"].append("Manifest contains no image records")
        return report

    crop_labels, parsed_labels = _supported_labels()
    seen_ids: dict[str, int] = {}
    hashes: dict[str, list[int]] = defaultdict(list)
    for row_number, raw in enumerate(rows, start=2):
        row = {key: (value or "").strip() for key, value in raw.items() if key is not None}
        issues = []
        warnings = []
        rights_columns_present = OPTIONAL_RIGHTS_COLUMNS.issubset(columns)
        for field in RIGHTS_PERMISSION_FIELDS:
            value = row.get(field, "").strip().lower() or "unknown"
            row[field] = value
            if value not in PERMISSION_STATUSES:
                issues.append(
                    f"{field} must be allowed, not_allowed, or unknown; permission is never inferred"
                )
            elif value == "unknown":
                warnings.append(f"{field} is unknown; do not use this record for that purpose")
            elif value in {"allowed", "not_allowed"}:
                if not row.get("rights_evidence", "").strip():
                    issues.append(f"rights_evidence is required when {field} is {value}")
                if not row.get("rights_restrictions", "").strip():
                    issues.append(
                        f"rights_restrictions is required when {field} is {value}; "
                        "record conditions or explicitly state none were identified"
                    )
        if not rights_columns_present:
            warnings.append(
                "legacy manifest has no explicit rights fields; all use permissions default to unknown"
            )
        image_id = row.get("image_id", "")
        if not image_id:
            issues.append("image_id is required")
        elif image_id in seen_ids:
            issues.append(f"duplicate image_id; first seen on CSV row {seen_ids[image_id]}")
        else:
            seen_ids[image_id] = row_number

        relative = row.get("image_path", "")
        image_path = (manifest_path.parent / relative).resolve() if relative else None
        digest = None
        if not relative:
            issues.append("image_path is required")
        elif Path(relative).is_absolute() or not image_path.is_relative_to(manifest_path.parent):
            issues.append("image_path must be relative and remain inside the manifest directory")
        elif not image_path.is_file():
            issues.append(f"image file does not exist: {relative}")
        elif image_path.suffix.lower() not in IMAGE_SUFFIXES:
            issues.append(f"unsupported image extension: {image_path.suffix or '(none)'}")
        else:
            try:
                with Image.open(image_path) as image:
                    image.verify()
                digest = _image_digest(image_path)
                hashes[digest].append(len(report["records"]))
            except (OSError, UnidentifiedImageError, ValueError) as error:
                issues.append(f"invalid image file: {error}")

        crop = row.get("crop", "")
        if not crop:
            issues.append("crop is required")
        elif crop not in crop_labels:
            issues.append(f"unsupported crop for this model: {crop}")

        status = row.get("health_status", "").lower()
        if status not in HEALTH_STATES:
            issues.append("health_status must be healthy, diseased, or unknown")

        disease_label = row.get("disease_label", "")
        label_status = row.get("review_status", "").lower()
        if label_status not in REVIEW_STATUSES:
            issues.append("review_status must be confirmed, reviewed, unreviewed, or unknown")
        if status in {"healthy", "diseased"} and label_status not in {"confirmed", "reviewed"}:
            issues.append("healthy/diseased labels must be confirmed or reviewed; retain pending labels as unknown")
        if status == "healthy":
            if disease_label:
                issues.append("healthy record has a contradictory disease_label; it must be blank")
        elif status == "diseased":
            disease_info = parsed_labels.get(disease_label) if disease_label else None
            if not disease_label:
                warnings.append(
                    "disease identity is unknown; record is usable for health-status evaluation only"
                )
            elif disease_info is None:
                warnings.append(
                    f"unsupported disease_label for this model taxonomy: {disease_label}; "
                    "record remains usable for health-status evaluation only"
                )
            elif disease_info[1]:
                issues.append("diseased record has a contradictory healthy disease_label")
            elif disease_info[0] != crop:
                issues.append("disease_label belongs to a different crop")
            if label_status not in {"confirmed", "reviewed"}:
                issues.append("diseased record requires a confirmed/reviewed disease label")
        elif status == "unknown" and disease_label:
            issues.append("unknown health status must not carry an inferred disease_label")

        if not row.get("label_source"):
            issues.append("label_source is required; record how the label was established")
        if label_status in {"confirmed", "reviewed"} and not row.get("reviewer"):
            issues.append("reviewer is required for confirmed/reviewed labels")
        confidence = row.get("label_confidence", "").lower()
        if confidence not in CONFIDENCE_VALUES:
            try:
                numeric_confidence = float(confidence)
                if not 0 <= numeric_confidence <= 1:
                    raise ValueError
            except (TypeError, ValueError):
                issues.append("label_confidence must be high/medium/low/unknown or a number from 0 to 1")
        source_id = row.get("source_id", "").lower()
        source_url = row.get("source_url", "").lower()
        if (not source_id or source_id in {"unknown", "unresolved", "n/a"}) and (
            not source_url or source_url in {"unknown", "unresolved", "n/a"}
        ):
            issues.append("source_id or source_url is required")
        for field in ("license", "attribution"):
            value = row.get(field, "").strip().lower()
            if not value or value in {"unknown", "unresolved", "n/a"}:
                issues.append(f"{field} is required; unresolved metadata cannot be treated as complete")
        if row.get("image_source", "").lower() not in IMAGE_SOURCES:
            issues.append("image_source must be controlled_dataset or field_photograph")

        report["records"].append({
            "csv_row": row_number,
            "image_id": image_id,
            "image_path": relative,
            "sha256": digest,
            "duplicate_group_id": row.get("duplicate_group_id", ""),
            "valid": not issues,
            "issues": issues,
            "warnings": warnings,
            "record": row,
        })

    for duplicate_indices in hashes.values():
        if len(duplicate_indices) > 1:
            for index in duplicate_indices:
                report["records"][index]["issues"].append(
                    "duplicate exact image SHA-256; assign one duplicate group and retain one intake copy"
                )
                report["records"][index]["valid"] = False

    valid_records = [item for item in report["records"] if item["valid"]]
    report["record_count"] = len(rows)
    report["valid_count"] = len(valid_records)
    report["invalid_count"] = len(rows) - len(valid_records)

    health_counts: dict[str, Counter] = defaultdict(Counter)
    disease_counts: Counter = Counter()
    source_counts: Counter = Counter()
    license_counts: Counter = Counter()
    review_counts: Counter = Counter()
    confidence_counts: Counter = Counter()
    group_ids = set()
    plant_ids = set()
    capture_groups = set()
    for item in valid_records:
        row = item["record"]
        crop, status = row["crop"], row["health_status"].lower()
        health_counts[crop][status] += 1
        if status == "diseased":
            disease_label = row.get("disease_label", "")
            if disease_label in parsed_labels and not parsed_labels[disease_label][1]:
                disease_counts[disease_label] += 1
        source_counts[row["image_source"].lower()] += 1
        license_counts[row["license"]] += 1
        review_counts[row["review_status"].lower()] += 1
        confidence_counts[row["label_confidence"].lower()] += 1
        if row.get("duplicate_group_id"):
            group_ids.add(row["duplicate_group_id"])
        elif item.get("sha256"):
            group_ids.add(item["sha256"])
        if row.get("plant_id"):
            plant_ids.add(row["plant_id"])
        if row.get("capture_group"):
            capture_groups.add(row["capture_group"])

    crop_readiness = {}
    for crop in sorted(crop_labels):
        counts = health_counts[crop]
        crop_readiness[crop] = {
            "healthy": counts["healthy"],
            "diseased": counts["diseased"],
            "unknown": counts["unknown"],
            "disease_classes": {
                label: disease_counts[label]
                for label in sorted(crop_labels[crop])
                if label in disease_counts and not parsed_labels[label][1]
            },
            "binary_coverage": "both" if counts["healthy"] and counts["diseased"] else (
                "healthy_missing" if not counts["healthy"] and counts["diseased"] else (
                    "diseased_missing" if counts["healthy"] and not counts["diseased"] else "neither"
                )
            ),
            "sample_size_note": "Counts are descriptive; no statistical sufficiency threshold is asserted.",
        }
    report["readiness"] = {
        "valid_label_counts_by_crop": crop_readiness,
        "disease_class_counts": dict(sorted(disease_counts.items())),
        "diseased_without_supported_exact_class": sum(
            1 for item in valid_records
            if item["record"]["health_status"].lower() == "diseased"
            and item["record"].get("disease_label", "") not in parsed_labels
        ),
        "image_source_counts": dict(source_counts),
        "license_counts": dict(license_counts),
        "review_status_counts": dict(review_counts),
        "label_confidence_counts": dict(confidence_counts),
        "rights_permission_counts": {
            field: dict(Counter(
                item["record"].get(field, "unknown")
                for item in report["records"]
            ))
            for field in RIGHTS_PERMISSION_FIELDS
        },
        "source_complete_records": sum(
            bool(item["record"].get("source_id") or item["record"].get("source_url"))
            for item in report["records"]
        ),
        "license_complete_records": sum(
            bool(item["record"].get("license")) and
            item["record"].get("license", "").lower() not in {"unknown", "unresolved", "n/a"}
            for item in report["records"]
        ),
        "attribution_complete_records": sum(
            bool(item["record"].get("attribution")) and
            item["record"].get("attribution", "").lower() not in {"unknown", "unresolved", "n/a"}
            for item in report["records"]
        ),
        "distinct_duplicate_or_exact_hash_groups": len(group_ids),
        "distinct_plant_ids": len(plant_ids),
        "distinct_capture_groups": len(capture_groups),
        "exact_hash_duplicate_images": sum(max(0, len(indices) - 1) for indices in hashes.values()),
        "invalid_record_count_included_for_audit": report["invalid_count"],
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--report", type=Path, help="Optional JSON output path; existing files are never overwritten")
    args = parser.parse_args()
    report = validate_manifest(args.manifest)
    serialized = json.dumps(report, indent=2, ensure_ascii=False)
    if args.report:
        try:
            with args.report.open("x", encoding="utf-8") as stream:
                stream.write(serialized + "\n")
        except FileExistsError:
            parser.error(f"report already exists; refusing to overwrite: {args.report}")
    print(serialized)
    return 1 if report["manifest_issues"] or report["invalid_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
