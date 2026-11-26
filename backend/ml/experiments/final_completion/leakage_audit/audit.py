"""Read-only evidence inventory and exact split-overlap audit for Plant Guard AI.

Run from any directory with:
  .venv.stage3/Scripts/python.exe backend/ml/experiments/final_completion/leakage_audit/audit.py

The script reads existing artifacts only. It does not extract or alter datasets,
models, manifests, database records, or Stage 4 evaluation results.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
STAGE3 = ROOT / "backend/ml/experiments/stage3_preflight"
MODEL_DIR = ROOT / "backend/ml/models"
RESULTS = ROOT / "backend/ml/experiments/final_completion/recovery/colab_results"
DOWNLOADS = Path(r"C:\Users\Varsh\Downloads")
ONEDRIVE_SCREENSHOTS = Path(r"C:\Users\Varsh\OneDrive\Pictures\Screenshots")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def record_inventory(item: str, path: Path, notes: str, *, hash_file: bool = True,
                     missing_status: str = "MISSING") -> dict[str, str]:
    rec = {
        "item": item,
        "status": "FOUND" if path.is_file() else missing_status,
        "path": str(path),
        "size_bytes": "",
        "modified_local": "",
        "sha256": "",
        "notes": notes,
    }
    if path.is_file():
        stat = path.stat()
        rec["size_bytes"] = str(stat.st_size)
        rec["modified_local"] = datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds")
        if hash_file:
            rec["sha256"] = sha256(path)
    return rec


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        digest = row.get("sha256", "").strip().lower()
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError(f"Missing/invalid SHA-256 in {path}: {row.get('member', '<unknown>')}")
    return rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    test_path = STAGE3 / "plantvillage_test.csv"
    train_path = STAGE3 / "plantvillage_train.csv"
    val_path = STAGE3 / "plantvillage_validation.csv"
    audit_path = STAGE3 / "plantvillage_manifest_audit.json"
    classes_path = MODEL_DIR / "classes.json"
    class_names_path = MODEL_DIR / "class_names.txt"
    test, train, val = map(read_manifest, (test_path, train_path, val_path))
    classes = json.loads(classes_path.read_text(encoding="utf-8"))["classes"]
    split_audit = json.loads(audit_path.read_text(encoding="utf-8"))

    for name, rows, expected in (("test", test, "test"), ("train", train, "train"), ("validation", val, "validation")):
        wrong = sum(row.get("split") != expected for row in rows)
        if wrong:
            raise ValueError(f"{name} manifest has {wrong} rows with unexpected split labels")
        if not {row["class_name"] for row in rows}.issubset(set(classes)):
            raise ValueError(f"{name} manifest contains a label outside classes.json")
        if len({row["member"] for row in rows}) != len(rows):
            raise ValueError(f"{name} manifest has duplicate archive-member paths")

    class_names_lines = [line.strip().split(": ", 1)[-1] for line in class_names_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    class_order_matches = classes == class_names_lines
    if len(classes) != 38 or not class_order_matches:
        raise ValueError("The production class map does not contain the approved matching 38-class order")

    result_json_path = RESULTS / "colab_onnx_evaluation.json"
    result_data = json.loads(result_json_path.read_text(encoding="utf-8"))
    result_summary = result_data["summary"]
    with (RESULTS / "colab_onnx_confusion_matrix.csv").open("r", encoding="utf-8-sig", newline="") as f:
        cm_reader = csv.reader(f)
        cm_rows = list(cm_reader)
    cm_headers = cm_rows[0][1:]
    cm_labels = [row[0] for row in cm_rows[1:]]
    cm = [[int(value) for value in row[1:]] for row in cm_rows[1:]]
    cm_total = sum(sum(row) for row in cm)
    cm_diagonal = sum(cm[i][i] for i in range(min(len(cm), len(cm[0]) if cm else 0)))
    cm_off_diagonal = cm_total - cm_diagonal
    test_supports = Counter(row["class_name"] for row in test)
    cm_supports_match = len(cm) == 38 and all(sum(cm[i]) == test_supports[label] for i, label in enumerate(classes))
    per_class_rows = list(csv.DictReader((RESULTS / "colab_onnx_per_class_metrics.csv").open("r", encoding="utf-8-sig", newline="")))
    per_class_all_perfect = len(per_class_rows) == 38 and all(
        row["class_name"] == classes[i]
        and float(row["precision"]) == 1.0
        and float(row["recall"]) == 1.0
        and float(row["f1-score"]) == 1.0
        for i, row in enumerate(per_class_rows)
    )
    eval_bundle_consistent = (
        result_summary.get("images") == 8154
        and result_summary.get("classes") == 38
        and result_summary.get("accuracy") == 1.0
        and cm_headers == classes
        and cm_labels == classes
        and cm_total == 8154
        and cm_diagonal == 8154
        and cm_off_diagonal == 0
        and cm_supports_match
        and per_class_all_perfect
    )

    comparisons: list[dict[str, object]] = []
    matched_hash_test_images: set[str] = set()
    for reference_name, reference_rows, reference_path in (
        ("Stage3 generated train split", train, train_path),
        ("Stage3 generated validation split", val, val_path),
    ):
        ref_by_hash: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in reference_rows:
            ref_by_hash[row["sha256"].lower()].append(row)
        for row in test:
            for ref in ref_by_hash.get(row["sha256"].lower(), []):
                matched_hash_test_images.add(row["member"])
                comparisons.append({
                    "comparison": f"test_vs_{reference_name.lower().replace(' ', '_')}",
                    "match_type": "exact_sha256",
                    "test_member": row["member"],
                    "reference_member": ref["member"],
                    "test_sha256": row["sha256"],
                    "reference_sha256": ref["sha256"],
                    "hamming_distance": "",
                    "result": "EXACT_MATCH",
                })
        test_paths = {row["member"] for row in test}
        for ref in reference_rows:
            if ref["member"] in test_paths:
                comparisons.append({
                    "comparison": f"test_vs_{reference_name.lower().replace(' ', '_')}",
                    "match_type": "archive_member_path",
                    "test_member": ref["member"],
                    "reference_member": ref["member"],
                    "test_sha256": next(x["sha256"] for x in test if x["member"] == ref["member"]),
                    "reference_sha256": ref["sha256"],
                    "hamming_distance": "",
                    "result": "PATH_MATCH",
                })
        comparisons.append({
            "comparison": f"test_vs_{reference_name.lower().replace(' ', '_')}",
            "match_type": "summary",
            "test_member": "",
            "reference_member": "",
            "test_sha256": "",
            "reference_sha256": "",
            "hamming_distance": "",
            "result": f"{len(test)} test rows checked against {len(reference_rows)} reference rows; exact overlapping test images={sum(1 for row in test if row['sha256'].lower() in ref_by_hash)}; path overlaps={len(test_paths.intersection(r['member'] for r in reference_rows))}",
        })

    phash_modules = [name for name in ("imagehash", "imagededup", "cv2", "phash") if importlib.util.find_spec(name)]
    comparisons.append({
        "comparison": "test_vs_Stage3_generated_train_and_validation",
        "match_type": "perceptual_hash_availability",
        "test_member": "",
        "reference_member": "",
        "test_sha256": "",
        "reference_sha256": "",
        "hamming_distance": "",
        "result": "NOT_RUN; installed candidates: " + (", ".join(phash_modules) if phash_modules else "none of imagehash, imagededup, cv2, phash"),
    })
    write_csv(OUT / "train_test_overlap.csv", [
        "comparison", "match_type", "test_member", "reference_member", "test_sha256", "reference_sha256", "hamming_distance", "result"
    ], comparisons)

    # Detect exact duplicate groups and whether any group crosses the three saved splits.
    all_rows = [("train", r) for r in train] + [("validation", r) for r in val] + [("test", r) for r in test]
    groups: dict[str, list[tuple[str, dict[str, str]]]] = defaultdict(list)
    for split_name, row in all_rows:
        groups[row["sha256"].lower()].append((split_name, row))
    exact_duplicate_groups = [(h, g) for h, g in groups.items() if len(g) > 1]
    cross_split_duplicate_groups = [(h, g) for h, g in exact_duplicate_groups if len({s for s, _ in g}) > 1]
    duplicate_rows: list[dict[str, object]] = []
    for digest, members in exact_duplicate_groups:
        group_id = digest[:16]
        split_names = sorted({split_name for split_name, _ in members})
        class_names = sorted({row["class_name"] for _, row in members})
        for split_name, row in members:
            duplicate_rows.append({
                "group_id": group_id,
                "sha256": digest,
                "split": split_name,
                "class_name": row["class_name"],
                "archive_member": row["member"],
                "group_size": len(members),
                "group_splits": ";".join(split_names),
                "group_classes": ";".join(class_names),
                "cross_split": len(split_names) > 1,
            })
    write_csv(OUT / "exact_duplicate_groups.csv", [
        "group_id", "sha256", "split", "class_name", "archive_member", "group_size", "group_splits", "group_classes", "cross_split"
    ], duplicate_rows)

    inv: list[dict[str, str]] = []
    def add(item: str, relpath: str, notes: str, *, absolute: Path | None = None,
            status: str = "MISSING", hash_file: bool = True) -> None:
        p = absolute if absolute is not None else ROOT / relpath
        inv.append(record_inventory(item, p, notes, hash_file=hash_file, missing_status=status))

    add("Colab-referenced 8,154-image PlantVillage test manifest", "backend/ml/experiments/stage3_preflight/plantvillage_test.csv", "Current deterministic Stage 3 manifest used by the Colab notebook; this does not prove original model-training membership.")
    add("Stage3 generated train manifest", "backend/ml/experiments/stage3_preflight/plantvillage_train.csv", "Generated seed-42 split; not recovered original training membership.")
    add("Stage3 generated validation manifest", "backend/ml/experiments/stage3_preflight/plantvillage_validation.csv", "Generated seed-42 split; not recovered original training membership.")
    add("Stage3 manifest audit", "backend/ml/experiments/stage3_preflight/plantvillage_manifest_audit.json", f"Recorded {split_audit.get('total_images')} images/38 classes; cross-split exact hashes={split_audit.get('cross_split_exact_hashes')}.")
    add("Original run train membership manifest", "backend/ml/experiments/final_completion/recovery/source/train_manifest.csv", "No original run membership file found in the searched accessible locations.")
    add("Original run validation membership manifest", "backend/ml/experiments/final_completion/recovery/source/validation_manifest.csv", "No original run membership file found in the searched accessible locations.")
    add("PlantVillage dataset archive", "datasets/plantvillage-source.zip", "Preserved source archive; SHA-256 is computed by this script. Image payload manifest hashes were produced from ZIP members in the prior Stage 3 audit.")
    add("PlantVillage extracted folder", "datasets/plantvillage/raw/color", "No extracted tree expected; the preserved dataset is ZIP-backed.", status="NOT EXTRACTED")
    add("Production ONNX model", "backend/ml/models/efficientnet_v2_s_best.onnx", "Current production artifact; ONNX graph structurally matches torchvision EfficientNetV2-S, but this alone does not identify the Colab bytes.")
    add("ONNX external tensor data", "backend/ml/models/efficientnet_v2_s_best.onnx.data", "Required external tensor data for the current production model.")
    add("Production class mapping", "backend/ml/models/classes.json", "38 ordered output labels; checked against class_names.txt and manifest labels.")
    add("Production class_names.txt", "backend/ml/models/class_names.txt", f"Exact ordered mapping match with classes.json={class_order_matches}.")
    add("Colab held-out evaluation notebook", "backend/ml/experiments/stage3_preflight/PlantVillage_ONNX_Heldout_Colab.ipynb", "Evaluation-only notebook; zero stored execution counts/outputs in local copy.")
    add("Original EfficientNetV2-S training notebook", "backend/ml/experiments/final_completion/recovery/source/training.ipynb", "Not found in accessible project/Git/user-folder searches; Drive/Colab source folder is not mounted/connected.")
    add("Original EfficientNetV2-S checkpoint", "backend/ml/experiments/final_completion/recovery/source/best_checkpoint.keras", "Not found; production ONNX is an exported deployment model, not original training checkpoint.")
    add("Legacy EfficientNetB0 Keras model", "backend/ml/models/plant_disease_efficientnet.keras", "Present, but serialized config identifies EfficientNetB0 with 38 outputs; not the V2-S source checkpoint.")
    add("Original epoch history and TensorBoard logs", "backend/ml/experiments/final_completion/recovery/source/training_history.csv", "No original epoch history, TensorBoard events, or run logs found in accessible search locations.")
    add("Recovered evaluation JSON", "backend/ml/experiments/final_completion/recovery/colab_results/colab_onnx_evaluation.json", "Recovered from Downloads; reported metrics do not include model or manifest hashes.")
    add("Recovered per-class metrics CSV", "backend/ml/experiments/final_completion/recovery/colab_results/colab_onnx_per_class_metrics.csv", "Recovered unchanged from Downloads.")
    add("Recovered confusion matrix CSV", "backend/ml/experiments/final_completion/recovery/colab_results/colab_onnx_confusion_matrix.csv", "Recovered unchanged from Downloads.")
    add("Recovered confusion matrix PNG", "backend/ml/experiments/final_completion/recovery/colab_results/colab_onnx_confusion_matrix.png", "Recovered unchanged from Downloads.")
    add("Recovered Colab execution screenshot", "backend/ml/experiments/final_completion/recovery/colab_results/colab_evaluation_screenshot_2026-11-25.png", "Screenshot shows inference cell completion on T4; it does not display aggregate metrics.")
    for name in ("colab_onnx_evaluation.json", "colab_onnx_per_class_metrics.csv", "colab_onnx_confusion_matrix.csv", "colab_onnx_confusion_matrix.png"):
        add(f"Original downloaded {name}", name, "Original recovered source output in Downloads; compare SHA-256 to preserved recovery copy.", absolute=DOWNLOADS / name)
    add("Original OneDrive Colab screenshot", "Screenshot 2026-11-25 225002.png", "Original screenshot from accessible OneDrive screenshots folder.", absolute=ONEDRIVE_SCREENSHOTS / "Screenshot 2026-11-25 225002.png")
    add("Existing Stage 4 PlantDoc report", "backend/ml/experiments/stage4_independent_validation/stage4_validation_report.md", "Preserved baseline; not modified or rerun by this audit.")

    write_csv(OUT / "file_inventory.csv", ["item", "status", "path", "size_bytes", "modified_local", "sha256", "notes"], inv)

    summary = {
        "manifest_rows": {"test": len(test), "train": len(train), "validation": len(val)},
        "test_sha_coverage": f"{sum(bool(r.get('sha256')) for r in test)}/{len(test)}",
        "exact_test_train_overlap_images": sum(1 for row in test if row["sha256"].lower() in {r["sha256"].lower() for r in train}),
        "exact_test_validation_overlap_images": sum(1 for row in test if row["sha256"].lower() in {r["sha256"].lower() for r in val}),
        "exact_member_path_test_train_overlap": len({r["member"] for r in test} & {r["member"] for r in train}),
        "exact_member_path_test_validation_overlap": len({r["member"] for r in test} & {r["member"] for r in val}),
        "all_split_exact_duplicate_groups": len(exact_duplicate_groups),
        "all_split_exact_duplicate_extra_images": sum(len(g) - 1 for _, g in exact_duplicate_groups),
        "cross_split_exact_duplicate_groups": len(cross_split_duplicate_groups),
        "class_order_matches_class_names": class_order_matches,
        "classes_in_test": len({r["class_name"] for r in test}),
        "recovered_eval_summary": result_summary,
        "recovered_confusion_matrix": {"header_order_matches": cm_headers == classes, "row_order_matches": cm_labels == classes, "total": cm_total, "diagonal": cm_diagonal, "off_diagonal": cm_off_diagonal, "supports_match_test_manifest": cm_supports_match},
        "recovered_per_class_values_all_1": per_class_all_perfect,
        "recovered_eval_bundle_arithmetic_consistent": eval_bundle_consistent,
        "manifest_audit_recorded_cross_split_exact_hashes": split_audit.get("cross_split_exact_hashes"),
        "perceptual_hash_modules_found": phash_modules,
        "scope_note": "These are exact comparisons among the current Stage 3 generated split manifests; they are not a comparison to the missing original model-training membership list.",
    }
    (OUT / "overlap_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
