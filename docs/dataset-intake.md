# Dataset intake and evaluation readiness

## Manifest format

Use UTF-8 CSV with the columns in [`dataset-manifest-template.csv`](dataset-manifest-template.csv). Keep one row per original image. `image_path` must be relative to the CSV and stay under its directory. Give each image a stable `image_id`; do not use a person's name, phone number, or precise home/farm coordinates.

| Field | Meaning |
| --- | --- |
| `image_id`, `image_path` | Stable record key and relative image file path. |
| `crop` | Exact crop spelling exposed by the model labels (for example `Tomato`, `Pepper, bell`, `Cherry (including sour)`). |
| `health_status` | Independently reviewed `healthy`, `diseased`, or `unknown`. Generic labels such as “leaf” remain `unknown`; they never imply healthy. A confirmed health status can be used even when exact disease identity is unknown. |
| `disease_label` | Optional exact disease identity, not health status. Use blank when disease identity is not established and for healthy/unknown records. A confirmed diseased record may leave it blank. If supplied, supported model disease labels must match the crop; healthy labels are contradictory here. A well-sourced disease label outside the 38-class model is retained with a warning and can support binary health evaluation, but not exact-class evaluation. |
| `label_source`, `reviewer`, `label_confidence`, `review_status` | How the label was established, anonymized reviewer ID, confidence (`high`/`medium`/`low`/`unknown` or 0–1), and `confirmed`/`reviewed`/`unreviewed`/`unknown` state. |
| `source_id`, `source_url`, `license`, `attribution` | Dataset or collection identifier/link, exact licence, and required attribution. An explicit statement such as `Attribution not required by licence` is suitable only when verified. Unknown licence/source is incomplete. |
| `training_permission`, `original_image_redistribution`, `model_weights_redistribution` | Separate permission decisions for training, redistribution of original images, and redistribution of derived model weights. Allowed values are `allowed`, `not_allowed`, and `unknown`. Missing values and legacy manifests default to `unknown`, never approval. |
| `rights_evidence`, `rights_restrictions` | Source and basis for the rights decision (for example, exact licence/version and relevant terms URL), plus conditions or restrictions. When any permission is `allowed` or `not_allowed`, both fields are required. Record conditions such as attribution, non-commercial use, or no image redistribution; explicitly state `No additional conditions identified after review` only if that conclusion was actually checked. |
| `plant_id`, `capture_group`, `duplicate_group_id` | Optional pseudonymous grouping values for the same plant, capture session/site group, source/augmentation family, or known duplicate cluster. Do not store precise coordinates. |
| `image_source` | `controlled_dataset` or `field_photograph`. |

`review_status` must be `confirmed` or `reviewed` for `healthy`/`diseased`; use `unknown` for unknown status. A supplied disease identity must be supported by its label source/reviewer even when outside the model taxonomy. The validator reports an unsupported exact disease identity as a warning rather than discarding an otherwise confirmed diseased record. This separates binary health-status data from exact 38-class disease evaluation. It does not permit an unsupported crop: `crop` remains one of the current model's crop names.

Permission fields are independent. A public download or attribution requirement does not by itself establish permission for model training, image redistribution, or model-weight redistribution. Use `allowed` only when the evidence has been reviewed and its conditions can be followed; use `not_allowed` when the source terms prohibit the use; leave `unknown` if terms are silent, ambiguous, or unreviewed. For conditional licences, record the conditions in `rights_restrictions`; `allowed` means the intended use is permitted subject to those recorded conditions. Model-weight permission remains `unknown` unless the terms or a documented rights decision address that use. The validator checks that explicit decisions cite evidence and restrictions, but it does not interpret licences or provide legal advice. Existing manifests without these optional columns remain readable and receive `unknown` defaults plus warnings.

`valid` means that the record passed the manifest's structural, image, label, and provenance checks; it does **not** mean that every intended use is permitted. Before training, filter to records whose `training_permission` is `allowed` and whose recorded conditions have been satisfied. Apply the corresponding permission field before redistributing original images or model weights. Do not use `unknown` as approval.

Validate with the existing Python environment:

```powershell
python backend\dataset_manifest.py datasets\intake\manifest.csv
```

The command prints a JSON report and returns nonzero if the manifest or any row is invalid. It does not discard invalid records. The header-only template includes one explanatory comment row; comment rows beginning with `#` in the `image_id` column are ignored, and existing CSV manifests without comments remain accepted. The five rights columns are optional for backwards compatibility. To save a report, use `--report path.json`; it creates the path exclusively and refuses to overwrite an existing file. The readiness report counts valid records, shows invalid record reasons and non-fatal warnings, health and supported disease labels by crop, the count of diseased records without a supported exact class, source/licence completeness, each permission status, exact-hash duplicates, and crop coverage. Counts are descriptive; the report does not declare a statistically sufficient sample size.

The validator checks exact SHA-256 duplicates and any supplied group IDs. It does **not** detect near-duplicates, the same leaf after substantial crop/rotation/compression, or the same plant from unrecorded sessions. Those require metadata and human review or a separately validated perceptual-image review. Do not claim near-duplicate protection from the SHA-256 check.

## Leakage-safe split procedure

