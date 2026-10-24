# PlantDoc evaluation workflow

The local PlantDoc copy belongs under `datasets/plantdoc/`, which is excluded by
`.gitignore`. Keep the original `train/` and `test/` directories separate. The
manifest records each image's original ZIP path, ground-truth folder label,
split, dimensions, SHA-256, and any image-loading error. On Windows, filenames
that cannot be represented or coexist are encoded/shortened deterministically;
the original archive path remains in the manifest and image bytes are unchanged.

## Prepare and rerun

The archive is available from the official repository at
<https://github.com/pratikkayal/PlantDoc-Dataset>, pinned to snapshot
`5467f6012d78d1c446145d5f582da6096f852ae8`. From the repository root:

```powershell
.\scripts\plantdoc-evaluate.ps1 -Prepare
```

Preparation downloads the official codeload archive if it is not already in
`datasets/plantdoc-source.zip`, verifies ZIP CRCs and every image, then writes
`datasets/plantdoc/manifest.jsonl`. Subsequent runs use the retained manifest:

```powershell
.\scripts\plantdoc-evaluate.ps1
```

The evaluation calls the same `ml.predict.predict_disease` path used by the
backend. It runs inference on every image in the original test split. Accuracy,
per-class precision/recall, and the 38-class confusion matrix use only test
labels with explicit crop-and-disease compatibility mappings in
`backend/plantdoc_dataset.py`. Generic labels such as `Apple leaf` are not
assumed healthy. Unmappable labels are still inferred and recorded, but excluded
from classification metrics. Test files with SHA-256 hashes also present in the
train split are likewise excluded from metrics to avoid train/test leakage;
their inference records remain in the report. Failures are retained in
`datasets/plantdoc/plantdoc-evaluation.json`.

PlantDoc's README describes 2,598 examples, 13 plant species, and up to 17
disease classes. The checked-out official archive currently contains 2,578
image files in its provided train/test folders (2,342 train, 236 test); the
difference from the README's stated total is disclosed rather than filled with
other sources. The repository includes `LICENSE.txt` under CC BY 4.0. Keep
creator attribution, the license link, and the local filename-adjustment notice
in `datasets/plantdoc/ATTRIBUTION.txt` with the data.

Evaluation is on an untouched test split; do not use those images to train or
tune. PlantDoc is a separate source from the PlantVillage data identified in the
active model card, but exact source-image overlap has not been independently
audited. The resulting subset metrics do not represent all model classes or
real-world field conditions, and model output scores remain uncalibrated.
