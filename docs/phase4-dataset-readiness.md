# Phase 4 dataset readiness report

Audit date: 2026-10-28. No data was downloaded, relabeled, or moved. The existing PlantDoc manifest and evaluation report were not modified.

## Existing local data

`datasets/plantdoc/manifest.jsonl` is an existing provenance manifest, not the new Phase 4 intake schema. It contains **2,578** PlantDoc rows (2,342 train / 236 test), 28 source folder labels, image paths, dimensions, SHA-256, source URL/revision and load-error fields. All 2,578 listed image paths exist and the manifest reports no image-load errors. The repository-level `LICENSE.txt` and `ATTRIBUTION.txt` are present, but licence and attribution are not repeated on each row. It has no explicit health-status, reviewer, label-confidence, capture-group or duplicate-group fields.

| Readiness item | Count / result |
| --- | ---: |
| Legacy manifest image rows / readable existing files | 2,578 / 2,578 |
| Invalid/missing files or manifest loading errors | 0 |
| Distinct SHA-256 values | 2,566 |
| Extra exact-duplicate copies | 12 |
| Exact-hash identities crossing train and test | 11 |
| Explicitly mapped disease rows | 1,536 |
| Ambiguous/generic labels retained as unknown | 1,042 |
| Explicit healthy rows | 0 |
| Records validated against the new CSV intake schema | 0 (the legacy JSONL is not that schema) |

The **1,536 diseased** count comes only from the existing explicit `COMPATIBLE_LABELS` mapping; the 1,042 generic/ambiguous labels are unknown, never healthy. These 17 disease classes are present:

| Model disease label | Count |
| --- | ---: |
| Apple scab / cedar apple rust | 93 / 89 |
| Corn gray leaf spot / common rust | 68 / 116 |
| Grape black rot | 64 |
| Bell pepper bacterial spot | 71 |
| Potato early / late blight | 117 / 105 |
| Squash powdery mildew | 130 |
| Tomato bacterial spot / early blight / late blight / leaf mold / Septoria / spider mites / yellow leaf curl virus / mosaic virus | 110 / 88 / 111 / 91 / 151 / 2 / 76 / 54 |

Crop-level mapped disease and unknown counts (healthy count is zero for every crop):

| Crop | Diseased | Unknown | Binary healthy/disease coverage |
| --- | ---: | ---: | --- |
| Apple | 182 | 91 | Missing healthy |
| Blueberry | 0 | 117 | Missing healthy and mapped disease |
| Cherry | 0 | 57 | Missing healthy and mapped disease |
| Corn (maize) | 184 | 192 | Missing healthy |
| Grape | 64 | 69 | Missing healthy |
| Orange | 0 | 0 | No PlantDoc records |
| Peach | 0 | 112 | Missing healthy and mapped disease |
| Pepper, bell | 71 | 61 | Missing healthy |
| Potato | 222 | 0 | Missing healthy |
| Raspberry | 0 | 119 | Missing healthy and mapped disease |
| Soybean | 0 | 65 | Missing healthy and mapped disease |
| Squash | 130 | 0 | Missing healthy |
| Strawberry | 0 | 96 | Missing healthy and mapped disease |
| Tomato | 683 | 63 | Missing healthy |

“Unknown” counts preserve source folders whose names do not establish a disease or healthy condition. Some generic folder names identify a crop but not a disease; the “Corn leaf blight” label is also too broad for an exact disease mapping. Per-image expert review would be required to change those statuses.

The stored cross-dataset report remains **20.63% top-1** on 126 compatible PlantDoc test images after excluding 11 exact train/test overlaps. It is a disease-only metric: its compatible test labels contain 134 images before duplicate exclusion and **zero healthy ground-truth samples**. It cannot produce a healthy-vs-diseased score. PlantDoc/model-training-image overlap has not been independently audited, and near-duplicates have not been audited.

No crop currently has both explicit healthy and mapped diseased records in this dataset. Therefore **no crop is ready for a healthy-vs-diseased test from PlantDoc**, and no meaningful healthy/disease sample sufficiency claim is possible. All current 38-class model crops must remain outside binary performance claims until both statuses are reviewed and represented. This includes the model’s structurally incomplete crops: Blueberry, Raspberry, Soybean (healthy-only model labels) and Orange, Squash (disease-only model labels).

## Proposed intake and storage

See [`dataset-intake.md`](dataset-intake.md) for the CSV schema, validator command, grouping procedure, and model-comparison protocol. The CSV template currently has a header only; no new intake images are present.

| Candidate | Source-reported download | Licence / suitability |
| --- | ---: | --- |
| [Mendeley seven-crop leaf dataset](https://data.mendeley.com/datasets/hgshn2zg3t/1) | 9.46 MB resized original archive; 74.1 MB augmented archive. Extracted size is not listed; reserve archive plus extracted data and a working copy after inspecting contents. | CC BY 4.0. Includes healthy and diseased examples, but none of its seven crops overlaps current supported model crops and most images reportedly use a plain white background. Workflow pilot only. |
| [Hugging Face PlantVillage](https://huggingface.co/datasets/mohanty/PlantVillage) | 2.18 GB archive; allow archive plus extracted data and a working copy (several GB total; exact extracted size to measure). | CC BY-SA 3.0 per dataset card. It overlaps the model’s PlantVillage training source, so it is not an independent final test for this production model. Licence review required before use. |
| [PlantDoc](https://github.com/pratikkayal/PlantDoc-Dataset) | Already local; source archive about 984 MB. | CC BY 4.0 at the repository; root licence and attribution files are local. It remains useful as disease-oriented cross-dataset evidence, not as a binary healthy/disease test. |

These source sizes and licence declarations were checked against the dataset pages/repository. The estimates for extraction and working copies are storage planning only. Do not download a candidate until the intended use, per-image rights, attribution, archive contents and required free disk space are reviewed and approved.

## Next data blocker

The highest-priority missing data is expert-reviewed field photography for supported crops with both healthy and diseased labels, provenance and group metadata. The existing local datasets do not meet that requirement. A separate binary candidate and a two-stage system can be compared only after such data is split by plant/source/capture group into train, validation, locked test and external field evaluation sets. Near-duplicate protection requires a real perceptual review process; the new validator currently detects exact hashes only.