1. Freeze each source version, licence text, original file list, label decisions, and hashes. Resolve label disagreements before model fitting; preserve unresolved records as `unknown` and exclude them from supervised metrics with an explicit count/reason.
2. Build connected groups from exact hashes and supplied `duplicate_group_id`, `plant_id`, `capture_group`, source-image identity, and augmentation lineage. Every connected group stays in one partition. Review perceptual-hash candidates manually; a perceptual match is a review aid, not proof of identity.
3. Assign groups to training, validation, and locked final test partitions before fitting. Stratify by crop and health/disease status where group counts allow; document impossible strata instead of splitting a group. Use training for fitting, validation for model/threshold selection, and open the final test only once for the chosen frozen system.
4. Keep a separate external field evaluation partition by source/site/time/device where possible. Do not mix it into training or tune on it. Report controlled and field results separately.
5. Preserve the manifest revision, group assignment file, random seed, code revision, model hash, and evaluation JSON for reproducibility. For later comparisons, evaluate the same locked examples with A) the existing 38-class ONNX model, B) a binary healthy/diseased candidate, and C) a two-stage candidate only if validation supports it.

Report health-status precision, recall, F1 and a 2×3 confusion matrix (true healthy/diseased; predicted healthy/diseased/uncertain), coverage, abstention rate and selective accuracy by crop and source. Report exact disease top-1 accuracy, macro F1, per-class support/precision/recall/F1 and confusion matrix separately. Unknown labels are not silently converted to healthy or disease labels. Incomplete model coverage remains outside the claimed scope: Blueberry, Raspberry and Soybean have only healthy output classes; Orange and Squash have only disease output classes. The other nine crop families have both kinds of output labels, but this is model-label availability, not evidence that the intake data covers them.

The existing evaluator's folder interface expects exact model class names. For new binary-labeled intake, first create a reviewed, leakage-safe export with exact supported class folders; do not alter unknown labels to make them fit that interface. The manifest validator itself does not run model inference or assign splits.

## Current local readiness

An existing `datasets/plantdoc/manifest.jsonl` records 2,578 PlantDoc source files, paths, split names, dimensions, exact hashes, source and revision. It predates this CSV intake schema and is not rewritten or automatically coerced; generic source folder labels do not establish healthy status. The repository has dataset-level licence and attribution files, but the JSONL does not contain per-record health status, review, or use-specific rights decisions. The detailed inventory and crop coverage are in [`phase4-dataset-readiness.md`](phase4-dataset-readiness.md). The CSV template contains no image records, so there are currently zero records validated against the intake schema. The stored PlantDoc result remains the only baseline: 20.63% top-1 on 126 compatible disease-only test examples after 11 exact train/test overlaps were excluded. It cannot establish binary healthy/diseased performance.

## Candidate sources for approval (nothing downloaded)

| Source | Published size / storage | Licence and fit |
| --- | --- | --- |
| [Mendeley Leaf Image Dataset, V1](https://data.mendeley.com/datasets/hgshn2zg3t/1) | 1,545 original 256×256 images; source lists a 9.46 MB resized archive and a 74.1 MB augmented archive. Plan for at least the archive size plus extraction space and a second working copy if needed. | CC BY 4.0. Seven crops with healthy/disease labels and expert review described by the authors, but none are current supported crops; most images have plain white backgrounds. Useful only as a workflow pilot, not target-crop accuracy evidence. Confirm archive contents and attribution before use. |
| [Hugging Face PlantVillage](https://huggingface.co/datasets/mohanty/PlantVillage) | Repository lists 2.18 GB `data.zip`; allow at least 2.2 GB download plus extracted data and a working copy (several GB free). | Dataset card declares CC BY-SA 3.0. Strong crop/class overlap with the production model’s training source, so use only for development/fine-tuning after licence review, never as independent final evaluation for this model. |
| [PlantDoc dataset](https://github.com/pratikkayal/PlantDoc-Dataset) | Already present locally; its source archive is about 984 MB. No new storage needed unless a separate immutable copy is requested. | Repository declares CC BY 4.0. It is realistic disease-oriented evaluation data, but current generic “leaf” labels cannot be assumed healthy, and it already has exact train/test duplicates that must remain excluded/grouped. |

For the main competition comparison, the highest-priority addition is an expert-reviewed, licence-cleared **field** dataset for Plant Guard-supported crops with both healthy and diseased examples. A suitable candidate source, exact archive size, per-image redistribution/training rights, crop coverage and label provenance must be checked before approval. Do not download any candidate in this phase. The Mendeley and PlantVillage sizes above are source-reported; disk space requirements are estimates and depend on extraction and retained copies.

## Current model scope and comparison plan

The production 38-label set spans 14 crops. Blueberry, Raspberry and Soybean have healthy labels only; Orange and Squash have disease labels only. A system cannot be evaluated as crop-specific healthy-vs-diseased for these incomplete classes without new supported labels, so keep them out of binary performance claims and return unsupported/uncertain where existing application logic requires it.

After data intake and licence approval, compare A/B/C on identical locked test IDs and an external field set, using validation-only model selection and calibration/rejection thresholds. Preserve all model artifacts separately and record hashes. CPU-only development on the i5-1334U with integrated graphics can support data checks and small inference/evaluation runs; training-time estimates need a measured pilot and RAM availability. No framework installation, download, training, or production-model change is part of this preparation phase.
