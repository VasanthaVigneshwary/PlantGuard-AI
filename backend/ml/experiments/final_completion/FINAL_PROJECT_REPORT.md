# Plant Guard AI - Final Completion Report

**Date:** 2026-11-26  
**Overall:** Evidence gathering, reuse, and safe functional checks are complete. The requested model project is **not ready to claim completed 38-class training or independent 38-class validation**. The frontend now displays the existing API top-three outputs. No model, dataset, manifest, database/schema, or backend file was modified.

## Previously completed work reused

- Stage 3 preflight validated the preserved PlantVillage ZIP: 54,305 color images across 38 approved classes. It created seed-42 train/validation/test manifests and duplicate/integrity reports.
- Stage 4 completed an external PlantDoc-only evaluation. Its existing metrics and prediction artifacts were reused without rerunning inference.
- Production inference already uses the 38-class ONNX model and sidecar through `backend/ml/predict.py`; production and existing reports were left untouched.

## Phase 1 - Diagnosis

The active model is `efficientnet_v2_s_best.onnx` (1,392,480 bytes) plus `efficientnet_v2_s_best.onnx.data` (80,609,280 bytes). Existing frozen-input hashes were rechecked: model `14c03ae2b47b23a90a0176e70fe2fc46077fc5ae26dc46813966abdee0eb0c0a`; sidecar `038e6093bb41434def59a3c2375fbfc13c86f6af046e7f0a5b7b9015aa29b497`. ONNX Runtime 1.32.0 loaded them using CPUExecutionProvider; input is float32 `[batch,3,224,224]`, output is float32 `[batch,38]` (`logits`).

Production preprocessing is EXIF correction, RGB, bilinear resize to 224x224, divide by 255, ImageNet mean/std normalization, then NCHW. The model README says preprocessing is not embedded in the ONNX graph. TensorFlow 2.21.0 and Keras 3.15.1 are installed in `.venv.stage3`, but importing TensorFlow is blocked by Windows Application Control at `_pywrap_stacktrace_handler`; no protection was bypassed.

The saved legacy Keras archive is a Sequential EfficientNetB0 model with 38 outputs and internal rescaling/normalization layers. Its reported 41.68% on 511 images is not a like-for-like result for the active EfficientNetV2-S ONNX artifact. The active ONNX graph identifies a PyTorch torchvision EfficientNet with feature-stage depths `[2,4,4,6,9,15]`, structurally matching EfficientNetV2-S. Four Colab result files and a related OneDrive screenshot were recovered. The screenshot shows the held-out inference cell completed on a T4 runtime; the JSON reports 100% on the 8,154-image test split, and the saved matrix/supports exactly match the local test manifest with 8,154 diagonal and 0 off-diagonal counts. The notebook source targets the active ONNX filename and same preprocessing, but neither the JSON nor screenshot records a model/manifest/archive hash. The Hugging Face repository linked by the model card has cached contents for an EfficientNetB0 Keras model and no ONNX file, so that link does not verify the V2-S ONNX's origin. The 100% report is therefore a recovered, arithmetic-verified test result strongly associated with the V2-S ONNX path, while exact bitwise model binding and model-training independence remain unverified. Original ONNX training code/config, matching logs, export record, and image membership list were not found.

Class order agrees among `classes.json`, `class_names.txt`, and active prediction code. A read-only PostgreSQL audit found a unique mapping for each of the 38 classes and detail coverage for all; 27/27 application-rate records lack verified source metadata. The frontend already showed the primary model score and uncertainty in English/Tamil, but did not consume the API's top-prediction list. A targeted frontend change now renders the first three model scores with a clear uncalibrated-score note in both languages.

Hardware checks: 12 logical CPU threads, 15.69 GiB RAM with 1.70 GiB available, D: free space 167,272,599,552 bytes (about 155.8 GiB). WMI returned access denied (`HRESULT 0x80041003`); `nvidia-smi` and `nvcc` were absent. No NVIDIA GPU/VRAM was verified. Installed runtime versions: Python 3.13.17, TensorFlow 2.21.0, Keras 3.15.1, NumPy 2.5.4, Pillow 12.3.0, ONNX Runtime 1.32.0, FastAPI 0.165.0, Starlette 1.10.0, httpx 0.28.1, psycopg2-binary 2.9.13. pytest is not installed; no dependencies were added.

## Phase 2 - Dataset audit

The existing validation reports show archive CRC pass, 38/38 classes, 0 corrupt images, 12 healthy classes and 15,084 healthy images. Class counts range from 152 to 5,507. Existing seed-42 manifests contain 37,993 train, 8,158 validation, and 8,154 test images: 69.962%, 15.023%, and 15.015%. The hash audit found 21 exact duplicate groups, all kept within split boundaries, with zero cross-split exact hashes. Existing source documentation identifies the PlantVillage mirror and CC BY-SA 3.0 declaration. No manifests or image data were regenerated or changed.

## Phase 3 - Training status

No reproducible EfficientNetV2-S training run, epoch history, source checkpoint, or export lineage was recovered. The active ONNX deployment model does exist and loads; absence of local history does not establish that training never occurred. The legacy EfficientNetB0 Keras file is a different architecture and is not a V2-S checkpoint. Local training is not practical with no verified GPU, low currently available RAM, and blocked TensorFlow import. **No training, weight download, or checkpoint creation occurred.** `TRAINING_PLAN.md` remains a fallback only, not a recommendation to restart from scratch.

## Phase 4 - Evaluation results

### PlantVillage

