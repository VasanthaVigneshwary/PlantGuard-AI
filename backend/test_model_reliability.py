"""Focused tests for model preprocessing, label ordering, and uncertain inputs."""

import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from ml import predict as prediction  # noqa: E402
import evaluate_model  # noqa: E402


class ModelReliabilityTests(unittest.TestCase):
    def test_runtime_signature_accepts_expected_dynamic_batch_shapes(self):
        session = SimpleNamespace(
            get_inputs=lambda: [SimpleNamespace(type="tensor(float)", shape=["batch_size", 3, 224, 224])],
            get_outputs=lambda: [SimpleNamespace(type="tensor(float)", shape=["batch_size", 38])],
        )
        prediction.validate_inference_signature(session)

    def test_runtime_signature_rejects_incompatible_input_output_and_dtype(self):
        bad_sessions = [
            ("Model input must", [SimpleNamespace(type="tensor(float)", shape=["batch", 3, 256, 256])],
             [SimpleNamespace(type="tensor(float)", shape=["batch", 38])]),
            ("Model output must", [SimpleNamespace(type="tensor(float)", shape=["batch", 3, 224, 224])],
             [SimpleNamespace(type="tensor(float)", shape=["batch", 37])]),
            ("one float32 image input", [SimpleNamespace(type="tensor(uint8)", shape=["batch", 3, 224, 224])],
             [SimpleNamespace(type="tensor(float)", shape=["batch", 38])]),
        ]
        for message, inputs, outputs in bad_sessions:
            with self.subTest(message=message):
                session = SimpleNamespace(get_inputs=lambda: inputs, get_outputs=lambda: outputs)
                with self.assertRaisesRegex(RuntimeError, message):
                    prediction.validate_inference_signature(session)

    def test_preprocessing_matches_upstream_shape_dtype_and_rgb_normalization(self):
        image = Image.new("RGB", (13, 29), (255, 0, 0))
        tensor = prediction.preprocess_image(image)
        self.assertEqual(tensor.shape, (1, 3, 224, 224))
        self.assertEqual(tensor.dtype, np.float32)
        np.testing.assert_allclose(tensor[0, 0], (1.0 - 0.485) / 0.229, rtol=1e-6)
        np.testing.assert_allclose(tensor[0, 1], (0.0 - 0.456) / 0.224, rtol=1e-6)
        np.testing.assert_allclose(tensor[0, 2], (0.0 - 0.406) / 0.225, rtol=1e-6)

    def test_every_class_index_matches_upstream_json_and_indexed_text_list(self):
        model_dir = BACKEND_DIR / "ml" / "models"
        metadata = json.loads((model_dir / "classes.json").read_text(encoding="utf-8"))
        indexed = [line.strip().split(": ", 1)[1] for line in
                   (model_dir / "class_names.txt").read_text(encoding="utf-8").splitlines()]
        with patch.object(prediction, "_class_names", []):
            self.assertEqual(prediction.get_class_names(), metadata["classes"])
        self.assertEqual(metadata["num_classes"], 38)
        self.assertEqual(indexed, metadata["classes"])
        self.assertEqual(len(metadata["classes"]), 38)

    def test_mismatched_class_files_are_rejected(self):
        directory = BACKEND_DIR / ".test-model-reliability-tmp"
        directory.mkdir(exist_ok=True)
        try:
            json_path = directory / "classes.json"
            text_path = directory / "class_names.txt"
            json_path.write_text('{"classes":["A","B"]}', encoding="utf-8")
            text_path.write_text("0: B\n1: A\n", encoding="utf-8")
            with (
                patch.object(prediction, "CLASSES_JSON_PATH", json_path),
                patch.object(prediction, "CLASS_NAMES_TXT_PATH", text_path),
                patch.object(prediction, "_class_names", []),
            ):
                with self.assertRaisesRegex(RuntimeError, "disagree"):
                    prediction.get_class_names()
        finally:
            json_path.unlink(missing_ok=True)
            text_path.unlink(missing_ok=True)
            directory.rmdir()

    def test_prediction_errors_for_missing_and_corrupt_images(self):
        with self.assertRaises(FileNotFoundError):
            prediction.predict_disease("missing-reliability-test.jpg")
        directory = BACKEND_DIR / ".test-model-reliability-tmp"
        directory.mkdir(exist_ok=True)
        image_path = directory / "corrupt.jpg"
        try:
            image_path.write_bytes(b"not an image")
            with self.assertRaises((OSError, ValueError)):
                prediction.predict_disease(image_path)
        finally:
            image_path.unlink(missing_ok=True)
            directory.rmdir()

    def test_low_detail_image_is_rejected_before_it_can_get_a_disease_label(self):
        directory = BACKEND_DIR / ".test-model-reliability-tmp"
        directory.mkdir(exist_ok=True)
        try:
            image_path = directory / "low-detail.png"
            Image.new("RGB", (64, 64), (128, 128, 128)).save(image_path)
            with self.assertRaisesRegex(prediction.ImageQualityError, "too little visual contrast"):
                prediction.predict_disease(image_path)
        finally:
            image_path.unlink(missing_ok=True)
            directory.rmdir()

    def test_any_image_result_warns_that_unsupported_inputs_can_get_a_class(self):
        result = prediction.predict_disease(BACKEND_DIR.parent / "test_images" / "sample_leaf.jpg")
        self.assertIn("unsupported images may still receive a class prediction", result["uncertainty_warning"])
        self.assertEqual(result["status"], "Uncalibrated model score")

    def test_distinct_real_images_produce_distinct_preprocessed_tensors_and_logits(self):
        project_root = BACKEND_DIR.parent
        image_paths = (
            project_root / "test_images" / "sample_leaf.jpg",
            BACKEND_DIR / "uploads" / "leaf-spot-fungus-920x518.webp",
        )
        self.assertTrue(all(path.is_file() for path in image_paths))
        tensors = []
        logits = []
        session = prediction.get_inference_session()
        input_name = session.get_inputs()[0].name
        for image_path in image_paths:
            with Image.open(image_path) as image:
                tensors.append(prediction.preprocess_image(image))
            logits.append(np.asarray(session.run(None, {input_name: tensors[-1]})[0][0]))

        self.assertFalse(np.array_equal(tensors[0], tensors[1]))
        self.assertFalse(np.allclose(logits[0], logits[1]))
        first_prediction = prediction.predict_disease(image_paths[0])["disease"]
        second_prediction = prediction.predict_disease(image_paths[1])["disease"]
        self.assertNotEqual(first_prediction, second_prediction)

    def test_evaluator_reports_metrics_for_a_labeled_independent_folder(self):
        root = BACKEND_DIR / ".test-model-reliability-tmp"
        (root / "A").mkdir(parents=True, exist_ok=True)
        (root / "B").mkdir(parents=True, exist_ok=True)
        try:
            (root / "A" / "one.jpg").write_bytes(b"fixture")
            (root / "A" / "two.jpg").write_bytes(b"fixture")
            (root / "B" / "three.jpg").write_bytes(b"fixture")

            def fake_prediction(path, top_k):
                predicted = "B" if Path(path).name in {"two.jpg", "three.jpg"} else "A"
                return {"disease": predicted}

            with (
                patch.object(evaluate_model, "get_class_names", return_value=["A", "B"]),
                patch.object(evaluate_model, "predict_disease", side_effect=fake_prediction),
            ):
                report = evaluate_model.evaluate(root, "test source")
            self.assertEqual(report["sample_count"], 3)
            self.assertAlmostEqual(report["accuracy"], 2 / 3)
            self.assertEqual(report["per_class"]["A"]["precision"], 1.0)
            self.assertEqual(report["per_class"]["A"]["recall"], 0.5)
            self.assertEqual(report["per_class"]["B"]["precision"], 0.5)
            self.assertEqual(report["per_class"]["B"]["recall"], 1.0)
            self.assertEqual(report["confusion_matrix"]["counts"], [[1, 1], [0, 1]])
            self.assertEqual(report["dataset_source"], "test source")
        finally:
            for file in root.rglob("*"):
                if file.is_file():
                    file.unlink()
            for directory in sorted((path for path in root.rglob("*") if path.is_dir()), reverse=True):
                directory.rmdir()
            root.rmdir()


if __name__ == "__main__":
    unittest.main()
