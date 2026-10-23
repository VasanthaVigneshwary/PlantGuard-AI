"""Read-only audit of model labels against the PostgreSQL knowledge base."""

import json
from pathlib import Path

from database import get_connection
from services.database_service import _has_verified_rate_source


CLASSES_PATH = Path(__file__).resolve().parent / "ml" / "models" / "classes.json"


def load_model_classes():
    """Read the ordered output labels without loading the inference runtime."""
    with CLASSES_PATH.open("r", encoding="utf-8") as class_file:
        metadata = json.load(class_file)
    classes = metadata.get("classes")
    if not isinstance(classes, list) or not all(isinstance(item, str) for item in classes):
        raise ValueError(f"Invalid class list in {CLASSES_PATH}")
    if not classes or len(classes) != len(set(classes)):
        raise ValueError("Model class labels must be non-empty and unique")
    return classes


def audit_knowledge_base():
    """Return class, knowledge-detail, and rate coverage without writes."""
    classes = load_model_classes()
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute("SET TRANSACTION READ ONLY;")
        cursor.execute(
            """
                SELECT
                    d.prediction_key,
                    COUNT(DISTINCT d.id) AS disease_count,
                    COUNT(DISTINCT d.id) FILTER (WHERE d.description IS NOT NULL),
                    COUNT(DISTINCT ds.symptom_id),
                    COUNT(DISTINCT dc.cause_id),
                    COUNT(DISTINCT t.id),
                    COUNT(DISTINCT dp.prevention_id)
                FROM diseases d
                LEFT JOIN disease_symptoms ds ON ds.disease_id = d.id
                LEFT JOIN disease_causes dc ON dc.disease_id = d.id
                LEFT JOIN treatments t ON t.disease_id = d.id
                LEFT JOIN disease_prevention dp ON dp.disease_id = d.id
                WHERE d.prediction_key IS NOT NULL
                GROUP BY d.prediction_key;
            """
        )
        mapping_rows = cursor.fetchall()
        mapping_counts = {row[0]: row[1] for row in mapping_rows}
        detail_indices = {
            "description": 2,
            "symptoms": 3,
            "causes": 4,
            "treatments": 5,
            "prevention": 6,
        }
        details_by_class = {row[0]: row for row in mapping_rows}

        cursor.execute("SELECT notes FROM application_rates;")
        rate_notes = [row[0] for row in cursor.fetchall()]

        missing_classes = [label for label in classes if label not in mapping_counts]
        duplicate_mappings = {
            label: mapping_counts[label]
            for label in classes
            if mapping_counts.get(label, 0) > 1
        }
        unverified_rates = sum(
            not _has_verified_rate_source(notes) for notes in rate_notes
        )
        missing_class_details = {
            category: [
                label for label in classes
                if label in details_by_class and details_by_class[label][index] == 0
            ]
            for category, index in detail_indices.items()
        }
        detail_coverage = {
            category: sum(
                label in details_by_class and details_by_class[label][index] > 0
                for label in classes
            )
            for category, index in detail_indices.items()
        }

        return {
            "model_class_count": len(classes),
            "mapped_class_count": sum(label in mapping_counts for label in classes),
            "missing_classes": missing_classes,
            "duplicate_mappings": duplicate_mappings,
            "mapping_coverage_complete": not missing_classes and not duplicate_mappings,
            "detail_coverage_by_class": detail_coverage,
            "classes_missing_details": missing_class_details,
            "application_rate_count": len(rate_notes),
            "unverified_application_rate_count": unverified_rates,
        }
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def main():
    report = audit_knowledge_base()
    print(json.dumps(report, indent=2))
    return 0 if report["mapping_coverage_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
