"""Database-isolated tests for the plant upload API."""

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

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
                "[verified] https://agriculture.example/guidance"
            )
        )
        self.assertFalse(database_service._has_verified_rate_source("Source: TNAU Agritech Portal"))
        self.assertFalse(
            database_service._has_verified_rate_source(
                "[verified] http://agriculture.example/guidance"
            )
        )

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
