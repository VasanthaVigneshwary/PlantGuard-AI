# Final Train/Test Leakage and Model Provenance Audit

**Audit date:** 2026-11-26
**Scope:** Evidence-only audit. No training, inference rerun, model conversion, dataset/manifests/class map/database edits, or Stage 4 changes were made.

## Executive finding

- **VERIFIED:** the recovered PlantVillage Colab bundle reports 100% top-1, macro precision, macro recall, macro F1 and weighted F1 on 8,154 images and 38 classes. The saved 38×38 confusion matrix has 8,154 total, 8,154 diagonal and zero off-diagonal; all row supports match the current test manifest, and all 38 per-class scores are 1.0. This is an arithmetic and label-support check, not a fresh inference run.
- **VERIFIED:** exact SHA-256 comparison of the current 8,154-row test manifest against the current generated Stage 3 train (37,993) and validation (8,158) manifests found zero overlapping test images. All test rows had a SHA-256. There are 21 exact duplicate groups/21 extra files across the complete current split manifests; every group is confined to one split and one class, so there are zero cross-split exact-duplicate groups. The member-level details are in `exact_duplicate_groups.csv`.
- **UNABLE TO ESTABLISH:** the 8,154 test images' independence from the original EfficientNetV2-S training, validation, checkpoint-selection, and tuning process. The Stage 3 split manifests were generated for preflight/evaluation and are not the model's original membership records. No original train/validation list was found.
- **PLAUSIBLY LINKED:** the historical 100% result to the current production ONNX inference path, because the Colab notebook names that ONNX and external sidecar, its inference cell completion is shown in a T4 screenshot, and the output files were downloaded shortly afterward. The files do not contain model/data hashes, so exact artifact identity remains unverified.
- **NOT VERIFIED:** original model-training provenance, original preprocessing, checkpoint identity, epoch count, training/validation metrics, and whether any held-out images influenced model selection.

Accordingly, retain the result with this label: **“Historical 100% PlantVillage evaluation result — test-set independence and model provenance not yet verified.”** It is not proof of independent 38-class generalization and is not proven invalid.

## Evidence inventory and recovered items

`file_inventory.csv` records found/missing status, path, size, local modification time, SHA-256 where available, and notes. It includes the source PlantVillage ZIP (2,184,723,441 bytes), the current generated manifests, the recovered evaluation bundle and screenshot, production ONNX + sidecar, class mapping, local Colab notebook, legacy Keras artifact, and missing original-run evidence.

The recovered JSON, per-class CSV, confusion-matrix CSV/PNG and screenshot are preserved unchanged in `../recovery/colab_results/`. The four evaluation output hashes match the originals in Downloads; the screenshot is from the accessible OneDrive Screenshots folder. Hashes are recorded in the inventory and `../recovery/MODEL_PROVENANCE.md`.

## Train/test overlap

### Current saved Stage 3 manifests

| Comparison | Test images checked | Reference images | Exact SHA-256 test overlap | Archive-member path overlap |
|---|---:|---:|---:|---:|
| Test vs Stage 3 generated train | 8,154 (100%) | 37,993 | 0 | 0 |
| Test vs Stage 3 generated validation | 8,154 (100%) | 8,158 | 0 | 0 |

The 21 exact duplicate groups found across the three generated splits comprise 13 train, 5 validation and 3 test groups. All are within one split and one class; none crosses split boundaries. The three duplicate groups inside test mean the test manifest contains 3 extra byte-identical files relative to unique content. They do not overlap train or validation. Exact results and paths are in `train_test_overlap.csv` and `exact_duplicate_groups.csv`.

**Perceptual hash:** NOT RUN. No suitable perceptual-hash package (`imagehash`, `imagededup`, OpenCV `cv2`, or `phash`) is installed in the existing `.venv.stage3`. No package was installed solely for this audit. Thus near-duplicate similarity between PlantVillage splits was not assessed here.

### Original model-training membership

**MISSING:** no original V2-S run train manifest, validation manifest, image membership list, or training checkpoint/log. The zero overlaps above apply only to the current Stage 3 generated manifests. They cannot establish that the older model was trained without the 8,154 test images.

The local model README attributes the ONNX to PlantVillage and a 54,306-image training dataset. The currently audited archive manifests contain 54,305 images. This near-full-dataset claim raises material leakage concern, but the one-image count difference and absence of image-level membership records prevent an exact overlap conclusion. The README's reported 99.89% validation accuracy was not independently reproduced in this audit.

