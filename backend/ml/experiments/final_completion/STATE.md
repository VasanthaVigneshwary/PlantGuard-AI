# Final Completion State

- Updated: 2026-11-27
- Core prediction stabilization: complete locally; deployment verification remains pending.
- ONNX hash IDENTICAL: 14c03ae2b47b23a90a0176e70fe2fc46077fc5ae26dc46813966abdee0eb0c0a.
- External tensor hash IDENTICAL: 038e6093bb41434def59a3c2375fbfc13c86f6af046e7f0a5b7b9015aa29b497.
- Production preprocessing matches the specified Colab sequence line-by-line.
- Existing validation split: 8,158/8,158 correct, 38 classes, SHA checks passed, CPUExecutionProvider.
- Validation-selected uncertain cutoff: 0.6628152132034302, 95% target accuracy, 100% validation coverage; heuristic only.
- Historical PlantVillage test report: 8,154/8,154 correct; in-distribution; exact model training independence remains unverified.
- PlantDoc external indicator: 123 images, 19.51% top-1, 37.40% top-3, 19.47% macro-F1.
- Database: all 38 class records/details present; 27 application-rate sources unverified.
- Tests: 7 core tests, 14 reliability tests, 5 safe API tests passed; frontend lint/typecheck passed. pytest unavailable.
- Backups: recovery/backups/*pre_core_stabilization_20261127.bak.
- Deployment checklist: DEPLOYMENT_CHECKLIST.md; production configuration remains unverified.
- Git: core stabilization commit 3ca84d8932a79773bde1b6679e55ca962d2b4f25 and prior Stage 4 work pushed; origin/master verified at 3ca84d89.
- Unrelated pre-existing worktree changes remain unstaged and preserved.
