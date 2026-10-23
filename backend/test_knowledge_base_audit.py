"""Tests for the non-mutating model/database coverage audit."""

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@127.0.0.1:1/test")

import audit_knowledge_base  # noqa: E402


class KnowledgeBaseAuditTests(unittest.TestCase):
    def make_connection(self, mapping_details, rate_notes):
        connection = Mock()
        cursor = Mock()
        connection.cursor.return_value = cursor
        cursor.fetchall.side_effect = [mapping_details, [(note,) for note in rate_notes]]
        return connection, cursor

    def test_reports_complete_coverage_and_unverified_rate_count_read_only(self):
        connection, cursor = self.make_connection(
            [
                ("Apple___healthy", 1, 1, 2, 1, 1, 2),
                ("Tomato___Early_blight", 1, 1, 3, 2, 1, 1),
            ],
            ["[verified] https://example.org/label", "Source: extension guide"],
        )
        with (
            patch.object(audit_knowledge_base, "load_model_classes", return_value=[
                "Apple___healthy", "Tomato___Early_blight"
            ]),
            patch.object(audit_knowledge_base, "get_connection", return_value=connection),
        ):
            report = audit_knowledge_base.audit_knowledge_base()

        self.assertEqual(report["mapped_class_count"], 2)
        self.assertEqual(report["missing_classes"], [])
        self.assertEqual(report["duplicate_mappings"], {})
        self.assertTrue(report["mapping_coverage_complete"])
        self.assertEqual(report["detail_coverage_by_class"]["symptoms"], 2)
        self.assertEqual(report["classes_missing_details"]["treatments"], [])
        self.assertEqual(report["application_rate_count"], 2)
        self.assertEqual(report["unverified_application_rate_count"], 1)
        self.assertEqual(cursor.execute.call_args_list[0].args[0], "SET TRANSACTION READ ONLY;")
        connection.commit.assert_not_called()
        connection.rollback.assert_not_called()
        connection.close.assert_called_once()

    def test_reports_missing_and_duplicate_model_labels(self):
        connection, _ = self.make_connection(
            [("Apple___healthy", 2, 1, 0, 0, 0, 0)],
            [],
        )
        with (
            patch.object(audit_knowledge_base, "load_model_classes", return_value=[
                "Apple___healthy", "Tomato___healthy"
            ]),
            patch.object(audit_knowledge_base, "get_connection", return_value=connection),
        ):
            report = audit_knowledge_base.audit_knowledge_base()

        self.assertEqual(report["missing_classes"], ["Tomato___healthy"])
        self.assertEqual(report["duplicate_mappings"], {"Apple___healthy": 2})
        self.assertFalse(report["mapping_coverage_complete"])
        self.assertEqual(report["classes_missing_details"]["symptoms"], ["Apple___healthy"])
        self.assertEqual(report["detail_coverage_by_class"]["description"], 1)


if __name__ == "__main__":
    unittest.main()
