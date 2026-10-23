from datetime import datetime, timezone
import re

from database import get_connection


def _normalize_prediction_part(value):
    normalized = value.replace("_", " ").replace("-", " ")
    return " ".join(normalized.lower().split())


def _has_verified_rate_source(notes):
    """Only expose a rate after a person marks it verified and adds a source URL."""
    if not isinstance(notes, str):
        return False
    return "[verified]" in notes.lower() and re.search(r"https://\S+", notes) is not None


_GENERATED_REMINDER_TEMPLATES = {
    (
        "Plant health monitoring reminder",
        "Review the current crop health and upload a fresh leaf image if symptoms have changed.",
    ),
    (
        "Regular crop inspection reminder",
        "Inspect leaves, stems, and soil routinely to catch early signs of stress or disease.",
    ),
    (
        "Disease prevention reminder",
        "Keep growing areas clean, improve airflow, and remove infected plant material promptly.",
    ),
    (
        "Treatment and application reminder",
        "Follow the recommended treatment instructions and product label before applying any control measures.",
    ),
    (
        "General plant-care reminder",
        "Maintain balanced watering, soil health, and crop spacing to support strong plant growth.",
    ),
}


def get_disease_details_by_prediction(prediction):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id FROM diseases
            WHERE prediction_key = %s
            LIMIT 1;
        """, (prediction,))
        row = cursor.fetchone()
        cursor.close()
        connection.close()
        if row:
            return get_disease_details(row[0])
    except Exception:
        try:
            connection.close()
        except Exception:
            pass

    prediction_parts = prediction.split("___", 1)

    if len(prediction_parts) != 2:
        return None

    crop_name = _normalize_prediction_part(prediction_parts[0])
    predicted_disease = _normalize_prediction_part(prediction_parts[1])

    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT d.id, d.name, c.name AS crop_name
            FROM diseases d
            JOIN crops c
                ON d.crop_id = c.id
            ORDER BY d.id;
        """)

        matching_disease_id = None

        for disease_id, disease_name, database_crop_name in cursor.fetchall():
            normalized_crop_name = _normalize_prediction_part(database_crop_name)
            normalized_disease_name = _normalize_prediction_part(disease_name)

            if normalized_crop_name != crop_name:
                continue

            candidates = {
                normalized_disease_name,
            }

            crop_prefix = f"{crop_name} "
            if normalized_disease_name.startswith(crop_prefix):
                candidates.add(normalized_disease_name[len(crop_prefix):])

            if predicted_disease in candidates:
                matching_disease_id = disease_id
                break

        if matching_disease_id is None:
            return None

    finally:
        cursor.close()
        connection.close()

    return get_disease_details(matching_disease_id)


def get_all_crops():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, name, scientific_name, description
            FROM crops
            ORDER BY id;
        """)

        crops = cursor.fetchall()

        return crops

    finally:
        cursor.close()
        connection.close()


def get_all_diseases():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                d.id,
                d.name,
                c.name AS crop_name,
                d.description
            FROM diseases d
            JOIN crops c
                ON d.crop_id = c.id
            ORDER BY d.id;
        """)

        diseases = cursor.fetchall()

        return diseases

    finally:
        cursor.close()
        connection.close()


def ensure_default_user():
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM users ORDER BY id LIMIT 1;")
        existing_user = cursor.fetchone()

        if existing_user is not None:
            return existing_user[0]

        cursor.execute(
            "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id;",
            ("Plant Guard User", "plantguard@local.test")
        )
        user_id = cursor.fetchone()[0]
        connection.commit()
        return user_id

    finally:
        cursor.close()
        connection.close()


def get_notifications():
    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                id,
                user_id,
                prediction_id,
                title,
                message,
                notification_type,
                scheduled_at,
                is_read,
                created_at
            FROM notifications
            ORDER BY created_at DESC, id DESC;
        """)

        rows = cursor.fetchall()
        notifications = []

        for row in rows:
            if (
                row[2] is None
                and row[6] is None
                and (row[3], row[4]) in _GENERATED_REMINDER_TEMPLATES
            ):
                continue
            notifications.append({
                "id": row[0],
                "user_id": row[1],
                "prediction_id": row[2],
                "title": row[3],
                "message": row[4],
                "notification_type": row[5],
                "scheduled_at": row[6].isoformat() if row[6] is not None else None,
                "is_read": bool(row[7]) if row[7] is not None else False,
                "created_at": row[8].isoformat() if row[8] is not None else None,
            })

        return notifications

    finally:
        cursor.close()
        connection.close()


def normalize_name(value):
    if value is None:
        return ""

    return " ".join(
        value.replace("_", " ").replace("-", " ").lower().split()
    )


def get_disease_by_name(disease_name, crop_name=None):
    disease_name = (disease_name or "").strip()

    if not disease_name:
        return None

    normalized_target_disease = normalize_name(disease_name)
    normalized_crop_name = normalize_name(crop_name)

    connection = get_connection()

    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                d.id,
                d.name,
                c.name AS crop_name,
                d.description
            FROM diseases d
            JOIN crops c
                ON d.crop_id = c.id
            ORDER BY d.id;
        """)

        for disease_id, db_disease_name, db_crop_name, description in cursor.fetchall():
            normalized_db_disease = normalize_name(db_disease_name)
            normalized_db_crop = normalize_name(db_crop_name)

            if normalized_crop_name and normalized_db_crop != normalized_crop_name:
                continue

            candidates = {
                normalized_db_disease,
            }

            if normalized_db_disease.startswith(f"{normalized_crop_name} "):
                candidates.add(normalized_db_disease[len(normalized_crop_name) + 1:])

            if normalized_target_disease in candidates:
                return get_disease_details(disease_id)

            if normalized_target_disease in normalized_db_disease:
                return get_disease_details(disease_id)

        return None

    finally:
        cursor.close()
        connection.close()