## Training workflow and reconstruction

Only `stage3_preflight/PlantVillage_ONNX_Heldout_Colab.ipynb` was found locally. Source inspection confirms an evaluation-only workflow: it reads the fixed 8,154-row test manifest, predicts with ONNX Runtime in batches, computes metrics and saves reports. It has six cells, zero stored execution counts and zero outputs. The screenshot corroborates a completed inference cell on a T4 but displays no metric summary. See `notebook_training_evidence.md` for cell-by-cell findings.

The original training workflow is MISSING from accessible project/Git, Downloads, Documents, OneDrive and Codex attachment locations. Google Drive/My Drive is not mounted and there is no Drive/Colab connector available. The Stage 3 manifests use seed 42 but were generated for preflight/evaluation; no original split ratio, seed, exact dataset revision or original split code is established. Reconstructing from them would be **INVALID AS PROOF OF ORIGINAL SPLIT INDEPENDENCE**, so no reconstruction was attempted.

## Model provenance and class/preprocessing review

Production model and sidecar hashes, input/output contract, class order, and inference preprocessing are detailed in `model_provenance.md` and `file_inventory.csv`.

- Current ONNX: 224×224 NCHW float32 input and 38 outputs; model is structurally consistent with torchvision EfficientNetV2-S.
- `classes.json`, `class_names.txt`, test-manifest labels, and saved confusion-matrix axis order agree on the same 38 classes.
- The Colab evaluation preprocessing is identical to production `backend/ml/predict.py`: EXIF orientation, RGB, bilinear resize, `[0,1]` scaling, ImageNet mean/std and NCHW. The original training preprocessing is unknown.
- The only local Keras artifact is EfficientNetB0 with a 38-unit head, and its hash matches local Hugging Face cache metadata. The cached repository listing contains no ONNX model. It cannot serve as the V2-S source checkpoint or support parity testing.
- Direct checkpoint-to-ONNX verification is unavailable. ONNX graph architecture evidence supports but does not prove the original trained architecture or checkpoint lineage.

## Recovered 100% result versus Stage 4 PlantDoc

The PlantVillage result remains a historical PlantVillage test-split result with unverified model-training independence. It is distinct from the existing Stage 4 PlantDoc external evaluation, which is preserved and was not rerun or changed: 123 eligible examples, 16 observed mapped disease classes, top-1 19.51%, top-3 37.40%, macro-F1 19.47%. PlantDoc covers only a subset of the 38 outputs and is a different image domain. The two metrics are not combined or directly equivalent.

## Verdict table

| Question | Verdict | Basis |
|---|---|---|
| Do the current generated Stage 3 train/validation/test manifests have exact split leakage? | **VERIFIED: no cross-split exact SHA or member-path overlap** | 8,154 test hashes compared with both generated reference manifests; 0 overlap. This is not original model-training membership. |
| Was the recovered test set independent of the model's original training, validation or selection data? | **UNABLE TO ESTABLISH** | Original run manifests, membership records, checkpoint, training process and logs are missing. |
| Is the 100% report internally consistent with the saved 8,154-row test split? | **VERIFIED: yes, arithmetic/support alignment** | Confusion matrix, class axes, class supports and all per-class values match; no new inference was run. |
| Is that report exactly bound to current ONNX bytes? | **NOT VERIFIED; PLAUSIBLY LINKED** | Notebook uses the active ONNX path and screenshot supports execution; result omits model hash. |
| Is production ONNX architecture consistent with EfficientNetV2-S? | **STRUCTURALLY CONSISTENT** | ONNX graph producer/operator details and torchvision stage depths; no training checkpoint/export record. |
| Is production ONNX training provenance independently verified? | **NOT VERIFIED** | No original checkpoint, epoch history, training code/config or export lineage. |

## Limitations and next evidence needed

1. Provide the original Google Drive/Colab training-run folder as a read-only synced location under `backend/ml/experiments/final_completion/recovery/source/`, retaining notebook/script/config, original train/validation membership, checkpoint(s), epoch logs, export record and any model/test hashes.
2. Compare exact image hashes of the recovered original training and validation membership against all 8,154 test rows; include any established original split paths. Resolve checkpoint-to-ONNX linkage with architecture/export evidence and hashes.
3. If a suitable pHash library is available in the recovered original environment, optionally screen near-duplicates; review candidates rather than treating perceptual matches as proof.

Until that source run evidence is available, the historical 100% report can be preserved and described as reported, but no claim of independent test-set generalization should be made.
