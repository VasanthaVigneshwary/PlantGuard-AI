"""Database-isolated tests for the plant upload API."""

import os
from io import BytesIO
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from PIL import Image

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@127.0.0.1:1/test")

from main import app  # noqa: E402
from services import database_service  # noqa: E402


class PlantApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.image_bytes = (PROJECT_ROOT / "test_images" / "sample_leaf.jpg").read_bytes()

    def test_health_route(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Plant Guard AI", response.json()["message"])

    def test_cors_allows_local_frontend_and_rejects_arbitrary_vercel_origin(self):
        allowed = self.client.options(
            "/api/upload",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.headers.get("access-control-allow-origin"), "http://localhost:3000")

        disallowed = self.client.options(
            "/api/upload",
            headers={
                "Origin": "https://attacker.vercel.app",
                "Access-Control-Request-Method": "POST",
            },
        )
        self.assertNotEqual(disallowed.headers.get("access-control-allow-origin"), "https://attacker.vercel.app")

    def test_empty_upload_is_rejected(self):
        response = self.client.post("/api/upload", files={"file": ("empty.jpg", b"", "image/jpeg")})
        self.assertEqual(response.status_code, 400)

    def test_corrupted_upload_is_rejected_before_inference(self):
        with patch("routes.plant.predict_disease") as predict:
            response = self.client.post(
                "/api/upload", files={"file": ("broken.jpg", b"not an image", "image/jpeg")}
            )
        self.assertEqual(response.status_code, 400)
        predict.assert_not_called()

    def test_low_detail_upload_gets_actionable_client_error(self):
        image_buffer = BytesIO()
        Image.new("RGB", (64, 64), (128, 128, 128)).save(image_buffer, format="PNG")
        response = self.client.post(
            "/api/upload",
            files={"file": ("low-detail.png", image_buffer.getvalue(), "image/png")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("too little visual contrast", response.json()["detail"])

    def test_prediction_without_knowledge_record_is_honest_and_saved(self):
        seen_temp_paths = []

        def predict(temp_path):
            path = Path(temp_path)
            self.assertTrue(path.is_file())
            seen_temp_paths.append(path)
            return {
                "disease": "Apple___Apple_scab",
                "crop": "Apple",
                "condition": "Apple scab",
                "is_healthy": False,
                "confidence": 90.35,
                "status": "Uncalibrated model score",
                "uncertainty_warning": "Uncalibrated score",
                "top_predictions": [],
            }

        with (
            patch("routes.plant.predict_disease", side_effect=predict),
            patch("routes.plant.get_disease_details_by_prediction", return_value=None),
            patch("routes.plant.save_prediction", return_value=17) as save_prediction,
        ):
            response = self.client.post(
                "/api/upload",
                files={"file": ("leaf.jpg", self.image_bytes, "image/jpeg")},
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["prediction"], "Apple___Apple_scab")
        self.assertIsNone(body["disease"]["description"])
        self.assertEqual(body["symptoms"], [])
        self.assertTrue(body["history_saved"])
        self.assertEqual(body["prediction_id"], 17)
        save_prediction.assert_called_once()
        self.assertEqual(save_prediction.call_args.kwargs["crop_name"], "Apple")
        self.assertIsNone(save_prediction.call_args.kwargs["disease_id"])
        self.assertIsNone(save_prediction.call_args.kwargs["image_url"])
        self.assertTrue(all(not path.exists() for path in seen_temp_paths))

    def test_separate_real_uploads_are_inferred_from_their_own_image_bytes(self):
        image_paths = (
            PROJECT_ROOT / "test_images" / "sample_leaf.jpg",
            BACKEND_DIR / "uploads" / "leaf-spot-fungus-920x518.webp",
        )
        image_bytes = [path.read_bytes() for path in image_paths]
        self.assertNotEqual(image_bytes[0], image_bytes[1])

        with (
            patch("routes.plant.get_disease_details_by_prediction", return_value=None),
            patch("routes.plant.save_prediction", return_value=1),
        ):
            responses = [
                self.client.post(
                    "/api/upload",
                    files={"file": (path.name, contents, "application/octet-stream")},
                )
                for path, contents in zip(image_paths, image_bytes)
            ]

        self.assertEqual([response.status_code for response in responses], [200, 200])
        predictions = [response.json()["prediction"] for response in responses]
        self.assertEqual(predictions, ["Apple___Apple_scab", "Tomato___Early_blight"])

    def test_knowledge_database_failure_returns_service_unavailable(self):
        with (
            patch(
                "routes.plant.predict_disease",
                return_value={
                    "disease": "Apple___Apple_scab",
                    "crop": "Apple",
                    "condition": "Apple scab",
                    "is_healthy": False,
                    "confidence": 90.35,
                    "status": "Uncalibrated model score",
                    "top_predictions": [],
                },
            ),
            patch("routes.plant.get_disease_details_by_prediction", side_effect=RuntimeError("db offline")),
        ):
            response = self.client.post(
                "/api/upload",
                files={"file": ("leaf.jpg", self.image_bytes, "image/jpeg")},
            )

        self.assertEqual(response.status_code, 503)
        self.assertIn("knowledge database is unavailable", response.json()["detail"])

    def test_model_error_does_not_expose_server_path(self):
        private_path = "D:/private/server/model/path"
        with patch("routes.plant.predict_disease", side_effect=FileNotFoundError(private_path)):
            response = self.client.post(
                "/api/upload",
                files={"file": ("leaf.jpg", self.image_bytes, "image/jpeg")},
            )
        self.assertEqual(response.status_code, 500)
        self.assertNotIn(private_path, response.text)

    def test_history_save_failure_is_reported_without_claiming_success(self):
        prediction = {
            "disease": "Apple___Apple_scab",
            "crop": "Apple",
            "condition": "Apple scab",
            "is_healthy": False,
            "confidence": 90.35,
            "status": "Uncalibrated model score",
            "uncertainty_warning": "Uncalibrated score",
            "top_predictions": [],
        }
        with (
            patch("routes.plant.predict_disease", return_value=prediction),
            patch("routes.plant.get_disease_details_by_prediction", return_value=None),
            patch("routes.plant.save_prediction", side_effect=RuntimeError("database write failed")),
        ):
            response = self.client.post(
                "/api/upload",
                files={"file": ("leaf.jpg", self.image_bytes, "image/jpeg")},
            )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["history_saved"])
        self.assertIsNone(response.json()["prediction_id"])
        self.assertTrue(response.json()["history_warning"])

    def test_empty_history_response(self):
        with patch("routes.plant.get_prediction_history", return_value=[]):
            response = self.client.get("/api/history")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"count": 0, "history": []})

    def test_empty_notifications_stay_empty(self):
        with patch("routes.plant.get_notification_records", return_value=[]):
            response = self.client.get("/api/notifications")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"count": 0, "notifications": []})