def get_disease_details(disease_id):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        # Disease and crop
        cursor.execute("""
            SELECT
                d.id,
                d.name,
                c.name AS crop_name,
                d.description
            FROM diseases d
            JOIN crops c
                ON d.crop_id = c.id
            WHERE d.id = %s;
        """, (disease_id,))

        disease = cursor.fetchone()

        if not disease:
            return None

        # Symptoms
        cursor.execute("""
            SELECT
                s.id,
                s.name,
                s.description
            FROM symptoms s
            JOIN disease_symptoms ds
                ON s.id = ds.symptom_id
            WHERE ds.disease_id = %s
            ORDER BY s.id;
        """, (disease_id,))

        symptoms = cursor.fetchall()

        # Causes
        cursor.execute("""
            SELECT
                c.id,
                c.name,
                c.description
            FROM causes c
            JOIN disease_causes dc
                ON c.id = dc.cause_id
            WHERE dc.disease_id = %s
            ORDER BY c.id;
        """, (disease_id,))

        causes = cursor.fetchall()

        # Prevention
        cursor.execute("""
            SELECT
                p.id,
                p.title,
                p.description
            FROM prevention p
            JOIN disease_prevention dp
                ON p.id = dp.prevention_id
            WHERE dp.disease_id = %s
            ORDER BY p.id;
        """, (disease_id,))

        prevention = cursor.fetchall()

        # Treatments and application rates
        cursor.execute("""
            SELECT
                t.id,
                t.name,
                t.type,
                t.description,
                t.instructions,
                t.precautions,
                ar.id,
                ar.application_method,
                ar.measurement_unit,
                ar.rate,
                ar.basis,
                ar.notes
            FROM treatments t
            LEFT JOIN application_rates ar
                ON t.id = ar.treatment_id
            WHERE t.disease_id = %s
            ORDER BY t.id, ar.id;
        """, (disease_id,))

        treatment_rows = cursor.fetchall()
        treatment_rows = [
            row if row[6] is None or _has_verified_rate_source(row[11])
            else tuple(row[:6]) + (None,) * 6
            for row in treatment_rows
        ]

        return {
            "disease": disease,
            "symptoms": symptoms,
            "causes": causes,
            "prevention": prevention,
            "treatments": treatment_rows
        }

    finally:
        cursor.close()
        connection.close()


def save_prediction(crop_id, disease_id, confidence, image_url=None, model_version="efficientnet_v2_s", user_id=None, crop_name=None):
    """Save a raw model score; the legacy API accepts and returns percentages."""
    score_percentage = float(confidence)
    if not 0 <= score_percentage <= 100:
        raise ValueError("Model score percentage must be between 0 and 100")
    score_fraction = score_percentage / 100.0
    connection = get_connection()
    try:
        cursor = connection.cursor()
        if crop_id is None and disease_id is not None:
            cursor.execute("SELECT crop_id FROM diseases WHERE id = %s LIMIT 1;", (disease_id,))
            disease_crop = cursor.fetchone()
            if disease_crop is not None:
                crop_id = disease_crop[0]
        if crop_id is None and crop_name:
            crop_aliases = {
                "corn (maize)": "Corn",
                "cherry (including sour)": "Cherry",
            }
            crop_name = crop_aliases.get(crop_name.strip().lower(), crop_name)
            cursor.execute(
                "SELECT id FROM crops WHERE lower(name) = lower(%s) LIMIT 1;",
                (crop_name,),
            )
            crop_row = cursor.fetchone()
            if crop_row is None:
                raise ValueError(f"No database crop mapping exists for {crop_name!r}")
            crop_id = crop_row[0]
        if crop_id is None:
            raise ValueError("A database crop mapping is required to save prediction history")
        if user_id is None:
            user_id = ensure_default_user()

        cursor.execute(
            """
                INSERT INTO predictions
                    (user_id, crop_id, disease_id, confidence, image_url, model_version, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """,
            (
                user_id,
                crop_id,
                disease_id,
                score_fraction,
                image_url,
                model_version,
                datetime.now(timezone.utc).replace(tzinfo=None),
            ),
        )
        prediction_id = cursor.fetchone()[0]
        connection.commit()
        return prediction_id
    finally:
        cursor.close()
        connection.close()


def get_prediction_history(limit=20):
    """Retrieve recent predictions from the database."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                p.id,
                p.confidence,
                p.image_url,
                p.model_version,
                p.created_at,
                c.name AS crop_name,
                d.name AS disease_name,
                d.id AS disease_id
            FROM predictions p
            LEFT JOIN crops c ON p.crop_id = c.id
            LEFT JOIN diseases d ON p.disease_id = d.id
            ORDER BY p.created_at DESC, p.id DESC
            LIMIT %s;
        """, (limit,))

        rows = cursor.fetchall()
        history = []
        for r in rows:
            history.append({
                "id": r[0],
                "confidence": float(r[1]) * 100 if r[1] is not None else None,
                "image_url": r[2],
                "model_version": r[3],
                "created_at": r[4].isoformat() if r[4] is not None else None,
                "crop_name": r[5] or "Unknown",
                "disease_name": r[6] or "Unknown",
                "disease_id": r[7]
            })
        return history
    finally:
        cursor.close()
        connection.close()
