# Stage 4 — Independent Model Validation Plan

**Status:** planning only; no dataset downloaded, no inference run, and no model, manifest, or source data modified.

## 1. Stage 3 starting point

- The production artifact remains `backend/ml/models/efficientnet_v2_s_best.onnx` plus its external `.onnx.data` tensor file; model weights must remain untouched.
- Stage 3 verified a 38-label output mapping, the ONNX input contract `[batch, 3, 224, 224]`, and inference preprocessing in `backend/ml/predict.py`: EXIF orientation, RGB, bilinear 224×224 resize, float32 scaling to [0,1], ImageNet mean/std normalization, then NCHW layout.
- The 8,154-image PlantVillage test split is exact-duplicate separated from the new train/validation manifests, but it is not independent of this pre-existing model: the model is documented as trained on PlantVillage and no image-level training records exist. Do not use it to make an independent-validation claim.
- A prior Colab result reported 100% on that PlantVillage split; internal arithmetic checks passed, but the run did not record model, manifest, or archive hashes. Its score does not establish independent performance.
- The prior Keras score (41.68% on 511 images) used a different artifact and undocumented/absent test folders; it is not a fair baseline comparison.
- Stage 3 reports also identify limited local resources and a Windows TensorFlow Code Integrity restriction. Stage 4 uses the existing ONNX Runtime inference path, not TensorFlow or retraining.

## 2. Dataset recommendations and coverage

### Primary candidate: existing PlantDoc snapshot