class PredictionPersistenceTests(unittest.TestCase):
    def test_percentage_score_is_stored_as_fraction_and_crop_is_resolved(self):
        connection = Mock()
        cursor = Mock()
        connection.cursor.return_value = cursor
        cursor.fetchone.side_effect = [(8,), (24,)]

        with (
            patch.object(database_service, "get_connection", return_value=connection),
            patch.object(database_service, "ensure_default_user", return_value=3),
        ):
            prediction_id = database_service.save_prediction(
                crop_id=None,
                crop_name="Apple",
                disease_id=None,
                confidence=90.35,
            )

        self.assertEqual(prediction_id, 24)
        self.assertEqual(cursor.execute.call_args_list[0].args[1], ("Apple",))
        insert_values = cursor.execute.call_args_list[1].args[1]
        self.assertEqual(insert_values[:4], (3, 8, None, 0.9035))
        connection.commit.assert_called_once()

    def test_known_disease_uses_its_database_crop_mapping(self):
        connection = Mock()
        cursor = Mock()
        connection.cursor.return_value = cursor
        cursor.fetchone.side_effect = [(12,), (25,)]

        with (
            patch.object(database_service, "get_connection", return_value=connection),
            patch.object(database_service, "ensure_default_user", return_value=3),
        ):
            database_service.save_prediction(
                crop_id=None,
                crop_name="Corn (maize)",
                disease_id=41,
                confidence=70,
            )

        self.assertEqual(cursor.execute.call_args_list[0].args[1], (41,))
        insert_values = cursor.execute.call_args_list[1].args[1]
        self.assertEqual(insert_values[1], 12)


