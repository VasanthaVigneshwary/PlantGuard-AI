# Real-world EfficientNetV2-S experiment (manual Colab T4)

Preparation only. This directory does not authorize training or production replacement. Do not run the training command until the owner explicitly approves. No command below downloads datasets or pretrained weights.

## Drive layout

Upload the repository files needed by the scripts to `MyDrive/PlantGuard-AI/`, preserving these paths:

```text
PlantGuard-AI/
  datasets/plantvillage-source.zip
  datasets/plantdoc-source.zip
  datasets/plantdoc/manifest.jsonl
  backend/ml/models/classes.json
  backend/ml/models/efficientnet_v2_s_best.onnx
  backend/ml/models/efficientnet_v2_s_best.onnx.data
  backend/ml/experiments/stage3_preflight/plantvillage_train.csv
  backend/ml/experiments/stage3_preflight/plantvillage_test.csv
  backend/ml/experiments/stage4_independent_validation/plantdoc_predictions.csv
  backend/ml/experiments/final_completion/realworld/  # all prepared files
```

The PlantDoc evaluation file is used only after training for final comparison. The training script reads only `field_train.csv`, `field_val.csv`, and `plantvillage_train_filtered.csv`.

## Colab commands

1. In Colab select **Runtime > Change runtime type > T4 GPU**, then run:

```python
from google.colab import drive
drive.mount('/content/drive')
```

2. Copy the experiment scripts/manifests to Colab local storage (so checkpoints/logs are fast); project manifests, model and ZIP archives remain read-only on Drive:

```bash
export ROOT=/content/drive/MyDrive/PlantGuard-AI
export EXP_SRC=$ROOT/backend/ml/experiments/final_completion/realworld
export EXP=/content/realworld
mkdir -p "$EXP"
cp -a "$EXP_SRC/." "$EXP/"
python -c "import torch, torchvision, sklearn, PIL, numpy; print(torch.__version__, torchvision.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NO CUDA')"
python -c "import torch; from pathlib import Path; from torchvision.models import EfficientNet_V2_S_Weights as W; p=Path(torch.hub.get_dir())/'checkpoints'/Path(W.IMAGENET1K_V1.url).name; print('cached ImageNet weights:',p,p.is_file())"
```

If the required cached ImageNet weights are absent, stop. Do not select pretrained weights that trigger downloads, install additional packages, or train from random initialization without separate approval. Export needs `onnx`; evaluation needs `onnxruntime` (and CUDA provider for GPU evaluation). If imports/provider are unavailable, stop and request approval before installing packages.

3. Extract only training/validation members into Colab local storage. This verifies every extracted file against its manifest SHA-256. The held-out PlantVillage test and 123 PlantDoc evaluation images are not extracted in this step:

```bash
python "$EXP/extract_colab_data.py" --project-root "$ROOT" --output-root /content/plantguard-data
```

4. **Only after explicit training approval**, start the bounded run (maximum 75 minutes; no automatic restart):

```bash
python "$EXP/train_realworld.py" --project-root "$ROOT" --plantvillage-root /content/plantguard-data/plantvillage --plantdoc-root /content/plantguard-data/plantdoc
```

5. After a completed or time-limited run, add evaluation data without changing the split. This reuses and hash-checks files already extracted:

```bash
python "$EXP/extract_colab_data.py" --project-root "$ROOT" --output-root /content/plantguard-data --include-evaluation
python "$EXP/export_onnx.py"
python "$EXP/verify_onnx_parity.py" --project-root "$ROOT" --plantdoc-root /content/plantguard-data/plantdoc
python "$EXP/evaluate_old_vs_new.py" --project-root "$ROOT" --data-root /content/plantguard-data
```

Export, parity and evaluation outputs are written under `/content/realworld/export/` and a unique `/content/realworld/evaluation/run_*` folder. Copy verified results/checkpoints back only after the run, for example `rsync -a "$EXP/training/" "$EXP_SRC/training/"; rsync -a "$EXP/export/" "$EXP_SRC/export/"; rsync -a "$EXP/evaluation/" "$EXP_SRC/evaluation/"`. Evaluation uses the exact existing 8,154-image PlantVillage test manifest and the exact 123 eligible PlantDoc images; the test sets never feed training, checkpoint selection, or threshold selection. Review runtime-provider evidence in `evaluation.json` before describing GPU execution. Model scores are raw softmax scores, not calibrated probabilities.

## Prepared configuration and limits

EfficientNetV2-S, original 38-class order, cached ImageNet weights only; 2 frozen-head + up to 8 full-network epochs; AdamW 1e-4, cosine schedule, 0.1 label smoothing; up to 300 PlantVillage images/class/epoch and at least 40% field samples; field-val macro-F1 checkpoint selection; augmentation only on training. 21 classes have no field-train examples and 22 have fewer than 10, so the experiment remains primarily supported by PlantVillage. Runtime estimate: roughly 35–75 minutes on T4 is a planning estimate only, not measured; the enforced cutoff is checked at epoch boundaries. No metrics exist for this new experiment until it is run.
