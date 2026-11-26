# Stage 4 Completion and Evidence Recovery Report

**Date:** 2026-11-26  
**Status:** **PARTIALLY COMPLETE — GPU execution requires one Colab action**

## Scope and safeguards

This report records the Stage 4 PlantVillage GPU evaluation handoff and the evidence available locally. No training, fine-tuning, model export, dataset/manifest modification, production-code modification, or PlantDoc reevaluation was performed. The Stage 4 PlantDoc report and outputs remain untouched. No browser automation was used.

## Completed before this run

- Stage 3 preparation and fixed PlantVillage manifests exist. The test manifest has 8,154 rows, exactly one `test` split, all 38 classes, and SHA-256 values for each image.
- A prior leakage audit reports no exact image-hash or path overlap between the current train, validation, and test manifests. That audit is about the current manifests; it cannot establish membership in the model's original training set.
- The existing ONNX model and external tensor file are present: `backend/ml/models/efficientnet_v2_s_best.onnx` (1,392,480 bytes) and `efficientnet_v2_s_best.onnx.data` (80,609,280 bytes). `classes.json` is present.
- The Stage 4 PlantVillage GPU notebook and its preparation documentation are present under `plantvillage_onnx_heldout_gpu/`. The notebook has eight cells but no saved cell outputs and no execution counts, so it is a prepared workflow, not a completed run.
- The PlantDoc evaluation remains in `stage4_validation_report.md`: 123 eligible images, 16 mapped classes, top-1 accuracy 19.51%, top-3 accuracy 37.40%, macro F1 19.47%. This is a distinct external dataset and is not directly comparable to PlantVillage.
- Previous local commits include `6a12b3d4` (`prep(ml): add Stage 4 PlantVillage GPU evaluation workflow`), `25dbe099` (leakage/provenance audit), and `784c8846` (recovered evaluation/provenance documentation).

## Evidence reused and independently checked

### Fixed test manifest

- Path: `backend/ml/experiments/stage3_preflight/plantvillage_test.csv`
- Rows: **8,154**
- Split values: **8,154 test**
- Distinct `class_name` values: **38**
- SHA-256: `3a29ab682c815a15cb78d490cfdcbc0c54128e7c0f6c8f048676298503560010`
- The saved manifest audit is `backend/ml/experiments/stage3_preflight/plantvillage_manifest_audit.json` (SHA-256 `3f18626557b1a92aebd239682a1c5712a0853e1e7a4ef756b5cf0db32ca7ad00`).

### Historical Colab result (not a new execution)

Recovered at `backend/ml/experiments/final_completion/recovery/colab_results/`:

- `colab_onnx_evaluation.json` — SHA-256 `7a6269341534aee79c7840cdd45ddfb128f4d6202a1ca7306afdb25571f30ca4`
- `colab_onnx_per_class_metrics.csv` — SHA-256 `263e85e46cad4d9152390de63f52033a121de80810370b83460f582088e2b532`
- `colab_onnx_confusion_matrix.csv` — SHA-256 `62493658db7e93c2a1a7f6b42a98df53e0a391fa6264968b652e35e6e0853674`
- `colab_onnx_confusion_matrix.png` — SHA-256 `4abf74b7697033f15df068295310581543755c46b6eee685f1c58916c35fe7c2`
- `colab_evaluation_screenshot_2026-11-25.png` is also present.

The recovered JSON claims 8,154 images, 38 classes, 1.0 accuracy, macro precision/recall/F1 and weighted F1, and lists CUDA and CPU providers. This is historical reported evidence only. There are no image-level prediction records, selected-image hash audit, model/manifest hash binding, or ONNX profiling trace in that recovery folder to independently bind this result to the current model bytes, exact manifest contents, and actual CUDA-executed nodes. The listed providers alone do not prove that CUDA executed model nodes. The result therefore remains suspicious/unverified as a reproduced run and does not establish independence from the model's unknown training/selection data.

### Current local runtime

The existing `.venv.stage3` imports ONNX Runtime 1.32.0. Its available providers are `AzureExecutionProvider` and `CPUExecutionProvider`; `CUDAExecutionProvider` is absent. `nvidia-smi` is not available in this Windows execution environment. Therefore this runtime cannot produce the requested proof of ONNX CUDA node execution. A full 8,154-image local CPU evaluation was not started.

### New-run artifact search

No new `evaluation.json`, `runtime_preflight.json`, `onnxruntime_profile.json`, full `predictions.csv`, hash-verification report, inference-failure report, or completed Stage 4 execution report exists in the new GPU-run folder. The notebook has no outputs. The local historical recovery bundle is not a substitute for these artifacts.

## Technical conclusions

- **Preparation:** completed and reusable. The notebook is configured to find the project in Google Drive, use the existing fixed test manifest, production preprocessing and ordered class mapping, hash selected image bytes, and require a profiled CUDA node before calling a run GPU-confirmed.
- **New execution:** not completed. No new test inference was run in this environment.
- **GPU:** not verified for the current evaluation. Local ONNX Runtime has no CUDA provider; the recovered historical provider list is insufficient proof of node assignment.
- **Image coverage:** manifest and class coverage are verified locally, but this run did not re-read and hash all 8,154 images from the archive.
- **Metrics:** the only available PlantVillage metrics are the recovered historical 100% report above. They are not presented as newly reproduced or independently validated metrics.
- **Independence:** unknown. Exact duplicate checks among current manifests do not resolve possible overlap with model training or model selection because the original image-level training membership/provenance is unavailable.
- **PlantDoc:** its 19.51% top-1 result remains preserved and should be interpreted as a domain-shift/external-data result on 123 images across 16 mapped classes, not as a like-for-like score against the 8,154-image, 38-class PlantVillage test report.

## Remaining external blocker and smallest next action

No connected Colab or Google Drive execution interface is available to this session, and the local runtime lacks ONNX CUDA support. The notebook is prepared but cannot be launched from this environment. **One action is required:** open `PlantVillage_ONNX_Stage4_GPU.ipynb` in the Colab session where the T4 GPU is connected, ensure the project folder is available in Drive at the notebook's expected path (or set `PROJECT_OVERRIDE` if its location differs), then select **Runtime → Run all** once. The notebook creates a timestamped run directory under `backend/ml/experiments/stage4_independent_validation/plantvillage_onnx_heldout_gpu/`.

After that run, retrieve the timestamped run outputs and verify `runtime_preflight.json` and the full `onnxruntime_profile.json` show at least one CUDA-assigned node before treating any metrics as GPU-evaluated. If these files are not generated by the run, the result remains incomplete; do not infer missing metrics.

## Git and preservation

The branch is `master`, configured author is `VarshaMurugadhass <varshascrafty@gmail.com>`. The initial working tree contained numerous unrelated modifications and untracked files; they were preserved. No push was performed. The Stage 4 preparation notebook already has commit `6a12b3d4`. This report is the only new file created for this work and should be committed separately after review.
