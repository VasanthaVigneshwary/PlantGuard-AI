"""Focused contract tests for the core 38-class prediction flow."""
from __future__ import annotations

import json
import os
from io import BytesIO
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@127.0.0.1:1/test")

from main import app  # noqa: E402
from ml import predict  # noqa: E402
from routes import plant as plant_route  # noqa: E402


class CorePredictionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.image_path = ROOT / "test_images" / "sample_leaf.jpg"
        cls.image_bytes = cls.image_path.read_bytes()

    def test_38_class_order_matches_metadata(self):
        metadata = json.loads(predict.CLASSES_JSON_PATH.read_text(encoding="utf-8"))
        classes = predict.get_class_names()
        self.assertEqual(len(classes), 38)
        self.assertEqual(classes, metadata["classes"])

    def test_preprocessing_is_nchw_float32(self):
        tensor = predict.preprocess_image(Image.new("RGB", (80, 64), (120, 80, 40)))
        self.assertEqual(tensor.shape, (1, 3, 224, 224))
        self.assertEqual(tensor.dtype, np.float32)

    def test_actual_onnx_prediction_returns_38_class_top_three_scores(self):
        result = predict.predict_disease(self.image_path, top_k=3)
        self.assertIn(result["disease"], predict.get_class_names())
        self.assertEqual(len(result["top_predictions"]), 3)
        for item in result["top_predictions"]:
            self.assertTrue(item["class"])
            self.assertTrue(item["display_name"])
            self.assertIsInstance(item["score"], float)
            self.assertEqual(item["score_type"], "uncalibrated_model_score")

    def test_low_model_score_sets_uncertain_without_claiming_calibration(self):
        class FakeSession:
            def get_inputs(self):
                return [type("Input", (), {"name": "input"})()]

            def run(self, _outputs, _inputs):
                return [np.zeros((1, 38), dtype=np.float32)]

        with patch.object(predict, "get_inference_session", return_value=FakeSession()), \
             patch.object(predict, "get_uncertainty_score_threshold", return_value=0.80):
            result = predict.predict_disease(self.image_path, top_k=3)
        self.assertTrue(result["uncertain"])
        self.assertTrue(result["is_uncertain"])
        self.assertIn("not a calibrated probability", result["uncertainty_warning"])

    def test_invalid_small_blank_and_near_black_uploads_are_4xx(self):
        cases = [("not-image.png", b"not an image"), ("oversized.png", b"x" * (10 * 1024 * 1024 + 1))]
        for name, size, color in [
            ("small.png", (63, 64), (120, 140, 100)),
            ("blank.png", (64, 64), (120, 120, 120)),
            ("black.png", (64, 64), (0, 0, 0)),
        ]:
            stream = BytesIO()
            Image.new("RGB", size, color).save(stream, format="PNG")
            cases.append((name, stream.getvalue()))
        with patch("routes.plant.predict_disease") as inference:
            for name, contents in cases:
                response = self.client.post("/api/upload", files={"file": (name, contents, "image/png")})
                self.assertEqual(response.status_code, 400, name)
                self.assertTrue(response.json().get("detail"), name)
            inference.assert_not_called()

    def test_upload_response_keeps_legacy_fields_and_adds_score_and_top_three_schema(self):
        top_predictions = [
            {"class": f"class-{i}", "display_name": f"Display {i}", "crop": "Crop", "condition": "Condition",
             "score": 90.0-i, "score_type": "uncalibrated_model_score", "confidence": 90.0-i}
            for i in range(3)
        ]
        result = {"disease":"Apple___Apple_scab", "crop":"Apple", "condition":"Apple scab",
                  "is_healthy":False, "is_uncertain":True, "uncertain":True, "confidence":91.0,
                  "status":"Uncertain", "uncertainty_warning":"Uncalibrated model score",
                  "top_predictions":top_predictions}
        with (
            patch("routes.plant.predict_disease", return_value=result) as inference,
            patch("routes.plant.get_disease_details_by_prediction", return_value=None),
            patch("routes.plant.save_prediction", return_value=None),
            patch.object(Path, "write_bytes", autospec=True),
        ):
            response = self.client.post("/api/upload", files={"file": ("leaf.jpg", self.image_bytes, "image/jpeg")})
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["prediction"], "Apple___Apple_scab")
        self.assertEqual(body["confidence"], 91.0)
        self.assertEqual(body["score"], 91.0)
        self.assertEqual(body["score_type"], "uncalibrated_model_score")
        self.assertTrue(body["uncertain"])
        self.assertTrue(body["is_uncertain"])
        self.assertEqual(len(body["top_predictions"]), 3)
        self.assertTrue(all({"class", "display_name", "score"} <= item.keys() for item in body["top_predictions"]))
        inference.assert_called_once()
        self.assertEqual(inference.call_args.kwargs.get("top_k"), 3)

    def test_real_upload_api_returns_uncalibrated_top_three(self):
        with (
            patch("routes.plant.get_disease_details_by_prediction", return_value=None),
            patch("routes.plant.save_prediction", return_value=None),
            patch.object(Path, "write_bytes", autospec=True),
        ):
            response = self.client.post("/api/upload", files={"file": ("leaf.jpg", self.image_bytes, "image/jpeg")})
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(len(body["top_predictions"]), 3)
        self.assertEqual(body["score_type"], "uncalibrated_model_score")
        self.assertIn(body["prediction"], predict.get_class_names())
        for item in body["top_predictions"]:
            self.assertTrue({"class", "display_name", "score"} <= item.keys())
            self.assertEqual(item["score_type"], "uncalibrated_model_score")


if __name__ == "__main__":
    unittest.main()
