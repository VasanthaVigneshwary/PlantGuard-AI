# Frozen-Backbone Linear-Probe Bake-Off

## Status (2026-11-27)

| Backbone | Status | Reason / metrics |
|---|---|---|
| Production EfficientNetV2-S ONNX | BLOCKED | Existing graph exposes only 38 logits; no verified penultimate feature output. Do not substitute other weights. |
| DINOv2 ViT-S/14 | BLOCKED | PyTorch/torchvision and checkpoint/code cache unavailable locally. |
| DINOv2 ViT-B/14 | BLOCKED | PyTorch/torchvision and checkpoint/code cache unavailable locally. |
| BioCLIP ViT-B/16 | BLOCKED | `open_clip`, PyTorch and checkpoint cache unavailable locally. |

No embeddings, classifiers, or evaluation metrics were produced. The cached-only runner was executed and wrote a BLOCKED result with zero metric rows; no download or install was attempted. This is not an accuracy result.

## Method

- Uses the approved 38-class order, existing `field_train.csv` / `field_val.csv`, filtered PlantVillage training manifest, fixed PlantVillage test manifest, and 123 eligible protected PlantDoc images.
- Samples up to 300 PlantVillage train images/class (11,400 total here), then samples field training rows with replacement to reach at least 40% field share globally (7,600 / 19,000 here). Field validation/evaluation are never oversampled.
- Uses each encoder's inference transform and raw feature vector; caches features as `.npy` with manifest digests. LogisticRegression uses the fixed C grid `0.001, 0.01, 0.1, 1, 10, 100`; C is selected only by covered-class macro-F1 on `field_val`.
- Reports direct 38-class and crop-first predictions. Crop-first predicts crop/species, then selects disease candidates using the predicted crop. Evaluation does not use true crop labels for candidate restriction.
- Final metrics, once a model is available, include top-1/top-3, 38-class macro-F1, crop accuracy, covered/uncovered class subsets, per-class supports, paired-image bootstrap 95% percentile intervals on the 123-image PlantDoc set, and CPU embedding timing. Field-val metrics are tuning-set results.
- Fixed seed: `20261127`; default batch size: 32. Protected image SHA-256 values are checked before and after; the preflight also checks exact SHA and pHash distance ≤6 against train/validation features. Existing split tests verify zero field group overlap and zero PlantVillage train/test exact hash/member overlap.

## Integrity and limits

- Preflight passed on the prepared splits: 38 classes; 1,069 field-train / 268 field-val; 37,993 PlantVillage train source rows; 8,154 PlantVillage test rows; 123 protected PlantDoc images; 17 field-covered classes; 0 field train/validation SHA or group overlap; 0 exact PlantVillage train/test overlap; 0 protected exact or pHash≤6 matches; protected hashes unchanged.
- Local runtime lacks `torch`, `torchvision`, `scikit-learn`, `onnx`, and `open_clip`; CUDA is unavailable. No model weights are cached. Production ONNX logits cannot serve as penultimate embeddings.
- DINOv2 base S/14 and B/14 code/weights are Apache-2.0 per the [official repository](https://github.com/facebookresearch/dinov2); confirm the exact downloaded checkpoint variant. BioCLIP ViT-B/16 model card declares MIT ([official model card](https://huggingface.co/imageomics/bioclip)); review its upstream data and dependency terms too. Production ONNX weight lineage/license is undocumented locally. PlantVillage source data is separately declared CC BY-SA 3.0 in the project source documentation.
- Results describe a frozen-feature linear probe on this mixed dataset, not production-model performance. PlantDoc is small and covers only 16 mapped disease classes; 21 classes have no field-train examples. No performance guarantee is made.

## Colab T4 commands (run only with required weights already cached)

```bash
python -m pip install scikit-learn onnx onnxruntime open_clip_torch
python backend/ml/experiments/final_completion/realworld/bakeoff/preflight.py
python backend/ml/experiments/final_completion/realworld/bakeoff/run_bakeoff.py --project-root /content/PlantGuard-AI --run-dir /content/bakeoff-run --batch-size 32
```

Colab must already have compatible PyTorch/torchvision, local DINOv2 hub code plus `dinov2_vits14_pretrain.pth` and `dinov2_vitb14_pretrain.pth`, and the BioCLIP `open_clip_pytorch_model.bin` cache. Do not let model loaders fetch weights implicitly. The production ONNX backbone remains blocked until a feature-output graph derived from the exact production weights is supplied and hash/parity verified.
