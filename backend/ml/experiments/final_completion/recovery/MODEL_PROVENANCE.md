# Model and Evaluation Provenance

## Artifact inventory

| Artifact | Observed evidence | Interpretation |
|---|---|---|
| `backend/ml/models/efficientnet_v2_s_best.onnx` | 1,392,480 bytes; SHA-256 `14c03ae2b47b23a90a0176e70fe2fc46077fc5ae26dc46813966abdee0eb0c0a`; tracked by Git LFS; added in `a56d6987` on 2026-10-23. ONNX Runtime reports float32 input `[batch,3,224,224]`, logits `[batch,38]`. Graph producer is PyTorch; embedded torchvision EfficientNet block group depths are `[2,4,4,6,9,15]`. | Existing production artifact; graph structure matches EfficientNetV2-S. Successfully loadable; training/checkpoint lineage is absent locally. |
| `efficientnet_v2_s_best.onnx.data` | 80,609,280 bytes; SHA-256 `038e6093bb41434def59a3c2375fbfc13c86f6af046e7f0a5b7b9015aa29b497`; tracked by LFS alongside ONNX. | Required external tensor weights for production ONNX. |
| `backend/ml/models/plant_disease_efficientnet.keras` | 38,655,526 bytes; SHA-256 `24573478ea38cfbc1aa2e0d5495f746062a9c94e49adc4677d1a8a3d52d88f49`; serialized config says Sequential / EfficientNetB0 / 38 outputs. LFS-added in `0fd34071` on 2026-09-29. | Legacy Keras model. Not the EfficientNetV2-S checkpoint for the active ONNX. |
| `plant_disease_efficientnet_BACKUP.keras` | Same byte size and SHA-256 as the legacy Keras file. | Exact duplicate backup; preserved and never overwritten. |

The two Keras copies' SHA also matches local Hugging Face cache metadata for `BiernyVR/crop-disease-classifier`. The cached repository file listing contains the README, class names, inference code, and this EfficientNetB0 Keras artifact, but no ONNX file. The README/model-card link that attributes the ONNX to the repository is therefore not verified by the cache contents. The Keras artifact's EfficientNetB0 architecture means it cannot be treated as the source checkpoint for the V2-S ONNX. No parity/export test was performed; TensorFlow import is blocked by Windows Application Control, and the architectures differ.

## Colab test result identity

Original downloaded result artifacts and SHA-256:

| File | SHA-256 |
|---|---|
| `colab_onnx_evaluation.json` | `7a6269341534aee79c7840cdd45ddfb128f4d6202a1ca7306afdb25571f30ca4` |
| `colab_onnx_per_class_metrics.csv` | `263e85e46cad4d9152390de63f52033a121de80810370b83460f582088e2b532` |
| `colab_onnx_confusion_matrix.csv` | `62493658db7e93c2a1a7f6b42a98df53e0a391fa6264968b652e35e6e0853674` |
| `colab_onnx_confusion_matrix.png` | `4abf74b7697033f15df068295310581543755c46b6eee685f1c58916c35fe7c2` |
| `colab_evaluation_screenshot_2026-11-25.png` | `162e42e751954feb80dd21fea42140238aa88262dc4533098d8cf512a4026876` |

The screenshot shows the Colab notebook's PlantVillage inference cell completed (cell 13, about one minute) on a T4 GPU runtime shortly before the output files were downloaded. It displays the batch inference code and 8,154-row assertion, but not the metrics themselves. Result JSON metadata fields present: image count, class count, reported aggregate/per-class metrics, execution providers, and manifest filename. It omits model/checkpoint SHA, manifest/archive SHA, code version, and per-image prediction rows. The screenshot and notebook source make association with the active ONNX path substantially more likely, but do not cryptographically prove the exact model bytes used.

## Reported metrics and verification

- Dataset/split indicated: PlantVillage `plantvillage_test.csv`, 8,154 rows, all 38 approved labels.
- Reported top-1 accuracy: 100%; macro precision/recall/F1: 100%; weighted F1: 100%; all 38 per-class precision/recall/F1: 100%.
- Saved confusion matrix: 38×38, diagonal 8,154, off-diagonal 0.
- Every matrix row support equals the matching class count in the local test manifest; all supports sum to 8,154.
- Providers are reported as CUDA and CPU. The exact Colab runtime version and device type are not retained in the result JSON.

Classification: **reported held-out test result for the Colab notebook's EfficientNetV2-S ONNX path; arithmetic and class-support alignment verified; exact model-byte binding and model-vs-test independence unverified.**

## Training source and leakage

The model documentation attributes the active ONNX model to PlantVillage and reports a 54,306-image training dataset, but the training set manifest, checkpoint, epoch history, TensorBoard logs, export script, and image-level membership records are not available locally. Since 54,306 approximates the full PlantVillage release, overlap with the 8,154-image test split is a material risk. The available evidence does not prove either overlap or separation.

The Stage 3 manifest audit confirms no exact duplicate hashes among its new train/validation/test partitions. It cannot determine whether the pre-existing ONNX training process used the same images. Keep the 100% result and state this limitation explicitly; it is not independent external validation. PlantDoc's separate 123-image/16-class Stage 4 baseline remains unchanged.