Use the already available `datasets/plantdoc/` snapshot and its preserved original test partition first; do not redownload it. The project records 2,578 images in its pinned snapshot (2,342 train / 236 test). Its source paper describes internet-scraped images across 13 plant species and up to 17 disease classes. This better reflects varied image conditions than controlled PlantVillage imagery, though it is web-sourced rather than a purpose-built farm survey. [PlantDoc source repository](https://github.com/pratikkayal/PlantDoc-Dataset), [PlantDoc paper](https://arxiv.org/abs/1911.10317).

The approved local direct-equivalence map covers **17 of 38 output labels**:

| Crop | Directly mapped PlantDoc labels |
|---|---|
| Apple | Apple scab; cedar apple rust |
| Corn (maize) | Cercospora/gray leaf spot; common rust |
| Grape | Black rot |
| Bell pepper | Bacterial spot |
| Potato | Early blight; late blight |
| Squash | Powdery mildew |
| Tomato | Bacterial spot; early blight; late blight; leaf mold; Septoria leaf spot; two-spotted spider mite; yellow leaf curl virus; mosaic virus |

It **does not cover these 21 model labels**: Apple black rot; Apple healthy; Blueberry healthy; Cherry powdery mildew; Cherry healthy; Corn northern leaf blight; Corn healthy; Grape Esca; Grape leaf blight; Grape healthy; Orange Huanglongbing; Peach bacterial spot; Peach healthy; Bell pepper healthy; Potato healthy; Raspberry healthy; Soybean healthy; Strawberry leaf scorch; Strawberry healthy; Tomato target spot; Tomato healthy.

PlantDoc supplies no explicitly healthy labels in the local audit, so it cannot validate healthy-class recall or a complete disease-versus-healthy metric. The existing Stage 2 evaluation reports 20.63% top-1 accuracy and 20.73% macro F1 on 126 compatible disease-labeled test images after excluding 11 exact train/test duplicates. Keep that result as prior evidence; do not treat it as the new Stage 4 run or as full 38-class performance. PlantDoc/model-training image overlap and near-duplicates remain unaudited. [Local Stage 2 report](../stage2_dataset/STAGE2_REPORT.md), [local PlantDoc evaluation workflow](../../../../docs/plantdoc-evaluation.md).

### Optional complementary candidate: Plant Pathology 2020 (FGVC7)

This is a manually captured, expert-annotated, real-life apple dataset with variable lighting, angles, surfaces, and noise. It directly overlaps only **3 of 38** model classes: Apple healthy, Apple scab, and Apple cedar apple rust. The mixed/complex-disease category is not a single 38-class output and must remain unmapped for exact-class metrics. It is useful as an apple-only complement, never as a full-model validation. Access is through Kaggle and its competition rules; data use is limited to competition/academic research and the data may not be redistributed. Accept/review the required Kaggle terms before any access. [Dataset paper](https://arxiv.org/abs/2004.11958), [official Kaggle rules](https://www.kaggle.com/competitions/plant-pathology-2020-fgvc7/rules).

### Not a first choice: Plant Pathology 2021 (FGVC8)

It is another apple-focused, field-oriented source with multi-label and mixed-disease categories. Only direct labels such as healthy, scab, and rust overlap, while multi-disease and other disease labels do not map one-to-one to the 38 outputs. Dataset release/count reconciliation and its competition terms would need review. Prefer the existing PlantDoc snapshot and the smaller 2020 apple subset before considering this larger source. [Kaggle competition](https://www.kaggle.com/competitions/plant-pathology-2021-fgvc8), [project’s prior dataset assessment](../../../../docs/phase5-dataset-options.md).

**Coverage conclusion:** no reviewed candidate supplies independent field-like test examples for all 38 outputs, especially healthy classes. A genuinely comprehensive 38-class external validation will require separately sourced, expert-reviewed images for the missing classes, with provenance and capture-group metadata. Do not fill missing labels by guessing from generic folders or merge similarly named diseases.

## 3. Proposed evaluation procedure (after approval)

1. **Freeze the evaluation inputs.** Use the existing ONNX file, sidecar, `classes.json`, inference implementation, and the untouched PlantDoc test partition. Record SHA-256 hashes for the model, sidecar, class file, source manifest/archive, and evaluator before inference. Confirm model/runtime and dataset revisions in the result metadata.
2. **Audit source and leakage.** Verify image readability, label mapping, exact SHA-256 duplicates, and perceptual near-duplicate candidates between PlantDoc train/test and against any obtainable model-training records. Exclude exact duplicates across PlantDoc train/test from scoring and disclose exclusions. Because model training records are unavailable, classify model-level overlap as unknown, not zero.
3. **Keep label semantics strict.** Score only source labels with an approved direct 38-class mapping. Retain generic, ambiguous, healthy-unknown, and multi-disease images in an inference/exclusion log but exclude them from exact-class metrics. Do not evaluate train or validation images.
4. **Run the unchanged production path.** Call `backend/ml/predict.py` / `predict_disease` using its existing EXIF, RGB, resize, normalization, layout, and mapping logic. Do not calibrate, tune thresholds, adjust mappings, or alter weights on this test set.
5. **Produce metrics only for observed mapped labels.** Report image count, correct/incorrect, top-1 accuracy, top-3 accuracy, macro and weighted precision/recall/F1, per-class support/precision/recall/F1, and a labeled confusion matrix. Explicitly identify the observed subset; do not label these metrics “38-class accuracy.” Record raw softmax score as uncalibrated; optionally report ECE/Brier as diagnostics with binning/method stated, not as calibrated confidence.
6. **Review errors and reliability.** Save sample IDs and predicted/true labels for misclassified cases (avoid redistributing images); summarize errors by source class and crop. Record inference time/provider and failures. Do not tune a rejection rule on the locked test data.
7. **Report source-specific results separately.** PlantDoc results and, if separately authorized/accessed, Plant Pathology 2020 results remain separate tables. Do not pool them because class coverage, acquisition source, label semantics, and support differ.

## 4. Planned files after approval

Evaluation outputs will be stored under `backend/ml/experiments/stage4_independent_validation/`:

- `evaluation_config.yaml` — frozen model/data paths, source revision, seed where relevant, batch size, metric definitions, and exclusions.
- `input_hashes.json` — SHA-256 hashes and runtime/version details.
- `plantdoc_predictions.csv` — per-image IDs, split, source label, mapped label, output index, prediction, score, correctness, failure/exclusion reason; no image bytes.
- `plantdoc_metrics.json` — aggregate and per-class metrics with exact sample counts and limitations.
- `plantdoc_confusion_matrix.csv` and `.png` — observed mapped classes, explicitly named and labeled.
- `plantdoc_error_review.csv` — misclassified item IDs and metadata for manual review.
- `stage4_validation_report.md` — results, provenance, exclusions, leakage status, and limitations.

If Plant Pathology 2020 is separately approved and access terms accepted, use parallel `plant_pathology_2020_*` outputs with its own mapping and metrics.

## 5. Limitations and blockers

- Only 17 disease classes map directly from existing PlantDoc; no explicit healthy samples are available. Full 38-class independent coverage is unavailable among reviewed local data.
- Existing PlantDoc/model-training image overlap is unknown. PlantDoc is a separate dataset source from PlantVillage but its internet-scraped images could still overlap public training sources; provenance records for the ONNX model are absent.
- The existing PlantDoc 20.63% evaluation is narrow, small (126 scored items), and disease-only; its per-class supports vary. It is not all-38 validation.
- PlantDoc image-level rights may be more complex than the repository-level CC BY 4.0 statement because the source describes internet-scraped imagery. Preserve attribution and review source terms before redistribution.
- Plant Pathology 2020 requires Kaggle access/terms and covers only three direct output classes; its mixed category is not a direct 38-class label.
- No class-level performance may be reported for a class with zero eligible external test images.

## 6. Exact next steps

1. Approve or revise the dataset scope: existing PlantDoc-only (no new download), plus optional Plant Pathology 2020 apple subset.
2. After approval, verify the local PlantDoc files and stored test manifest against their source snapshot, then produce a new immutable Stage 4 input-hash record; do not alter Stage 2 files.
3. Audit exact/near duplicates and the approved source-to-model mapping; mark model training overlap unknown if no source image list can be obtained.
4. Run ONNX inference only on eligible untouched external test images using the unchanged backend preprocessing.
5. Review metrics, exclusions, and error examples; issue a source-specific Stage 4 report. Keep the 38-class coverage gap explicit.

**Stage gate:** stop here. No download, inference, model change, or dataset/manifest change was performed. Await approval before any Stage 4 evaluation work.
