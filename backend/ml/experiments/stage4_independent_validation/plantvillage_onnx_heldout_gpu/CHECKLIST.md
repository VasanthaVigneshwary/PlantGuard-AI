# Stage 4 Colab Execution Checklist

## Completed preparation

- [x] Existing Stage 4 PlantDoc report and files inspected; preserve them unchanged.
- [x] Stage 3 model, external tensor path, class order, fixed test manifest and ZIP paths inspected.
- [x] Current PlantVillage test manifest is 8,154 rows, test-only, all 38 labels; its exact SHA split audit remains in Stage 3.
- [x] Separate Stage 4 output location prepared; the Stage 3 notebook is left unchanged.
- [x] New notebook imports the production preprocessing function and verifies class order against production metadata.
- [x] Notebook requires ONNX Runtime profiling to confirm actual CUDA node execution before full inference.
- [x] Notebook writes each run to a unique folder and does not overwrite existing Stage 3/Stage 4 files.
- [x] No training, fine-tuning, model export or model/data edits were run.

## User-reported, not independently verified in this workspace

- [ ] Colab T4 runtime is connected.
- [ ] PyTorch reports CUDA available.
- [ ] Colab has confirmed all 8,154 manifest members exist in the ZIP.
- [ ] ONNX Runtime CUDA provider has not yet been confirmed active.

## Pending Colab execution

- [ ] Open `PlantVillage_ONNX_Stage4_GPU.ipynb` in Colab with the GPU runtime selected.
- [ ] Confirm the mounted Drive project root contains all required paths; if nested, set `PROJECT_OVERRIDE` to the directory containing `backend/`, `datasets/`, and `scripts/`.
- [ ] Run dependency setup and runtime diagnostics; record Python, PyTorch, CUDA, ONNX Runtime and provider versions.
- [ ] Confirm an ONNX Runtime session loads the production ONNX and external data, input `[batch,3,224,224]`, output 38.
- [ ] Confirm the profiled smoke batch has at least one node assigned to `CUDAExecutionProvider`; if not, stop and retain the failure/preflight output without claiming GPU evaluation.
- [ ] Complete inference only on the fixed test manifest; confirm 8,154/8,154 rows, all image hashes, all 38 classes and no failures.
- [ ] Review `evaluation.json`, `runtime_preflight.json`, `onnxruntime_profile.json`, predictions, all-class metrics and confusion matrix.
- [ ] Download/copy the complete unique run directory into this local folder without overwriting prior runs; verify recorded hashes.
- [ ] Update this checklist and preparation report with actual run evidence only after the files are present and inspected.

## Interpretation guardrail

Even if metrics reproduce 100%, label the result as a PlantVillage held-out test-split result. Original model training/selection membership is unknown, so it does not establish independent validation. Keep the separate PlantDoc result (123 eligible images, 16 observed classes, 19.51% top-1) unchanged and report it separately.
