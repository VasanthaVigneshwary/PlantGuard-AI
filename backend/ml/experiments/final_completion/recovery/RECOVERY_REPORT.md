# Emergency Model Recovery Report

**Date:** 2026-11-26  
**Disposition:** Existing production ONNX model and a previously downloaded 100% PlantVillage test-evaluation bundle were recovered. No retraining or evaluation rerun was performed. The result is internally consistent with the saved test manifest but is not cryptographically bound to the active model bytes or its training membership.

## Search performed

Searched the project (excluding virtual environments, node modules, Python runtime, and raw dataset contents), Git history and Git LFS inventory, `C:\Users\Varsh\Downloads`, `Documents`, `OneDrive`, and accessible Codex attachment storage for `.ipynb`, Keras/HDF5, TensorFlow checkpoints, PyTorch/safetensors, ONNX, TensorBoard, training logs, CSV/JSON metrics, and screenshots. The relevant accessible user folders contained the four evaluation outputs in Downloads; no additional Plant Guard training checkpoint, executed notebook, history, TensorBoard event, or training screenshot was found. ZIPs in Downloads were listed without extraction; none contained model/training members.

Google Drive/My Drive paths are not mounted (`C:\Users\Varsh\Google Drive`, `C:\Users\Varsh\My Drive`, `G:\My Drive`, and `H:\My Drive` were absent), and no Drive/Colab connector is available in this session. Browser/Colab access was not attempted. OneDrive was searchable, but had no candidate training artifacts.

### Project and Git evidence

- The local, loadable model remains `backend/ml/models/efficientnet_v2_s_best.onnx` plus its 80.6 MB external tensor file. SHA-256: ONNX `14c03ae2b47b23a90a0176e70fe2fc46077fc5ae26dc46813966abdee0eb0c0a`; sidecar `038e6093bb41434def59a3c2375fbfc13c86f6af046e7f0a5b7b9015aa29b497`. The artifact is tracked through Git LFS; Git history adds it at `a56d6987` (2026-10-23), in a commit described as inference/workflow verification, not training or export.
- ONNX Runtime metadata says the graph producer is PyTorch and graph strings identify `torchvision.models.efficientnet.EfficientNet`. Embedded block groups have depths `[2,4,4,6,9,15]`, structurally matching the EfficientNetV2-S torchvision layout. This is stronger architecture evidence than the filename; the exact export source/checkpoint remains absent.
- The only Keras artifacts found are `backend/ml/models/plant_disease_efficientnet.keras` and the protected root backup `plant_disease_efficientnet_BACKUP.keras`. They are byte-identical (38,655,526 bytes; SHA-256 `24573478ea38cfbc1aa2e0d5495f746062a9c94e49adc4677d1a8a3d52d88f49`) and their archived model config is EfficientNetB0 with 38 outputs, not EfficientNetV2-S. Hugging Face cache metadata for `BiernyVR/crop-disease-classifier` matches this Keras hash; its cached file listing contains no ONNX artifact. The model card's ONNX link therefore does not establish that this ONNX was exported from that repository's cached Keras model. They are not verified V2-S checkpoints and were not loaded, exported, changed, or overwritten.
- Git LFS history identifies the Keras artifact at `0fd34071` (2026-09-29), and the ONNX artifact at `a56d6987`. No separate best/latest checkpoint or training log appeared in project/Git history. The only local notebook is `stage3_preflight/PlantVillage_ONNX_Heldout_Colab.ipynb`; it has six cells, zero execution counts and zero saved outputs. It is an evaluation notebook, not a training notebook.

## Recovered 100% result

The four original output files were found in `C:\Users\Varsh\Downloads` and copied unchanged to `recovery/colab_results/`. A related OneDrive screenshot was also recovered and copied unchanged; its SHA-256 is recorded in `MODEL_PROVENANCE.md`.

The JSON identifies **8,154 images**, **38 classes**, top-1 accuracy 1.0, macro precision/recall/F1 1.0, weighted F1 1.0, and providers `CUDAExecutionProvider` and `CPUExecutionProvider`. Its key is `plantvillage_test.csv`; therefore this is a reported **held-out test evaluation**, not training or validation accuracy.

Independent arithmetic checks against the saved local test manifest found:

- Reported confusion matrix is 38×38; row/column order exactly matches the approved 38-class mapping.
- Matrix sum = 8,154; diagonal sum = 8,154; off-diagonal sum = 0.
- Every one of the 38 reported class supports matches the current local `plantvillage_test.csv`; support totals 8,154.
- All 38 rows in the saved per-class CSV report precision, recall and F1 of 1.0.
- The Colab notebook source requests the exact filename `backend/ml/models/efficientnet_v2_s_best.onnx` and sidecar, reads the fixed `plantvillage_test.csv`, asserts 8,154 test rows and 38 labels, and uses CUDA-enabled ONNX Runtime. Its preprocessing matches production code: EXIF transpose, RGB, bilinear 224×224, divide by 255, ImageNet mean/std, NCHW.

The recovered screenshot shows `PlantVillage_ONNX_Heldout_Colab.ipynb`, test-inference cell `[13]` marked complete in about one minute, and a T4 (Python 3) runtime. The visible cell contains the batched ONNX loop and the 8,154-row assertion; the screenshot does not display the aggregate metrics. The screenshot timestamp (22:50) precedes the downloaded JSON and CSV timestamps (22:51), consistent with the same Colab run. Together these provide stronger evidence that the downloaded JSON came from the completed notebook on a T4 GPU. The notebook targets the current ONNX filename, whose graph structure matches EfficientNetV2-S. The downloaded JSON still does **not** contain the actual model SHA-256, test-manifest SHA-256, source-archive hash, evaluator version/commit, preprocessing record, per-image predictions, or checkpoint identifier. Therefore the result is strongly associated with the V2-S ONNX test run, but not cryptographically bound to these exact model bytes.

## Training and leakage assessment

The active model README/model card describes the ONNX artifact as EfficientNetV2-S trained on PlantVillage and reports its own validation figure. The image-level training list, source checkpoint, training code/config, epoch history, export record, and best/latest checkpoint were not recovered. The model card's claimed 54,306-image dataset count is close to the full PlantVillage source; it raises a substantial possibility that the 8,154-image split was included in training or model selection, but the exact overlap is **unknown**, not confirmed. The saved train/validation/test manifests themselves have zero exact cross-split hash leakage; that only proves separation among the new manifests, not separation from the pre-existing model's training data.

The 100% result should therefore be retained as a real recovered Colab report, reported as **PlantVillage test-split accuracy (reported 100%; arithmetic verified; exact model binding and test independence unverified)**. Do not relabel it as training accuracy, validation accuracy, or independent external validation. PlantDoc Stage 4 remains a separate baseline and was not rerun or used for any selection.

## Recovery action

The existing ONNX is available and has already passed local load/inference smoke tests; further PlantVillage evaluation or retraining is not needed to recover the saved result. Full provenance recovery is blocked only by inaccessible Google Drive/Colab source material and missing hashes/logs. See `RECOVERY_PLAN.md` for the single required access action. No `TRAINING_NOTEBOOK_PLAN.md` was created because training is not established as necessary and a usable ONNX already exists.
