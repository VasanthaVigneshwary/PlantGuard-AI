"""Tests for candidate data-split leakage prevention and metrics."""

from pathlib import Path
import sys
import unittest

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))
import train_plantdoc_candidate as candidate  # noqa: E402


def row(split, label, digest, name):
    return {
        "split": split,
        "ground_truth_label": label,
        "sha256": digest,
        "image_path": f"{split}/{label}/{name}.jpg",
        "loading_error": None,
    }


class CandidateDataTests(unittest.TestCase):
    def test_train_test_and_validation_are_deduplicated_and_label_conflicts_removed(self):
        rows = []
        rows.append(row("test", "Apple Scab Leaf", "test-apple", "test"))
        rows.append(row("test", "Potato leaf early blight", "test-potato", "test"))
        rows.append(row("train", "Apple Scab Leaf", "test-apple", "overlap"))
        rows.extend(row("train", "Apple Scab Leaf", f"apple-{i}", f"apple-{i}") for i in range(5))
        rows.extend(row("train", "Potato leaf early blight", f"potato-{i}", f"potato-{i}") for i in range(5))
        rows.append(row("train", "Potato leaf early blight", "conflict", "conflict-early"))
        rows.append(row("train", "Potato leaf late blight", "conflict", "conflict-late"))

        splits = candidate.make_data_splits(rows, seed=2)
        train_hashes = {x["sha256"] for x in splits["train"]}
        val_hashes = {x["sha256"] for x in splits["validation"]}
        test_hashes = {x["sha256"] for x in splits["test"]}
        self.assertFalse(train_hashes & val_hashes)
        self.assertFalse(train_hashes & test_hashes)
        self.assertFalse(val_hashes & test_hashes)
        self.assertNotIn("conflict", train_hashes | val_hashes)
        self.assertEqual(len(splits["duplicate_conflicts"]), 1)
        self.assertEqual(splits["train_test_overlap_excluded_count"], 1)
        self.assertEqual(len(splits["test"]), 1)

    def test_metrics_include_support_precision_recall_and_f1(self):
        report = candidate.classification_metrics([0, 0, 1], [0, 1, 1], ["A", "B"])
        self.assertAlmostEqual(report["accuracy"], 2 / 3)
        self.assertEqual(report["per_class"]["A"]["support"], 2)
        self.assertEqual(report["per_class"]["A"]["precision"], 1.0)
        self.assertEqual(report["per_class"]["A"]["recall"], 0.5)
        self.assertAlmostEqual(report["per_class"]["A"]["f1"], 2 / 3)
        self.assertEqual(report["confusion_matrix"]["counts"], [[1, 1], [0, 1]])


if __name__ == "__main__":
    unittest.main()
