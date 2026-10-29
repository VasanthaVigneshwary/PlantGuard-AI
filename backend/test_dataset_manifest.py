"""Safety tests for dataset-manifest validation and readiness counts."""

import csv
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

import dataset_manifest  # noqa: E402


LABELS = [
    "Tomato___healthy",
    "Tomato___Early_blight",
    "Apple___healthy",
    "Apple___Apple_scab",
]


class DatasetManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.images = self.root / "images"
        self.images.mkdir()
        self.manifest = self.root / "manifest.csv"
        self.patcher = patch.object(dataset_manifest, "get_class_names", return_value=LABELS)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.addCleanup(self.temp.cleanup)

    def make_image(self, name="leaf.png", color=(30, 140, 60)):
        path = self.images / name
        Image.new("RGB", (24, 24), color).save(path)
        return path

    def row(self, **overrides):
        row = {
            "image_id": "img-001",
            "image_path": "images/leaf.png",
            "crop": "Tomato",
            "health_status": "diseased",
            "disease_label": "Tomato___Early_blight",
            "label_source": "plant pathologist review",
            "reviewer": "reviewer-01",
            "source_id": "dataset-v1",
            "source_url": "https://example.test/dataset",
            "license": "CC BY 4.0",
            "attribution": "Credit dataset authors",
            "plant_id": "",
            "capture_group": "",
            "image_source": "field_photograph",
            "label_confidence": "high",
            "review_status": "confirmed",
            "duplicate_group_id": "",
            "training_permission": "unknown",
            "original_image_redistribution": "unknown",
            "model_weights_redistribution": "unknown",
            "rights_evidence": "",
            "rights_restrictions": "",
        }
        row.update(overrides)
        return row

    def write_rows(self, rows, columns=None):
        columns = columns or list(self.row().keys())
        with self.manifest.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)

    def test_valid_records_report_counts_and_missing_crop_coverage(self):
        self.make_image()
        healthy = self.row(
            image_id="img-002", image_path="images/healthy.png", health_status="healthy",
            disease_label="",
        )
        Image.new("RGB", (24, 24), (50, 180, 70)).save(self.images / "healthy.png")
        self.write_rows([self.row(), healthy])
        with patch.object(dataset_manifest, "get_class_names", return_value=LABELS):
            report = dataset_manifest.validate_manifest(self.manifest)
        self.assertEqual((report["valid_count"], report["invalid_count"]), (2, 0))
        self.assertEqual(report["readiness"]["valid_label_counts_by_crop"]["Tomato"]["binary_coverage"], "both")
        self.assertEqual(report["readiness"]["valid_label_counts_by_crop"]["Apple"]["binary_coverage"], "neither")
        self.assertEqual(report["readiness"]["disease_class_counts"]["Tomato___Early_blight"], 1)

    def test_missing_and_traversing_image_paths_are_reported(self):
        self.write_rows([
            self.row(image_path="images/missing.png"),
            self.row(image_id="img-002", image_path="../outside.png"),
        ])
        report = dataset_manifest.validate_manifest(self.manifest)
        self.assertEqual(report["invalid_count"], 2)
        self.assertIn("does not exist", " ".join(report["records"][0]["issues"]))
        self.assertIn("remain inside", " ".join(report["records"][1]["issues"]))

    def test_unsupported_crop_and_disease_mismatch_are_rejected(self):
        self.make_image()
        self.write_rows([
            self.row(crop="Mung bean"),
            self.row(image_id="img-002", crop="Apple"),
        ])
        report = dataset_manifest.validate_manifest(self.manifest)
        self.assertEqual(report["invalid_count"], 2)
        self.assertIn("unsupported crop", " ".join(report["records"][0]["issues"]))
        self.assertIn("different crop", " ".join(report["records"][1]["issues"]))

    def test_healthy_contradiction_and_unconfirmed_disease_are_rejected(self):
        self.make_image()
        self.make_image("second.png", color=(20, 60, 180))
        self.write_rows([
            self.row(health_status="healthy", disease_label="Tomato___Early_blight"),
            self.row(
                image_id="img-002", image_path="images/second.png", disease_label="",
                review_status="unreviewed",
            ),
        ])
        report = dataset_manifest.validate_manifest(self.manifest)
        self.assertEqual(report["invalid_count"], 2)
        self.assertIn("contradictory", " ".join(report["records"][0]["issues"]))
        self.assertIn("disease_label; it must be blank", " ".join(report["records"][0]["issues"]))
        self.assertIn("confirmed/reviewed", " ".join(report["records"][1]["issues"]))

    def test_confirmed_diseased_without_exact_identity_is_valid_binary_record(self):
        self.make_image()
        self.write_rows([self.row(disease_label="")])
        report = dataset_manifest.validate_manifest(self.manifest)
        record = report["records"][0]
        self.assertTrue(record["valid"])
        self.assertIn("identity is unknown", " ".join(record["warnings"]))
        self.assertEqual(report["readiness"]["diseased_without_supported_exact_class"], 1)

    def test_confirmed_diseased_with_supported_exact_identity_is_valid(self):
        self.make_image()
        self.write_rows([self.row(disease_label="Tomato___Early_blight")])
        report = dataset_manifest.validate_manifest(self.manifest)
        self.assertTrue(report["records"][0]["valid"])
        self.assertEqual(report["readiness"]["disease_class_counts"]["Tomato___Early_blight"], 1)

    def test_unknown_health_status_is_valid_without_inferred_identity(self):
        self.make_image()
        self.write_rows([self.row(health_status="unknown", disease_label="", review_status="unknown")])
        record = dataset_manifest.validate_manifest(self.manifest)["records"][0]
        self.assertTrue(record["valid"])
        self.assertEqual(record["record"]["health_status"], "unknown")

    def test_unsupported_disease_identity_is_retained_with_clear_warning(self):
        self.make_image()
        label = "Tomato___Unlisted_condition"
        self.write_rows([self.row(disease_label=label)])
        report = dataset_manifest.validate_manifest(self.manifest)
        record = report["records"][0]
        self.assertTrue(record["valid"])
        self.assertIn(label, " ".join(record["warnings"]))
        self.assertEqual(report["readiness"]["diseased_without_supported_exact_class"], 1)

    def test_diseased_record_with_healthy_model_label_is_contradictory(self):
        self.make_image()
        self.write_rows([self.row(disease_label="Tomato___healthy")])
        record = dataset_manifest.validate_manifest(self.manifest)["records"][0]
        self.assertFalse(record["valid"])
        self.assertIn("contradictory healthy", " ".join(record["issues"]))

    def test_rights_permissions_can_be_recorded_with_evidence_and_conditions(self):
        self.make_image()
        self.write_rows([self.row(
            training_permission="allowed",
            original_image_redistribution="not_allowed",
            model_weights_redistribution="unknown",
            rights_evidence="Dataset licence v1, reviewed by counsel; https://example.test/licence",
            rights_restrictions="Training attribution required; original images may not be redistributed.",
        )])
        report = dataset_manifest.validate_manifest(self.manifest)
        record = report["records"][0]
        self.assertTrue(record["valid"])
        self.assertIn("model_weights_redistribution is unknown", " ".join(record["warnings"]))
        self.assertEqual(
            report["readiness"]["rights_permission_counts"]["training_permission"]["allowed"], 1
        )

    def test_rights_default_to_unknown_and_are_never_approval(self):
        self.make_image()
        row = self.row(
            training_permission="", original_image_redistribution="",
            model_weights_redistribution="",
        )
        self.write_rows([row])
        record = dataset_manifest.validate_manifest(self.manifest)["records"][0]
        self.assertTrue(record["valid"])
        self.assertEqual(record["record"]["training_permission"], "unknown")
        self.assertIn("do not use this record", " ".join(record["warnings"]))

    def test_invalid_rights_permission_values_are_rejected(self):
        self.make_image()
        self.write_rows([self.row(training_permission="probably allowed")])
        record = dataset_manifest.validate_manifest(self.manifest)["records"][0]
        self.assertFalse(record["valid"])
        self.assertIn("must be allowed, not_allowed, or unknown", " ".join(record["issues"]))

    def test_allowed_rights_decision_requires_evidence_and_restrictions(self):
        self.make_image()
        self.write_rows([self.row(training_permission="allowed")])
        record = dataset_manifest.validate_manifest(self.manifest)["records"][0]
        message = " ".join(record["issues"])
        self.assertIn("rights_evidence is required", message)
        self.assertIn("rights_restrictions is required", message)

    def test_legacy_csv_without_rights_columns_remains_compatible(self):
        self.make_image()
        legacy_fields = [
            "image_id", "image_path", "crop", "health_status", "disease_label",
            "label_source", "reviewer", "source_id", "source_url", "license",
            "attribution", "plant_id", "capture_group", "image_source",
            "label_confidence", "review_status", "duplicate_group_id",
        ]
        row = self.row()
        self.write_rows([{key: row[key] for key in legacy_fields}], columns=legacy_fields)
        record = dataset_manifest.validate_manifest(self.manifest)["records"][0]
        self.assertTrue(record["valid"])
        self.assertEqual(record["record"]["model_weights_redistribution"], "unknown")
        self.assertIn("no explicit rights fields", " ".join(record["warnings"]))

    def test_duplicate_ids_and_exact_hashes_are_rejected(self):
        self.make_image("one.png")
        # Identical bytes, distinct path and identifier.
        (self.images / "two.png").write_bytes((self.images / "one.png").read_bytes())
        self.write_rows([
            self.row(image_path="images/one.png"),
            self.row(image_id="img-001", image_path="images/two.png"),
        ])
        report = dataset_manifest.validate_manifest(self.manifest)
        self.assertEqual(report["invalid_count"], 2)
        self.assertIn("duplicate image_id", " ".join(report["records"][1]["issues"]))
        self.assertTrue(all("duplicate exact image SHA-256" in " ".join(r["issues"]) for r in report["records"]))
        self.assertEqual(report["readiness"]["exact_hash_duplicate_images"], 1)

    def test_missing_source_license_and_attribution_are_actionable(self):
        self.make_image()
        self.write_rows([self.row(source_id="", source_url="", license="", attribution="")])
        record = dataset_manifest.validate_manifest(self.manifest)["records"][0]
        message = " ".join(record["issues"])
        self.assertIn("source_id or source_url", message)
        self.assertIn("license is required", message)
        self.assertIn("attribution is required", message)

    def test_unknown_or_unreviewed_labels_remain_nonconfirmed(self):
        self.make_image()
        self.make_image("second.png", color=(20, 60, 180))
        self.write_rows([
            self.row(
                health_status="unknown", disease_label="", review_status="unknown",
                reviewer="", label_confidence="unknown",
            ),
            self.row(
                image_id="img-002", image_path="images/second.png", health_status="healthy",
                disease_label="", review_status="unreviewed",
            ),
        ])
        records = dataset_manifest.validate_manifest(self.manifest)["records"]
        self.assertTrue(records[0]["valid"])
        self.assertEqual(records[0]["record"]["health_status"], "unknown")
        self.assertEqual(records[0]["record"]["review_status"], "unknown")
        self.assertFalse(records[1]["valid"])
        self.assertIn("must be confirmed or reviewed", " ".join(records[1]["issues"]))

    def test_invalid_image_file_is_reported(self):
        (self.images / "leaf.png").write_text("not an image", encoding="utf-8")
        report = dataset_manifest.validate_manifest(self.manifest) if self.manifest.exists() else None
        if report is None:
            self.write_rows([self.row()])
            report = dataset_manifest.validate_manifest(self.manifest)
        self.assertEqual(report["invalid_count"], 1)
        self.assertIn("invalid image file", " ".join(report["records"][0]["issues"]))

    def test_empty_and_incomplete_manifests_are_reported(self):
        self.write_rows([])
        report = dataset_manifest.validate_manifest(self.manifest)
        self.assertIn("no image records", " ".join(report["manifest_issues"]))
        with self.manifest.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=["image_id", "image_path"])
            writer.writeheader()
            writer.writerow({"image_id": "img-001", "image_path": "images/leaf.png"})
        report = dataset_manifest.validate_manifest(self.manifest)
        self.assertIn("Missing required CSV columns", " ".join(report["manifest_issues"]))


if __name__ == "__main__":
    unittest.main()
