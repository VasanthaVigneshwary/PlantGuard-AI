# EfficientNetV2-S Training Plan (Not Executed)

## Decision

No valid completed EfficientNetV2-S 38-class training run with epoch history/checkpoint was found. The existing legacy `.keras` archive is EfficientNetB0, and the active ONNX model's training history is not available. A new run is **not feasible on the inspected local host**: no NVIDIA/CUDA device was found, only 1.70 GiB RAM was available, and TensorFlow's native import is blocked by Windows Application Control. No training, weight download, or checkpoint write was attempted.

## Frozen objective and data

- Model: EfficientNetV2-S, 224×224 input, original 38 labels in the approved `classes.json` order.
- Dataset: preserved PlantVillage ZIP and existing seed-42 70/15/15 manifests (37,993 train / 8,158 validation / 8,154 test).
- Train only on the train split; use validation for callbacks and selection; keep test locked until a final approved run. Never use PlantDoc to tune, calibrate, or select the model.
- Use the existing ZIP-member loader or a tested streaming equivalent; no extraction/cache of all images is required.

## Proposed bounded schedule (from existing Stage 3 config)

1. Seed Python, NumPy and TensorFlow with 42; enable deterministic operations where supported and record any unsupported determinism.
2. Initialize `tf.keras.applications.EfficientNetV2S` for 38 outputs, preserving 224×224 resolution. Do not change the class order or replace the backbone.
3. Feature extraction: ImageNet initialization, frozen backbone, AdamW, learning rate 1e-3, maximum 8 epochs.
4. Fine-tuning: unfreeze upper 45% of backbone, freeze Batch Normalization, AdamW at 3e-5 with cosine decay, maximum 35 epochs.
5. Apply augmentation only to training batches; stream data with no full-dataset cache, prefetch 1. Begin at batch 8 on a GPU only after a memory smoke test; adjust only from train/validation feasibility, never by using test or PlantDoc results.
6. Use categorical cross-entropy (sparse labels if the loader emits integer IDs), early stopping on validation loss, best-validation checkpoint, and reduce-learning-rate scheduling if compatible with cosine decay. Record per-epoch loss/accuracy plus macro/per-class precision, recall, and F1.
7. Save checkpoints, class order, config, package/runtime manifest, and epoch history under a new experiment-only path. Do not replace production ONNX/Keras artifacts.

## Required gates before execution

- Use a supported Linux GPU runtime with a verified NVIDIA device, preferably at least 16 GiB VRAM for an initial batch-8 feasibility trial, and sufficient host RAM/disk. These are planning targets, not measured guarantees; benchmark a short train/validation pilot before committing to all epochs.
- Restore a compatible TensorFlow environment without bypassing Windows security; verify import, tensor ops, EfficientNetV2-S construction, forward/backward pass, and resource use.
- **Resolve preprocessing explicitly before training/export.** The active ONNX serving path uses RGB, bilinear 224×224, `[0,1]`, ImageNet mean/std, NCHW. The ONNX artifact's original training preprocessing is unknown. Keras EfficientNetV2's `include_preprocessing` setting must be chosen and recorded; do not combine built-in preprocessing with external normalization accidentally. Validate a frozen train/export/serving path on synthetic and train/validation examples only. Do not infer or tune it from PlantDoc.
- Confirm pretrained-weight access and licensing separately before any weight download. No large pretrained weights have been downloaded in this work.
- Estimate full run time only after an approved short pilot reports actual step time and peak memory.

## Generalization note

PlantVillage provides controlled leaf imagery and does not establish performance on varied field photographs. The existing PlantDoc evaluation is a noisy, disease-only external subset (123 images / 16 mapped classes, 19.51% top-1); it shows limited transfer but must remain an untouched baseline. Improving real-world performance requires a separately collected, rights-cleared, expert-reviewed field dataset with healthy and diseased labels, source/capture groups, and coverage of all 38 target classes. PlantDoc must not be recycled into training or model-selection data.
