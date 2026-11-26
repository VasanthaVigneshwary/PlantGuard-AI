# Final Completion State

- Updated: 2026-11-26
- Overall: Final leakage/provenance audit complete; model training-history and original split independence remain unresolved.
- Recovery/reports commit: `784c88464530127276f2ecb8ed35f42336310e1d` (`docs(ml): record recovered model and evaluation provenance`). No push.
- Reused completed Stage 3 dataset audit and Stage 4 PlantDoc evaluation; no evaluation or training rerun.
- Stage 3 dataset: 54,305 images, 38 classes; seed-42 generated split: 37,993 / 8,158 / 8,154.
- Exact hash audit: 8,154/8,154 current test hashes compared with generated train/validation; 0 test/train and 0 test/validation overlaps.
- 21 exact duplicate groups (21 extra files) are confined to one split/class; 0 cross-split groups. Perceptual hash not run; no suitable package installed.
- Recovered Colab bundle reports 100% on 8,154 test images/38 classes; matrix/supports and all per-class values reconcile. No model/data hashes in the report.
- Recovered result is PLAUSIBLY LINKED to the current ONNX path; exact model-byte identity is not verified.
- Original V2-S train/validation membership, checkpoint, notebook/script, logs, training preprocessing and export lineage: NOT FOUND in accessible locations.
- Test-set independence from original training/model selection: UNABLE TO ESTABLISH; model-card 54,306-image claim is a material but unproven overlap risk.
- Production ONNX has 38 outputs and structure consistent with V2-S; legacy Keras is EfficientNetB0 and not its source checkpoint.
- Evaluation preprocessing matches production inference. Original training preprocessing remains unknown.
- Existing Stage 4 PlantDoc baseline remains unchanged: 123 eligible images, top-1 19.51%, top-3 37.40%, macro-F1 19.47% (16 observed mapped classes).
- Audit complete: `leakage_audit/AUDIT_REPORT.md`, `file_inventory.csv`, `train_test_overlap.csv`, `exact_duplicate_groups.csv`, `notebook_training_evidence.md`, and `model_provenance.md`.
- Remaining blocker: original Google Drive/Colab run folder is inaccessible. Make it available read-only at `recovery/source/` to establish original membership and model lineage.
- Safety: no retraining, model/dataset/manifest/class-map/database/Stage 4 changes, push, reset, or cleanup; unrelated working-tree changes preserved.