Training accuracy: unavailable. Validation accuracy: unavailable. The recovered Colab report states **100% top-1 accuracy** on 8,154 test images and 38 classes; macro precision, recall, F1 and weighted F1 are also 100%. Its matrix and all class supports match the local held-out test manifest exactly. Treat this as a recovered test-split result with verified arithmetic, not a fresh rerun. The JSON does not hash the model or data, and independence from the model's documented PlantVillage training source cannot be confirmed. The test was not rerun.

### PlantDoc (existing Stage 4 baseline, reused)

- 123 eligible held-out images; 16 of the 38 model classes represented; no explicit healthy labels.
- Top-1 accuracy 19.51%; top-3 accuracy 37.40% (top-3 values are raw model scores/rankings, not calibrated probabilities).
- Macro precision 37.66%, macro recall 18.62%, macro F1 19.47%; weighted precision 40.84%, weighted recall 19.51%, weighted F1 20.87%.
- Largest existing confusion counts include Bell pepper bacterial spot -> Bell pepper healthy (5), Tomato yellow leaf curl virus -> Strawberry leaf scorch (4), and Grape black rot -> Strawberry leaf scorch (4).
- The full Stage 4 report records integrity checks, exact/near duplicate exclusions, per-class support/metrics, predictions, confusion matrix, and hashes. No PlantDoc inference was repeated. PlantDoc/model-training overlap is unknown; full 38-class independent validation is not established.

## Phase 5 - Reliability evidence

- `test_model_reliability.py`: 14 tests passed, including model signature, preprocessing shape/dtype/RGB normalization, EXIF, index mapping, repeatability, corrupt/missing/low-detail input handling, unsupported-input warning, and distinct real fixtures.
- `test_model.py`: two real fixture smoke predictions passed (sample leaf -> Apple scab; webp fixture -> Tomato early blight). These are functional checks, not accuracy measurements.
- API rejected empty, corrupt, low-detail, and >10 MiB synthetic uploads. Fifty CPU inference runs on the sample fixture after five warmups: median 35.46 ms, p95 40.02 ms. This is a single local fixture benchmark, not a production capacity guarantee.
- Raw softmax scores are uncalibrated. No temperature scaling, confidence threshold selection, or OOD guarantee was attempted. PlantDoc was not used for any tuning.

## Phase 6 - Application integration

- Five safe existing FastAPI tests passed: health, CORS, empty upload, corrupt image, and low-detail image.
- Two real sample-image upload requests (English and Tamil) returned 200, correct canonical class mapping, top-5 outputs, raw score and uncertainty fields. Database/persistence calls were mocked read-only and permanent image writes were blocked during this check. This verifies the local API path, not deployment.
- Frontend fix: added the API's optional `top_predictions` type and a localized top-three panel; no inference or response contract was changed.
- Read-only database audit: 38/38 disease class mappings, no missing or duplicate mapping, all five detail categories covered; all 27 application-rate records remain unverified and should not be used as validated product-rate guidance.
- Frontend validation: ESLint completed with 0 errors and 2 existing `<img>` optimization warnings; TypeScript `npx tsc --noEmit` passed. No frontend production build was run.
- No full backend suite was run because some existing endpoint tests persist uploaded images into `backend/uploads`, which contains pre-existing untracked user files. pytest is absent and was not installed.

## Files created

All new completion deliverables, recovered Colab copies, and safety copies are under `backend/ml/experiments/final_completion/`:

- `STAGE1_DIAGNOSIS.md`, `STAGE2_AUDIT.md`, `TRAINING_PLAN.md`
- `STAGE_STATUS.md`, `STATE.md`, `FINAL_PROJECT_REPORT.md`
- `recovery/RECOVERY_REPORT.md`, `recovery/MODEL_PROVENANCE.md`, `recovery/RECOVERY_PLAN.md`, and the four copied evaluation outputs plus the related screenshot in `recovery/colab_results/`
- Timestamped `STATE_before_phase*_update_20261126.md` copies and `TRAINING_PLAN_before_revision_20261126.md`
- `FINAL_PROJECT_REPORT_before_frontend_update_20261126.md`, `STAGE_STATUS_before_frontend_update_20261126.md`, `STATE_before_frontend_update_20261126.md`, and `frontend_page_before_top3_20261126.tsx` safety copies

Only one existing source file was modified: `frontend/app/page.tsx`, to display the top-three candidates the API already returns. Its original is backed up under `final_completion/`. All other existing user changes/untracked files were preserved. No commits, pushes, reset, clean, or staging commands were performed.

## Remaining blockers and next steps

1. Make the original Google Drive training folder read-only accessible as described in `recovery/RECOVERY_PLAN.md` to recover the training notebook/config, checkpoints/history and export metadata. First compare hashes; do not retrain unless recovery proves impossible and training is necessary.
2. Recover exact ONNX training source, preprocessing config, export lineage, and image-level training records. Without these, exact Colab model binding and test independence remain limited.
3. Only if a new training run becomes necessary, obtain a supported GPU runtime and resolve TensorFlow Windows Code Integrity without bypassing security; freeze the preprocessing contract before training. Do not select preprocessing with PlantDoc.
4. If a new training run is approved and feasible, use the existing 38-class manifests, save an experimental checkpoint/history, then evaluate the locked test once only if independence from training/model selection can be established.
5. To establish real-world 38-class performance, collect a rights-cleared, expert-reviewed field dataset covering all 38 classes including healthy classes, with provenance and capture-group/duplicate controls.
6. Review application-rate source verification before those records are presented as recommendations.

**Readiness decision:** current application inference is functionally operational in local tests; model training is not complete, PlantVillage held-out accuracy is unverified, and independent external validation covers only 16 classes. Do not claim Master Prompt 1 completion or full 38-class independent validation yet.
