# PlantDoc candidate experiment

## Current evidence

The active `EfficientNetV2-S` ONNX pipeline uses RGB resize to 224×224,
ImageNet normalization, and the verified 38-entry order in `classes.json` and
`class_names.txt`. A pinned PlantDoc evaluation found 20.63% top-1 accuracy on
126 disease-labeled test images whose hashes do not occur in train. Eleven test
images overlap train by exact bytes; one additional training duplicate has
conflicting potato early/late blight labels. These are excluded from training
or metrics as appropriate. This evaluation is a limited dataset benchmark, not
a field-wide accuracy claim.

## Candidate experiment

`backend/train_plantdoc_candidate.py` trains a **from-scratch** torchvision
MobileNetV3-Small on the compatible PlantDoc training labels. It uses a stable,
stratified 85/15 train/validation split, image augmentations, class-weighted
cross entropy, AdamW, and early stopping on validation macro F1. It checks SHA
overlap between train/validation/test and excludes conflicted duplicate hashes.
The 126-image final test set is read only after training and checkpoint
selection. It compares the candidate against the saved production ONNX
predictions on the exact same test paths.

The October 24, 2026 CPU run used 1,181 training, 208 validation, and 126
leakage-free test images. The from-scratch candidate stopped after six epochs,
selected epoch 1, and collapsed to predicting only `Squash___Powdery_mildew`.
Its held-out top-1 accuracy was **4.76%** and macro F1 **0.57%**. The unchanged
production model scored **20.63%** top-1 and macro F1 **20.73%** on the same 126
examples. This candidate is a clear regression and must not be deployed. The
metrics are limited to the explicitly compatible PlantDoc subset, not all 38
classes or field images generally.

Run from the repository root, with PyTorch and torchvision installed in the
project environment:

```powershell
.venv\Scripts\python.exe backend\train_plantdoc_candidate.py datasets\plantdoc
.venv\Scripts\python.exe backend\benchmark_plantdoc_candidate.py datasets\plantdoc
```

The candidate checkpoint and report are written to the ignored
`datasets/plantdoc/candidate/` directory. The report contains class order,
training configuration, selected epoch, accuracy, per-class precision/recall/F1,
and confusion matrices for both models. The candidate has 16 outputs because
that is the explicitly mapped PlantDoc test subset. It is not a 38-class
replacement; production remains unchanged regardless of this experiment.

The local CPU diagnostic benchmark ran 30 test images with warmed runtimes:
candidate preprocessing plus inference median 25.53 ms (p95 167.92 ms); the
production full prediction path median 238.37 ms (p95 995.37 ms). These
single-machine timings are noisy and are not a service latency guarantee.
Exact measurements are emitted into the ignored `candidate/latency.json`.

## Other dataset sources reviewed

PlantVillage's [Mendeley Data record](https://data.mendeley.com/datasets/tywbtsjrjv/1)
states CC0 1.0 and describes 61,486 augmented images across 39 classes,
including a background class. Its images/augmentation variants are not an
independent field test, and the active model is already documented as trained
on PlantVillage. The authors' [repository](https://github.com/spMohanty/PlantVillage-Dataset)
provides grouping-aware splits but does not itself state a license in the
repository README. We therefore did not mix it into PlantDoc evaluation or
download it for this run.

Plant Pathology 2021 FGVC8 is an approximately 23,000-image, field-oriented
apple dataset. The official [Kaggle rules](https://www.kaggle.com/c/plant-pathology-2021-fgvc8/rules)
restrict data access to competition and academic research, and require
accepting the competition rules. It covers apple only and is not necessary for
this no-login, 16-class prototype milestone, so we did not retrieve it.

PlantDoc's CC BY 4.0 attribution is retained with the downloaded data in
`datasets/plantdoc/ATTRIBUTION.txt`. Do not publish the candidate as a deployed
model without a separate license/provenance review and broader-class
evaluation. No unsupported-plant/non-leaf negative dataset is currently
available, so an OOD detector is still unvalidated.

The immediate model-improvement step is to obtain a legally usable pretrained
candidate with an auditable class order (or train from a properly licensed,
verified source), then repeat the same split-safe comparison. The local Keras
backup is not used because its training-data provenance and output ordering
have not been verified.
