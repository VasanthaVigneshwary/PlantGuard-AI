# Stage 1 – Root-Cause Diagnosis

**Date:** 2026-11-26  
**Status:** Partially completed; the non-comparable evaluation cause is confirmed, but exact ONNX training/preprocessing provenance and parity remain unavailable.

## Production artifact and runtime

- Active artifact: `backend/ml/models/efficientnet_v2_s_best.onnx` plus external tensor data. Sizes are 1,392,480 and 80,609,280 bytes. SHA-256 values from the completed Stage 4 frozen-input record are `14c03ae2b47b23a90a0176e70fe2fc46077fc5ae26dc46813966abdee0eb0c0a` and `038e6093bb41434def59a3c2375fbfc13c86f6af046e7f0a5b7b9015aa29b497`; the active files still match those hashes.
- ONNX Runtime metadata identifies PyTorch as graph producer; embedded graph strings identify torchvision EfficientNet blocks with stage depths `[2,4,4,6,9,15]`, structurally matching EfficientNetV2-S. The Colab notebook targets this ONNX filename, but its output does not carry the ONNX hash.
- ONNX Runtime 1.32.0 loads the model with `CPUExecutionProvider`; input is float32 `[batch,3,224,224]`, output is float32 `[batch,38]` named `logits`. The 38 output labels agree in order across `classes.json`, `class_names.txt`, and the production prediction module.
- Isolated runtime: Python 3.13.17, TensorFlow 2.21.0, Keras 3.15.1, NumPy 2.5.4, Pillow 12.3.0, ONNX Runtime 1.32.0, FastAPI 0.165.0. TensorFlow cannot load its native `_pywrap_stacktrace_handler` because Windows Application Control blocks it (verified in the existing Stage 3 report); no security setting was changed.
- Hardware checks available without administrator access: 12 logical CPUs, 15.69 GiB physical RAM with 1.70 GiB available at inspection, D: with 167,272,599,552 bytes free. WMI calls returned `HRESULT 0x80041003` / Access denied. `nvidia-smi` and `nvcc` were not found, so no usable NVIDIA GPU/VRAM was verified. ORT exposed CPU only for the production session.

## Preprocessing evidence

- Production `backend/ml/predict.py` corrects EXIF orientation, converts to RGB, bilinear-resizes to 224×224, converts to float32 and divides by 255, applies channel mean `[0.485,0.456,0.406]` and standard deviation `[0.229,0.224,0.225]`, and transposes to NCHW. It rejects very low-detail images before inference.
- `backend/ml/models/README.md` states the ONNX graph has no embedded image preprocessing and documents the same Python-side normalization. ONNX input/output signatures were verified via the live runtime. The Python `onnx` graph-inspection package is absent, so the README's no-preprocessing-node statement was not independently inspected at protobuf-node level.
- The legacy `.keras` archive was inspected without loading TensorFlow. Its serialized config is a Sequential model with an `efficientnetb0` backbone and 38-unit output, with internal Rescaling, Normalization, and Rescaling layers. The legacy inference script calls Keras EfficientNet `preprocess_input`. This is different from the active EfficientNetV2-S ONNX artifact and its external Python preprocessing. No claim of preprocessing parity is justified.
- No training code/configuration tied to the exact active ONNX file, matching training logs, export record, or checkpoint lineage was found. Stage 3 training configuration is proposed preparation work, not evidence for the ONNX artifact's training procedure.

## Mapping and integration checks

- The indexed `class_names.txt` equals the ordered list in `classes.json` (38 labels). The active predictor checks this alignment and the 38-logit output. The legacy folder mapping has 40 names/aliases covering indices 0–37; its test folders/results are unavailable for a fresh audit.
- The FastAPI route uses `predict_disease` and returns the canonical class string, raw model score, uncertainty fields and top predictions. The frontend consumes those fields and has Tamil/English display paths. A read-only PostgreSQL audit found one mapping per model class (38/38), no missing/duplicate mappings, and all required detail categories present for all classes.

## Keras/ONNX and score discrepancy

- The 41.68% / 511-image figure is documented only for the legacy Keras artifact. The inspected archive is EfficientNetB0, not EfficientNetV2-S. The image list, split, exact label mapping, preprocessing record, and per-image outcomes behind that reported score are not present. It is not a like-for-like score for the production ONNX model.
- The four Colab PlantVillage output files were recovered from Downloads and copied to `recovery/colab_results/`. The notebook source targets `efficientnet_v2_s_best.onnx` and the fixed test manifest. The 38x38 matrix is diagonal with 8,154/8,154 correct; row supports match the local test manifest exactly and all 38 per-class metrics are 1.0. The JSON lacks model/manifest/archive hashes, so the exact model bytes and training/test independence are not bound to this result.
- The existing PlantDoc Stage 4 baseline (19.51% top-1 over 123 eligible examples in 16 classes) is a different external domain with partial coverage; it is evidence of poor transfer on that subset, not a diagnosis of preprocessing and not a basis for model selection.
- **Confirmed explanation:** 41.68% belongs to the legacy EfficientNetB0 Keras artifact; 100% is a recovered report of the fixed PlantVillage test-set evaluation from the EfficientNetV2-S ONNX notebook path. These are different models/evaluations, not a same-model discrepancy. The ONNX graph structure supports the V2-S architecture, while the result file lacks an ONNX hash. **Not confirmed:** active ONNX preprocessing or mapping bug. Exact report-to-checkpoint and training-to-serving parity remain unresolved.

## Parity and remaining issues

No Keras–ONNX parity test was run: the available Keras artifact is a different EfficientNetB0 model, and TensorFlow import is blocked by Windows Code Integrity. The original model card identifies the active file as EfficientNetV2-S trained on PlantVillage, but image-level training records and reproducible training evidence are unavailable. PlantDoc/test overlap with the original model training set therefore remains unknown. No preprocessing change is recommended or made.
