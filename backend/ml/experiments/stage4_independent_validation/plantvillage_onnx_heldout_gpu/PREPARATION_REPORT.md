# Stage 4 PlantVillage GPU Evaluation — Preparation Report

**Status:** Prepared; Colab execution and CUDA activation are pending.

**Date:** 2026-11-26

## Completed locally

- Inspected `stage3_preflight` configuration, the saved manifest audit and Colab held-out notebook, production model documentation/preprocessor, and the existing Stage 4 PlantDoc plan, evaluator, configuration, metrics and report.
- The local expected inputs exist: EfficientNetV2-S ONNX, its required external tensor data, `classes.json`, `class_names.txt`, the 8,154-row fixed test manifest, and preserved `datasets/plantvillage-source.zip`.
- The local ZIP central directory contains 163,034 entries; this is a metadata inspection only. The notebook checks all 8,154 fixed test-member names and verifies each selected payload hash during inference.
- The manifest has 8,154 test rows and all 38 labels. `classes.json` and `class_names.txt` agree in approved order. The ONNX contract was previously verified as `[batch,3,224,224]` input and 38 output values.
- The evaluation preprocessing is aligned to production by importing `backend.ml.predict.preprocess_image`; no alternate normalization or class ordering is introduced.
- A new Stage 4 subfolder separates the PlantVillage run from Stage 3 evidence and the completed PlantDoc Stage 4 baseline.

## Path audit

| Input | Expected local path | Existing Colab Stage 3 notebook | New Stage 4 notebook |
|---|---|---|---|
| Project root | `D:\PlantGuard-AI` | `/content/drive/MyDrive/PlantGuard-AI` | Bounded auto-detection of root or one nested repo; explicit `PROJECT_OVERRIDE` if needed |
| ONNX + sidecar | `backend/ml/models/efficientnet_v2_s_best.onnx[.data]` | Correct relative path under `PROJECT` | Same relative path; both required and hashed |
| Labels | `backend/ml/models/classes.json` | Correct path under `MODEL_DIR` | Same path; additionally compared to production `class_names.txt` and `get_class_names()` |
| Fixed test manifest | `backend/ml/experiments/stage3_preflight/plantvillage_test.csv` | Correct path under `STAGE3` | Same read-only source; asserts 8,154 rows and test-only split |
| ZIP | `datasets/plantvillage-source.zip` | Correct path under `PROJECT` | Same path; checks all test members and each payload SHA during inference |
| Results | Stage 3 folder in old notebook | **Unsafe:** old notebook writes four `colab_onnx_*` files under `stage3_preflight` | Unique timestamped run folder under this Stage 4 subfolder; no Stage 3 overwrite |

The existing Stage 3 notebook's input paths are internally consistent if the `PROJECT` folder in Drive is the repository root. It can fail if Drive has a different or nested folder name; the new notebook detects the canonical and one-level nested layouts and otherwise requires setting `PROJECT_OVERRIDE`. The important functional issue corrected in the new workflow is output placement: results are now isolated in Stage 4, not written beside the Stage 3 manifest.

The local file identities checked during preparation were: ONNX `14c03ae2b47b23a90a0176e70fe2fc46077fc5ae26dc46813966abdee0eb0c0a`; external tensor data `038e6093bb41434def59a3c2375fbfc13c86f6af046e7f0a5b7b9015aa29b497`; class mapping `e2ca06291e5e079b7d6b0badec52673cd71a630fdee58d87d947c82f4b8a6d98`; fixed test manifest `3a29ab682c815a15cb78d490cfdcbc0c54128e7c0f6c8f048676298503560010`; and source ZIP `fba30c6a7965e49be94b47a62f8aff6cfb1c35c27f475f22092b56db41745e84`. The notebook recalculates and records model, sidecar, label, manifest and preprocessor hashes at run time; it hashes every selected image payload against its manifest row.

## Existing Stage 4 evidence retained

The existing parent folder is the completed PlantDoc independent-validation run. Its report remains unchanged: 123 eligible images, 16 mapped classes with examples, 19.51% top-1, 37.40% top-3 and 19.47% macro-F1. This new PlantVillage workflow is supplemental runtime/held-out evaluation, not a replacement or a full independent 38-class validation. The PlantVillage model-training overlap remains unknown.

## Colab execution state

User reports that a T4 is attached, PyTorch CUDA is available and all fixed test paths exist in the archive. These facts were not independently inspected from this Windows workspace. ONNX Runtime CUDA session activation is still **unverified**. The notebook uses `CUDAExecutionProvider` before CPU and requires profiled CUDA-assigned model nodes during its smoke batch before proceeding to full inference. Merely listing the provider will not be counted as GPU confirmation.

No accuracy, precision, recall, F1, inference timing or GPU success is claimed for this prepared run. The historical Colab 100% report was not reused as Stage 4 output. Full details and the run checklist are in `CHECKLIST.md`; execution notebook is `PlantVillage_ONNX_Stage4_GPU.ipynb`.
