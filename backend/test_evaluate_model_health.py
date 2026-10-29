"""Tests for healthy/diseased metrics in the independent evaluator."""

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

import evaluate_model  # noqa: E402


class HealthStatusMetricTests(unittest.TestCase):
    def test_confusion_counts_abstentions_as_misses_and_reports_coverage(self):
        report = evaluate_model.health_status_metrics([
            {"crop": "Tomato", "truth": "healthy", "prediction": "healthy"},
            {"crop": "Tomato", "truth": "healthy", "prediction": "uncertain"},
            {"crop": "Tomato", "truth": "diseased", "prediction": "diseased"},
        ])

        self.assertEqual(
            report["confusion_matrix"]["counts"],
            [[1, 0, 1], [0, 1, 0]],
        )
        self.assertEqual(report["accuracy"], 2 / 3)
        self.assertEqual(report["coverage"], 2 / 3)
        self.assertEqual(report["selective_accuracy"], 1.0)
        self.assertEqual(report["per_class"]["healthy"]["recall"], 0.5)
        self.assertEqual(report["per_crop"]["Tomato"]["sample_count"], 3)

    def test_evaluate_includes_binary_status_metrics_and_uncertain_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            healthy = root / "Tomato___healthy"
            diseased = root / "Tomato___Early_blight"
            healthy.mkdir()
            diseased.mkdir()
            (healthy / "healthy.jpg").write_bytes(b"healthy-fixture")
            (diseased / "diseased.jpg").write_bytes(b"diseased-fixture")

            def fake_prediction(path, top_k):
                if Path(path).parent.name == "Tomato___healthy":
                    return {
                        "disease": "Tomato___healthy",
                        "is_healthy": True,
                        "is_uncertain": False,
                    }
                return {
                    "disease": "Tomato___Early_blight",
                    "is_healthy": False,
                    "is_uncertain": True,
                }

            with (
                patch.object(
                    evaluate_model,
                    "get_class_names",
                    return_value=["Tomato___healthy", "Tomato___Early_blight"],
                ),
                patch.object(evaluate_model, "predict_disease", side_effect=fake_prediction),
            ):
                report = evaluate_model.evaluate(root, "test source")

        self.assertAlmostEqual(report["accuracy"], 1.0)
        self.assertAlmostEqual(report["macro_f1"], 1.0)
        health = report["health_status"]
        self.assertEqual(health["confusion_matrix"]["counts"], [[1, 0, 0], [0, 0, 1]])
        self.assertEqual(health["coverage"], 0.5)
        self.assertEqual(health["per_crop"]["Tomato"]["sample_count"], 2)


if __name__ == "__main__":
    unittest.main()
