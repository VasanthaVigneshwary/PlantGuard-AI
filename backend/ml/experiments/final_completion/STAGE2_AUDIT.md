# Stage 2 – Dataset and Split Audit

**Date:** 2026-11-26  
**Status:** Completed by reusing the existing Stage 3 validation artifacts and checking manifest row counts; no images or manifests were changed.

## PlantVillage source and integrity

- Source: existing preserved `datasets/plantvillage-source.zip`, 2,184,723,441 bytes; CRC test passed. Existing validation records 54,305 images in `raw/color`, all 38 approved labels, zero missing classes, zero corrupt images, and exact order agreement with `classes.json` and the Stage 2 class mapping.
- The color dataset contains 12 healthy classes and 15,084 healthy images. Per-class counts range from 152 (`Potato___healthy`) to 5,507 (`Orange___Haunglongbing_(Citrus_greening)`), about a 36.2:1 max/min ratio. All classes exceed the prior 100-image severe-underrepresentation threshold. Full counts remain in `plantvillage_color_class_counts.csv`.
- Source report identifies the Hugging Face mirror of PlantVillage and the dataset card's CC BY-SA 3.0 license declaration. Retain attribution and comply with that license if redistributing derived content.

## Fixed manifests

Existing, deterministic, seed-42 manifests contain 37,993 train, 8,158 validation, and 8,154 test examples (54,305 total): 69.962%, 15.023%, and 15.015%, respectively. This is consistent with the intended 70/15/15 split. Every class is represented in the dataset; the class audit and prepared manifest reports hold per-class split counts.

The saved hash audit found 21 exact-duplicate groups (21 extra duplicate files) and **zero exact image hashes crossing train/validation/test splits**. Source members remain referenced in place through the ZIP-aware loader. No class was merged, dropped, or relabeled during this completion work. Earlier validation reports zero image decode errors. No second full archive scan or duplicate rehash was run.

## Other local data

The existing PlantDoc snapshot was preserved as a separate external dataset and used only for the previously completed Stage 4 test evaluation. It was not used for model training, validation, preprocessing choice, threshold selection, or calibration.

## Evidence files reused

- `backend/ml/experiments/stage3_preflight/dataset_validation.json`
- `backend/ml/experiments/stage3_preflight/plantvillage_manifest_audit.json`
- `backend/ml/experiments/stage3_preflight/plantvillage_color_class_counts.csv`
- `backend/ml/experiments/stage3_preflight/plantvillage_{train,validation,test}.csv`
- `backend/ml/experiments/stage3_preflight/preflight_report.md`
