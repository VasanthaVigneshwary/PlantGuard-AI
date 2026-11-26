# Recovery Plan - One Required Access Action

## Current state

The production ONNX and its external tensor data already exist and load. The recovered Colab result reports 100% on the 8,154-image PlantVillage test manifest; its confusion matrix, supports, and per-class metrics are internally consistent. No retraining is recommended now.

The remaining blocker is binding that report to the exact ONNX bytes and determining whether the test images were used by the original training/model-selection run. The notebook/JSON omit those hashes and image-level training records. No Google Drive folder is mounted or connected, and Colab browser access is unavailable in this session.

## Exact next action

Make the original Google Drive training folder used by Colab available to this workspace as a **read-only synced folder**, or place its original run directory at:

`backend/ml/experiments/final_completion/recovery/source/`

The folder should contain the original training notebook/script and config, checkpoint(s), per-epoch history/logs, export script/metadata, and any saved model/manifest hashes or training-image list. Preserve the originals; do not rename or replace production files. Once accessible, compare the recovered model/checkpoint SHA and manifest membership with the four copied Colab results before making any accuracy or independence claim.

No additional training notebook plan is warranted until the original run has been searched and an actual need for training is established.
