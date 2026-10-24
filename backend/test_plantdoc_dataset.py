"""Unit tests for PlantDoc label audit and test-split evaluation rules."""

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))
import plantdoc_dataset as plantdoc  # noqa: E402


class PlantDocDatasetTests(unittest.TestCase):
    def test_direct_and_compatible_labels_are_explicit_and_ambiguous_stay_unmapped(self):
        classes = ["Apple___Apple_scab", "Apple___healthy", "Potato___Early_blight"]
        audit = plantdoc.label_audit(
            ["Apple___Apple_scab", "Apple Scab Leaf", "Apple leaf", "Unknown label"], classes
        )
        self.assertEqual(audit["exact"], [{"plantdoc_label": "Apple___Apple_scab", "model_class": "Apple___Apple_scab"}])
        self.assertEqual(audit["compatible"][0]["model_class"], "Apple___Apple_scab")
        self.assertEqual(audit["ambiguous"][0]["plantdoc_label"], "Apple leaf")
        self.assertEqual(audit["unsupported"][0]["plantdoc_label"], "Unknown label")
        self.assertNotIn("Apple leaf", {x["plantdoc_label"] for x in audit["compatible"]})

    def test_inference_reads_every_test_image_but_scores_only_explicitly_mapped_labels(self):
        with tempfile.TemporaryDirectory(dir=BACKEND_DIR) as tmp:
            root = Path(tmp)
            records = []
            for split, label, name, digest in [
                ("train", "Apple Scab Leaf", "train.jpg", "trainhash"),
                ("test", "Apple Scab Leaf", "duplicate.jpg", "trainhash"),
                ("test", "Apple Scab Leaf", "known.jpg", "testhash1"),
                ("test", "Apple leaf", "ambiguous.jpg", "testhash2"),
            ]:
                path = root / split / label / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"image")
                records.append({
                    "image_path": path.relative_to(root).as_posix(),
                    "source_archive_path": f"PlantDoc-Dataset-master/{split}/{label}/{name}",
                    "ground_truth_label": label, "source": plantdoc.SOURCE_URL,
                    "split": split, "width": 32, "height": 32, "sha256": digest,
                    "loading_error": None,
                })
            (root / "manifest.jsonl").write_text("\n".join(json.dumps(row) for row in records), encoding="utf-8")
            mock_classes = ["Apple___Apple_scab", "Apple___healthy", "Potato___Early_blight"]

            def fake_predict(path, top_k):
                return {"disease": "Apple___Apple_scab", "confidence": 98.1, "top_predictions": []}

            with patch.object(plantdoc, "get_class_names", return_value=mock_classes), \
                    patch.object(plantdoc, "predict_disease", side_effect=fake_predict) as infer:
                report = plantdoc.evaluate(root)
            self.assertEqual(infer.call_count, 3)
            self.assertTrue(all(Path(call.args[0]).parts[-1] != "train.jpg" for call in infer.call_args_list))
            self.assertEqual(report["test_image_count"], 3)
            self.assertEqual(report["usable_test_images_inferred"], 3)
            self.assertEqual(report["usable_images_in_compatible_metric_subset"], 1)
            self.assertEqual(report["test_images_excluded_for_train_overlap"], 1)
            self.assertEqual(report["accuracy"], 1.0)
            self.assertEqual(report["label_coverage"]["ambiguous"][0]["plantdoc_label"], "Apple leaf")
            self.assertEqual(report["train_test_sha256_overlap_count"], 1)


if __name__ == "__main__":
    unittest.main()
