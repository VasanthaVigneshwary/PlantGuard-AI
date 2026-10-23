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
    """Return exact label coverage and rate-verification counts without writes."""
    classes = load_model_classes()
    connection = get_connection()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute("SET TRANSACTION READ ONLY;")
        cursor.execute(
            """
                SELECT prediction_key, COUNT(*)
                FROM diseases
                WHERE prediction_key IS NOT NULL
                GROUP BY prediction_key;
            """
        )
        mapping_counts = dict(cursor.fetchall())

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

        return {
            "model_class_count": len(classes),
            "mapped_class_count": sum(label in mapping_counts for label in classes),
            "missing_classes": missing_classes,
            "duplicate_mappings": duplicate_mappings,
            "mapping_coverage_complete": not missing_classes and not duplicate_mappings,
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
