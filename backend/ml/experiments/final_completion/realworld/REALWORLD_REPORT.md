# Real-world accuracy experiment preparation

## Diagnosis (reused Stage 4 PlantDoc predictions)
- Evaluation support: 123 images, 16 observed classes; 113 other saved rows were excluded by the prior Stage 4 audit.
- Correct crop/species: 44/123 (35.77%); exact disease class: 24/123 (19.51%).
- 79/123 errors cross crop/species; 20/123 preserve crop but miss disease. The larger failure is crop/species confusion.
- Frequent wrong pairs: Pepper bell Bacterial spot → Pepper bell healthy (5); Tomato Yellow Leaf Curl Virus → Strawberry Leaf scorch (4); Grape Black rot → Strawberry Leaf scorch (4); Apple Cedar apple rust → Corn Cercospora/Gray leaf spot (3); Tomato mosaic virus → Pepper bell healthy (3).
- Diagnosis script: `diagnose_plantdoc.py`; outputs `DIAGNOSIS.md` and `diagnosis.json`. No inference was rerun.

## Local data inventory and mappings
- PlantDoc source manifest: 2,578 images; 1,346 usable mapped original-source-train candidates from 17 directly compatible classes; 996 original-train rows remain unmapped/ambiguous. All candidate files and source-manifest hashes verified.
- Protected PlantDoc external set: exactly 123 eligible images; excluded from every training/validation and selection role. Existing Stage 4 results remain unchanged.
- PlantDoc licence: CC BY 4.0, from local `ATTRIBUTION.txt` (revision `5467f6012d78d1c446145d5f582da6096f852ae8`).
- Partial PlantDoc extract: 681 images; 0 admitted (uncertain source association/licence); inventory-only pHash matches are recorded in `leakage_audit.csv`.
- `backend/uploads`: 33 unlabeled/provenance-unknown photos, excluded. `test_images`: 1 fixture, excluded. No local PlantWild found.
- Follow-up hash audit: 34 upload/fixture paths hashed, 1 is undecodable; 450 duplicate-reference records (all exact SHA matches) include 20 upload files matching PlantVillage train, 0 matches to the 123-image PlantDoc evaluation set, and duplicates within the unlabeled folders. None are admitted for training.
- PlantVillage: existing archive has 54,305 images/38 classes; existing training manifest has 37,993 raw/color rows. Stage 3 records CC BY-SA 3.0; these are lab images.
- Field coverage is incomplete: 17/38 classes have field-train images; 21/38 have none; 22/38 have fewer than 10. `field_class_counts.csv` lists all 38 in approved order.

## Leakage-controlled data preparation
- Fixed seed: 20261127; exact SHA-256 checks and 64-bit DCT pHash (Hamming distance ≤6) were run. All 37,993 PlantVillage train ZIP members and all 1,346 mapped PlantDoc candidate files were verified against their manifests.
- PlantDoc protected-evaluation overlap: 0 candidate or PlantVillage-train matches. PlantVillage train rows removed for protected PlantDoc duplicates: 0.
- 1 PlantDoc field candidate matched PlantVillage train and was excluded; 8 conflicting-label near-duplicate candidate rows were excluded; 7 same-label near-duplicate rows were grouped to prevent train/validation separation.
- Result: `field_train.csv` 1,069; `field_val.csv` 268 (80/20 by class-level groups); group overlap 0. `plantvillage_train_filtered.csv` retains all 37,993 train rows. No original manifest/data changed.
- The 8,154 PlantVillage test manifest was not read by split generation. Prior path/SHA/stem checks remain evidence only; this experiment does not use those test images for training or model selection.
- pHash is a duplicate screen, not proof against all semantic/edited-image duplicates. Partial extract is not a training source.

## Prepared training/export/evaluation pipeline
- `train_realworld.py`: torchvision EfficientNetV2-S, unchanged 38-class order, cached ImageNet weights only; checks CUDA/T4, paths and SHA; 2 frozen-head + up to 8 full-network epochs; AdamW 1e-4, cosine schedule, label smoothing 0.1; field-val macro-F1 best checkpoint; 75-minute epoch-boundary cutoff.
- Field images are oversampled to at least 40% per epoch; PlantVillage capped at 300/class/epoch. Training augmentation only. Evaluation preprocessing matches production: EXIF transpose, RGB, direct 224×224 BILINEAR resize, /255, ImageNet mean/std, NCHW float32.
- `extract_colab_data.py` extracts only manifest members to `/content`, verifies SHA, and adds held-out data only with explicit `--include-evaluation` after training.
- `export_onnx.py`, `verify_onnx_parity.py`, `evaluate_old_vs_new.py`, and `README.md` provide separate experimental export, 20-image field-val parity, and same-preprocessing old/new comparisons.
- Evaluation scripts cover field_val, fixed 8,154-image PlantVillage test, and exactly 123 PlantDoc images; include top-1/top-3, macro/weighted F1, all-class metrics, confusion matrices, top confusions, hashes, failures, uncertainty/coverage, runtime/provider details. Threshold selection is field_val-only.

## Execution status and limitations
- Preparation: completed locally. Split audit/diagnosis executed and verified.
- Training: **TRAINING: NOT YET RUN**. Export/parity/new-model evaluation: **EVALUATION: NOT YET RUN**. **MODEL REPLACEMENT: NOT AUTHORIZED**.
- No dataset/weight downloads, installations, training, export or ONNX evaluation were performed. pytest is unavailable in the local experiment Python; syntax and artifact integrity checks are reported separately.
- T4 runtime estimate 35-75 minutes is unmeasured; small field coverage, label mapping noise, PlantDoc source/style differences, possible residual near-duplicates, and unknown original model provenance remain limitations. ONNX CUDA execution is not verified until Colab profiling records CUDA provider nodes.
- Recommendation: NEEDS MORE DATA
