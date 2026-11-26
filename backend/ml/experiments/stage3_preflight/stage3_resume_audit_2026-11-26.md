# Stage 3 resume audit — 2026-11-26

## Verified artifacts and training status

- The only saved EfficientNetV2-S deployment artifact found is `backend/ml/models/efficientnet_v2_s_best.onnx` (1,392,480 bytes) with required external tensor file `efficientnet_v2_s_best.onnx.data` (80,609,280 bytes). Previous local verification loaded both through ONNX Runtime 1.32.0 using `CPUExecutionProvider` and classified the known Apple scab fixture as Apple scab. This is a smoke test only.
- `backend/ml/models/plant_disease_efficientnet.keras` (38,655,526 bytes) is the legacy Keras artifact. No new training checkpoint, epoch history, TensorBoard event, or training log was found in the ML experiment tree. Stage 3 training did not complete according to the available reports/artifacts.
- No saved `onnx_plantvillage_heldout_evaluation.json`, confusion matrix, per-class evaluation table, or Colab output files were found. The Colab notebook exists but has not been executed in the available record.

## Split and class mapping

- Existing fixed test manifest contains 8,154 rows, uses split label `test`, references all 38 output classes, and has distinct member paths. It is the held-out evaluation set and must remain unchanged.
- Archive-backed inputs are under `raw/color`; their path format and RGB/224 preprocessing are implemented in the local evaluator. Existing model preprocessing is EXIF transpose, RGB conversion, bilinear resize to 224x224, float32 [0,1] scaling, ImageNet mean/std normalization, and NCHW layout.

## Metrics status

No held-out metrics have been calculated. Missing results include overall accuracy; macro and weighted precision, recall, and F1; support, precision, recall, and F1 for each of 38 classes; the 38x38 confusion matrix; evaluation throughput/duration; and misclassified sample review. No metric should be inferred from softmax scores or the model card.

## Accuracy discrepancy

- The model README attributes 41.68% on 511 images to the legacy Keras artifact. The supplied description does not establish that those images, preprocessing, label mapping, or model hash match the current ONNX artifact.
- The current ONNX artifact’s model card has a self-reported 99.89% validation figure, but no matching independent local evaluation output is present.
- A repository-wide text search found no evidence for a measured 100% held-out accuracy. Treat any 100% figure as unverified unless its source, dataset, split, code, and model hash are produced.
- Therefore these numbers are not yet a controlled like-for-like comparison. The held-out PlantVillage test manifest can measure in-domain performance of the current artifact but cannot establish external field-photo performance or prove the model card's training history.

## Execution and remaining gap

- Local environment previously verified ONNX Runtime 1.32.0, NumPy 2.5.4, Pillow 12.3.0, and FastAPI 0.165.0; providers were Azure and CPU, with no CUDA provider.
- The 8,154-image CPU run was stopped for runtime reasons. Per current instruction, do not retry full evaluation on local CPU.
- The Colab notebook is committed at `backend/ml/experiments/stage3_preflight/PlantVillage_ONNX_Heldout_Colab.ipynb`; its execution requires an authenticated Colab GPU runtime and access to the project folder in Drive. Browser automation was unavailable in the prior attempt. No Colab outputs are available locally.
- Existing FastAPI API suite previously passed 20 tests under the isolated Stage 3 environment, including real-image upload tests. This is API regression evidence, not held-out accuracy.

## Gate

Stage 3 evaluation is not complete. The only remaining quantitative evaluation step is execution of the committed notebook on a Colab GPU and retrieval of its generated JSON, per-class CSV, confusion-matrix CSV, and confusion-matrix PNG. Do not claim accuracy or begin Master Prompt 2 until those real outputs are reviewed and tied to the local model and fixed test manifest.