class ApplicationRateVerificationTests(unittest.TestCase):
    def test_rate_requires_explicit_verification_marker_and_https_source(self):
        self.assertTrue(
            database_service._has_verified_rate_source(
                "Product/formulation: Mancozeb 75% WP; [verified]; Source: https://agritech.tnau.ac.in/guidance"
            )
        )
        self.assertFalse(database_service._has_verified_rate_source("Source: TNAU Agritech Portal"))
        self.assertFalse(
            database_service._has_verified_rate_source(
                "Product/formulation: Mancozeb 75% WP; [verified]; Source: http://agritech.tnau.ac.in/guidance"
            )
        )
        self.assertFalse(
            database_service._has_verified_rate_source(
                "[verified]; Source: https://agritech.tnau.ac.in/guidance"
            )
        )
        self.assertFalse(
            database_service._has_verified_rate_source(
                "Product/formulation: Mancozeb 75% WP; [verified]; "
                "Source: https://unverified.example/guidance"
            )
        )
        for unsafe_source in (
            "https://user:secret@agritech.tnau.ac.in/label",
            "https://agritech.tnau.ac.in:8443/label",
            "https://[malformed",
        ):
            self.assertFalse(
                database_service._has_verified_rate_source(
                    f"Product/formulation: Mancozeb 75% WP; [verified]; Source: {unsafe_source}"
                )
            )

    def test_verified_rate_metadata_requires_exact_product_and_source_reference(self):
        metadata = database_service.get_verified_application_rate_metadata(
            "Product/formulation: Copper hydroxide 53.8% DF; [verified]; "
            "Source: https://agritech.tnau.ac.in/approved-label."
        )
        self.assertEqual(metadata["product_formulation"], "Copper hydroxide 53.8% DF")
        self.assertEqual(metadata["source_url"], "https://agritech.tnau.ac.in/approved-label")

    def test_unverified_rate_is_removed_from_disease_details(self):
        connection = Mock()
        cursor = Mock()
        connection.cursor.return_value = cursor
        cursor.fetchone.return_value = (42, "Apple Scab", "Apple", "Description")
        cursor.fetchall.side_effect = [
            [],
            [],
            [],
            [
                (1, "Scab treatment", "chemical", "description", "instructions", "precautions",
                 10, "spray", "g/acre", 200, "per acre", "Source: https://example.org/label"),
                (2, "Verified treatment", "chemical", "description", "instructions", "precautions",
                 11, "spray", "g/acre", 150, "per acre",
                 "Product/formulation: Product 50% WP; [verified]; Source: https://agritech.tnau.ac.in/label"),
            ],
        ]

        with patch.object(database_service, "get_connection", return_value=connection):
            details = database_service.get_disease_details(42)

        rate_rows = details["treatments"]
        self.assertIsNone(rate_rows[0][6])
        self.assertEqual(rate_rows[1][6], 11)
        self.assertFalse(connection.commit.called)

    def test_disease_details_expose_product_formulation_and_source_for_verified_rate(self):
        with patch(
            "main.get_disease_details",
            return_value={
                "disease": (42, "Apple Scab", "Apple", "Description"),
                "symptoms": [],
                "causes": [],
                "prevention": [],
                "treatments": [
                    (1, "Scab treatment", "chemical", "desc", "instructions", "precautions",
                     11, "spray", "g/acre", 150, "per acre",
                     "Product/formulation: Product 50% WP; [verified]; "
                     "Source: https://agritech.tnau.ac.in/label"),
                    (2, "Unverified treatment", "chemical", "desc", "instructions", "precautions",
                     12, "spray", "g/acre", 999, "per acre",
                     "[verified]; Source: https://agritech.tnau.ac.in/label"),
                ],
            },
        ):
            response = TestClient(app).get("/api/diseases/42")

        self.assertEqual(response.status_code, 200)
        rates = [
            rate
            for treatment in response.json()["treatments"]
            for rate in treatment["application_rates"]
        ]
        self.assertEqual(len(rates), 1)
        self.assertTrue(rates[0]["verified"])
        self.assertEqual(rates[0]["disease_id"], 42)
        self.assertEqual(rates[0]["product_formulation"], "Product 50% WP")
        self.assertEqual(rates[0]["source_url"], "https://agritech.tnau.ac.in/label")

    def test_generated_notification_templates_are_not_returned_as_records(self):
        connection = Mock()
        cursor = Mock()
        connection.cursor.return_value = cursor
        cursor.fetchall.return_value = [
            (
                1,
                1,
                None,
                "Plant health monitoring reminder",
                "Review the current crop health and upload a fresh leaf image if symptoms have changed.",
                "monitoring",
                None,
                False,
                None,
            ),
            (6, 1, 12, "Saved alert", "Review this saved prediction.", "diagnosis", None, False, None),
        ]

        with patch.object(database_service, "get_connection", return_value=connection):
            notifications = database_service.get_notifications()

        self.assertEqual([item["id"] for item in notifications], [6])


if __name__ == "__main__":
    unittest.main()
