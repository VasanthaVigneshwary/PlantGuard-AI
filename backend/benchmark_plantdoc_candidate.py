"""Measure single-image CPU inference latency on the pinned PlantDoc test subset.

This diagnostic does not change model weights or use labels for model selection.
Run after `train_plantdoc_candidate.py`; results are written under the ignored
dataset candidate directory.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
from ml.predict import predict_disease  # noqa: E402
from train_plantdoc_candidate import make_data_splits, read_manifest, IMAGE_SIZE, IMAGENET_MEAN, IMAGENET_STD  # noqa: E402


def summarize(samples: list[float]) -> dict:
    ordered = sorted(samples)
    return {
        "sample_count": len(samples),
        "mean_ms": statistics.mean(samples),
        "median_ms": statistics.median(samples),
        "p95_ms": ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))],
    }


def benchmark(dataset_root: Path, limit: int = 30) -> dict:
    from torchvision.models import mobilenet_v3_small

    rows = make_data_splits(read_manifest(dataset_root))["test"][:limit]
    report_path = dataset_root / "candidate" / "evaluation.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    classes = report["class_order"]
    checkpoint = torch.load(report["candidate_artifact"], map_location="cpu", weights_only=True)
    candidate = mobilenet_v3_small(weights=None, num_classes=len(classes)).eval()
    candidate.load_state_dict(checkpoint["state_dict"])
    transform = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE), interpolation=transforms.InterpolationMode.BILINEAR),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])

    paths = [dataset_root / Path(row["image_path"]) for row in rows]
    # Warm model runtimes, then measure preprocessing+single-image inference
    # on identical files, reporting CPU latency only.
    for path in paths[:2]:
        with Image.open(path) as image, torch.inference_mode():
            candidate(transform(image.convert("RGB")).unsqueeze(0))
    candidate_ms = []
    for path in paths:
        started = time.perf_counter()
        with Image.open(path) as image, torch.inference_mode():
            tensor = transform(image.convert("RGB")).unsqueeze(0)
            candidate(tensor)
        candidate_ms.append((time.perf_counter() - started) * 1000)

    # Warm the cached ONNX session before timing production's full single-image path.
    for path in paths[:2]:
        predict_disease(path, top_k=1)
    production_ms = []
    for path in paths:
        started = time.perf_counter()
        predict_disease(path, top_k=1)
        production_ms.append((time.perf_counter() - started) * 1000)

    result = {
        "dataset_source": report.get("dataset_source"),
        "test_subset_count": len(paths),
        "runtime": "CPU; warmed runtimes; single-image wall clock",
        "candidate_pipeline_ms": summarize(candidate_ms),
        "production_pipeline_ms": summarize(production_ms),
        "limitations": [
            "Candidate timing covers image open, preprocessing, and model inference.",
            "Production timing covers its image open, quality checks, preprocessing, and ONNX inference.",
            "This is a local diagnostic benchmark, not a hardware-independent service latency guarantee.",
        ],
    }
    output_path = dataset_root / "candidate" / "latency.json"
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be positive")
    print(json.dumps(benchmark(args.dataset_root, args.limit), indent=2))
