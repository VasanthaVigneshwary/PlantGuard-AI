# Model Provenance Audit

**Audit date:** 2026-11-26

## Artifacts and verified identities

| Artifact | SHA-256 | Finding |
|---|---|---|
| Production `efficientnet_v2_s_best.onnx` (1,392,480 bytes) | `14c03ae2b47b23a90a0176e70fe2fc46077fc5ae26dc46813966abdee0eb0c0a` | Present, loadable in prior verified ONNX Runtime checks, tracked by Git LFS; added at `a56d6987` in an inference/workflow commit. |
| External tensor `efficientnet_v2_s_best.onnx.data` (80,609,280 bytes) | `038e6093bb41434def59a3c2375fbfc13c86f6af046e7f0a5b7b9015aa29b497` | Required sidecar, present and tracked by Git LFS. |
| `classes.json` (1,550 bytes) | `e2ca06291e5e079b7d6b0badec52673cd71a630fdee58d87d947c82f4b8a6d98` | Exactly 38 ordered classes; matches `class_names.txt`; all 38 appear in the evaluation test manifest. |
| Legacy `plant_disease_efficientnet.keras` (38,655,526 bytes) | `24573478ea38cfbc1aa2e0d5495f746062a9c94e49adc4677d1a8a3d52d88f49` | Archived config is EfficientNetB0 with a 38-unit output layer, not the V2-S ONNX architecture. The protected root backup is byte-identical. |

No original EfficientNetV2-S training checkpoint, training notebook/script, export record, epoch history, or training-image membership list was found in accessible locations. There is no compatible V2-S Keras checkpoint for a parity test. TensorFlow import is also blocked by Windows Application Control in the available Windows environment. No model conversion or inference rerun was performed in this audit.

## Result-to-production association

The recovered Colab notebook explicitly loads `backend/ml/models/efficientnet_v2_s_best.onnx` and its `.onnx.data` sidecar from the project Drive folder. It checks a float image input of `[batch,3,224,224]` and 38 outputs. The screenshot shows the corresponding test inference cell completed on a T4; output files were downloaded shortly afterward. The active ONNX graph producer is PyTorch and its torchvision EfficientNet block depths `[2,4,4,6,9,15]` structurally match EfficientNetV2-S. These are mutually supportive clues that the result used the production ONNX path.

However, the evaluation JSON and screenshot do not store a model hash, sidecar hash, test-manifest hash, archive hash, code commit, or per-image predictions. Therefore the exact model bytes used in that Colab session cannot be proven from the recovered output bundle.

**Provenance verdict for recovered 100% result versus current production ONNX: PLAUSIBLY LINKED.** The notebook path, completed-cell screenshot, timestamps, and structural architecture evidence support the link; absent hashes and run artifacts prevent a verified byte-level connection. This is not a checkpoint-to-ONNX proof.

## Architecture, labels and preprocessing

- **Output dimension and input contract — VERIFIED for the current ONNX:** float32 `[batch,3,224,224]` input and float32 `[batch,38]` output according to the existing ONNX Runtime contract checks.
- **Label order — VERIFIED:** `classes.json` equals `class_names.txt` in exact order; the test manifest contains all 38 labels; the recovered confusion-matrix row and column order matches that mapping.
- **ONNX architecture — STRUCTURALLY CONSISTENT, not lineage-proven:** PyTorch/torchvision EfficientNet graph with stage depths matching V2-S. The filename and model README are supporting claims, not checkpoint provenance.
- **Colab versus production inference preprocessing — VERIFIED equal:** EXIF orientation, RGB conversion, bilinear 224×224 resize, float32 scale by 255, ImageNet mean/std normalization, NCHW. This confirms the evaluation/serving transform, not the original training transform.
- **Original training preprocessing — UNABLE TO ESTABLISH:** the training pipeline/config is missing; do not infer it from serving code or normalization embedded in the unrelated B0 model.
- **Keras parity — NOT AVAILABLE:** the recovered Keras artifact is EfficientNetB0 and therefore not a valid source for V2-S parity or export verification.

## Evaluation outputs

Original downloads were preserved unchanged in `../recovery/colab_results/`. Their JSON reports 8,154 images, 38 classes, 100% accuracy, 100% macro precision/recall/F1 and weighted F1. The confusion matrix sums to 8,154 with all counts on the diagonal; its class supports equal the saved test manifest, and every per-class metric is 100%. These checks verify output arithmetic and alignment, not model identity or independence.

## Trust boundary

The production artifact is a valid existing 38-output deployment model with a plausible connection to the historical Colab result. The **historical 100% PlantVillage evaluation result—test-set independence and model provenance not yet verified**. It must not be presented as proof of independent generalization. Direct checkpoint-to-ONNX verification is unavailable until the original training run files and hashes are recovered.
