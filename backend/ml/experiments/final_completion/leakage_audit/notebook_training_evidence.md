# Notebook and Training-Process Evidence

**Audit date:** 2026-11-26

## Accessible search scope

Reused the Stage 3 recovery search documented in `../recovery/RECOVERY_REPORT.md`. It covered the project (excluding environments, node modules, the Python runtime and raw dataset contents), Git/Git LFS history, Downloads, Documents, OneDrive and accessible Codex attachment storage. Google Drive/My Drive is not mounted, and no Drive/Colab connector is available. No original training notebook, script, checkpoint, epoch history, TensorBoard event, or image-level original training membership list was found in those accessible locations.

The only local Colab notebook found is `../../stage3_preflight/PlantVillage_ONNX_Heldout_Colab.ipynb`. It has six cells; every code cell has a null execution count and there are zero saved cell outputs. It is an evaluation notebook, not a training notebook.

## Actual notebook workflow

Inspection of the notebook cell source and ordering found:

1. Mounts Google Drive and points to the project folder on Drive.
2. Installs ONNX Runtime GPU and evaluation/plotting dependencies; asserts CUDA provider availability.
3. Loads `classes.json`, asserts the 38 unique classes, reads `plantvillage_test.csv`, asserts 8,154 rows and only `test` split, checks all labels and unique member paths, and opens the existing ONNX plus external tensor file.
4. Uses an ONNX Runtime session configured for CUDA with CPU fallback. Checks input `[batch,3,224,224]` and 38 outputs.
5. Applies EXIF orientation, RGB conversion, bilinear 224×224 resize, float32 `/255`, ImageNet mean/std normalization, then NCHW. Batches images from the ZIP and predicts with the existing ONNX model.
6. Calls `classification_report`, `confusion_matrix`, and `accuracy_score` on those predictions, writes the four evaluation result files and offers them for download.

The source contains no model construction, `fit`, `validation_data`, `ModelCheckpoint`, `EarlyStopping`, `ReduceLROnPlateau`, checkpoint-selection, or training loop. Its explicit use of test rows occurs only in inference and metric calculation. The local notebook's empty execution metadata means that copy alone is not evidence it ran. A recovered screenshot shows the inference cell completed on a T4 runtime; it does not show training cells or the metric output. The downloaded result bundle is arithmetically consistent with the test manifest but lacks model and data hashes.

## Questions the available evidence cannot answer

| Question | Finding |
|---|---|
| Was the original test dataset passed to model fitting? | **UNABLE TO ESTABLISH.** The original training process is missing. The accessible evaluation notebook uses the test set for inference only. |
| Was the test set used as validation data or monitored during training? | **UNABLE TO ESTABLISH.** No original training notebook/script/config or logs were recovered. |
| Did test results select a checkpoint or tune hyperparameters? | **UNABLE TO ESTABLISH.** No checkpoint-selection record, experiment log, or run history was found. |
| What architecture was actually trained? | **NOT VERIFIED.** The ONNX graph is structurally consistent with torchvision EfficientNetV2-S. No training source checkpoint or architecture config ties that graph to a run. The legacy Keras model is EfficientNetB0 and is not that source. |
| How many epochs and what training/validation metrics were recorded? | **MISSING.** No original epoch history or TensorBoard records were found. The 100% figures are a recovered test-evaluation report, not training or validation metrics. |
| Can the original split be reconstructed? | **NO—INVALID AS PROOF.** The available seed-42 Stage 3 manifests were generated on 2026-11-22 for preflight/evaluation. The original run's split code, seed, exact dataset revision and original membership list are absent. Reconstructing from these manifests cannot establish what the earlier model saw. |
| Does evaluation preprocessing match production inference? | **VERIFIED.** The evaluation notebook's transform equals `backend/ml/predict.py` for EXIF orientation, RGB, resize, scale, ImageNet normalization and NCHW. This does not establish the model's original training preprocessing. |

## Relevant Git/model records

- Git added the production ONNX artifact in commit `a56d6987` on 2026-10-23, described as inference/workflow verification; this is not a training/export record.
- Git added the legacy Keras artifact in `0fd34071` on 2026-09-29. Its archived config is EfficientNetB0 with 38 outputs.
- The local model README attributes the ONNX to EfficientNetV2-S/PlantVillage and reports 99.89% validation accuracy on a stated 54,306-image dataset. No matching run record was found. The current verified manifest total is 54,305, so the one-image count difference is unresolved and is not evidence of exact membership.
- Local Hugging Face cache metadata matches the legacy B0 Keras hash; the cached file listing contains no ONNX. The model-card link alone does not prove ONNX export lineage.

The search findings above describe accessible locations only. They do not establish that training files do not exist in an unmounted Drive/Colab account or another unavailable storage location.
