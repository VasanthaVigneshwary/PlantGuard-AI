# PlantVillage ONNX GPU Held-out Workflow

## Purpose and scope

This is a separate, reproducible ONNX inference workflow for the existing fixed PlantVillage test manifest. It is **not training** and does not create a new split. It evaluates the existing 38-output production ONNX model and records whether ONNX Runtime actually assigned model nodes to CUDA.

The PlantVillage test images come from the same dataset named in the model documentation, while original training membership is unavailable. Therefore this workflow is **same-source held-out evaluation / runtime verification**, not independent validation and not proof of generalization. Keep its results separate from the existing PlantDoc Stage 4 report.

## Inputs and paths

Paths are relative to the repository root, which must be mirrored in Drive as `/content/drive/MyDrive/PlantGuard-AI` (or selected in the notebook's bounded root detection):

- Model: `backend/ml/models/efficientnet_v2_s_best.onnx`
- External tensor data: `backend/ml/models/efficientnet_v2_s_best.onnx.data`
- Ordered labels: `backend/ml/models/classes.json` (must match `class_names.txt`)
- Fixed test manifest: `backend/ml/experiments/stage3_preflight/plantvillage_test.csv` (8,154 rows, `split=test`)
- Preserved ZIP: `datasets/plantvillage-source.zip`
- Production preprocessing implementation: `backend/ml/predict.py::preprocess_image`

The local paths resolve under `D:\PlantGuard-AI`. The prior Stage 3 notebook used the same model/data/manifest/archive paths when its `PROJECT` variable points at the repository root, but wrote evaluation outputs into `stage3_preflight`. This Stage 4 notebook instead writes only beneath this folder, in a unique timestamped run directory. The Stage 3 notebook and all Stage 3 outputs are left unchanged.

## CUDA verification gate

The notebook records PyTorch CUDA status, ONNX Runtime version, available/registered providers, session providers, and per-node provider counts from ONNX Runtime profiling. A CUDA provider listed in `get_available_providers()` or `session.get_providers()` is not by itself evidence that the model ran on the GPU: providers are prioritized and unsupported nodes may fall back to CPU. The notebook requires at least one profiled model node assigned to `CUDAExecutionProvider` during a small real-model preflight before beginning the full test pass, then records provider assignment counts for the full pass. If this check fails, it stops without reporting GPU evaluation success.

The procedure follows ONNX Runtime's [Execution Provider documentation](https://onnxruntime.ai/docs/execution-providers/) and [profiling documentation](https://onnxruntime.ai/docs/performance/tune-performance/profiling-tools.html). Colab execution remains pending; no CUDA session has been confirmed from this local workspace.

## Expected evidence

Each Colab execution creates a unique `run_YYYYMMDD_HHMMSS_UTC/` directory, avoiding overwrite of earlier runs. Expected files:

- `runtime_preflight.json` — Colab/T4 information, ONNX Runtime provider availability and profiled CUDA/CPU node assignment from the smoke batch.
- `evaluation.json` — exact input hashes/metadata, class distribution, metrics, duration, inference provider profile counts and limitation statement.
- `predictions.csv` — one row per fixed test image; true/predicted index and class, top-three ranking, raw uncalibrated top score, integrity status.
- `per_class_metrics.csv` — support, precision, recall and F1 for all 38 labels in approved order.
- `confusion_matrix.csv` and `confusion_matrix.png` — all 38 classes in the same order.
- `onnxruntime_profile.json` — provider-assignment profiling from the full inference session.

No result files are committed before an actual Colab run. A recovered historical 100% PlantVillage result exists elsewhere, but it is not substituted for this run and has unresolved model-hash/training-membership provenance.
